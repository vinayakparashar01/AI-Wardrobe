"""Test configuration and fixtures for AI Wardrobe backend.

Ensures strict test database isolation:
- Tests ONLY run against an isolated test database (e.g. 'ai_wardrobe_test').
- Tests will NEVER touch, create, drop, or truncate the development database.
- Database credentials and secrets are kept confidential and never printed.
- Dependency overrides are safely applied and cleaned up.
- Test-owned media/files are stored in a temporary directory and removed.
"""

import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from uuid import uuid4

# Ensure backend directory is on sys.path regardless of execution directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import httpx
import pytest
from app.app import app
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.database import Base, get_db

# Import all models to ensure they are registered on Base.metadata
from app.models.clothing_item import ClothingItem  # noqa: F401
from app.models.outfit import Outfit  # noqa: F401
from app.models.outfit_item import OutfitItem  # noqa: F401
from app.models.user import User
from fastapi.testclient import TestClient
from httpx import ASGITransport
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# ---------------------------------------------------------------------------
# 1. Test Database URL Resolution & Strict Safety Checks
# ---------------------------------------------------------------------------


def _resolve_test_database_url() -> str:
    """Determine the test database URL and enforce safety constraints."""
    # Allow overriding via TEST_DATABASE_URL environment variable
    env_test_url = os.getenv("TEST_DATABASE_URL")
    if env_test_url:
        target_url = env_test_url
    else:
        # Fall back to deriving from settings.database_url by changing db name to 'ai_wardrobe_test'
        parsed_dev = make_url(settings.database_url)
        target_url = parsed_dev.set(database="ai_wardrobe_test").render_as_string(
            hide_password=False
        )

    url_obj = make_url(target_url)
    test_db_name = url_obj.database
    dev_db_name = make_url(settings.database_url).database

    # CRITICAL SAFETY GATE:
    # 1. Database name must contain 'test'.
    # 2. Database name must NOT match the development database.
    if not test_db_name or "test" not in test_db_name.lower():
        raise RuntimeError(
            f"SAFETY ABORT: Test database name must contain 'test', but got '{test_db_name}'. "
            "Tests are strictly forbidden from running against non-test databases."
        )

    if test_db_name == dev_db_name:
        raise RuntimeError(
            f"SAFETY ABORT: Test database '{test_db_name}' matches development database '{dev_db_name}'. "
            "Tests will NEVER run against the development database."
        )

    return target_url


TEST_DATABASE_URL = _resolve_test_database_url()

# Create dedicated asynchronous engine and sessionmaker for tests using NullPool
# NullPool prevents asyncpg connections from being reused across different event loops.
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestingAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# 2. Session-Level Setup: Ensure Tables Exist in Test Database
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def verify_and_init_test_database():
    """Verify test database connectivity and ensure schema tables exist."""
    import asyncio

    async def _init():
        try:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as exc:
            raise RuntimeError(
                "FAILED TO INITIALIZE TEST DATABASE: Could not connect to 'ai_wardrobe_test'. "
                "Please ensure PostgreSQL is running and database 'ai_wardrobe_test' has been created.\n"
                "Command to create if missing: CREATE DATABASE ai_wardrobe_test;\n"
                "Tests will NEVER fall back to the development database."
            ) from exc

    asyncio.run(_init())
    yield
    asyncio.run(test_engine.dispose())


# ---------------------------------------------------------------------------
# 3. Per-Test Isolation: Dependency Override & Data Cleanup
# ---------------------------------------------------------------------------


async def _clear_test_tables():
    """Delete all rows from test database tables in reverse dependency order."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture(autouse=True)
async def clean_database_per_test():
    """Ensure every test executes in a clean database state.

    Cleanup Strategy:
    Explicit deletion of all table rows before and after each test in reverse
    foreign-key order.

    Why this strategy:
    - Allows endpoints to execute real `commit()` and `rollback()` calls.
    - Accurately tests transactions, foreign keys, cascade deletes, and refresh.
    - Fast on local PostgreSQL (~few milliseconds for 4 tables).

    Limitations:
    - Slightly higher overhead than in-memory SQLite (which doesn't support asyncpg/PG specifics).
    - If running parallel pytest workers against the same database, tests would conflict.
      (Parallel testing requires separate worker databases or single-worker execution).
    """
    await _clear_test_tables()
    yield
    await _clear_test_tables()


@pytest.fixture(autouse=True)
def override_get_db_dependency():
    """Override FastAPI's get_db to inject the test database session."""

    async def _test_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingAsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _test_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# 4. Media Directory Isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolate_media_directory(tmp_path, monkeypatch):
    """Point MEDIA_DIR to a temporary folder during tests to prevent polluting media/."""
    test_media_dir = tmp_path / "test_media"
    test_media_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("app.utils.files.MEDIA_DIR", test_media_dir)
    monkeypatch.setattr("app.services.clothing_service.MEDIA_DIR", test_media_dir)
    return test_media_dir


# ---------------------------------------------------------------------------
# 5. Client Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Synchronous TestClient for simple or legacy synchronous tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Asynchronous HTTP client using httpx and ASGITransport."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Direct asynchronous database session on the test database."""
    async with TestingAsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# 6. User and Authentication Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """Create a primary test user in the test database and return auth credentials."""
    user = User(
        name="Test User",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("Password123!"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "user": user,
        "token": token,
        "headers": headers,
        "password": "Password123!",
    }


@pytest.fixture
async def second_user(db_session: AsyncSession) -> dict:
    """Create a second distinct test user for authorization / cross-user isolation tests."""
    user = User(
        name="Second User",
        email=f"second_{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("AnotherPassword456!"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "user": user,
        "token": token,
        "headers": headers,
        "password": "AnotherPassword456!",
    }
