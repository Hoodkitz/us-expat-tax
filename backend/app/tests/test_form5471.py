"""
Tests for Form 5471 CFC Reporting Assistant.

Covers (≥25 tests):
- Filing requirement: Category 4 ownership > 50% → must_file = True
- Filing requirement: Category 5 ownership >= 10% → must_file = True
- Filing requirement: Category 5 ownership < 10% → must_file = False
- Filing requirement: Category 2 officer/director → must_file = True
- Filing requirement: Category 2 non-officer < 10% → must_file = False
- Filing requirement: Category 3 ownership >= 10% → must_file = True
- Filing requirement: Category 1 → must_file = True
- Filing requirement: response structure validation
- Subpart F: passive income > 0 → inclusion_required = True
- Subpart F: all zeros → inclusion_required = False
- Subpart F: high_tax_exception_may_apply flag
- Subpart F: response structure validation
- GILTI: basic calculation (inclusion = tested_income − DTIR)
- GILTI: DTIR covers full tested income → gilti_inclusion = 0
- GILTI: ownership_pct < 100% reduces pro-rata share
- GILTI: 50% §250 deduction for corporations
- Income calculation: combined Subpart F + GILTI
- Income calculation: response structure validation
- Income calculation: total_inclusion = subpart_f + gilti
- GET /overview: 200 OK, no auth required
- GET /overview: expected keys present
- POST /filing-requirement without token → 401
- POST /subpart-f-income without token → 401
- POST /gilti-calculator without token → 401
- POST /income-calculation without token → 401
"""
from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import create_access_token

client = TestClient(app)

BASE = "/api/v1/form5471"

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def auth_token() -> str:
    return create_access_token({
        "sub": f"form5471-test-{uuid.uuid4().hex[:8]}@example.com",
        "tenant_id": str(uuid.uuid4()),
    })


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Filing Requirement Tests
# ---------------------------------------------------------------------------


def test_filing_requirement_category4_over50_must_file(auth_token):
    """Category 4 filer with >50% ownership → must_file = True."""
    payload = {
        "category_of_filer": "4",
        "ownership_percentage": 75.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True
    assert "4" in data["categories_triggered"]
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) >= 1
    assert "75" in data["reasons"][0] or "control" in data["reasons"][0].lower()


