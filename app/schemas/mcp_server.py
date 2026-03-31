from pydantic import BaseModel


class ServerCreate(BaseModel):
    name: str | None = None
    github_url: str | None = None
    local_path: str | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    auto_update: bool = True
    auto_restart: bool = True


class ServerUpdate(BaseModel):
    name: str | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    enabled: bool | None = None
    auto_update: bool | None = None
    auto_restart: bool | None = None


class ServerResponse(BaseModel):
    id: int
    name: str
    github_url: str | None = None
    local_path: str
    project_type: str | None = None
    command: str
    args: list[str] = []
    env: dict[str, str] = {}
    enabled: bool = True
    auto_update: bool = True
    auto_restart: bool = True
    status: str = "stopped"
    last_commit: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    tools_count: int = 0
