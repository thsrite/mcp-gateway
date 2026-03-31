from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
            "gateway_endpoint": "/sse",
        }
    )
