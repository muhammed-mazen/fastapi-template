from pydantic import Field

from .base import Config, LogFormat


class ProdConfig(Config):
    FRONTEND_CORS_ORIGIN: list[str] = Field(default_factory=lambda: ["*"])
    LOG_FORMAT: LogFormat = "json"

    class Config:
        env_file = ".env"
