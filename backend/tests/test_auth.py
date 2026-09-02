"""
Tests for authentication endpoints — /api/register and /api/login.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Registering a new user returns 201 and success message."""
    response = await client.post("/api/register", json={
        "username": "newuser",
        "password": "securepass123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User created"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Registering with an existing username returns 409."""
    await client.post("/api/register", json={
        "username": "dupuser",
        "password": "password123",
    })
    response = await client.post("/api/register", json={
        "username": "dupuser",
        "password": "anotherpass",
    })
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_short_username(client: AsyncClient):
    """Registering with a too-short username returns 422."""
    response = await client.post("/api/register", json={
        "username": "ab",
        "password": "password123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Registering with a too-short password returns 422."""
    response = await client.post("/api/register", json={
        "username": "validuser",
        "password": "short",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Logging in with correct credentials returns a token."""
    await client.post("/api/register", json={
        "username": "loginuser",
        "password": "mypassword",
    })
    response = await client.post("/api/login", json={
        "username": "loginuser",
        "password": "mypassword",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["username"] == "loginuser"
    assert len(data["access_token"]) > 20  # JWT tokens are long


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Logging in with wrong password returns 401."""
    await client.post("/api/register", json={
        "username": "wrongpwuser",
        "password": "correctpass",
    })
    response = await client.post("/api/login", json={
        "username": "wrongpwuser",
        "password": "incorrectpass",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Logging in with a non-existent username returns 401."""
    response = await client.post("/api/login", json={
        "username": "ghostuser",
        "password": "whatever",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient):
    """Accessing a protected endpoint without a token returns 403."""
    response = await client.get("/api/history")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(client: AsyncClient):
    """Accessing a protected endpoint with an invalid token returns 401."""
    response = await client.get(
        "/api/history",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401
