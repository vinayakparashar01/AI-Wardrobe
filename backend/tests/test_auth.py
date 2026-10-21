"""Tests for authentication and token validation in AI Wardrobe."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user: dict):
    """Valid login credentials return 200 with an access token and bearer token type."""
    response = await async_client.post(
        "/auth/login",
        data={
            "username": test_user["user"].email,
            "password": test_user["password"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str) and len(data["access_token"]) > 10
    assert data.get("token_type", "").lower() == "bearer"


@pytest.mark.asyncio
async def test_login_incorrect_password(async_client: AsyncClient, test_user: dict):
    """Incorrect password returns 401 with appropriate error detail."""
    response = await async_client.post(
        "/auth/login",
        data={
            "username": test_user["user"].email,
            "password": "CompletelyWrongPassword!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_unknown_email(async_client: AsyncClient):
    """Unknown email returns 401."""
    response = await async_client.post(
        "/auth/login",
        data={
            "username": "nonexistent_user_999@example.com",
            "password": "SomePassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_missing_fields(async_client: AsyncClient):
    """Missing username or password returns 422 Unprocessable Entity."""
    # Completely empty form
    res1 = await async_client.post("/auth/login", data={})
    assert res1.status_code == 422

    # Only username provided
    res2 = await async_client.post("/auth/login", data={"username": "user@example.com"})
    assert res2.status_code == 422

    # Only password provided
    res3 = await async_client.post("/auth/login", data={"password": "SecretPassword!"})
    assert res3.status_code == 422


@pytest.mark.asyncio
async def test_token_malformed(async_client: AsyncClient):
    """Malformed token string returns 401."""
    response = await async_client.get(
        "/clothing-items/",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_token_expired(async_client: AsyncClient, test_user: dict):
    """Expired token returns 401."""
    expired_time = datetime.now(UTC) - timedelta(minutes=15)
    expired_payload = {
        "sub": str(test_user["user"].id),
        "exp": expired_time,
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = await async_client.get(
        "/clothing-items/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_token_nonexistent_user(async_client: AsyncClient):
    """Token signed with secret key but referencing a non-existent user returns 401."""
    fake_user_id = str(uuid4())
    payload = {
        "sub": fake_user_id,
        "exp": datetime.now(UTC) + timedelta(minutes=15),
    }
    valid_jwt_fake_user = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = await async_client.get(
        "/clothing-items/",
        headers={"Authorization": f"Bearer {valid_jwt_fake_user}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_token_invalid_uuid_subject(async_client: AsyncClient):
    """Token with non-UUID subject returns 401."""
    payload = {
        "sub": "not-a-valid-uuid-string",
        "exp": datetime.now(UTC) + timedelta(minutes=15),
    }
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = await async_client.get(
        "/clothing-items/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_get_current_user_me_endpoint(async_client: AsyncClient, test_user: dict):
    """GET /user/me returns current authenticated user details."""
    response = await async_client.get("/user/me", headers=test_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user["user"].id)
    assert data["email"] == test_user["user"].email
    assert data["name"] == test_user["user"].name
