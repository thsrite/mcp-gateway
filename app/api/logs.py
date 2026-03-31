import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import get_server
from app.db.engine import get_session
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_log_collector():
    from app.main import log_collector
    return log_collector


@router.get("/servers/{server_id}/logs", response_model=ApiResponse)
async def api_get_logs(
    server_id: int,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    log_collector = _get_log_collector()
    logs = log_collector.get_logs(server_id, limit=limit) if log_collector else []
    return ApiResponse(data=logs)


@router.get("/servers/{server_id}/logs/stream")
async def api_stream_logs(
    server_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    log_collector = _get_log_collector()
    if not log_collector:
        raise HTTPException(status_code=500, detail="Log collector not initialized")

    queue = log_collector.subscribe(server_id)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    entry = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(entry)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        finally:
            log_collector.unsubscribe(server_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
