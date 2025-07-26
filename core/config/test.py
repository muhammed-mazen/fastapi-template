import os

from core.config.base import Config, LogFormat, get_base_dir


class TestConfig(Config):
    JWT_SECRET: str = "6ba4e05e642a4124ffb4a60435e37832296b74aefd078c45b4466d90684522d8"
    DATABASE_URL: str = "postgresql+asyncpg://testuser:testpassword@localhost/testdb"
    USERS_PATH: str = os.path.join(get_base_dir(), "test_users.json")
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: LogFormat = "plain"  # json,colored,uvicorn
    LOG_DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False
    LOG_REQUEST_RESPONSE: bool = True
    ENABLE_METRICS: bool = True
