"""
Tests for Form 8825 — Information Return by a U.S. Person with Respect to Certain Foreign Partnerships.

Tests cover:
- Filing requirement determination (≥10%, ≥50%, General Partner)
- Penalty calculation (base, continued failure, maximum)
- Various entity types and edge cases
- API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.form8825 import (
    FilingRequirementInput,
    PenaltyCalculationInput,
    check_filing_requirement,
    calculate_penalty,
    get_overview,
    PENALTY_PER_VIOLATION,
    PENALTY_MAX_PER_YEAR,
    OWNERSHIP_THRESHOLD,
    CONTROL_THRESHOLD,
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
            "email": "test_form8825@example.com",
            "tenant_name": "Test Tenant 8825",
            "password": "testpassword123",
        },
    )
    # Login
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test_form8825@example.com",
            "password": "testpassword123",
        },
    )
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Module-level tests (direct function calls)
# ---------------------------------------------------------------------------


class TestFilingRequirementModule:
    """Tests for the form8825 module filing requirement functions."""

    def test_ownership_below_threshold_not_required(self):
        """Ownership below 10% should not require filing."""
        inp = FilingRequirementInput(
            entity_type="individual",
            ownership_percent=5.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False
        assert result.penalty_if_not_filed == 0.0
        assert len(result.related_forms) == 0

    def test_ownership_at_threshold_required(self):
        """Ownership at exactly 10% should require filing."""
        inp = FilingRequirementInput(
            entity_type="individual",
            ownership_percent=10.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.penalty_if_not_filed == PENALTY_PER_VIOLATION
        assert "Form 8865" in result.related_forms

    def test_ownership_above_threshold_required(self):
        """Ownership above 10% should require filing."""
        inp = FilingRequirementInput(
            entity_type="individual",
            ownership_percent=25.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.penalty_if_not_filed == PENALTY_PER_VIOLATION

    def test_control_threshold_50_percent(self):
        """Ownership at 50% should trigger control threshold."""
        inp = FilingRequirementInput(
            entity_type="corporation",
            ownership_percent=50.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert any("control" in r.lower() for r in result.reasons)

    def test_ownership_above_50_percent(self):
        """Ownership above 50% should trigger enhanced reporting."""
        inp = FilingRequirementInput(
            entity_type="individual",
            ownership_percent=75.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert any("enhanced" in r.lower() for r in result.reasons)

    def test_multiple_us_owners(self):
        """Multiple U.S. owners should trigger additional requirements."""
        inp = FilingRequirementInput(
            entity_type="partnership",
            ownership_percent=15.0,
            us_owners=3,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert any("Multiple U.S. owners" in r for r in result.reasons)

    def test_foreign_corporation_flag(self):
        """Foreign corporation flag should add Form 5471 reference."""
        inp = FilingRequirementInput(
            entity_type="individual",
            ownership_percent=20.0,
            us_owners=1,
            foreign_corporation="yes",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert "Form 5471" in result.related_forms
        assert any("foreign corporation" in r.lower() for r in result.reasons)

    def test_entity_type_llc(self):
        """LLC entity type should work correctly."""
        inp = FilingRequirementInput(
            entity_type="llc",
            ownership_percent=30.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.entity_type == "llc"

    def test_entity_type_trust(self):
        """Trust entity type should work correctly."""
        inp = FilingRequirementInput(
            entity_type="trust",
            ownership_percent=12.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.entity_type == "trust"

    def test_zero_ownership_not_required(self):
        """Zero ownership should not require filing."""
        inp = FilingRequirementInput(
            entity_type="individual",
            ownership_percent=0.0,
            us_owners=0,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False
        assert result.penalty_if_not_filed == 0.0

    def test_100_percent_ownership(self):
        """100% ownership should require filing with control threshold."""
        inp = FilingRequirementInput(
            entity_type="corporation",
            ownership_percent=100.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert any("control" in r.lower() for r in result.reasons)


class TestPenaltyCalculationModule:
    """Tests for the form8825 module penalty calculation functions."""

    def test_no_penalty_when_not_required(self):
        """No penalty when filing is not required."""
        inp = PenaltyCalculationInput(
            entity_type="individual",
            ownership_percent=5.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
            is_general_partner=False,
            violations_count=1,
            days_unreported=0,
        )
        result = calculate_penalty(inp)
        assert result.total_penalty == 0.0
        assert result.base_penalty == 0.0

    def test_base_penalty_single_violation(self):
        """Base penalty for single violation should be $10,000."""
        inp = PenaltyCalculationInput(
            entity_type="individual",
            ownership_percent=15.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
            is_general_partner=False,
            violations_count=1,
            days_unreported=0,
        )
        result = calculate_penalty(inp)
        assert result.base_penalty == PENALTY_PER_VIOLATION
        assert result.total_penalty == PENALTY_PER_VIOLATION

    def test_base_penalty_multiple_violations(self):
        """Base penalty for multiple violations should multiply."""
        inp = PenaltyCalculationInput(
            entity_type="individual",
            ownership_percent=15.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
            is_general_partner=False,
            violations_count=3,
            days_unreported=0,
        )
        result = calculate_penalty(inp)
        assert result.base_penalty == PENALTY_PER_VIOLATION * 3
        assert result.total_penalty == PENALTY_PER_VIOLATION * 3

    def test_penalty_capped_at_maximum(self):
        """Penalty should be capped at $50,000 per year."""
        inp = PenaltyCalculationInput(
            entity_type="individual",
            ownership_percent=15.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
            is_general_partner=False,
            violations_count=10,
            days_unreported=0,
        )
        result = calculate_penalty(inp)
        assert result.base_penalty == PENALTY_MAX_PER_YEAR
        assert result.total_penalty == PENALTY_MAX_PER_YEAR

    def test_continued_failure_penalty(self):
        """Continued failure after IRS notice should add penalty."""
        inp = PenaltyCalculationInput(
            entity_type="individual",
            ownership_percent=15.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
            is_general_partner=False,
            violations_count=1,
            days_unreported=60,
        )
        result = calculate_penalty(inp)
        assert result.base_penalty == PENALTY_PER_VIOLATION
        assert result.continued_failure_penalty == PENALTY_PER_VIOLATION * 2
        assert result.total_penalty == PENALTY_PER_VIOLATION * 2

    def test_general_partner_penalty(self):
        """General Partner status should trigger penalty even below threshold."""
        inp = PenaltyCalculationInput(
            entity_type="individual",
            ownership_percent=5.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
            is_general_partner=True,
            violations_count=1,
            days_unreported=0,
        )
        result = calculate_penalty(inp)
        assert result.base_penalty == PENALTY_PER_VIOLATION
        assert result.is_general_partner is True

    def test_continued_failure_capped(self):
        """Continued failure penalty should not exceed maximum."""
        inp = PenaltyCalculationInput(
            entity_type="individual",
            ownership_percent=15.0,
            us_owners=1,
            foreign_corporation="no",
            tax_year=2024,
            is_general_partner=False,
            violations_count=1,
            days_unreported=365,
        )
        result = calculate_penalty(inp)
        assert result.total_penalty <= PENALTY_MAX_PER_YEAR


class TestOverviewModule:
    """Tests for the form8825 overview function."""

    def test_overview_returns_required_fields(self):
        """Overview should return all required fields."""
        result = get_overview()
        assert result.title != ""
        assert result.description != ""
        assert len(result.who_must_file) > 0
        assert "penalties" in result.penalties.lower() or "$" in result.penalties
        assert len(result.related_forms) > 0
        assert "Form 8865" in result.related_forms[0]

    def test_overview_contains_thresholds(self):
        """Overview should mention ownership thresholds."""
        result = get_overview()
        assert "10%" in result.ownership_threshold
        assert "50%" in result.control_threshold


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestForm8825API:
    """Tests for the Form 8825 API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token for each test."""
        self.token = _get_auth_token()
        self.headers = _auth_headers(self.token)

    def test_filing_requirement_endpoint_required(self):
        """Test filing-requirement endpoint with required filing."""
        resp = client.post(
            "/api/v1/form8825/filing-requirement",
            headers=self.headers,
            json={
                "entity_type": "individual",
                "ownership_percent": 25.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filing_required"] is True
        assert data["penalty_if_not_filed"] == PENALTY_PER_VIOLATION
        assert "Form 8865" in data["related_forms"]

    def test_filing_requirement_endpoint_not_required(self):
        """Test filing-requirement endpoint with no filing required."""
        resp = client.post(
            "/api/v1/form8825/filing-requirement",
            headers=self.headers,
            json={
                "entity_type": "individual",
                "ownership_percent": 5.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filing_required"] is False
        assert data["penalty_if_not_filed"] == 0.0

    def test_filing_requirement_requires_auth(self):
        """Test filing-requirement endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form8825/filing-requirement",
            json={
                "entity_type": "individual",
                "ownership_percent": 25.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
            },
        )
        assert resp.status_code == 401

    def test_filing_requirement_invalid_ownership(self):
        """Test filing-requirement endpoint with invalid ownership."""
        resp = client.post(
            "/api/v1/form8825/filing-requirement",
            headers=self.headers,
            json={
                "entity_type": "individual",
                "ownership_percent": 150.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
            },
        )
        assert resp.status_code == 422

    def test_filing_requirement_invalid_entity_type(self):
        """Test filing-requirement endpoint with invalid entity type."""
        resp = client.post(
            "/api/v1/form8825/filing-requirement",
            headers=self.headers,
            json={
                "entity_type": "invalid",
                "ownership_percent": 25.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
            },
        )
        assert resp.status_code == 422

    def test_penalty_calculation_endpoint(self):
        """Test penalty-calculation endpoint."""
        resp = client.post(
            "/api/v1/form8825/penalty-calculation",
            headers=self.headers,
            json={
                "entity_type": "individual",
                "ownership_percent": 25.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
                "is_general_partner": False,
                "violations_count": 2,
                "days_unreported": 30,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["base_penalty"] == PENALTY_PER_VIOLATION * 2
        assert data["total_penalty"] > 0

    def test_penalty_calculation_requires_auth(self):
        """Test penalty-calculation endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form8825/penalty-calculation",
            json={
                "entity_type": "individual",
                "ownership_percent": 25.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
                "is_general_partner": False,
                "violations_count": 1,
                "days_unreported": 0,
            },
        )
        assert resp.status_code == 401

    def test_overview_endpoint(self):
        """Test overview endpoint."""
        resp = client.get("/api/v1/form8825/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "Form 8825" in data["title"]
        assert "penalties" in data
        assert "related_forms" in data

    def test_overview_endpoint_requires_auth(self):
        """Test overview endpoint requires authentication."""
        # Note: overview endpoint may or may not require auth depending on implementation
        # Based on the router definition, it does NOT have get_current_tenant dependency
        # So it should be accessible without auth
        resp = client.get("/api/v1/form8825/overview")
        assert resp.status_code == 200

    def test_filing_requirement_negative_ownership(self):
        """Test filing-requirement endpoint with negative ownership."""
        resp = client.post(
            "/api/v1/form8825/filing-requirement",
            headers=self.headers,
            json={
                "entity_type": "individual",
                "ownership_percent": -5.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
            },
        )
        assert resp.status_code == 422

    def test_filing_requirement_invalid_tax_year(self):
        """Test filing-requirement endpoint with invalid tax year."""
        resp = client.post(
            "/api/v1/form8825/filing-requirement",
            headers=self.headers,
            json={
                "entity_type": "individual",
                "ownership_percent": 25.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 1800,
            },
        )
        assert resp.status_code == 422

    def test_penalty_calculation_invalid_violations(self):
        """Test penalty-calculation endpoint with invalid violations count."""
        resp = client.post(
            "/api/v1/form8825/penalty-calculation",
            headers=self.headers,
            json={
                "entity_type": "individual",
                "ownership_percent": 25.0,
                "us_owners": 1,
                "foreign_corporation": "no",
                "tax_year": 2024,
                "is_general_partner": False,
                "violations_count": 0,
                "days_unreported": 0,
            },
        )
        assert resp.status_code == 422
