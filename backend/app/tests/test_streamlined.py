"""
Tests for IRS Streamlined Filing Compliance Procedures.
Covers SFOP qualification, SDOP qualification, willfulness bar,
penalty calculations, overview endpoint, and edge cases.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.streamlined_router import (
    _assess_eligibility,
    _calculate_penalty,
    _is_nonresident,
    EligibilityRequest,
    PenaltyCalculationRequest,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

REGISTER_PAYLOAD = {
    "email": "streamlined-test@example.com",
    "password": "securepassword123",
    "tenant_name": "Streamlined Test Corp",
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


# ---------------------------------------------------------------------------
# Helper: build eligibility payload dict
# ---------------------------------------------------------------------------

def _eligibility_payload(
    days_in_us: list[int] | None = None,
    had_filing_requirement: bool = True,
    filed_returns: bool = False,
    filed_fbars: bool = False,
    is_willful: bool = False,
    account_balance_usd: float = 100_000.0,
    years_unreported: int = 3,
) -> dict:
    return {
        "days_in_us_per_year": days_in_us if days_in_us is not None else [20, 25, 30],
        "had_filing_requirement": had_filing_requirement,
        "filed_returns": filed_returns,
        "filed_fbars": filed_fbars,
        "is_willful": is_willful,
        "account_balance_usd": account_balance_usd,
        "years_unreported": years_unreported,
    }


# ===========================================================================
# 1. Non-residency helper
# ===========================================================================

def test_is_nonresident_true_all_under_35():
    """All years ≤35 days → qualifies as non-resident."""
    assert _is_nonresident([20, 25, 35]) is True


def test_is_nonresident_false_one_year_over_35():
    """One year >35 days → fails non-residency test."""
    assert _is_nonresident([20, 36, 30]) is False


def test_is_nonresident_boundary_exactly_35():
    """Exactly 35 days is still within the non-resident limit."""
    assert _is_nonresident([35, 35, 35]) is True


# ===========================================================================
# 2. SFOP qualification (non-resident, non-willful)
# ===========================================================================

def test_sfop_qualification():
    """Non-resident (<= 35 days/year) + non-willful → SFOP."""
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[10, 15, 20]))
    result = _assess_eligibility(req)

    assert result["qualifies_sfop"] is True
    assert result["qualifies_sdop"] is False
    assert result["procedure"] == "SFOP"
    assert result["penalty_rate"] == 0.0
    assert result["estimated_penalty_usd"] == 0.0
    assert result["non_willful_certification_required"] is True
    assert result["required_returns"] == 3
    assert result["required_fbars"] == 6
    assert len(result["steps"]) > 0
    assert "14653" in " ".join(result["steps"])


def test_sfop_zero_penalty():
    """SFOP always yields zero penalty regardless of account balance."""
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[5, 5, 5], account_balance_usd=5_000_000.0))
    result = _assess_eligibility(req)
    assert result["procedure"] == "SFOP"
    assert result["estimated_penalty_usd"] == 0.0


# ===========================================================================
# 3. SDOP qualification (US resident, non-willful)
# ===========================================================================

def test_sdop_qualification():
    """US resident (>35 days in a year) + non-willful → SDOP."""
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[200, 180, 210]))
    result = _assess_eligibility(req)

    assert result["qualifies_sfop"] is False
    assert result["qualifies_sdop"] is True
    assert result["procedure"] == "SDOP"
    assert result["penalty_rate"] == 0.05
    assert result["non_willful_certification_required"] is True
    assert result["required_returns"] == 3
    assert result["required_fbars"] == 6
    assert "14654" in " ".join(result["steps"])


def test_sdop_penalty_calculation_embedded():
    """SDOP estimated_penalty_usd = 5% of account_balance_usd."""
    balance = 200_000.0
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[180, 200, 190], account_balance_usd=balance))
    result = _assess_eligibility(req)
    assert result["procedure"] == "SDOP"
    assert result["estimated_penalty_usd"] == pytest.approx(balance * 0.05)


# ===========================================================================
# 4. Willful = no qualification
# ===========================================================================

def test_willful_disqualifies_sfop():
    """Willful non-compliance bars SFOP."""
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[10, 15, 20], is_willful=True))
    result = _assess_eligibility(req)
    assert result["qualifies_sfop"] is False
    assert result["procedure"] == "none"


def test_willful_disqualifies_sdop():
    """Willful non-compliance bars SDOP."""
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[200, 190, 210], is_willful=True))
    result = _assess_eligibility(req)
    assert result["qualifies_sdop"] is False
    assert result["procedure"] == "none"


def test_willful_returns_warning():
    """Willful result includes a warning about OVDP."""
    req = EligibilityRequest(**_eligibility_payload(is_willful=True))
    result = _assess_eligibility(req)
    assert len(result["warnings"]) > 0
    assert any("willful" in w.lower() or "OVDP" in w for w in result["warnings"])


def test_willful_steps_empty():
    """Willful result has no steps (no procedure to follow)."""
    req = EligibilityRequest(**_eligibility_payload(is_willful=True))
    result = _assess_eligibility(req)
    assert result["steps"] == []
    assert result["non_willful_certification_required"] is False


# ===========================================================================
# 5. Standalone penalty calculation
# ===========================================================================

def test_penalty_calculation_basic():
    """5% of highest aggregate balance across analyzed years."""
    req = PenaltyCalculationRequest(
        account_balances_by_year={"2021": 100_000.0, "2022": 150_000.0, "2023": 120_000.0},
        years=["2021", "2022", "2023"],
    )
    result = _calculate_penalty(req)
    assert result["highest_aggregate_balance"] == pytest.approx(150_000.0)
    assert result["penalty_rate"] == 0.05
    assert result["penalty_amount"] == pytest.approx(7_500.0)
    assert "150,000" in result["explanation"]
    assert result["years_analyzed"] == ["2021", "2022", "2023"]


def test_penalty_calculation_single_year():
    """Penalty with a single year provided."""
    req = PenaltyCalculationRequest(
        account_balances_by_year={"2023": 80_000.0},
        years=["2023"],
    )
    result = _calculate_penalty(req)
    assert result["highest_aggregate_balance"] == pytest.approx(80_000.0)
    assert result["penalty_amount"] == pytest.approx(4_000.0)


def test_penalty_calculation_zero_balance():
    """Zero balance produces zero penalty."""
    req = PenaltyCalculationRequest(
        account_balances_by_year={"2023": 0.0},
        years=["2023"],
    )
    result = _calculate_penalty(req)
    assert result["penalty_amount"] == 0.0


# ===========================================================================
# 6. HTTP endpoint tests
# ===========================================================================

def test_eligibility_endpoint_sfop(auth_token):
    """HTTP POST /eligibility returns SFOP for non-resident."""
    resp = client.post(
        "/api/v1/streamlined/eligibility",
        json=_eligibility_payload(days_in_us=[10, 15, 20]),
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["procedure"] == "SFOP"
    assert data["penalty_rate"] == 0.0


def test_eligibility_endpoint_sdop(auth_token):
    """HTTP POST /eligibility returns SDOP for US resident."""
    resp = client.post(
        "/api/v1/streamlined/eligibility",
        json=_eligibility_payload(days_in_us=[200, 190, 210], account_balance_usd=100_000.0),
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["procedure"] == "SDOP"
    assert data["penalty_rate"] == 0.05
    assert data["estimated_penalty_usd"] == pytest.approx(5_000.0)


def test_eligibility_endpoint_willful(auth_token):
    """HTTP POST /eligibility returns none for willful taxpayer."""
    resp = client.post(
        "/api/v1/streamlined/eligibility",
        json=_eligibility_payload(is_willful=True),
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["procedure"] == "none"


def test_eligibility_endpoint_requires_auth():
    """Eligibility endpoint returns 401 without JWT."""
    resp = client.post(
        "/api/v1/streamlined/eligibility",
        json=_eligibility_payload(),
    )
    assert resp.status_code in (401, 403)


def test_penalty_endpoint(auth_token):
    """HTTP POST /penalty-calculation returns correct penalty."""
    resp = client.post(
        "/api/v1/streamlined/penalty-calculation",
        json={
            "account_balances_by_year": {"2021": 200_000.0, "2022": 250_000.0},
            "years": ["2021", "2022"],
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["highest_aggregate_balance"] == pytest.approx(250_000.0)
    assert data["penalty_amount"] == pytest.approx(12_500.0)


def test_penalty_endpoint_requires_auth():
    """Penalty endpoint returns 401 without JWT."""
    resp = client.post(
        "/api/v1/streamlined/penalty-calculation",
        json={
            "account_balances_by_year": {"2023": 50_000.0},
            "years": ["2023"],
        },
    )
    assert resp.status_code in (401, 403)


def test_overview_endpoint_public():
    """GET /overview is public (no JWT required) and returns key data."""
    resp = client.get("/api/v1/streamlined/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "SFOP" in data["procedures"]
    assert "SDOP" in data["procedures"]
    assert data["procedures"]["SFOP"]["requirements"]["amended_returns"] == 3
    assert data["procedures"]["SDOP"]["requirements"]["fbar_periods"] == 6
    assert "Rev. Proc. 2014-55" in data["authority"]
    assert len(data["key_facts"]) >= 4
    assert len(data["disqualifying_factors"]) >= 2


def test_overview_sfop_zero_penalty():
    """Overview correctly states SFOP has no miscellaneous offshore penalty."""
    resp = client.get("/api/v1/streamlined/overview")
    assert resp.status_code == 200
    data = resp.json()
    penalty_text = data["procedures"]["SFOP"]["requirements"]["penalty"]
    assert "0%" in penalty_text or "No" in penalty_text


def test_overview_sdop_five_percent():
    """Overview correctly states SDOP 5% miscellaneous offshore penalty."""
    resp = client.get("/api/v1/streamlined/overview")
    assert resp.status_code == 200
    data = resp.json()
    penalty_text = data["procedures"]["SDOP"]["requirements"]["penalty"]
    assert "5%" in penalty_text


# ===========================================================================
# 7. Edge cases
# ===========================================================================

def test_sfop_boundary_35_days_all_three_years():
    """Exactly 35 days in each of the 3 years still qualifies for SFOP."""
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[35, 35, 35]))
    result = _assess_eligibility(req)
    assert result["procedure"] == "SFOP"


def test_sdop_boundary_36_days_one_year():
    """36 days in one year tips into SDOP territory."""
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[36, 20, 20]))
    result = _assess_eligibility(req)
    assert result["procedure"] == "SDOP"


def test_revenue_procedure_always_present():
    """Revenue procedure reference is always included."""
    for days in [[10, 10, 10], [200, 200, 200]]:
        req = EligibilityRequest(**_eligibility_payload(days_in_us=days))
        result = _assess_eligibility(req)
        assert "Rev. Proc. 2014-55" in result["revenue_procedure"]


def test_already_filed_generates_warning():
    """Returns + FBARs already filed triggers an informational warning."""
    req = EligibilityRequest(**_eligibility_payload(days_in_us=[10, 10, 10], filed_returns=True, filed_fbars=True))
    result = _assess_eligibility(req)
    assert len(result["warnings"]) >= 1


def test_eligibility_invalid_days_list_too_short(auth_token):
    """Providing only 2 years of days data should return 422 validation error."""
    payload = _eligibility_payload()
    payload["days_in_us_per_year"] = [10, 20]  # only 2 years — invalid
    resp = client.post(
        "/api/v1/streamlined/eligibility",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 422
