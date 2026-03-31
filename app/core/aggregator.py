import asyncio
import logging
from dataclasses import dataclass

from mcp import types as mcp_types

from app.core.client_pool import ClientPool
from app.utils.namespace import NAMESPACE_SEPARATOR, add_namespace, parse_namespace

logger = logging.getLogger(__name__)


class ToolNotFoundError(Exception):
    pass


class ServerUnavailableError(Exception):
    pass


@dataclass
class NamespacedTool:
    original_name: str
    namespaced_name: str
    server_id: int
    namespace: str
    tool_schema: mcp_types.Tool


@dataclass
class NamespacedResource:
    original_uri: str
    namespaced_uri: str
    server_id: int
    namespace: str
    resource: mcp_types.Resource


@dataclass
class NamespacedPrompt:
    original_name: str
    namespaced_name: str
    server_id: int
    namespace: str
    prompt: mcp_types.Prompt


class Aggregator:
    """Aggregates tools/resources/prompts from all MCP servers with namespace prefixes."""

    def __init__(self, client_pool: ClientPool):
        self._pool = client_pool
        self._tools: dict[str, NamespacedTool] = {}
        self._resources: dict[str, NamespacedResource] = {}
        self._prompts: dict[str, NamespacedPrompt] = {}
        self._lock = asyncio.Lock()

    async def refresh(self):
        async with self._lock:
            new_tools = {}
            new_resources = {}
            new_prompts = {}

            for conn in self._pool.all_connections():
                if not conn.is_connected:
                    continue
                try:
                    tools = await conn.list_tools()
                    for tool in tools:
                        ns_name = add_namespace(conn.namespace, tool.name)
                        new_tools[ns_name] = NamespacedTool(
                            original_name=tool.name,
                            namespaced_name=ns_name,
                            server_id=conn.server_id,
                            namespace=conn.namespace,
                            tool_schema=mcp_types.Tool(
                                name=ns_name,
                                description=f"[{conn.namespace}] {tool.description or ''}",
                                inputSchema=tool.inputSchema,
                            ),
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to list tools from '{conn.namespace}': {e}"
                    )

                try:
                    resources = await conn.list_resources()
                    for res in resources:
                        ns_uri = f"{conn.namespace}://{res.uri}"
                        new_resources[ns_uri] = NamespacedResource(
                            original_uri=str(res.uri),
                            namespaced_uri=ns_uri,
                            server_id=conn.server_id,
                            namespace=conn.namespace,
                            resource=res,
                        )
                except Exception as e:
                    logger.debug(
                        f"Failed to list resources from '{conn.namespace}': {e}"
                    )

                try:
                    prompts = await conn.list_prompts()
                    for prompt in prompts:
                        ns_name = add_namespace(conn.namespace, prompt.name)
                        new_prompts[ns_name] = NamespacedPrompt(
                            original_name=prompt.name,
                            namespaced_name=ns_name,
                            server_id=conn.server_id,
                            namespace=conn.namespace,
                            prompt=mcp_types.Prompt(
                                name=ns_name,
                                description=f"[{conn.namespace}] {prompt.description or ''}",
                                arguments=prompt.arguments,
                            ),
                        )
                except Exception as e:
                    logger.debug(
                        f"Failed to list prompts from '{conn.namespace}': {e}"
                    )

            self._tools = new_tools
            self._resources = new_resources
            self._prompts = new_prompts
            logger.info(
                f"Aggregator refreshed: {len(new_tools)} tools, "
                f"{len(new_resources)} resources, {len(new_prompts)} prompts"
            )

    async def refresh_one(self, server_id: int):
        conn = self._pool.get(server_id)
        if not conn or not conn.is_connected:
            return

        async with self._lock:
            # Remove old entries for this server
            self._tools = {
                k: v for k, v in self._tools.items() if v.server_id != server_id
            }
            self._resources = {
                k: v for k, v in self._resources.items() if v.server_id != server_id
            }
            self._prompts = {
                k: v for k, v in self._prompts.items() if v.server_id != server_id
            }

            # Add new entries
            try:
                tools = await conn.list_tools()
                for tool in tools:
                    ns_name = add_namespace(conn.namespace, tool.name)
                    self._tools[ns_name] = NamespacedTool(
                        original_name=tool.name,
                        namespaced_name=ns_name,
                        server_id=conn.server_id,
                        namespace=conn.namespace,
                        tool_schema=mcp_types.Tool(
                            name=ns_name,
                            description=f"[{conn.namespace}] {tool.description or ''}",
                            inputSchema=tool.inputSchema,
                        ),
                    )
            except Exception as e:
                logger.warning(f"Failed to refresh tools for server {server_id}: {e}")

            try:
                resources = await conn.list_resources()
                for res in resources:
                    ns_uri = f"{conn.namespace}://{res.uri}"
                    self._resources[ns_uri] = NamespacedResource(
                        original_uri=str(res.uri),
                        namespaced_uri=ns_uri,
                        server_id=conn.server_id,
                        namespace=conn.namespace,
                        resource=res,
                    )
            except Exception:
                pass

            try:
                prompts = await conn.list_prompts()
                for prompt in prompts:
                    ns_name = add_namespace(conn.namespace, prompt.name)
                    self._prompts[ns_name] = NamespacedPrompt(
                        original_name=prompt.name,
                        namespaced_name=ns_name,
                        server_id=conn.server_id,
                        namespace=conn.namespace,
                        prompt=mcp_types.Prompt(
                            name=ns_name,
                            description=f"[{conn.namespace}] {prompt.description or ''}",
                            arguments=prompt.arguments,
                        ),
                    )
            except Exception:
                pass

    def remove_server(self, server_id: int):
        self._tools = {
            k: v for k, v in self._tools.items() if v.server_id != server_id
        }
        self._resources = {
            k: v for k, v in self._resources.items() if v.server_id != server_id
        }
        self._prompts = {
            k: v for k, v in self._prompts.items() if v.server_id != server_id
        }

    def list_all_tools(self) -> list[mcp_types.Tool]:
        return [nt.tool_schema for nt in self._tools.values()]

    def list_all_resources(self) -> list[mcp_types.Resource]:
        return [nr.resource for nr in self._resources.values()]

    def list_all_prompts(self) -> list[mcp_types.Prompt]:
        return [np.prompt for np in self._prompts.values()]

    def list_server_tools(self, server_id: int) -> list[dict]:
        return [
            {
                "name": nt.namespaced_name,
                "original_name": nt.original_name,
                "description": nt.tool_schema.description,
                "input_schema": nt.tool_schema.inputSchema,
            }
            for nt in self._tools.values()
            if nt.server_id == server_id
        ]

    def list_server_resources(self, server_id: int) -> list[dict]:
        return [
            {
                "uri": nr.namespaced_uri,
                "original_uri": nr.original_uri,
                "name": nr.resource.name,
                "description": nr.resource.description,
            }
            for nr in self._resources.values()
            if nr.server_id == server_id
        ]

    def get_tools_count(self, server_id: int) -> int:
        return sum(1 for nt in self._tools.values() if nt.server_id == server_id)

    def resolve_tool(self, namespaced_name: str) -> NamespacedTool | None:
        return self._tools.get(namespaced_name)

    def resolve_prompt(self, namespaced_name: str) -> NamespacedPrompt | None:
        return self._prompts.get(namespaced_name)

    async def call_tool(
        self, namespaced_name: str, arguments: dict
    ) -> mcp_types.CallToolResult:
        nt = self.resolve_tool(namespaced_name)
        if not nt:
            raise ToolNotFoundError(f"Tool not found: {namespaced_name}")

        conn = self._pool.get(nt.server_id)
        if not conn or not conn.is_connected:
            raise ServerUnavailableError(
                f"Server '{nt.namespace}' is not available"
            )

        return await conn.call_tool(nt.original_name, arguments)

    async def read_resource(self, namespaced_uri: str):
        nr = self._resources.get(namespaced_uri)
        if not nr:
            raise ToolNotFoundError(f"Resource not found: {namespaced_uri}")

        conn = self._pool.get(nr.server_id)
        if not conn or not conn.is_connected:
            raise ServerUnavailableError(
                f"Server '{nr.namespace}' is not available"
            )

        return await conn.read_resource(nr.original_uri)

    async def get_prompt(self, namespaced_name: str, arguments: dict | None = None):
        np = self.resolve_prompt(namespaced_name)
        if not np:
            raise ToolNotFoundError(f"Prompt not found: {namespaced_name}")

        conn = self._pool.get(np.server_id)
        if not conn or not conn.is_connected:
            raise ServerUnavailableError(
                f"Server '{np.namespace}' is not available"
            )

        return await conn.get_prompt(np.original_name, arguments)
