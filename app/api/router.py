from fastapi import APIRouter

from app.api.mcp_servers import router as servers_router
from app.api.mcp_tools import router as tools_router
from app.api.logs import router as logs_router
from app.api.system import router as system_router

api_router = APIRouter()
api_router.include_router(servers_router, prefix="/servers", tags=["servers"])
api_router.include_router(tools_router, prefix="/tools", tags=["tools"])
api_router.include_router(logs_router, tags=["logs"])
api_router.include_router(system_router, prefix="/system", tags=["system"])
