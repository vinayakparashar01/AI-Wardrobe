"""Tests for CORS configuration and origin handling."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.config import Settings


def test_cors_origins_property():
    """cors_origins property splits comma-separated origins and strips whitespace."""
    s1 = Settings(
        database_url="postgresql+asyncpg://u:p@localhost/db",
        allowed_origins="*",
    )
    assert s1.cors_origins == ["*"]

    s2 = Settings(
        database_url="postgresql+asyncpg://u:p@localhost/db",
        allowed_origins="https://ai-wardrobe.vercel.app, https://preview.vercel.app",
    )
    assert s2.cors_origins == [
        "https://ai-wardrobe.vercel.app",
        "https://preview.vercel.app",
    ]


def test_cors_wildcard_behavior():
    """When cors_origins is ['*'], preflight requests return allow-origin: * and no credentials conflict."""
    test_app = FastAPI()
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.get("/ping")
    def ping():
        return {"ping": "pong"}

    client = TestClient(test_app)

    # Preflight OPTIONS request
    preflight = client.options(
        "/ping",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "*"
    assert preflight.headers.get("access-control-allow-credentials") is None

    # Actual GET request
    response = client.get("/ping", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"


def test_cors_explicit_origins_behavior():
    """When explicit origins are specified, credentials are allowed and unauthorized origins are rejected."""
    allowed = ["https://ai-wardrobe.vercel.app", "http://localhost:5173"]
    test_app = FastAPI()
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.get("/ping")
    def ping():
        return {"ping": "pong"}

    client = TestClient(test_app)

    # Authorized origin
    res_allowed = client.get("/ping", headers={"Origin": "https://ai-wardrobe.vercel.app"})
    assert res_allowed.status_code == 200
    assert res_allowed.headers.get("access-control-allow-origin") == "https://ai-wardrobe.vercel.app"
    assert res_allowed.headers.get("access-control-allow-credentials") == "true"

    # Preflight for authorized origin
    preflight_allowed = client.options(
        "/ping",
        headers={
            "Origin": "https://ai-wardrobe.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight_allowed.status_code == 200
    assert preflight_allowed.headers.get("access-control-allow-origin") == "https://ai-wardrobe.vercel.app"
    assert preflight_allowed.headers.get("access-control-allow-credentials") == "true"

    # Unauthorized origin
    res_denied = client.get("/ping", headers={"Origin": "https://malicious-site.example.com"})
    assert res_denied.status_code == 200
    assert "access-control-allow-origin" not in res_denied.headers
