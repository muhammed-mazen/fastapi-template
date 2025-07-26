import asyncio

from pytest_asyncio import fixture as asyncio_fixture
from pytest import fixture
from sqlmodel import select

from app import create_app
from db.session import auto_generate_users, create_async_session, async_session_factory
from lib.auth import get_client, get_admin_client, get_user_client
from lib.utils import clear_database
from models import User, Profile
from core.config import get_config

config = get_config()


@fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@fixture(scope="session")
def app():
    return create_app()


@asyncio_fixture(scope="session")
async def client(app):
    return await get_client(app)


@asyncio_fixture(scope="session")
async def user_client(app):
    return await get_user_client(app)


@asyncio_fixture(scope="session")
async def admin_client(app):
    return await get_admin_client(app)


@asyncio_fixture(scope="session", autouse=True)
async def db():
    """Pytest fixture that runs before and after all tests."""
    db_session = await create_async_session()
    try:
        await auto_generate_users(db_session, add_test_users=True)
        yield db_session
    finally:
        await clear_database(db_session)
        await db_session.close()


@asyncio_fixture(scope="session")
async def session():
    """Creates a fresh session for each test."""
    async with async_session_factory() as db_session:
        yield db_session


@asyncio_fixture(scope="function")
async def test_user(session):
    result = await session.execute(select(User).where(User.is_admin.is_(False)))
    return result.scalars().first()


@asyncio_fixture(scope="session")
async def valid_users(session):
    result = await session.execute(select(User.username).where(User.is_admin.is_(False)))
    users = result.scalars().all()
    assert users, "There should be at least one valid user in the test DB"
    return users

@asyncio_fixture(scope="session")
async def current_user(session):
    result = await session.execute(select(User).where(User.username == config.USER_USERNAME))
    return result.scalars().first()

@asyncio_fixture(scope="session")
async def current_user_profile(session, current_user):
    """Ensures that the test user has a profile before testing."""
    if not current_user.profile:
        profile = Profile(
            user_id=current_user.id,
            first_name="Test",
            last_name="User",
            university="Test University",
            year=2025,
            speciality="Computer Science",
            department="Software Engineering",
            degree="Bachelor",
            role="Student"
        )
        session.add(profile)
        await session.commit()
    return current_user


@asyncio_fixture(scope="session")
async def current_admin(session):
    result = await session.execute(select(User).where(User.username == config.ADMIN_USERNAME))
    return result.scalars().first()
