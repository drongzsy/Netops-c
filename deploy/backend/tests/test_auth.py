"""Tests for auth service — password hashing and JWT token creation."""

from jose import jwt

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.services.auth import create_token, hash_password, verify_password


def test_password_hashing():
    pwd = hash_password("test123")
    assert pwd != "test123"
    assert verify_password("test123", pwd)
    assert not verify_password("wrong", pwd)


def test_token_creation():
    token = create_token(1, "admin")
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == "1"
    assert payload["username"] == "admin"
    assert "exp" in payload


def test_login_success(client, admin_user):
    resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_login_invalid_password(client, admin_user):
    resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


def test_login_invalid_user(client):
    resp = client.post("/api/auth/login", json={
        "username": "nonexistent",
        "password": "test123",
    })
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_user(client, auth_header):
    resp = client.get("/api/auth/me", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"
    assert resp.json()["role"] == "admin"
