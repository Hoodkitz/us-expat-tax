"""
Tests für den Auth-Router: /auth/register, /auth/login, /auth/me.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

REGISTER_PAYLOAD = {
    "email": "test-auth@example.com",
    "password": "securepassword123",
    "tenant_name": "Test GmbH",
}


@pytest.fixture(autouse=True)
def clean_tenant_store(tmp_path, monkeypatch):
    """Leere tenants.json für jeden Test (isolierte Ausführung)."""
    import app.auth.router as auth_router_module

    tenants_file = tmp_path / "tenants.json"
    monkeypatch.setattr(auth_router_module, "TENANTS_FILE", tenants_file)
    monkeypatch.setattr(auth_router_module, "DATA_DIR", tmp_path)
    yield


def _register_and_login(email: str = REGISTER_PAYLOAD["email"]) -> str:
    """Hilfsfunktion: registriert Mandant und gibt JWT zurück."""
    reg_payload = dict(REGISTER_PAYLOAD)
    reg_payload["email"] = email
    client.post("/auth/register", json=reg_payload)
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": REGISTER_PAYLOAD["password"]},
    )
    return login_resp.json()["access_token"]


class TestRegister:
    def test_register_success(self):
        resp = client.post("/auth/register", json=REGISTER_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == REGISTER_PAYLOAD["email"]
        assert data["tenant_name"] == REGISTER_PAYLOAD["tenant_name"]
        assert "tenant_id" in data
        assert "created_at" in data
        assert "password" not in data

    def test_register_duplicate_email_rejected(self):
        client.post("/auth/register", json=REGISTER_PAYLOAD)
        resp = client.post("/auth/register", json=REGISTER_PAYLOAD)
        assert resp.status_code == 409

    def test_register_short_password_rejected(self):
        payload = dict(REGISTER_PAYLOAD, password="short")
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 422

    def test_register_invalid_email_rejected(self):
        payload = dict(REGISTER_PAYLOAD, email="not-an-email")
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 422


class TestLogin:
    def test_login_success_returns_bearer_token(self):
        client.post("/auth/register", json=REGISTER_PAYLOAD)
        resp = client.post(
            "/auth/login",
            json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    def test_login_wrong_password_rejected(self):
        client.post("/auth/register", json=REGISTER_PAYLOAD)
        resp = client.post(
            "/auth/login",
            json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email_rejected(self):
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "somepassword"},
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_returns_tenant_info(self):
        token = _register_and_login()
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == REGISTER_PAYLOAD["email"]
        assert data["tenant_name"] == REGISTER_PAYLOAD["tenant_name"]

    def test_me_without_token_returns_401(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401
