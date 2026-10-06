"""
Tests for Form 2555 FEIE – module logic + HTTP router.
Covers Physical Presence Test, Bona Fide Residence Test,
year-specific limits, housing exclusion, and eligibility check.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.feie import (
    FEIEInput,
    calculate_feie,
    check_feie_eligibility,
    FEIE_LIMITS,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Auth helpers (mirror test_auth.py pattern)
# ---------------------------------------------------------------------------

REGISTER_PAYLOAD = {
    "email": "feie-test@example.com",
    "password": "securepassword123",
    "tenant_name": "FEIE Test Corp",
}


@pytest.fixture()
def auth_token(tmp_path, monkeypatch):
    """Register a fresh tenant and return a valid JWT."""
    import app.auth.router as auth_router_module

    monkeypatch.setattr(auth_router_module, "TENANTS_FILE", tmp_path / "tenants.json")
    monkeypatch.setattr(auth_router_module, "DATA_DIR", tmp_path)

    client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Module-level unit tests (no HTTP)
# ---------------------------------------------------------------------------


def test_qualifies_physical_presence():
    """330 days → Physical Presence Test passes."""
    inp = FEIEInput(
        tax_year=2024,
        foreign_earned_income=80_000.0,
        housing_costs=0.0,
        days_in_foreign_country=330,
        bona_fide_resident=False,
        filing_status="single",
    )
    result = calculate_feie(inp)
    assert result.qualifies_pp is True
    assert result.qualifies is True
    assert result.feie_exclusion == 80_000.0  # income < limit
    assert result.form_2555_required is True


def test_not_qualifies_329_days():
    """329 days and BFR=False → neither test passes → no exclusion."""
    inp = FEIEInput(
        tax_year=2024,
        foreign_earned_income=80_000.0,
        housing_costs=0.0,
        days_in_foreign_country=329,
        bona_fide_resident=False,
        filing_status="single",
    )
    result = calculate_feie(inp)
    assert result.qualifies_pp is False
    assert result.qualifies_bfr is False
    assert result.qualifies is False
    assert result.feie_exclusion == 0.0
    assert result.total_exclusion == 0.0
    assert result.taxable_income_estimate == 80_000.0
    assert result.form_2555_required is False


def test_qualifies_bona_fide():
    """BFR=True with 0 days → Bona Fide Residence Test passes."""
    inp = FEIEInput(
        tax_year=2024,
        foreign_earned_income=90_000.0,
        housing_costs=0.0,
        days_in_foreign_country=0,
        bona_fide_resident=True,
        filing_status="single",
    )
    result = calculate_feie(inp)
    assert result.qualifies_bfr is True
    assert result.qualifies_pp is False
    assert result.qualifies is True
    assert result.feie_exclusion == 90_000.0
    assert result.form_2555_required is True


def test_feie_2024_limit():
    """Income above 2024 limit ($126,500) → exclusion capped."""
    inp = FEIEInput(
        tax_year=2024,
        foreign_earned_income=200_000.0,
        housing_costs=0.0,
        days_in_foreign_country=335,
        bona_fide_resident=False,
        filing_status="single",
    )
    result = calculate_feie(inp)
    assert result.feie_limit == 126_500.0
    assert result.feie_exclusion == 126_500.0
    assert result.taxable_income_estimate == pytest.approx(
        200_000.0 - result.total_exclusion, abs=0.01
    )


def test_feie_2023_limit():
    """Tax year 2023 → limit is $120,000."""
    inp = FEIEInput(
        tax_year=2023,
        foreign_earned_income=150_000.0,
        housing_costs=0.0,
        days_in_foreign_country=335,
        bona_fide_resident=False,
        filing_status="single",
    )
    result = calculate_feie(inp)
    assert result.feie_limit == FEIE_LIMITS[2023]
    assert result.feie_limit == 120_000.0
    assert result.feie_exclusion == 120_000.0


def test_housing_exclusion():
    """Housing costs above base amount generate a housing exclusion."""
    inp = FEIEInput(
        tax_year=2024,
        foreign_earned_income=150_000.0,
        housing_costs=40_000.0,
        days_in_foreign_country=335,
        bona_fide_resident=False,
        filing_status="single",
    )
    result = calculate_feie(inp)
    # housing_base = 126500 * 0.16 = 20240
    expected_base = 126_500.0 * 0.16
    assert result.housing_base_amount == pytest.approx(expected_base, abs=0.01)
    # housing_exclusion = min(40000 - 20240, 126500*0.30)
    expected_he = min(40_000.0 - expected_base, 126_500.0 * 0.30)
    assert result.housing_exclusion == pytest.approx(expected_he, abs=0.01)
    assert result.housing_exclusion > 0.0


def test_total_capped_at_income():
    """Total exclusion (FEIE + housing) cannot exceed foreign earned income."""
    inp = FEIEInput(
        tax_year=2024,
        foreign_earned_income=10_000.0,
        housing_costs=30_000.0,
        days_in_foreign_country=335,
        bona_fide_resident=False,
        filing_status="single",
    )
    result = calculate_feie(inp)
    assert result.total_exclusion <= inp.foreign_earned_income
    assert result.taxable_income_estimate >= 0.0


# ---------------------------------------------------------------------------
# Eligibility check module tests
# ---------------------------------------------------------------------------


def test_check_eligibility_pp():
    """330+ days outside US → eligible via physical presence."""
    result = check_feie_eligibility(
        days_outside_us=335,
        bona_fide_resident=False,
        us_citizen_or_green_card=True,
    )
    assert result["eligible"] is True
    assert result["test_passed"] == "physical_presence"


def test_check_eligibility_bfr():
    """BFR=True, <330 days → eligible via bona fide residence."""
    result = check_feie_eligibility(
        days_outside_us=100,
        bona_fide_resident=True,
        us_citizen_or_green_card=True,
    )
    assert result["eligible"] is True
    assert result["test_passed"] == "bona_fide_residence"


def test_not_us_citizen():
    """Non-US citizen/green card holder → not eligible regardless of days."""
    result = check_feie_eligibility(
        days_outside_us=365,
        bona_fide_resident=True,
        us_citizen_or_green_card=False,
    )
    assert result["eligible"] is False
    assert result["test_passed"] == "none"
    assert "U.S. citizens" in result["reason"]


# ---------------------------------------------------------------------------
# HTTP router tests (JWT required for /calculate)
# ---------------------------------------------------------------------------


def test_router_calculate_requires_jwt():
    """POST /api/v1/feie/calculate without token → 401."""
    resp = client.post(
        "/api/v1/feie/calculate",
        json={
            "tax_year": 2024,
            "foreign_earned_income": 80_000.0,
            "housing_costs": 0.0,
            "days_in_foreign_country": 335,
            "bona_fide_resident": False,
            "filing_status": "single",
            "employer_provided_housing": 0.0,
        },
    )
    assert resp.status_code == 401


def test_router_calculate_with_jwt(auth_token):
    """POST /api/v1/feie/calculate with valid JWT → 200 and correct fields."""
    resp = client.post(
        "/api/v1/feie/calculate",
        json={
            "tax_year": 2024,
            "foreign_earned_income": 100_000.0,
            "housing_costs": 25_000.0,
            "days_in_foreign_country": 335,
            "bona_fide_resident": False,
            "filing_status": "single",
            "employer_provided_housing": 0.0,
        },
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["qualifies"] is True
    assert data["feie_limit"] == 126_500.0
    assert data["feie_exclusion"] == 100_000.0  # income < limit
    assert data["form_2555_required"] is True
    assert "notes" in data
    assert isinstance(data["notes"], list)


def test_router_check_eligibility_no_jwt():
    """POST /api/v1/feie/check-eligibility is public (no JWT needed)."""
    resp = client.post(
        "/api/v1/feie/check-eligibility",
        json={
            "days_outside_us": 335,
            "bona_fide_resident": False,
            "us_citizen_or_green_card": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["eligible"] is True
    assert data["test_passed"] == "physical_presence"
