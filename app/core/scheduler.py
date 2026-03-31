import logging
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.core.aggregator import Aggregator
from app.core.client_pool import ClientPool
from app.core.github_manager import GitHubManager
from app.core.log_collector import LogCollector

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(
        self,
        github_manager: GitHubManager,
        client_pool: ClientPool,
        aggregator: Aggregator,
        log_collector: LogCollector,
    ):
        self._github = github_manager
        self._pool = client_pool
        self._aggregator = aggregator
        self._log_collector = log_collector
        self._scheduler = AsyncIOScheduler()

    def start(self):
        self._scheduler.add_job(
            self._check_updates,
            "interval",
            minutes=settings.scheduler.update_interval_minutes,
            id="git_pull_check",
        )
        self._scheduler.add_job(
            self._health_check,
            "interval",
            seconds=settings.scheduler.health_check_interval_seconds,
            id="health_check",
        )
        self._scheduler.start()
        logger.info(
            f"Scheduler started: update every {settings.scheduler.update_interval_minutes}min, "
            f"health check every {settings.scheduler.health_check_interval_seconds}s"
        )

    def stop(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    async def _check_updates(self):
        from app.db.crud import list_auto_update_servers, update_server
        from app.db.engine import async_session_factory

        logger.info("Checking for git updates...")
        async with async_session_factory() as session:
            servers = await list_auto_update_servers(session)
            for server in servers:
                if not server.github_url:
                    continue
                try:
                    result = await self._github.pull(Path(server.local_path))
                    if result.has_updates:
                        logger.info(f"Updates found for {server.name}")
                        await update_server(
                            session, server.id, last_commit=result.commit_after
                        )
                        # Restart if running
                        conn = self._pool.get(server.id)
                        if conn and conn.is_connected:
                            await self._pool.reconnect(server.id)
                            await self._aggregator.refresh_one(server.id)
                            logger.info(f"Restarted {server.name} after update")
                except Exception as e:
                    logger.error(f"Update check failed for {server.name}: {e}")

    async def _health_check(self):
        from app.db.crud import get_server, update_server
        from app.db.engine import async_session_factory

        for conn in self._pool.all_connections():
            if not conn.is_connected:
                logger.warning(f"Server '{conn.namespace}' is disconnected")
                async with async_session_factory() as session:
                    server = await get_server(session, conn.server_id)
                    if server and server.auto_restart and server.enabled:
                        try:
                            logger.info(f"Auto-restarting '{conn.namespace}'...")
                            await self._pool.reconnect(conn.server_id)
                            await self._aggregator.refresh_one(conn.server_id)
                            await update_server(session, conn.server_id, status="running")
                        except Exception as e:
                            await update_server(session, conn.server_id, status="error")
                            logger.error(
                                f"Auto-restart failed for '{conn.namespace}': {e}"
                            )
                    else:
                        await update_server(session, conn.server_id, status="error")
