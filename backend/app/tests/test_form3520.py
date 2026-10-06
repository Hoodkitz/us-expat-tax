"""
Tests for Form 3520 Foreign Gift & Trust Reporting Assistant.

Covers:
- filing-requirement: individual gifts < $100k → no file
- filing-requirement: individual gifts > $100k → must file
- filing-requirement: corp gift > $16,815 → must file
- filing-requirement: trust beneficiary → always must file
- filing-requirement: transferred to foreign trust → must file
- filing-requirement: zero gifts, no trust → no filing
- gift-calculator: individual only, below threshold → no reporting
- gift-calculator: individual only, above threshold → reporting required
- gift-calculator: corp gift above threshold → reporting required
- gift-calculator: mixed gifts, correct aggregation
- gift-calculator: penalty formula present in response
- gift-calculator: empty gift list → no reporting required
- gift-calculator: multiple gifts same donor type → aggregated correctly
- trust-reporting: grantor trust → reporting_required=True
- trust-reporting: beneficiary with distributions > 0 → annual_report_requirement=True
- trust-reporting: beneficiary with zero distributions → reporting_required=True but no distributions
- trust-reporting: applicable_sections populated for beneficiary
- overview: 200 OK and contains expected keys
- auth: unauthenticated 401 on POST /filing-requirement
- auth: unauthenticated 401 on POST /gift-calculator
- auth: unauthenticated 401 on POST /trust-reporting
"""
from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import create_access_token

client = TestClient(app)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_token() -> str:
    return create_access_token({
        "sub": "form3520-test@example.com",
        "tenant_id": str(uuid.uuid4()),
    })


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE = "/api/v1/form3520"

FILING_REQ_BELOW = {
    "received_foreign_gifts_usd": 50_000.0,
    "received_from_foreign_person": True,
    "received_from_foreign_corporation_or_partnership": False,
    "is_beneficiary_of_foreign_trust": False,
    "transferred_to_foreign_trust": False,
    "tax_year": 2024,
}

FILING_REQ_ABOVE = {
    "received_foreign_gifts_usd": 150_000.0,
    "received_from_foreign_person": True,
    "received_from_foreign_corporation_or_partnership": False,
    "is_beneficiary_of_foreign_trust": False,
    "transferred_to_foreign_trust": False,
    "tax_year": 2024,
}

FILING_REQ_CORP = {
    "received_foreign_gifts_usd": 20_000.0,
    "received_from_foreign_person": False,
    "received_from_foreign_corporation_or_partnership": True,
    "is_beneficiary_of_foreign_trust": False,
    "transferred_to_foreign_trust": False,
    "tax_year": 2024,
}

FILING_REQ_TRUST = {
    "received_foreign_gifts_usd": 0.0,
    "received_from_foreign_person": False,
    "received_from_foreign_corporation_or_partnership": False,
    "is_beneficiary_of_foreign_trust": True,
    "transferred_to_foreign_trust": False,
    "tax_year": 2024,
}

FILING_REQ_TRANSFER = {
    "received_foreign_gifts_usd": 0.0,
    "received_from_foreign_person": False,
    "received_from_foreign_corporation_or_partnership": False,
    "is_beneficiary_of_foreign_trust": False,
    "transferred_to_foreign_trust": True,
    "tax_year": 2024,
}

FILING_REQ_ZERO = {
    "received_foreign_gifts_usd": 0.0,
    "received_from_foreign_person": False,
    "received_from_foreign_corporation_or_partnership": False,
    "is_beneficiary_of_foreign_trust": False,
    "transferred_to_foreign_trust": False,
    "tax_year": 2024,
}


# ---------------------------------------------------------------------------
# Filing Requirement Tests
# ---------------------------------------------------------------------------

def test_filing_requirement_individual_below_threshold(auth_token):
    """Individual gifts below $100k → must_file = False."""
    resp = client.post(f"{BASE}/filing-requirement", json=FILING_REQ_BELOW, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is False
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) >= 1


