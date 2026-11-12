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


# ---------------------------------------------------------------------------
# User Enumeration Prevention & User Registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthenticated_cannot_list_users(async_client: AsyncClient):
    """Unauthenticated requests cannot list users (GET /user/ is disallowed)."""
    response = await async_client.get("/user/")
    assert response.status_code in (404, 405)


@pytest.mark.asyncio
async def test_authenticated_user_cannot_list_users(
    async_client: AsyncClient,
    test_user: dict,
):
    """Authenticated normal users cannot list or enumerate other users."""
    response = await async_client.get("/user/", headers=test_user["headers"])
    assert response.status_code in (404, 405)


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(async_client: AsyncClient):
    """Verify registration creates a user, password is not exposed, and user can log in."""
    unique_email = f"registered_{uuid4().hex[:8]}@example.com"
    reg_response = await async_client.post(
        "/user/",
        json={
            "name": "Registered User",
            "email": unique_email,
            "password": "SecurePassword123!",
        },
    )
    assert reg_response.status_code == 201
    user_data = reg_response.json()
    assert "id" in user_data
    assert user_data["email"] == unique_email
    assert user_data["name"] == "Registered User"
    assert "password" not in user_data
    assert "password_hash" not in user_data

    # Log in with the newly registered user
    login_response = await async_client.post(
        "/auth/login",
        data={
            "username": unique_email,
            "password": "SecurePassword123!",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Access their own profile with the token
    me_response = await async_client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["id"] == user_data["id"]
    assert me_data["email"] == unique_email
    assert me_data["name"] == "Registered User"


@pytest.mark.asyncio
async def test_user_profile_isolation_between_accounts(
    async_client: AsyncClient,
    test_user: dict,
    second_user: dict,
):
    """Each user only retrieves their own profile from GET /user/me."""
    res1 = await async_client.get("/user/me", headers=test_user["headers"])
    assert res1.status_code == 200
    assert res1.json()["id"] == str(test_user["user"].id)
    assert res1.json()["email"] == test_user["user"].email

    res2 = await async_client.get("/user/me", headers=second_user["headers"])
    assert res2.status_code == 200
    assert res2.json()["id"] == str(second_user["user"].id)
    assert res2.json()["email"] == second_user["user"].email

    # Confirm identities are distinct
    assert res1.json()["id"] != res2.json()["id"]
    assert res1.json()["email"] != res2.json()["email"]


# ---------------------------------------------------------------------------
# Duplicate Email & Registration Validation Tests (Task Bundle 1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_registration_duplicate_email_returns_409(async_client: AsyncClient):
    """Registering an existing email returns HTTP 409 Conflict with exact error message."""
    email = f"conflict_{uuid4().hex[:8]}@example.com"

    # First registration succeeds
    res1 = await async_client.post(
        "/user/",
        json={
            "name": "Original User",
            "email": email,
            "password": "Password123!",
        },
    )
    assert res1.status_code == 201

    # Second registration with exact same email fails with 409
    res2 = await async_client.post(
        "/user/",
        json={
            "name": "Imposter User",
            "email": email,
            "password": "AnotherPassword456!",
        },
    )
    assert res2.status_code == 409
    assert res2.json()["detail"] == "This email is already registered. Please log in or use another email."

    # Normalized email (uppercase / mixed case) also returns 409
    res3 = await async_client.post(
        "/user/",
        json={
            "name": "Uppercase Email User",
            "email": email.upper(),
            "password": "YetAnotherPassword789!",
        },
    )
    assert res3.status_code == 409
    assert res3.json()["detail"] == "This email is already registered. Please log in or use another email."


@pytest.mark.asyncio
async def test_registration_invalid_email_rejected(async_client: AsyncClient):
    """Invalid email strings are rejected with 422 Unprocessable Entity."""
    for bad_email in ["not-an-email", "user@domain", "@missinguser.com", "plainaddress"]:
        response = await async_client.post(
            "/user/",
            json={
                "name": "Invalid Email",
                "email": bad_email,
                "password": "Password123!",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_registration_password_length_validation(async_client: AsyncClient):
    """Password shorter than 6 characters is rejected with 422."""
    response = await async_client.post(
        "/user/",
        json={
            "name": "Short Pass User",
            "email": f"short_{uuid4().hex[:8]}@example.com",
            "password": "12345",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registration_integrity_error_rollback(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Concurrent race condition causing IntegrityError triggers rollback and returns clean 409."""
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.ext.asyncio import AsyncSession

    original_commit = AsyncSession.commit

    async def mock_commit(self):
        raise IntegrityError("mock_statement", {}, Exception("mock_orig"))

    monkeypatch.setattr(AsyncSession, "commit", mock_commit)

    res = await async_client.post(
        "/user/",
        json={
            "name": "Race User",
            "email": f"race_{uuid4().hex[:8]}@example.com",
            "password": "Password123!",
        },
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "This email is already registered. Please log in or use another email."

