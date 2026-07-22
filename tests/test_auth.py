import pytest
from httpx import AsyncClient
from models import User

@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    """Test user registration."""
    response = await async_client.post(
        "/api/auth/register",
        json={"display_name": "newuser", "email": "new@example.com", "password": "password123", "role": "user"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["role"] == "user"

@pytest.mark.asyncio
async def test_register_existing_user(async_client: AsyncClient, test_user: User):
    """Test user registration with an existing username."""
    response = await async_client.post(
        "/api/auth/register",
        json={"display_name": "testuser", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert "dang ky" in response.json()["detail"].lower() or "đăng ký" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user: User):
    """Test successful login."""
    response = await async_client.post(
        "/api/auth/token",
        data={"username": "test@example.com", "password": "testpassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, test_user: User):
    """Test login with wrong password."""
    response = await async_client.post(
        "/api/auth/token",
        data={"username": "test@example.com", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert "khong dung" in response.json()["detail"].lower() or "không đúng" in response.json()["detail"].lower()
