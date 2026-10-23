"""Disclaimer must be public, present on every response, and not tenant-gated."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_disclaimer_endpoint_public():
    resp = client.get("/api/v1/disclaimer")
    assert resp.status_code == 200
    data = resp.json()
    assert "keine Steuer" in data["disclaimer_de"]
    assert "not provide tax" in data["disclaimer_en"]


def test_disclaimer_header_on_every_response():
    assert "not tax advice" in client.get("/health").headers["X-Tax-Disclaimer"].lower()
    # also on error responses (unauthenticated protected route)
    resp = client.post("/api/v1/tax/evaluate", json={})
    assert "X-Tax-Disclaimer" in resp.headers


def test_tollgate_requires_configured_secret(monkeypatch):
    from app.auth.utils import get_current_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"tenant_id": "t", "email": "a@b.c"}
    try:
        monkeypatch.delenv("TOLLGATE_SERVER_SECRET", raising=False)
        resp = client.post("/api/v1/submission/tollgate", json={"user_id": "u", "totp_code": "000000"})
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()
