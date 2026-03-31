import logging
from datetime import datetime, timedelta, timezone

import jwt
import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import BASE_DIR, settings
from app.db.crud import count_users, create_user, get_user_by_username, update_user_password
from app.db.engine import get_session
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth.token_expire_minutes)
    return jwt.encode(
        {"sub": username, "exp": expire},
        settings.auth.secret_key,
        algorithm="HS256",
    )


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.auth.secret_key, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_session),
):
    """Auth dependency: skips validation when auth is disabled."""
    if not settings.auth.enabled:
        return None

    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    username = verify_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await get_user_by_username(session, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/status", response_model=ApiResponse)
async def auth_status(session: AsyncSession = Depends(get_session)):
    """Return whether auth is enabled and whether initial setup is needed."""
    user_count = await count_users(session)
    return ApiResponse(data={
        "enabled": settings.auth.enabled,
        "initialized": user_count > 0,
    })


@router.post("/login", response_model=ApiResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    if not settings.auth.enabled:
        return ApiResponse(data={"token": "", "message": "Auth disabled"})

    user = await get_user_by_username(session, body.username)
    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(user.username)
    return ApiResponse(data={"token": token, "username": user.username})


@router.post("/setup", response_model=ApiResponse)
async def setup_admin(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    """Create initial admin user. Only works when no users exist."""
    user_count = await count_users(session)
    if user_count > 0:
        raise HTTPException(status_code=400, detail="Admin user already exists")

    if len(body.username) < 2 or len(body.password) < 4:
        raise HTTPException(status_code=400, detail="Username min 2 chars, password min 4 chars")

    hashed = pwd_context.hash(body.password)
    user = await create_user(session, body.username, hashed)
    token = create_token(user.username)
    logger.info(f"Admin user created: {user.username}")
    return ApiResponse(data={"token": token, "username": user.username})


@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not settings.auth.enabled or not current_user:
        raise HTTPException(status_code=400, detail="Auth is not enabled")

    if not pwd_context.verify(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    hashed = pwd_context.hash(body.new_password)
    await update_user_password(session, current_user.id, hashed)
    return ApiResponse(message="Password changed")


class AuthToggleRequest(BaseModel):
    enabled: bool


def _update_config_yaml(key_path: str, value):
    """Update a nested key in config.yaml and persist to disk."""
    config_path = BASE_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    keys = key_path.split(".")
    d = data
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value

    with open(config_path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)


@router.post("/toggle", response_model=ApiResponse)
async def toggle_auth(body: AuthToggleRequest, session: AsyncSession = Depends(get_session)):
    """Enable or disable authentication. When enabling, requires at least one user."""
    if body.enabled:
        user_count = await count_users(session)
        if user_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Please create an admin account first before enabling auth",
            )

    # Update runtime config
    settings.auth.enabled = body.enabled
    # Persist to config.yaml
    _update_config_yaml("auth.enabled", body.enabled)
    logger.info(f"Auth {'enabled' if body.enabled else 'disabled'} via API")
    return ApiResponse(data={"enabled": body.enabled})
