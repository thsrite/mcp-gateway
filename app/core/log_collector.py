import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    timestamp: str
    server_id: int
    level: str
    message: str


class LogCollector:
    def __init__(self, max_lines_per_server: int = 1000):
        self._max_lines = max_lines_per_server
        self._logs: dict[int, deque[LogEntry]] = {}
        self._subscribers: dict[int, list[asyncio.Queue]] = {}
        self._tasks: dict[int, asyncio.Task] = {}

    async def start_collecting(self, server_id: int, stderr_stream: asyncio.StreamReader):
        self._logs.setdefault(server_id, deque(maxlen=self._max_lines))
        task = asyncio.create_task(self._collect_loop(server_id, stderr_stream))
        self._tasks[server_id] = task

    async def _collect_loop(self, server_id: int, stderr_stream: asyncio.StreamReader):
        try:
            async for line in stderr_stream:
                text = line.decode("utf-8", errors="replace").rstrip()
                if not text:
                    continue
                entry = LogEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    server_id=server_id,
                    level="stderr",
                    message=text,
                )
                self._logs[server_id].append(entry)
                for queue in self._subscribers.get(server_id, []):
                    try:
                        queue.put_nowait(entry)
                    except asyncio.QueueFull:
                        pass
        except Exception as e:
            logger.debug(f"Log collection ended for server {server_id}: {e}")

    def stop_collecting(self, server_id: int):
        task = self._tasks.pop(server_id, None)
        if task and not task.done():
            task.cancel()

    def get_logs(self, server_id: int, limit: int = 100) -> list[dict]:
        logs = self._logs.get(server_id, deque())
        entries = list(logs)[-limit:]
        return [
            {
                "timestamp": e.timestamp,
                "server_id": e.server_id,
                "level": e.level,
                "message": e.message,
            }
            for e in entries
        ]

    def subscribe(self, server_id: int) -> asyncio.Queue:
        queue = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(server_id, []).append(queue)
        return queue

    def unsubscribe(self, server_id: int, queue: asyncio.Queue):
        subs = self._subscribers.get(server_id, [])
        if queue in subs:
            subs.remove(queue)

    def clear_logs(self, server_id: int):
        self._logs.pop(server_id, None)
