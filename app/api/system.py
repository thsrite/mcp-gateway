from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.crud import list_servers
from app.db.engine import get_session
from app.schemas.common import ApiResponse

router = APIRouter()


def _get_aggregator():
    from app.main import aggregator
    return aggregator


@router.get("/health", response_model=ApiResponse)
async def api_health():
    return ApiResponse(data={"status": "healthy"})


@router.get("/info", response_model=ApiResponse)
async def api_system_info(session: AsyncSession = Depends(get_session)):
    aggregator = _get_aggregator()
    servers = await list_servers(session)

    running = sum(1 for s in servers if s.status == "running")
    stopped = sum(1 for s in servers if s.status == "stopped")
    error = sum(1 for s in servers if s.status == "error")

    return ApiResponse(
        data={
            "total_servers": len(servers),
            "running": running,
            "stopped": stopped,
            "error": error,
            "total_tools": len(aggregator.list_all_tools()) if aggregator else 0,
            "total_resources": len(aggregator.list_all_resources()) if aggregator else 0,
            "total_prompts": len(aggregator.list_all_prompts()) if aggregator else 0,
            "mcp_port": settings.server.port + 1,
        }
    )


class SettingsUpdate(BaseModel):
    update_interval_minutes: int | None = None
    health_check_interval_seconds: int | None = None
    max_log_lines: int | None = None


@router.get("/settings", response_model=ApiResponse)
async def api_get_settings():
    return ApiResponse(data={
        "update_interval_minutes": settings.scheduler.update_interval_minutes,
        "health_check_interval_seconds": settings.scheduler.health_check_interval_seconds,
        "max_log_lines": settings.log.max_lines_per_server,
    })


@router.put("/settings", response_model=ApiResponse)
async def api_update_settings(body: SettingsUpdate):
    from app.api.auth import _update_config_yaml

    if body.update_interval_minutes is not None:
        settings.scheduler.update_interval_minutes = body.update_interval_minutes
        _update_config_yaml("scheduler.update_interval_minutes", body.update_interval_minutes)

    if body.health_check_interval_seconds is not None:
        settings.scheduler.health_check_interval_seconds = body.health_check_interval_seconds
        _update_config_yaml("scheduler.health_check_interval_seconds", body.health_check_interval_seconds)

    if body.max_log_lines is not None:
        settings.log.max_lines_per_server = body.max_log_lines
        _update_config_yaml("log.max_lines_per_server", body.max_log_lines)

    return ApiResponse(message="Settings saved")
