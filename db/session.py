from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.config import get_config
from lib.utils import auto_generate_users

config = get_config()

async_engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    pool_size=30,  # Default pool size
    max_overflow=20,  # Allow 20 additional connections beyond the pool size
    pool_timeout=30,  # Wait 30 seconds for a connection before timeout
    pool_recycle=1800,  # Recycle connections every 30 minutes
    pool_pre_ping=True  # Check connection health before using
)
async_session_factory = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()


async def create_async_session() -> AsyncSession:
    """Creates and returns an async database session."""
    return async_session_factory()


async def init_db():
    db_session = await create_async_session()
    try:
        if await auto_generate_users(db_session):
            print("Generated users")
            # if await reset_user_passwords(session):
            #     print("Reset user passwords")
    finally:
        await db_session.close()
