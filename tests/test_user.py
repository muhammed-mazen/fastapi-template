import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import get_config
from models import User, Profile

config = get_config()


@pytest.mark.asyncio
async def test_update_profile_success(user_client: AsyncClient):
    """User should be able to successfully update their profile."""

    response = await user_client.put("/profile", json={
        "first_name": "John",
        "last_name": "Doe",
        "university": "Test University",
        "year": 2025,
        "speciality": "Computer Science",
        "department": "Software Engineering",
        "degree": "Bachelor",
        "role": "Student",
        "current_password": config.USER_PASSWORD,
        "new_password": "newsecurepassword"
    })

    assert response.status_code == 200
    profile = response.json()
    assert profile["first_name"] == "John"
    assert profile["university"] == "Test University"


@pytest.mark.asyncio
async def test_update_profile_invalid_password(user_client: AsyncClient):
    """User should not be able to set an invalid new password (too short)."""

    response = await user_client.put("/profile", json={
        "first_name": "John",
        "last_name": "Doe",
        "university": "Test University",
        "year": 2025,
        "speciality": "Computer Science",
        "department": "Software Engineering",
        "degree": "Bachelor",
        "role": "Student",
        "current_password": "oldpassword",
        "new_password": "123"
    })

    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_update_profile_missing_current_password(user_client: AsyncClient):
    """User should not be able to change password without providing the current one."""

    response = await user_client.put("/profile", json={
        "first_name": "John",
        "last_name": "Doe",
        "university": "Test University",
        "year": 2025,
        "speciality": "Computer Science",
        "department": "Software Engineering",
        "degree": "Bachelor",
        "role": "Student",
        "new_password": "newsecurepassword"
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "current_password_required"


@pytest.mark.asyncio
async def test_update_profile_invalid_fields(user_client: AsyncClient):
    """User should receive validation errors for invalid profile fields."""

    response = await user_client.put("/profile", json={
        "first_name": "J",  # Too short
        "last_name": "D",
        "university": "",
        "year": 1800,  # Invalid year
        "speciality": "CS",
        "department": "",
        "degree": "B",
        "role": "S"
    })

    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_update_profile_has_password_reset(user_client: AsyncClient, session: AsyncSession, current_user: User):
    """If `has_password_reset` is True, the user must set a new password without requiring the current password."""

    # Manually set `has_password_reset` to True for this test case
    current_user.has_password_reset = True
    await session.commit()

    response = await user_client.put("/profile", json={
        "first_name": "John",
        "last_name": "Doe",
        "university": "Test University",
        "year": 2025,
        "speciality": "Computer Science",
        "department": "Software Engineering",
        "degree": "Bachelor",
        "role": "Student",
        "new_password": "newsecurepassword"  # No current_password needed
    })

    assert response.status_code == 200
    profile = response.json()
    assert profile["first_name"] == "John"

    await session.refresh(current_user)

    assert current_user.has_password_reset is False


@pytest.mark.asyncio
async def test_acknowledge_instructions(user_client: AsyncClient, session, current_user_profile):
    """User should be able to acknowledge instructions (set is_akg = True)."""

    current_user_profile.is_akg = False
    await session.commit()

    response = await user_client.get("/akg")

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"

    await session.refresh(current_user_profile)
    assert current_user_profile.is_akg is True


@pytest.mark.asyncio
async def test_acknowledge_instructions_idempotent(user_client: AsyncClient, session, current_user_profile):
    """If `is_akg` is already True, API should return the existing profile without updating."""

    current_user_profile.is_akg = True
    await session.commit()

    response = await user_client.get("/akg")

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"

    await session.refresh(current_user_profile)
    assert current_user_profile.is_akg is True


@pytest.mark.asyncio
async def test_acknowledge_instructions_no_profile(user_client: AsyncClient, session, current_user_profile):
    """If a user has no profile, the API should return a 404 error."""

    # Manually Delete the user profile
    await session.execute(delete(Profile).where(Profile.user_id == current_user_profile.id))
    await session.commit()

    response = await user_client.get("/akg")

    assert response.status_code == 404
    assert response.json()["detail"] == "User profile not found"


@pytest.mark.asyncio
async def test_acknowledge_instructions_unauthenticated(client: AsyncClient):
    """An unauthenticated user should not be able to access /akg."""

    response = await client.get("/akg")

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_get_current_user_unauthenticated(client: AsyncClient):
    """Unauthenticated users should receive 401 error."""

    response = await client.get("/me")

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_user_exists(session):
    result = await session.execute(select(User).where(User.username == config.USER_USERNAME))
    user = result.scalars().first()
    assert user is not None, "User should exist in the test database"


@pytest.mark.asyncio
async def test_admin_exists(session):
    result = await session.execute(select(User).where(User.username == config.ADMIN_USERNAME))
    user = result.scalars().first()
    assert user is not None, "Admin should exist in the test database"


@pytest.mark.asyncio
async def test_create_bulk_users(admin_client: AsyncClient, session):
    """Admin should be able to create users in bulk successfully."""

    response = await admin_client.get("/bulk_users/5")

    assert response.status_code == 200
    users = response.json()

    assert len(users) == 5  # Ensure the correct number of users are created
    for user in users:
        assert "username" in user
        assert "password" in user


@pytest.mark.asyncio
async def test_create_bulk_users_unique(admin_client: AsyncClient, session):
    """Ensures all created users have unique usernames."""

    response = await admin_client.get("/bulk_users/10")

    assert response.status_code == 200
    users = response.json()

    usernames = {user["username"] for user in users}
    assert len(usernames) == 10  # No duplicate usernames


@pytest.mark.asyncio
async def test_create_bulk_users_exceed_limit(admin_client: AsyncClient):
    """Requesting more than MAX_USERS_PER_REQUEST should return 400."""

    response = await admin_client.get(f"/bulk_users/{config.MAX_USERS_PER_REQUEST + 1}")

    assert response.status_code == 400
    assert "User count must be between 1 and" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_bulk_users_invalid_count(admin_client: AsyncClient):
    """Requesting zero or negative users should return 400."""

    response = await admin_client.get("/bulk_users/0")
    assert response.status_code == 400

    response = await admin_client.get("/bulk_users/-5")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_bulk_users_unauthorized(user_client: AsyncClient):
    """Non-admin users should not be able to create users in bulk."""

    response = await user_client.get("/bulk_users/5")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized"


@pytest.mark.asyncio
async def test_block_user(admin_client: AsyncClient, session, test_user):
    """Admin should be able to block a user."""

    response = await admin_client.post(f"/users/{test_user.username}/block")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "blocked" in response.json()["message"]

    await session.refresh(test_user)
    assert test_user.is_active is False


@pytest.mark.asyncio
async def test_unblock_user(admin_client: AsyncClient, session, test_user):
    """Admin should be able to unblock a user."""

    # Set user to inactive first
    test_user.is_active = False
    await session.commit()

    await session.refresh(test_user)

    response = await admin_client.post(f"/users/{test_user.username}/block")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "unblocked" in response.json()["message"]

    await session.refresh(test_user)
    assert test_user.is_active is True


@pytest.mark.asyncio
async def test_block_admin_user(admin_client: AsyncClient):
    """Attempting to block an admin user should return 400."""

    response = await admin_client.post(f"/users/{config.ADMIN_USERNAME}/block")

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot block/unblock an admin user"


@pytest.mark.asyncio
async def test_block_nonexistent_user(admin_client: AsyncClient):
    """Blocking a non-existent user should return 404."""

    response = await admin_client.post("/users/non_existent_user/block")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_block_user_unauthorized(user_client: AsyncClient, test_user):
    """Non-admin users should not be allowed to block/unblock users."""

    response = await user_client.post(f"/users/{test_user.username}/block")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized"