def test_filing_requirement_category4_exactly50_must_file(auth_token):
    """Category 4 filer with exactly 50% → must_file = True (constructive control)."""
    payload = {
        "category_of_filer": "4",
        "ownership_percentage": 50.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True


def test_filing_requirement_category4_below50_no_filing(auth_token):
    """Category 4 filer with <50% ownership → must_file = False."""
    payload = {
        "category_of_filer": "4",
        "ownership_percentage": 40.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is False
    assert data["categories_triggered"] == []


def test_filing_requirement_category5_over10_must_file(auth_token):
    """Category 5 filer with ≥10% ownership → must_file = True."""
    payload = {
        "category_of_filer": "5",
        "ownership_percentage": 15.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True
    assert "5" in data["categories_triggered"]


def test_filing_requirement_category5_below10_no_filing(auth_token):
    """Category 5 filer with <10% ownership → must_file = False."""
    payload = {
        "category_of_filer": "5",
        "ownership_percentage": 5.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is False
    assert "5" not in data["categories_triggered"]


def test_filing_requirement_category2_officer_must_file(auth_token):
    """Category 2 filer who is an officer → must_file = True."""
    payload = {
        "category_of_filer": "2",
        "ownership_percentage": 5.0,
        "is_officer_or_director": True,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True
    assert "2" in data["categories_triggered"]


def test_filing_requirement_category2_non_officer_below10_no_filing(auth_token):
    """Category 2 filer: not an officer, ownership < 10% → must_file = False."""
    payload = {
        "category_of_filer": "2",
        "ownership_percentage": 3.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is False


def test_filing_requirement_category3_over10_must_file(auth_token):
    """Category 3 filer with ≥10% → must_file = True."""
    payload = {
        "category_of_filer": "3",
        "ownership_percentage": 12.5,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True
    assert "3" in data["categories_triggered"]


def test_filing_requirement_category1_always_must_file(auth_token):
    """Category 1 filer → must_file = True regardless of ownership percentage."""
    payload = {
        "category_of_filer": "1",
        "ownership_percentage": 5.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True
    assert "1" in data["categories_triggered"]


def test_filing_requirement_response_structure(auth_token):
    """Response contains all required keys."""
    payload = {
        "category_of_filer": "4",
        "ownership_percentage": 60.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    for key in ("must_file", "categories_triggered", "reasons", "penalty_if_not_filed", "due_date"):
        assert key in data, f"Missing key: {key}"
    assert "10,000" in data["penalty_if_not_filed"]
    assert str(2025) in data["due_date"]  # tax_year + 1


# ---------------------------------------------------------------------------
# Subpart F Income Tests
# ---------------------------------------------------------------------------


def test_subpart_f_passive_income_triggers_inclusion(auth_token):
    """Passive income > 0 → inclusion_required = True."""
    payload = {
        "passive_income_usd": 50_000.0,
        "sales_income_usd": 0.0,
        "services_income_usd": 0.0,
        "foreign_base_company_income_usd": 0.0,
        "total_cfc_income_usd": 200_000.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/subpart-f-income", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["inclusion_required"] is True
    assert data["subpart_f_total_usd"] == 50_000.0


def test_subpart_f_fbci_triggers_inclusion(auth_token):
    """Foreign base company income > 0 → inclusion_required = True."""
    payload = {
        "passive_income_usd": 0.0,
        "sales_income_usd": 0.0,
        "services_income_usd": 0.0,
        "foreign_base_company_income_usd": 30_000.0,
        "total_cfc_income_usd": 100_000.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/subpart-f-income", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["inclusion_required"] is True
    assert data["subpart_f_total_usd"] == 30_000.0


def test_subpart_f_zero_income_no_inclusion(auth_token):
    """All income zeros → inclusion_required = False."""
    payload = {
        "passive_income_usd": 0.0,
        "sales_income_usd": 0.0,
        "services_income_usd": 0.0,
        "foreign_base_company_income_usd": 0.0,
        "total_cfc_income_usd": 0.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/subpart-f-income", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["inclusion_required"] is False
    assert data["subpart_f_total_usd"] == 0.0


def test_subpart_f_high_tax_exception_flag(auth_token):
    """Active income (sales + services) > subpart_f → high_tax_exception_may_apply = True."""
    payload = {
        "passive_income_usd": 10_000.0,
        "sales_income_usd": 80_000.0,
        "services_income_usd": 40_000.0,
        "foreign_base_company_income_usd": 5_000.0,
        "total_cfc_income_usd": 200_000.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/subpart-f-income", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["high_tax_exception_may_apply"] is True
    assert data["effective_foreign_rate_threshold_pct"] == 18.9


def test_subpart_f_response_structure(auth_token):
    """Response contains all required keys."""
    payload = {
        "passive_income_usd": 10_000.0,
        "sales_income_usd": 5_000.0,
        "services_income_usd": 5_000.0,
        "foreign_base_company_income_usd": 0.0,
        "total_cfc_income_usd": 50_000.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/subpart-f-income", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    for key in (
        "subpart_f_total_usd",
        "inclusion_required",
        "high_tax_exception_may_apply",
        "effective_foreign_rate_threshold_pct",
        "recommendations",
    ):
        assert key in data, f"Missing key: {key}"
    assert isinstance(data["recommendations"], list)


# ---------------------------------------------------------------------------
# GILTI Calculator Tests
# ---------------------------------------------------------------------------


def test_gilti_basic_calculation(auth_token):
    """Basic GILTI: 500k tested income, 1M QBAI at 10% → DTIR=100k, GILTI=400k."""
    payload = {
        "net_tested_income_usd": 500_000.0,
        "qualified_business_asset_investment_usd": 1_000_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
    }
    resp = client.post(f"{BASE}/gilti-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["dtir_usd"] == pytest.approx(100_000.0)
    assert data["gilti_inclusion_usd"] == pytest.approx(400_000.0)
    assert data["net_cfc_tested_income_usd"] == pytest.approx(500_000.0)


def test_gilti_dtir_exceeds_tested_income_zero_inclusion(auth_token):
    """DTIR > net tested income → gilti_inclusion_usd = 0."""
    payload = {
        "net_tested_income_usd": 50_000.0,
        "qualified_business_asset_investment_usd": 1_000_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
    }
    resp = client.post(f"{BASE}/gilti-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    # DTIR = 1,000,000 × 10% = 100,000 > 50,000
    assert data["gilti_inclusion_usd"] == 0.0
    assert "no gilti inclusion" in data["explanation"].lower() or "$0" in data["explanation"]


def test_gilti_ownership_pct_reduces_share(auth_token):
    """50% ownership → pro-rata share is halved."""
    payload = {
        "net_tested_income_usd": 400_000.0,
        "qualified_business_asset_investment_usd": 1_000_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 50.0,
    }
    resp = client.post(f"{BASE}/gilti-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    # Net tested income pro-rated: 400,000 × 50% = 200,000
    # DTIR pro-rated: 1,000,000 × 10% × 50% = 50,000
    # GILTI = 200,000 − 50,000 = 150,000
    assert data["net_cfc_tested_income_usd"] == pytest.approx(200_000.0)
    assert data["dtir_usd"] == pytest.approx(50_000.0)
    assert data["gilti_inclusion_usd"] == pytest.approx(150_000.0)


def test_gilti_section250_deduction_for_corporations(auth_token):
    """§250 deduction = 50% of GILTI inclusion for corporations."""
    payload = {
        "net_tested_income_usd": 1_000_000.0,
        "qualified_business_asset_investment_usd": 2_000_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
    }
    resp = client.post(f"{BASE}/gilti-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    # DTIR = 200,000; GILTI = 800,000; §250 = 400,000
    assert data["gilti_inclusion_usd"] == pytest.approx(800_000.0)
    assert data["deduction_80pct_corporations"] == pytest.approx(400_000.0)


def test_gilti_default_dtir_rate_10pct(auth_token):
    """Default deemed_tangible_income_return_pct of 10% is applied when not provided."""
    payload = {
        "net_tested_income_usd": 300_000.0,
        "qualified_business_asset_investment_usd": 500_000.0,
        "ownership_pct": 100.0,
    }
    resp = client.post(f"{BASE}/gilti-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    # Default 10%: DTIR = 50,000; GILTI = 250,000
    assert data["dtir_usd"] == pytest.approx(50_000.0)
    assert data["gilti_inclusion_usd"] == pytest.approx(250_000.0)


def test_gilti_explanation_present(auth_token):
    """GILTI response contains a non-empty explanation string."""
    payload = {
        "net_tested_income_usd": 200_000.0,
        "qualified_business_asset_investment_usd": 500_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
    }
    resp = client.post(f"{BASE}/gilti-calculator", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["explanation"], str)
    assert len(data["explanation"]) > 40


# ---------------------------------------------------------------------------
# Overview Tests
# ---------------------------------------------------------------------------


def test_overview_returns_200_no_auth():
    """GET /overview is publicly accessible (no auth) and returns 200."""
    resp = client.get(f"{BASE}/overview")
    assert resp.status_code == 200


def test_overview_expected_keys():
    """Overview response contains all required top-level keys."""
    resp = client.get(f"{BASE}/overview")
    assert resp.status_code == 200
    data = resp.json()
    for key in (
        "form",
        "title",
        "irc_section",
        "purpose",
        "categories_of_filers",
        "key_concepts",
        "penalties",
        "due_date",
        "gilti_high_tax_threshold_pct",
        "irs_reference",
    ):
        assert key in data, f"Missing key: {key}"


def test_overview_form_identifier():
    """Overview identifies as Form 5471."""
    resp = client.get(f"{BASE}/overview")
    data = resp.json()
    assert data["form"] == "Form 5471"
    assert "5471" in data["irs_reference"]


def test_overview_categories_all_five_present():
    """Overview has all 5 filer categories."""
    resp = client.get(f"{BASE}/overview")
    data = resp.json()
    cats = data["categories_of_filers"]
    for i in ("1", "2", "3", "4", "5"):
        assert i in cats, f"Category {i} missing from overview"


# ---------------------------------------------------------------------------
# Auth Tests (401 without JWT)
# ---------------------------------------------------------------------------


def test_filing_requirement_unauthenticated_401():
    """POST /filing-requirement without token → 401."""
    payload = {
        "category_of_filer": "4",
        "ownership_percentage": 60.0,
        "is_officer_or_director": False,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/filing-requirement", json=payload)
    assert resp.status_code == 401


def test_subpart_f_unauthenticated_401():
    """POST /subpart-f-income without token → 401."""
    payload = {
        "passive_income_usd": 50_000.0,
        "sales_income_usd": 0.0,
        "services_income_usd": 0.0,
        "foreign_base_company_income_usd": 0.0,
        "total_cfc_income_usd": 100_000.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/subpart-f-income", json=payload)
    assert resp.status_code == 401


def test_gilti_unauthenticated_401():
    """POST /gilti-calculator without token → 401."""
    payload = {
        "net_tested_income_usd": 500_000.0,
        "qualified_business_asset_investment_usd": 1_000_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
    }
    resp = client.post(f"{BASE}/gilti-calculator", json=payload)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Income Calculation (Combined Subpart F + GILTI) Tests
# ---------------------------------------------------------------------------


def test_income_calculation_combined(auth_token):
    """Combined income calculation returns both subpart_f and gilti results."""
    payload = {
        "passive_income_usd": 50_000.0,
        "sales_income_usd": 20_000.0,
        "services_income_usd": 10_000.0,
        "foreign_base_company_income_usd": 30_000.0,
        "total_cfc_income_usd": 200_000.0,
        "net_tested_income_usd": 500_000.0,
        "qualified_business_asset_investment_usd": 1_000_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/income-calculation", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "subpart_f" in data
    assert "gilti" in data
    assert "total_inclusion_usd" in data
    assert data["subpart_f"]["subpart_f_total_usd"] == 80_000.0
    assert data["gilti"]["gilti_inclusion_usd"] == 400_000.0
    assert data["total_inclusion_usd"] == 480_000.0


def test_income_calculation_response_structure(auth_token):
    """Income calculation response contains all required keys."""
    payload = {
        "passive_income_usd": 10_000.0,
        "sales_income_usd": 5_000.0,
        "services_income_usd": 5_000.0,
        "foreign_base_company_income_usd": 5_000.0,
        "total_cfc_income_usd": 50_000.0,
        "net_tested_income_usd": 300_000.0,
        "qualified_business_asset_investment_usd": 500_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/income-calculation", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    for key in ("subpart_f", "gilti", "total_inclusion_usd", "tax_year"):
        assert key in data, f"Missing key: {key}"
    assert isinstance(data["subpart_f"], dict)
    assert isinstance(data["gilti"], dict)
    assert data["tax_year"] == 2024


def test_income_calculation_total_inclusion(auth_token):
    """total_inclusion_usd = subpart_f_total_usd + gilti_inclusion_usd."""
    payload = {
        "passive_income_usd": 25_000.0,
        "sales_income_usd": 0.0,
        "services_income_usd": 0.0,
        "foreign_base_company_income_usd": 25_000.0,
        "total_cfc_income_usd": 100_000.0,
        "net_tested_income_usd": 200_000.0,
        "qualified_business_asset_investment_usd": 1_000_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/income-calculation", json=payload, headers=auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.json()
    expected_total = data["subpart_f"]["subpart_f_total_usd"] + data["gilti"]["gilti_inclusion_usd"]
    assert data["total_inclusion_usd"] == pytest.approx(expected_total)


def test_income_calculation_unauthenticated_401():
    """POST /income-calculation without token → 401."""
    payload = {
        "passive_income_usd": 10_000.0,
        "sales_income_usd": 0.0,
        "services_income_usd": 0.0,
        "foreign_base_company_income_usd": 0.0,
        "total_cfc_income_usd": 50_000.0,
        "net_tested_income_usd": 100_000.0,
        "qualified_business_asset_investment_usd": 500_000.0,
        "deemed_tangible_income_return_pct": 10.0,
        "ownership_pct": 100.0,
        "tax_year": 2024,
    }
    resp = client.post(f"{BASE}/income-calculation", json=payload)
    assert resp.status_code == 401
