"""
Tests for Form 8843 — Statement for Exempt Individuals.

Tests cover:
- Exempt individual status determination
- Substantial Presence Test calculations
- Various visa types and roles
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.form8843 import (
    ExemptIndividualInput,
    check_exempt_status,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: Get auth token
# ---------------------------------------------------------------------------


def _get_auth_token() -> str:
    """Register a test user and return JWT token."""
    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_form8843@example.com",
            "tenant_name": "Test Tenant",
            "password": "testpassword123",
        },
    )
    # Login
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test_form8843@example.com",
            "password": "testpassword123",
        },
    )
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Module-level tests (direct function calls)
# ---------------------------------------------------------------------------


class TestExemptIndividualModule:
    """Tests for the form8843 module functions."""

    def test_student_f_visa_is_exempt(self):
        """Student on F visa should be exempt."""
        inp = ExemptIndividualInput(
            us_days_present=120,
            foreign_days_present=245,
            tax_year=2024,
            visa_type="F",
            is_student=True,
        )
        result = check_exempt_status(inp)
        assert result.exempt_status is True
        assert result.days_counted == 0
        assert "Form 8843" in result.required_forms[0]

    def test_teacher_j_visa_is_exempt(self):
        """Teacher on J visa should be exempt."""
        inp = ExemptIndividualInput(
            us_days_present=100,
            foreign_days_present=265,
            tax_year=2024,
            visa_type="J",
            is_teacher=True,
        )
        result = check_exempt_status(inp)
        assert result.exempt_status is True
        assert result.days_counted == 0

    def test_trainee_j_visa_is_exempt(self):
        """Trainee on J visa should be exempt."""
        inp = ExemptIndividualInput(
            us_days_present=90,
            foreign_days_present=275,
            tax_year=2024,
            visa_type="J",
            is_trainee=True,
        )
        result = check_exempt_status(inp)
        assert result.exempt_status is True

    def test_researcher_q_visa_is_exempt(self):
        """Researcher on Q visa should be exempt."""
        inp = ExemptIndividualInput(
            us_days_present=150,
            foreign_days_present=215,
            tax_year=2024,
            visa_type="Q",
            is_researcher=True,
        )
        result = check_exempt_status(inp)
        assert result.exempt_status is True

    def test_athlete_p_visa_is_exempt(self):
        """Athlete on P visa should be exempt."""
        inp = ExemptIndividualInput(
            us_days_present=60,
            foreign_days_present=305,
            tax_year=2024,
            visa_type="P",
        )
        result = check_exempt_status(inp)
        assert result.exempt_status is True

    def test_h_visa_not_exempt(self):
        """H visa holder is not exempt."""
        inp = ExemptIndividualInput(
            us_days_present=200,
            foreign_days_present=165,
            tax_year=2024,
            visa_type="H",
        )
        result = check_exempt_status(inp)
        assert result.exempt_status is False
        assert result.days_counted == 200

    def test_b_visa_not_exempt(self):
        """B visa holder is not exempt."""
        inp = ExemptIndividualInput(
            us_days_present=30,
            foreign_days_present=335,
            tax_year=2024,
            visa_type="B",
        )
        result = check_exempt_status(inp)
        assert result.exempt_status is False

    def test_f_visa_without_role_not_exempt(self):
        """F visa holder without qualifying role is not exempt."""
        inp = ExemptIndividualInput(
            us_days_present=120,
            foreign_days_present=245,
            tax_year=2024,
            visa_type="F",
            is_student=False,
            is_teacher=False,
            is_trainee=False,
            is_researcher=False,
        )
        result = check_exempt_status(inp)
        assert result.exempt_status is False

    def test_substantial_presence_test_not_met(self):
        """SPT should not be met with few days."""
        inp = ExemptIndividualInput(
            us_days_present=30,
            foreign_days_present=335,
            tax_year=2024,
            visa_type="H",
        )
        result = check_exempt_status(inp)
        assert result.substantial_presence_test["meets_threshold"] is False

    def test_substantial_presence_test_met(self):
        """SPT should be met with many days."""
        inp = ExemptIndividualInput(
            us_days_present=200,
            foreign_days_present=165,
            tax_year=2024,
            visa_type="H",
        )
        result = check_exempt_status(inp)
        assert result.substantial_presence_test["meets_threshold"] is True

    def test_exempt_individual_spt_not_applicable(self):
        """SPT should not apply to exempt individuals."""
        inp = ExemptIndividualInput(
            us_days_present=200,
            foreign_days_present=165,
            tax_year=2024,
            visa_type="F",
            is_student=True,
        )
        result = check_exempt_status(inp)
        assert result.substantial_presence_test["applies"] is False


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestForm8843API:
    """Tests for the Form 8843 API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token for each test."""
        self.token = _get_auth_token()
        self.headers = _auth_headers(self.token)

    def test_exempt_status_endpoint_student(self):
        """Test exempt-status endpoint with student."""
        resp = client.post(
            "/api/v1/form8843/exempt-status",
            headers=self.headers,
            json={
                "us_days_present": 120,
                "foreign_days_present": 245,
                "tax_year": 2024,
                "visa_type": "F",
                "is_student": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["exempt_status"] is True
        assert data["days_counted"] == 0
        assert "Form 8843" in data["required_forms"][0]

    def test_exempt_status_endpoint_teacher(self):
        """Test exempt-status endpoint with teacher."""
        resp = client.post(
            "/api/v1/form8843/exempt-status",
            headers=self.headers,
            json={
                "us_days_present": 100,
                "foreign_days_present": 265,
                "tax_year": 2024,
                "visa_type": "J",
                "is_teacher": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["exempt_status"] is True

    def test_exempt_status_endpoint_not_exempt(self):
        """Test exempt-status endpoint with non-exempt visa."""
        resp = client.post(
            "/api/v1/form8843/exempt-status",
            headers=self.headers,
            json={
                "us_days_present": 200,
                "foreign_days_present": 165,
                "tax_year": 2024,
                "visa_type": "H",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["exempt_status"] is False

    def test_substantial_presence_endpoint(self):
        """Test substantial-presence endpoint."""
        resp = client.post(
            "/api/v1/form8843/substantial-presence",
            headers=self.headers,
            json={
                "us_days_present": 120,
                "prior_year_us_days": 60,
                "two_years_ago_us_days": 30,
                "tax_year": 2024,
                "is_exempt": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["applies"] is True
        assert data["current_year_days"] == 120
        assert data["prior_year_days_weighted"] == 20.0
        assert data["two_years_ago_days_weighted"] == 5.0
        assert data["total_days_counted"] == 145.0
        assert data["meets_threshold"] is False

    def test_substantial_presence_endpoint_exempt(self):
        """Test substantial-presence endpoint with exempt individual."""
        resp = client.post(
            "/api/v1/form8843/substantial-presence",
            headers=self.headers,
            json={
                "us_days_present": 200,
                "prior_year_us_days": 100,
                "two_years_ago_us_days": 50,
                "tax_year": 2024,
                "is_exempt": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["applies"] is False
        assert data["meets_threshold"] is False

    def test_overview_endpoint_public(self):
        """Test overview endpoint is public (no auth required)."""
        resp = client.get("/api/v1/form8843/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["form"] == "Form 8843"
        assert "exempt_visa_types" in data
        assert "substantial_presence_test" in data

    def test_exempt_status_requires_auth(self):
        """Test exempt-status endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form8843/exempt-status",
            json={
                "us_days_present": 120,
                "foreign_days_present": 245,
                "tax_year": 2024,
                "visa_type": "F",
                "is_student": True,
            },
        )
        assert resp.status_code == 401

    def test_substantial_presence_requires_auth(self):
        """Test substantial-presence endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form8843/substantial-presence",
            json={
                "us_days_present": 120,
                "prior_year_us_days": 60,
                "two_years_ago_us_days": 30,
                "tax_year": 2024,
                "is_exempt": False,
            },
        )
        assert resp.status_code == 401

    def test_exempt_status_invalid_visa_type(self):
        """Test exempt-status endpoint with invalid visa type."""
        resp = client.post(
            "/api/v1/form8843/exempt-status",
            headers=self.headers,
            json={
                "us_days_present": 120,
                "foreign_days_present": 245,
                "tax_year": 2024,
                "visa_type": "INVALID",
                "is_student": True,
            },
        )
        assert resp.status_code == 422

    def test_exempt_status_negative_days(self):
        """Test exempt-status endpoint with negative days."""
        resp = client.post(
            "/api/v1/form8843/exempt-status",
            headers=self.headers,
            json={
                "us_days_present": -10,
                "foreign_days_present": 245,
                "tax_year": 2024,
                "visa_type": "F",
                "is_student": True,
            },
        )
        assert resp.status_code == 422
