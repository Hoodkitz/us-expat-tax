"""
Tests for Form 8840 — Closer Connection Exception
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import get_current_tenant
from app.modules.form8840 import (
    Form8840Input,
    calculate_form8840,
    get_form8840_overview,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth():
    """Override get_current_tenant for all tests."""
    async def mock_get_current_tenant():
        return {
            "tenant_id": "test-tenant-123",
            "email": "test@example.com",
            "tenant_name": "Test Tenant",
        }
    app.dependency_overrides[get_current_tenant] = mock_get_current_tenant
    yield
    app.dependency_overrides.clear()


# ========================================================================
# Module-level tests (calculate_form8840)
# ========================================================================

class TestCalculateForm8840:
    """Tests for the calculate_form8840 function."""

    def test_spt_met_183_days(self):
        """SPT met: days_in_us >= 183 → Resident Alien."""
        data = Form8840Input(
            days_in_us=200,
            tax_year=2024,
            closer_connection=False,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is True
        assert result.days_in_us == 200
        assert result.closer_connection is False
        assert result.exempt_individual is False

    def test_spt_met_boundary_183(self):
        """Boundary: exactly 183 days → Resident Alien."""
        data = Form8840Input(
            days_in_us=183,
            tax_year=2024,
            closer_connection=False,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is True

    def test_spt_not_met_182_days(self):
        """Boundary: 182 days → NOT Resident Alien (without closer connection)."""
        data = Form8840Input(
            days_in_us=182,
            tax_year=2024,
            closer_connection=False,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is False

    def test_closer_connection_exception(self):
        """Closer Connection Exception: < 183 days but closer_connection=True → Resident Alien."""
        data = Form8840Input(
            days_in_us=100,
            tax_year=2024,
            closer_connection=True,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is True
        assert result.closer_connection is True

    def test_closer_connection_boundary_182(self):
        """Closer Connection at boundary: 182 days with closer_connection=True → Resident Alien."""
        data = Form8840Input(
            days_in_us=182,
            tax_year=2024,
            closer_connection=True,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is True

    def test_exempt_individual_overrides_spt(self):
        """Exempt individual overrides SPT: even with 200 days, NOT Resident Alien."""
        data = Form8840Input(
            days_in_us=200,
            tax_year=2024,
            closer_connection=False,
            exempt_individual=True,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is False
        assert result.exempt_individual is True

    def test_exempt_individual_overrides_closer_connection(self):
        """Exempt individual overrides closer connection: NOT Resident Alien."""
        data = Form8840Input(
            days_in_us=100,
            tax_year=2024,
            closer_connection=True,
            exempt_individual=True,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is False

    def test_zero_days_not_resident(self):
        """Zero days in US → NOT Resident Alien."""
        data = Form8840Input(
            days_in_us=0,
            tax_year=2024,
            closer_connection=False,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is False

    def test_zero_days_with_closer_connection(self):
        """Zero days but closer_connection=True → Resident Alien."""
        data = Form8840Input(
            days_in_us=0,
            tax_year=2024,
            closer_connection=True,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert result.resident_alien is True

    def test_explanation_for_spt_met(self):
        """Explanation mentions Substantial Presence Test when SPT is met."""
        data = Form8840Input(
            days_in_us=200,
            tax_year=2024,
            closer_connection=False,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert "Substantial Presence Test" in result.explanation
        assert "183" in result.explanation

    def test_explanation_for_closer_connection(self):
        """Explanation mentions Closer Connection when that exception applies."""
        data = Form8840Input(
            days_in_us=100,
            tax_year=2024,
            closer_connection=True,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert "closer connection" in result.explanation.lower()
        assert "Closer Connection" in result.explanation

    def test_explanation_for_exempt(self):
        """Explanation mentions exempt individual status."""
        data = Form8840Input(
            days_in_us=150,
            tax_year=2024,
            closer_connection=False,
            exempt_individual=True,
        )
        result = calculate_form8840(data)
        assert "exempt individual" in result.explanation.lower()

    def test_explanation_for_non_resident(self):
        """Explanation indicates NOT a resident alien when not meeting any criteria."""
        data = Form8840Input(
            days_in_us=50,
            tax_year=2024,
            closer_connection=False,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert "NOT classified as a U.S. Resident Alien" in result.explanation

    def test_explanation_contains_tax_year(self):
        """Explanation always contains the tax year."""
        data = Form8840Input(
            days_in_us=100,
            tax_year=2025,
            closer_connection=True,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert "2025" in result.explanation

    def test_result_fields_match_input(self):
        """All result fields correctly reflect input values."""
        data = Form8840Input(
            days_in_us=75,
            tax_year=2024,
            closer_connection=True,
            exempt_individual=False,
        )
        result = calculate_form8840(data)
        assert result.days_in_us == 75
        assert result.closer_connection is True
        assert result.exempt_individual is False
        # tax_year is not in the result model, but is used in explanation
        assert "2024" in result.explanation


# ========================================================================
# Overview tests
# ========================================================================

class TestGetForm8840Overview:
    """Tests for the get_form8840_overview function."""

    def test_overview_returns_dict(self):
        """Overview returns a dictionary."""
        overview = get_form8840_overview()
        assert isinstance(overview, dict)

    def test_overview_contains_form_name(self):
        """Overview contains form name."""
        overview = get_form8840_overview()
        assert overview["form"] == "Form 8840"

    def test_overview_contains_title(self):
        """Overview contains title."""
        overview = get_form8840_overview()
        assert "Closer Connection" in overview["title"]

    def test_overview_contains_purpose(self):
        """Overview contains purpose description."""
        overview = get_form8840_overview()
        assert "purpose" in overview
        assert len(overview["purpose"]) > 0

    def test_overview_contains_who_must_file(self):
        """Overview contains who must file list."""
        overview = get_form8840_overview()
        assert "who_must_file" in overview
        assert isinstance(overview["who_must_file"], list)
        assert len(overview["who_must_file"]) > 0

    def test_overview_contains_key_rules(self):
        """Overview contains key rules."""
        overview = get_form8840_overview()
        assert "key_rules" in overview
        assert isinstance(overview["key_rules"], list)
        assert len(overview["key_rules"]) >= 3

    def test_overview_contains_irs_reference(self):
        """Overview contains IRS reference URL."""
        overview = get_form8840_overview()
        assert "irs_reference" in overview
        assert overview["irs_reference"].startswith("https://www.irs.gov")

    def test_overview_contains_exempt_categories(self):
        """Overview contains exempt individual categories."""
        overview = get_form8840_overview()
        assert "exempt_individual_categories" in overview
        assert isinstance(overview["exempt_individual_categories"], list)

    def test_overview_contains_closer_connection_factors(self):
        """Overview contains closer connection factors."""
        overview = get_form8840_overview()
        assert "closer_connection_factors" in overview
        assert isinstance(overview["closer_connection_factors"], list)
        assert len(overview["closer_connection_factors"]) >= 5


# ========================================================================
# API endpoint tests
# ========================================================================

class TestForm8840API:
    """Tests for the Form 8840 API endpoints."""

    def test_calculate_endpoint_spt_met(self):
        """POST /calculate with SPT met returns correct result."""
        response = client.post(
            "/api/v1/form8840/calculate",
            json={
                "days_in_us": 200,
                "tax_year": 2024,
                "closer_connection": False,
                "exempt_individual": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_alien"] is True
        assert data["days_in_us"] == 200

    def test_calculate_endpoint_closer_connection(self):
        """POST /calculate with closer connection exception."""
        response = client.post(
            "/api/v1/form8840/calculate",
            json={
                "days_in_us": 100,
                "tax_year": 2024,
                "closer_connection": True,
                "exempt_individual": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_alien"] is True
        assert data["closer_connection"] is True

    def test_calculate_endpoint_exempt(self):
        """POST /calculate with exempt individual."""
        response = client.post(
            "/api/v1/form8840/calculate",
            json={
                "days_in_us": 200,
                "tax_year": 2024,
                "closer_connection": False,
                "exempt_individual": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_alien"] is False
        assert data["exempt_individual"] is True

    def test_calculate_endpoint_not_resident(self):
        """POST /calculate with non-resident."""
        response = client.post(
            "/api/v1/form8840/calculate",
            json={
                "days_in_us": 50,
                "tax_year": 2024,
                "closer_connection": False,
                "exempt_individual": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_alien"] is False

    def test_overview_endpoint(self):
        """GET /overview returns overview data."""
        response = client.get("/api/v1/form8840/overview")
        assert response.status_code == 200
        data = response.json()
        assert "form" in data
        assert "purpose" in data
        assert "who_must_file" in data
        assert "key_rules" in data
        assert "irs_reference" in data


# ========================================================================
# Input validation tests
# ========================================================================

class TestForm8840InputValidation:
    """Tests for Form 8840 input validation."""

    def test_invalid_negative_days(self):
        """Negative days_in_us should raise validation error."""
        with pytest.raises(Exception):
            Form8840Input(
                days_in_us=-1,
                tax_year=2024,
                closer_connection=False,
                exempt_individual=False,
            )

    def test_invalid_excessive_days(self):
        """days_in_us > 366 should raise validation error."""
        with pytest.raises(Exception):
            Form8840Input(
                days_in_us=367,
                tax_year=2024,
                closer_connection=False,
                exempt_individual=False,
            )

    def test_invalid_tax_year_low(self):
        """tax_year < 2000 should raise validation error."""
        with pytest.raises(Exception):
            Form8840Input(
                days_in_us=100,
                tax_year=1999,
                closer_connection=False,
                exempt_individual=False,
            )

    def test_invalid_tax_year_high(self):
        """tax_year > 2099 should raise validation error."""
        with pytest.raises(Exception):
            Form8840Input(
                days_in_us=100,
                tax_year=2100,
                closer_connection=False,
                exempt_individual=False,
            )

    def test_api_rejects_invalid_days(self):
        """API should reject negative days."""
        response = client.post(
            "/api/v1/form8840/calculate",
            json={
                "days_in_us": -5,
                "tax_year": 2024,
                "closer_connection": False,
                "exempt_individual": False,
            },
        )
        assert response.status_code == 422

    def test_api_rejects_missing_fields(self):
        """API should reject missing required fields."""
        response = client.post(
            "/api/v1/form8840/calculate",
            json={
                "days_in_us": 100,
                # missing tax_year, closer_connection, exempt_individual
            },
        )
        assert response.status_code == 422
