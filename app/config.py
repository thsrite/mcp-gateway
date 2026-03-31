from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 9000


class DatabaseConfig(BaseModel):
    url: str = "sqlite+aiosqlite:///data/gateway.db"


class ReposConfig(BaseModel):
    base_dir: str = "data/repos"


class SchedulerConfig(BaseModel):
    update_interval_minutes: int = 30
    health_check_interval_seconds: int = 60


class LogConfig(BaseModel):
    max_lines_per_server: int = 1000


class AppConfig(BaseSettings):
    server: ServerConfig = ServerConfig()
    database: DatabaseConfig = DatabaseConfig()
    repos: ReposConfig = ReposConfig()
    scheduler: SchedulerConfig = SchedulerConfig()
    log: LogConfig = LogConfig()


def load_config() -> AppConfig:
    config_path = BASE_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
        return AppConfig(**data)
    return AppConfig()


settings = load_config()
