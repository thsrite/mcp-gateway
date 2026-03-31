import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import get_server
from app.db.engine import get_session
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_aggregator():
    from app.main import aggregator
    return aggregator


@router.get("", response_model=ApiResponse)
async def api_list_all_tools():
    aggregator = _get_aggregator()
    tools = aggregator.list_all_tools()
    result = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema,
        }
        for t in tools
    ]
    return ApiResponse(data=result)


@router.get("/resources", response_model=ApiResponse)
async def api_list_all_resources():
    aggregator = _get_aggregator()
    resources = aggregator.list_all_resources()
    result = [
        {
            "uri": str(r.uri),
            "name": r.name,
            "description": r.description,
        }
        for r in resources
    ]
    return ApiResponse(data=result)
