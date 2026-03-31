import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, settings
from app.db.engine import close_db, init_db

logger = logging.getLogger(__name__)

# Global instances - initialized in lifespan
github_manager = None
process_manager = None
client_pool = None
aggregator = None
gateway_server = None
scheduler = None
log_collector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global github_manager, process_manager, client_pool, aggregator
    global gateway_server, scheduler, log_collector

    from app.core.aggregator import Aggregator
    from app.core.client_pool import ClientPool
    from app.core.gateway_server import GatewayServer
    from app.core.github_manager import GitHubManager
    from app.core.log_collector import LogCollector
    from app.core.process_manager import ProcessManager
    from app.core.scheduler import Scheduler

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize core modules
    repos_dir = BASE_DIR / settings.repos.base_dir
    repos_dir.mkdir(parents=True, exist_ok=True)

    log_collector = LogCollector(max_lines_per_server=settings.log.max_lines_per_server)
    github_manager = GitHubManager(repos_dir=repos_dir)
    process_manager = ProcessManager()
    client_pool = ClientPool(log_collector=log_collector)
    aggregator = Aggregator(client_pool=client_pool, log_collector=log_collector)
    gateway_server = GatewayServer(aggregator=aggregator)

    # Restore enabled servers
    await _restore_servers()

    # Start MCP endpoint on dedicated port
    mcp_port = settings.server.port + 1  # 9001
    await gateway_server.start(host=settings.server.host, port=mcp_port)

    # Start scheduler
    scheduler = Scheduler(
        github_manager=github_manager,
        client_pool=client_pool,
        aggregator=aggregator,
        log_collector=log_collector,
    )
    scheduler.start()
    logger.info("Scheduler started")

    logger.info(
        f"MCP Gateway running:\n"
        f"  Web UI:       http://{settings.server.host}:{settings.server.port}\n"
        f"  MCP Endpoint: http://{settings.server.host}:{mcp_port}/mcp"
    )

    yield

    # Shutdown
    scheduler.stop()
    await gateway_server.stop()
    await client_pool.disconnect_all()
    await close_db()
    logger.info("MCP Gateway shut down")


async def _restore_servers():
    from app.db.engine import async_session_factory
    from app.db.crud import list_enabled_servers

    async with async_session_factory() as session:
        servers = await list_enabled_servers(session)
        for server in servers:
            try:
                await client_pool.add(
                    server_id=server.id,
                    namespace=server.name,
                    command=server.command,
                    args=server.args or [],
                    cwd=server.local_path,
                    env=server.env,
                )
                await aggregator.refresh_one(server.id)
                server.status = "running"
                await session.commit()
                logger.info(f"Restored MCP server: {server.name}")
            except Exception as e:
                server.status = "error"
                await session.commit()
                logger.error(f"Failed to restore MCP server {server.name}: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title="MCP Gateway",
        description="Aggregate multiple MCP servers into a unified HTTP endpoint",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.router import api_router
    app.include_router(api_router, prefix="/api")

    # Serve frontend static files (if built)
    frontend_dist = BASE_DIR / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app
