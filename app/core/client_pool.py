import asyncio
import logging
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.log_collector import LogCollector

logger = logging.getLogger(__name__)


class ClientConnection:
    """A long-lived connection to a single STDIO MCP Server."""

    def __init__(
        self,
        server_id: int,
        namespace: str,
        params: StdioServerParameters,
        log_collector: LogCollector | None = None,
    ):
        self.server_id = server_id
        self.namespace = namespace
        self.params = params
        self.session: ClientSession | None = None
        self._log_collector = log_collector
        self._shutdown_event = asyncio.Event()
        self._ready_event = asyncio.Event()
        self._error: Exception | None = None
        self._task: asyncio.Task | None = None

    async def connect(self, timeout: float = 30.0):
        self._shutdown_event.clear()
        self._ready_event.clear()
        self._error = None
        self._task = asyncio.create_task(self._run())

        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self._shutdown_event.set()
            if self._task and not self._task.done():
                self._task.cancel()
            raise TimeoutError(
                f"Timeout connecting to MCP server '{self.namespace}' after {timeout}s"
            )

        if self._error:
            raise self._error

    async def _run(self):
        try:
            async with stdio_client(self.params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    self.session = session
                    await session.initialize()
                    logger.info(f"MCP session initialized for '{self.namespace}'")
                    self._ready_event.set()
                    await self._shutdown_event.wait()
        except Exception as e:
            self._error = e
            self._ready_event.set()  # Unblock waiter
            logger.error(f"MCP connection error for '{self.namespace}': {e}")
        finally:
            self.session = None

    async def disconnect(self):
        self._shutdown_event.set()
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()
        self.session = None
        logger.info(f"Disconnected from MCP server '{self.namespace}'")

    @property
    def is_connected(self) -> bool:
        return self.session is not None and not self._shutdown_event.is_set()

    async def list_tools(self):
        if not self.session:
            return []
        result = await self.session.list_tools()
        return result.tools

    async def list_resources(self):
        if not self.session:
            return []
        result = await self.session.list_resources()
        return result.resources

    async def list_prompts(self):
        if not self.session:
            return []
        result = await self.session.list_prompts()
        return result.prompts

    async def call_tool(self, name: str, arguments: dict):
        if not self.session:
            raise RuntimeError(f"Not connected to MCP server '{self.namespace}'")
        return await self.session.call_tool(name, arguments)

    async def read_resource(self, uri: str):
        if not self.session:
            raise RuntimeError(f"Not connected to MCP server '{self.namespace}'")
        return await self.session.read_resource(uri)

    async def get_prompt(self, name: str, arguments: dict | None = None):
        if not self.session:
            raise RuntimeError(f"Not connected to MCP server '{self.namespace}'")
        return await self.session.get_prompt(name, arguments)


def _build_env(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return env


class ClientPool:
    """Manages connections to all STDIO MCP Servers."""

    def __init__(self, log_collector: LogCollector | None = None):
        self._connections: dict[int, ClientConnection] = {}
        self._log_collector = log_collector
        self._lock = asyncio.Lock()

    async def add(
        self,
        server_id: int,
        namespace: str,
        command: str,
        args: list[str],
        cwd: str,
        env: dict[str, str] | None = None,
    ):
        async with self._lock:
            if server_id in self._connections:
                await self._connections[server_id].disconnect()

            params = StdioServerParameters(
                command=command,
                args=args,
                env=_build_env(env),
                cwd=cwd,
            )

            conn = ClientConnection(
                server_id=server_id,
                namespace=namespace,
                params=params,
                log_collector=self._log_collector,
            )
            await conn.connect()
            self._connections[server_id] = conn
            logger.info(f"Added MCP server to pool: {namespace} (id={server_id})")

    async def remove(self, server_id: int):
        async with self._lock:
            conn = self._connections.pop(server_id, None)
            if conn:
                await conn.disconnect()

    async def reconnect(self, server_id: int):
        async with self._lock:
            conn = self._connections.get(server_id)
            if not conn:
                return
            namespace = conn.namespace
            params = conn.params
            await conn.disconnect()

            new_conn = ClientConnection(
                server_id=server_id,
                namespace=namespace,
                params=params,
                log_collector=self._log_collector,
            )
            await new_conn.connect()
            self._connections[server_id] = new_conn
            logger.info(f"Reconnected MCP server: {namespace}")

    def get(self, server_id: int) -> ClientConnection | None:
        return self._connections.get(server_id)

    def all_connections(self) -> list[ClientConnection]:
        return list(self._connections.values())

    async def disconnect_all(self):
        async with self._lock:
            for conn in self._connections.values():
                try:
                    await conn.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting {conn.namespace}: {e}")
            self._connections.clear()
