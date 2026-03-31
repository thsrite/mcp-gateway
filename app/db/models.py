from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=func.now())


class McpServerModel(Base):
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    github_url = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=False)
    project_type = Column(String(20), nullable=True)
    command = Column(String(200), nullable=False)
    args = Column(JSON, default=list)
    env = Column(JSON, default=dict)
    enabled = Column(Boolean, default=True)
    auto_update = Column(Boolean, default=True)
    auto_restart = Column(Boolean, default=True)
    status = Column(String(20), default="stopped")
    last_commit = Column(String(40), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "github_url": self.github_url,
            "local_path": self.local_path,
            "project_type": self.project_type,
            "command": self.command,
            "args": self.args or [],
            "env": self.env or {},
            "enabled": self.enabled,
            "auto_update": self.auto_update,
            "auto_restart": self.auto_restart,
            "status": self.status,
            "last_commit": self.last_commit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
