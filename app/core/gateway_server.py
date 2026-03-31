import asyncio
import logging

from mcp.server.lowlevel import Server
from mcp import types

from app.core.aggregator import Aggregator

logger = logging.getLogger(__name__)


class GatewayServer:
    """Exposes aggregated MCP tools/resources/prompts as a standalone MCP HTTP server."""

    def __init__(self, aggregator: Aggregator):
        self._aggregator = aggregator
        self._server = Server("mcp-gateway")
        self._task: asyncio.Task | None = None
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

    async def start(self, host: str = "0.0.0.0", port: int = 9001):
        """Start the MCP server on a dedicated port using uvicorn."""
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from starlette.applications import Starlette
        from starlette.routing import Route
        import uvicorn

        session_manager = StreamableHTTPSessionManager(
            app=self._server,
            json_response=False,
            stateless=False,
        )

        # Build a standalone Starlette app
        from mcp.server.fastmcp.server import StreamableHTTPASGIApp
        http_app = StreamableHTTPASGIApp(session_manager)

        starlette_app = Starlette(
            routes=[Route("/mcp", endpoint=http_app, methods=["GET", "POST", "DELETE"])],
            lifespan=lambda app: session_manager.run(),
        )

        config = uvicorn.Config(
            starlette_app,
            host=host,
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        self._task = asyncio.create_task(server.serve())
        logger.info(f"MCP Gateway endpoint running at http://{host}:{port}/mcp")

    async def stop(self):
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            logger.info("MCP Gateway endpoint stopped")
