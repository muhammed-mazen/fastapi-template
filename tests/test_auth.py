import pytest
from httpx import AsyncClient
from core.config import get_config

config = get_config()


@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient):
    """Test user login with correct credentials"""
    response = await client.post("/login", json={"username": config.ADMIN_USERNAME, "password": config.ADMIN_PASSWORD})

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_admin_login_fail(client: AsyncClient):
    """Test user login with incorrect credentials"""
    response = await client.post("/login", json={"username": "wrong_username", "password": "wrong_password"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test user login with non-existent user"""
    response = await client.post("/login", json={"username": "nonexistent_user", "password": "password"})

    assert response.status_code == 401


