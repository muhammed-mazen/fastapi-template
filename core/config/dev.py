from .base import Config, LogFormat


class DevConfig(Config):
    PROFILING_ENABLED: bool = True
    JWT_SECRET: str = "6ba4e05e642a4124ffb4a60435e37832296b74aefd078c45b4466d90684522d8"
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: LogFormat = "plain"  # json,colored,uvicorn
    LOG_DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False
    LOG_REQUEST_RESPONSE: bool = True
    ENABLE_METRICS: bool = True

    class Config:
        env_file = ".env"
