import asyncio
import logging
import uuid

from fastapi import FastAPI, Request
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp import types
from starlette.responses import JSONResponse, Response

from app.core.aggregator import Aggregator

logger = logging.getLogger(__name__)


class _StreamableSession:
    """Manages a single Streamable HTTP session lifecycle."""

    def __init__(self, session_id: str, server: Server):
        self.session_id = session_id
        self.transport = StreamableHTTPServerTransport(
            mcp_session_id=session_id,
            is_json_response_enabled=True,
        )
        self._server = server
        self._task: asyncio.Task | None = None

    async def start(self):
        self._task = asyncio.create_task(self._run())
        await asyncio.sleep(0.05)

    async def _run(self):
        try:
            async with self.transport.connect() as (read_stream, write_stream):
                await self._server.run(
                    read_stream,
                    write_stream,
                    self._server.create_initialization_options(),
                )
        except Exception as e:
            logger.debug(f"Streamable session {self.session_id} ended: {e}")

    async def stop(self):
        self.transport.terminate()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass


class GatewayServer:
    """Exposes aggregated MCP tools/resources/prompts via HTTP/SSE and Streamable HTTP."""

    def __init__(self, aggregator: Aggregator):
        self._aggregator = aggregator
        self._server = Server("mcp-gateway")
        self._sse_transport: SseServerTransport | None = None
        self._sessions: dict[str, _StreamableSession] = {}
        self._setup_handlers()

    def _setup_handlers(self):
        @self._server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return self._aggregator.list_all_tools()

        @self._server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None = None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            result = await self._aggregator.call_tool(name, arguments or {})
            return result.content

        @self._server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            return self._aggregator.list_all_resources()

        @self._server.read_resource()
        async def handle_read_resource(uri) -> str | bytes:
            result = await self._aggregator.read_resource(str(uri))
            if result.contents:
                content = result.contents[0]
                if hasattr(content, "text"):
                    return content.text
                if hasattr(content, "blob"):
                    return content.blob
            return ""

        @self._server.list_prompts()
        async def handle_list_prompts() -> list[types.Prompt]:
            return self._aggregator.list_all_prompts()

        @self._server.get_prompt()
        async def handle_get_prompt(
            name: str, arguments: dict | None = None
        ) -> types.GetPromptResult:
            return await self._aggregator.get_prompt(name, arguments)

    def mount(self, app: FastAPI):
        """Initialize transports. Called during lifespan startup."""
        self._sse_transport = SseServerTransport("/messages/")
        app.mount("/messages", app=self._sse_transport.handle_post_message)
        logger.info("MCP endpoints ready: SSE at /sse, Streamable HTTP at /mcp")

    async def handle_sse(self, scope, receive, send):
        """Handle SSE endpoint via raw ASGI."""
        async with self._sse_transport.connect_sse(scope, receive, send) as streams:
            await self._server.run(
                streams[0],
                streams[1],
                self._server.create_initialization_options(),
            )

    async def handle_streamable_http(self, scope, receive, send):
        """Handle Streamable HTTP endpoint via raw ASGI."""
        # Ensure Accept header includes application/json to pass SDK validation.
        headers = dict(scope.get("headers", []))
        if b"accept" not in headers:
            scope = dict(scope)
            scope["headers"] = list(scope["headers"]) + [
                (b"accept", b"application/json, text/event-stream")
            ]
        else:
            accept_val = headers[b"accept"].decode()
            if "application/json" not in accept_val:
                scope = dict(scope)
                new_headers = [
                    (k, f"{v.decode()}, application/json".encode()) if k == b"accept" else (k, v)
                    for k, v in scope["headers"]
                ]
                scope["headers"] = new_headers

        request = Request(scope, receive, send)
        session_id = request.headers.get("mcp-session-id")

        if request.method == "POST" and not session_id:
            new_id = uuid.uuid4().hex
            session = _StreamableSession(new_id, self._server)
            self._sessions[new_id] = session
            await session.start()
            logger.info(f"New Streamable HTTP session: {new_id}")
            await session.transport.handle_request(scope, receive, send)
            return

        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]

            if request.method == "DELETE":
                await session.stop()
                self._sessions.pop(session_id, None)
                logger.info(f"Terminated session: {session_id}")
                response = Response(status_code=200)
                await response(scope, receive, send)
                return

            await session.transport.handle_request(scope, receive, send)
            return

        response = JSONResponse({"error": "Invalid or missing session"}, status_code=400)
        await response(scope, receive, send)
