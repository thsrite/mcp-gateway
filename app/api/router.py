from fastapi import APIRouter, Depends

from app.api.auth import get_current_user, router as auth_router
from app.api.mcp_servers import router as servers_router
from app.api.mcp_tools import router as tools_router
from app.api.logs import router as logs_router
from app.api.system import router as system_router

api_router = APIRouter()

# Auth routes are public (login, setup, status)
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# Protected routes require auth (when enabled)
protected = [Depends(get_current_user)]
api_router.include_router(servers_router, prefix="/servers", tags=["servers"], dependencies=protected)
api_router.include_router(tools_router, prefix="/tools", tags=["tools"], dependencies=protected)
api_router.include_router(logs_router, tags=["logs"], dependencies=protected)
api_router.include_router(system_router, prefix="/system", tags=["system"], dependencies=protected)
