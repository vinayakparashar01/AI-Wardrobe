
from fastapi.testclient import TestClient

from app.app import app

client = TestClient(app)


def test_homepage():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "AI Wardrobe is running"
    }


def test_get_clothing_items_without_authentication():
    response = client.get("/clothing-items/")

    assert response.status_code == 401


def test_get_clothing_items_with_invalid_token():
    response = client.get(
        "/clothing-items/",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_login_with_unknown_email():
    response = client.post(
        "/auth/login",
        data={
            "username": "unknown-user-test@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_with_missing_credentials():
    response = client.post(
        "/auth/login",
        data={},
    )

    assert response.status_code == 422