def test_filing_requirement_individual_above_threshold(auth_token):
    """Individual gifts above $100k → must_file = True."""
    resp = client.post(f"{BASE}/filing-requirement", json=FILING_REQ_ABOVE, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True
    assert any("100,000" in r or "150,000" in r for r in data["reasons"])
    assert "penalties_if_not_filed" in data
    assert "form_due_date" in data


def test_filing_requirement_corp_gift_above_threshold(auth_token):
    """Corp/partnership gift above $16,815 → must_file = True."""
    resp = client.post(f"{BASE}/filing-requirement", json=FILING_REQ_CORP, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True
    assert len(data["reasons"]) >= 1


def test_filing_requirement_trust_beneficiary_must_file(auth_token):
    """Being a trust beneficiary → must_file = True regardless of gift amount."""
    resp = client.post(f"{BASE}/filing-requirement", json=FILING_REQ_TRUST, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True
    assert any("trust" in r.lower() or "beneficiary" in r.lower() for r in data["reasons"])


def test_filing_requirement_transferred_to_foreign_trust(auth_token):
    """Transfer to foreign trust → must_file = True."""
    resp = client.post(f"{BASE}/filing-requirement", json=FILING_REQ_TRANSFER, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True


def test_filing_requirement_zero_gifts_no_trust(auth_token):
    """Zero gifts, no trust connection → must_file = False."""
    resp = client.post(f"{BASE}/filing-requirement", json=FILING_REQ_ZERO, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is False


def test_filing_requirement_response_structure(auth_token):
    """Response contains all required keys."""
    resp = client.post(f"{BASE}/filing-requirement", json=FILING_REQ_ABOVE, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    for key in ("must_file", "applicable_thresholds", "reasons", "penalties_if_not_filed", "form_due_date"):
        assert key in data, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Gift Calculator Tests
# ---------------------------------------------------------------------------

def test_gift_calculator_individual_below_threshold(auth_token):
    """Individual gift below $100k → no reporting required."""
    payload = {
        "gifts": [{"donor_type": "INDIVIDUAL", "amount_usd": 40_000.0, "date_received": "2024-05-10", "donor_country": "DE"}],
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/gift-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["reporting_required"] is False
    assert data["total_individual_gifts"] == 40_000.0


def test_gift_calculator_individual_above_threshold(auth_token):
    """Individual gift above $100k → reporting required."""
    payload = {
        "gifts": [{"donor_type": "INDIVIDUAL", "amount_usd": 120_000.0, "date_received": "2024-03-01", "donor_country": "FR"}],
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/gift-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["reporting_required"] is True
    assert data["total_individual_gifts"] == 120_000.0
    assert data["penalty_exposure_usd"] > 0


def test_gift_calculator_corp_above_threshold(auth_token):
    """Corp gift above $16,815 → reporting required."""
    payload = {
        "gifts": [{"donor_type": "CORPORATION", "amount_usd": 20_000.0, "date_received": "2024-07-20", "donor_country": "CH"}],
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/gift-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["reporting_required"] is True
    assert data["total_corp_gifts"] == 20_000.0


def test_gift_calculator_mixed_gifts_aggregation(auth_token):
    """Mixed individual + corp gifts are aggregated correctly per category."""
    payload = {
        "gifts": [
            {"donor_type": "INDIVIDUAL", "amount_usd": 60_000.0, "date_received": "2024-01-15", "donor_country": "DE"},
            {"donor_type": "INDIVIDUAL", "amount_usd": 55_000.0, "date_received": "2024-06-20", "donor_country": "AT"},
            {"donor_type": "CORPORATION", "amount_usd": 10_000.0, "date_received": "2024-09-01", "donor_country": "CH"},
        ],
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/gift-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_individual_gifts"] == 115_000.0
    assert data["total_corp_gifts"] == 10_000.0
    assert data["reporting_required"] is True  # individual > $100k


def test_gift_calculator_penalty_formula_present(auth_token):
    """Response always includes a penalty_formula string."""
    payload = {
        "gifts": [{"donor_type": "INDIVIDUAL", "amount_usd": 5_000.0, "date_received": "2024-02-10", "donor_country": "IT"}],
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/gift-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "penalty_formula" in data
    assert len(data["penalty_formula"]) > 20


def test_gift_calculator_empty_gifts(auth_token):
    """Empty gift list → no reporting required."""
    payload = {"gifts": [], "tax_year": 2024}
    resp = client.post(f"{BASE}/gift-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["reporting_required"] is False
    assert data["total_individual_gifts"] == 0.0
    assert data["total_corp_gifts"] == 0.0


def test_gift_calculator_multiple_same_donor_type(auth_token):
    """Multiple gifts from the same donor type are summed correctly."""
    payload = {
        "gifts": [
            {"donor_type": "PARTNERSHIP", "amount_usd": 8_000.0, "date_received": "2024-03-10", "donor_country": "DE"},
            {"donor_type": "PARTNERSHIP", "amount_usd": 9_000.0, "date_received": "2024-09-15", "donor_country": "DE"},
            {"donor_type": "PARTNERSHIP", "amount_usd": 2_000.0, "date_received": "2024-11-01", "donor_country": "DE"},
        ],
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/gift-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_corp_gifts"] == pytest.approx(19_000.0)
    assert data["reporting_required"] is True  # 19_000 > 16_815


# ---------------------------------------------------------------------------
# Trust Reporting Tests
# ---------------------------------------------------------------------------

def test_trust_reporting_grantor_reporting_required(auth_token):
    """Grantor of a foreign trust → reporting_required = True."""
    payload = {
        "trust_name": "Zurich Family Trust",
        "trust_country": "CH",
        "distributions_received_usd": 0.0,
        "is_grantor": True,
        "is_beneficiary": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/trust-reporting", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["reporting_required"] is True
    assert len(data["applicable_sections"]) >= 1


def test_trust_reporting_beneficiary_with_distributions_annual_report(auth_token):
    """Beneficiary with distributions > 0 → annual_report_requirement = True."""
    payload = {
        "trust_name": "London Equity Trust",
        "trust_country": "GB",
        "distributions_received_usd": 25_000.0,
        "is_grantor": False,
        "is_beneficiary": True,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/trust-reporting", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["reporting_required"] is True
    assert data["annual_report_requirement"] is True


def test_trust_reporting_beneficiary_zero_distributions(auth_token):
    """Beneficiary with zero distributions → reporting_required but annual_report_requirement may vary."""
    payload = {
        "trust_name": "Paris Trust",
        "trust_country": "FR",
        "distributions_received_usd": 0.0,
        "is_grantor": False,
        "is_beneficiary": True,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/trust-reporting", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["reporting_required"] is True


def test_trust_reporting_applicable_sections_for_beneficiary(auth_token):
    """Beneficiary response includes Part III in applicable_sections."""
    payload = {
        "trust_name": "Vienna Trust",
        "trust_country": "AT",
        "distributions_received_usd": 10_000.0,
        "is_grantor": False,
        "is_beneficiary": True,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/trust-reporting", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert any("Part III" in s for s in data["applicable_sections"])
    assert isinstance(data["penalty_structure"], str)
    assert len(data["penalty_structure"]) > 20
    assert isinstance(data["recommendations"], list)


# ---------------------------------------------------------------------------
# Overview Tests
# ---------------------------------------------------------------------------

def test_overview_returns_200():
    """GET /overview is publicly accessible and returns 200."""
    resp = client.get(f"{BASE}/overview")
    assert resp.status_code == 200


def test_overview_contains_expected_keys():
    """Overview contains all expected top-level keys."""
    resp = client.get(f"{BASE}/overview")
    assert resp.status_code == 200
    data = resp.json()
    for key in ("form", "title", "purpose", "who_must_file", "key_thresholds", "penalties", "due_date"):
        assert key in data, f"Missing key: {key}"


def test_overview_thresholds_values():
    """Overview thresholds contain the correct numerical values."""
    resp = client.get(f"{BASE}/overview")
    data = resp.json()
    thresholds = data["key_thresholds"]
    assert thresholds["individual_or_estate_gifts_usd"] == 100_000.0
    assert thresholds["corp_or_partnership_gifts_usd_inflation_adjusted"] == 16_815.0


# ---------------------------------------------------------------------------
# Auth Tests
# ---------------------------------------------------------------------------

def test_filing_requirement_unauthenticated_401():
    """POST /filing-requirement without token → 401."""
    resp = client.post(f"{BASE}/filing-requirement", json=FILING_REQ_ABOVE)
    assert resp.status_code == 401


def test_gift_calculator_unauthenticated_401():
    """POST /gift-calculator without token → 401."""
    payload = {
        "gifts": [{"donor_type": "INDIVIDUAL", "amount_usd": 120_000.0, "date_received": "2024-03-01", "donor_country": "FR"}],
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/gift-calculator", json=payload)
    assert resp.status_code == 401


def test_trust_reporting_unauthenticated_401():
    """POST /trust-reporting without token → 401."""
    payload = {
        "trust_name": "Test Trust",
        "trust_country": "DE",
        "distributions_received_usd": 5_000.0,
        "is_grantor": True,
        "is_beneficiary": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/trust-reporting", json=payload)
    assert resp.status_code == 401
