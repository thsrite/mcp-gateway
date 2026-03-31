import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class McpProcessInfo:
    server_id: int
    command: str
    args: list[str]
    cwd: str
    status: str = "stopped"
    started_at: datetime | None = None
    restart_count: int = 0


class ProcessManager:
    """Tracks MCP server process metadata.

    Actual process lifecycle is managed by ClientPool via stdio_client.
    This class maintains status information and restart counts.
    """

    def __init__(self):
        self._processes: dict[int, McpProcessInfo] = {}

    def register(
        self, server_id: int, command: str, args: list[str], cwd: str
    ) -> McpProcessInfo:
        info = McpProcessInfo(
            server_id=server_id,
            command=command,
            args=args,
            cwd=cwd,
            status="running",
            started_at=datetime.utcnow(),
        )
        self._processes[server_id] = info
        return info

    def mark_stopped(self, server_id: int):
        info = self._processes.get(server_id)
        if info:
            info.status = "stopped"

    def mark_error(self, server_id: int):
        info = self._processes.get(server_id)
        if info:
            info.status = "error"

    def mark_restarted(self, server_id: int):
        info = self._processes.get(server_id)
        if info:
            info.status = "running"
            info.restart_count += 1
            info.started_at = datetime.utcnow()

    def unregister(self, server_id: int):
        self._processes.pop(server_id, None)

    def get_info(self, server_id: int) -> McpProcessInfo | None:
        return self._processes.get(server_id)

    def get_all(self) -> dict[int, McpProcessInfo]:
        return dict(self._processes)
