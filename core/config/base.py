import os
from functools import lru_cache
from typing import TypeAlias, Literal

from pydantic import Field
from pydantic_settings import BaseSettings


def get_base_dir(): return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


LogLevel: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat: TypeAlias = Literal["plain", "json", "uvicorn"]


class Config(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    FRONTEND_CORS_ORIGIN: list[str] = Field(default_factory=lambda: ["*"])
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    MAX_USERS_PER_REQUEST: int = 100
    USERS_PATH: str = os.path.join(get_base_dir(), "users.json")
    ADMIN_USERNAME: str = "lg_admin"
    ADMIN_PASSWORD: str = "admin_password"
    USER_USERNAME: str = "user"
    USER_PASSWORD: str = "user_password"
    LOG_LEVEL: LogLevel = "INFO"
    LOG_FORMAT: LogFormat = "plain"  # json,colored,uvicorn
    LOG_DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False
    LOG_REQUEST_RESPONSE: bool = False
    PROFILING_ENABLED: bool = True
    ENABLE_METRICS: bool = True


@lru_cache
def get_config():
    return Config()
