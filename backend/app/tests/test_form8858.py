"""
Tests for Form 8858 FDE/FB Reporter.

Covers 20 tests:
- direct_fde + is_us_person=True -> must_file=True
- direct_fde + is_us_person=False -> must_file=False
- indirect_fde ownership >= 10 -> must_file=True
- indirect_fde ownership < 10 -> must_file=False
- foreign_branch is_us_person=True -> must_file=True
- cfc_fde always must_file=True (regardless of is_us_person)
- filing-requirement: has penalty_if_not_filed_usd=10000 in response
- filing-requirement response structure validation
- income-summary: profitable entity (gross > deductions)
- income-summary: loss entity (gross < deductions)
- income-summary: all zeros -> net 0, is_profitable=False
- income-summary: cost_of_goods_sold reduces gross_income
- penalty: 1 year no continuation -> 10000
- penalty: 2 years 3 continuation periods -> 80000, criminal=True
- penalty: max continuation 5 periods, 1 year -> 60000, criminal=True
- penalty: 1 year 0 continuation -> 10000, criminal=False
- GET /overview: 200 OK no auth
- GET /overview: has 'form_name' key
- POST /filing-requirement without token -> 401
- POST /income-summary without token -> 401
- POST /penalty-calculator without token -> 401
"""
from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import create_access_token

client = TestClient(app)

BASE = "/api/v1/form8858"

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def auth_token() -> str:
    return create_access_token({
        "sub": f"form8858-test-{uuid.uuid4().hex[:8]}@example.com",
        "tenant_id": str(uuid.uuid4()),
    })


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Filing Requirement Tests
# ---------------------------------------------------------------------------


def test_filing_requirement_direct_fde_us_person_must_file(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "direct_fde",
            "ownership_percentage": 100.0,
            "is_us_person": True,
            "entity_country": "Germany",
            "tax_year": 2024,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True


def test_filing_requirement_direct_fde_non_us_person_no_file(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "direct_fde",
            "ownership_percentage": 100.0,
            "is_us_person": False,
            "entity_country": "France",
            "tax_year": 2024,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is False


def test_filing_requirement_indirect_fde_above_threshold_must_file(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "indirect_fde",
            "ownership_percentage": 15.0,
            "is_us_person": True,
            "entity_country": "Japan",
            "tax_year": 2024,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True


def test_filing_requirement_indirect_fde_below_threshold_no_file(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "indirect_fde",
            "ownership_percentage": 9.9,
            "is_us_person": True,
            "entity_country": "Canada",
            "tax_year": 2024,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is False


def test_filing_requirement_foreign_branch_us_person_must_file(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "foreign_branch",
            "ownership_percentage": 100.0,
            "is_us_person": True,
            "entity_country": "United Kingdom",
            "tax_year": 2024,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True


def test_filing_requirement_cfc_fde_always_must_file(auth_token: str) -> None:
    """CFC-owned FDE always requires Form 8858 regardless of other factors."""
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "cfc_fde",
            "ownership_percentage": 0.0,
            "is_us_person": False,
            "entity_country": "Cayman Islands",
            "tax_year": 2024,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["must_file"] is True


def test_filing_requirement_has_penalty_field(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "direct_fde",
            "ownership_percentage": 100.0,
            "is_us_person": True,
            "entity_country": "Australia",
            "tax_year": 2023,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["penalty_if_not_filed_usd"] == 10_000


def test_filing_requirement_response_structure(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "foreign_branch",
            "ownership_percentage": 100.0,
            "is_us_person": True,
            "entity_country": "Singapore",
            "tax_year": 2024,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "must_file" in data
    assert "reason" in data
    assert "form_due_date" in data
    assert "penalty_if_not_filed_usd" in data
    assert "filing_instructions" in data


# ---------------------------------------------------------------------------
# Income Summary Tests
# ---------------------------------------------------------------------------


def test_income_summary_profitable_entity(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/income-summary",
        json={
            "gross_receipts_usd": 500_000.0,
            "cost_of_goods_sold_usd": 100_000.0,
            "operating_expenses_usd": 80_000.0,
            "depreciation_usd": 20_000.0,
            "other_income_usd": 10_000.0,
            "other_deductions_usd": 5_000.0,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_profitable"] is True
    assert data["net_income_loss_usd"] > 0


def test_income_summary_loss_entity(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/income-summary",
        json={
            "gross_receipts_usd": 50_000.0,
            "cost_of_goods_sold_usd": 30_000.0,
            "operating_expenses_usd": 80_000.0,
            "depreciation_usd": 10_000.0,
            "other_income_usd": 0.0,
            "other_deductions_usd": 5_000.0,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_profitable"] is False
    assert data["net_income_loss_usd"] < 0


def test_income_summary_all_zeros_break_even(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/income-summary",
        json={
            "gross_receipts_usd": 0.0,
            "cost_of_goods_sold_usd": 0.0,
            "operating_expenses_usd": 0.0,
            "depreciation_usd": 0.0,
            "other_income_usd": 0.0,
            "other_deductions_usd": 0.0,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["net_income_loss_usd"] == 0.0
    assert data["is_profitable"] is False


def test_income_summary_cogs_reduces_gross_income(auth_token: str) -> None:
    """cost_of_goods_sold should reduce gross_income correctly."""
    resp = client.post(
        f"{BASE}/income-summary",
        json={
            "gross_receipts_usd": 200_000.0,
            "cost_of_goods_sold_usd": 50_000.0,
            "operating_expenses_usd": 0.0,
            "depreciation_usd": 0.0,
            "other_income_usd": 0.0,
            "other_deductions_usd": 0.0,
        },
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["gross_income_usd"] == pytest.approx(150_000.0)


# ---------------------------------------------------------------------------
# Penalty Calculator Tests
# ---------------------------------------------------------------------------


def test_penalty_one_year_no_continuation(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/penalty-calculator",
        json={"years_not_filed": 1, "continued_failure_periods": 0},
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["base_penalty_usd"] == 10_000
    assert data["continuation_penalty_usd"] == 0
    assert data["total_penalty_usd"] == 10_000
    assert data["criminal_risk_flag"] is False


def test_penalty_two_years_three_continuation_periods(auth_token: str) -> None:
    """2 years × $10k base = $20k; 3 continuation × $10k × 2 years = $60k; total = $80k."""
    resp = client.post(
        f"{BASE}/penalty-calculator",
        json={"years_not_filed": 2, "continued_failure_periods": 3},
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["base_penalty_usd"] == 20_000
    assert data["continuation_penalty_usd"] == 60_000
    assert data["total_penalty_usd"] == 80_000
    assert data["criminal_risk_flag"] is True


def test_penalty_max_continuation_one_year(auth_token: str) -> None:
    """1 year × $10k base = $10k; 5 continuation × $10k × 1 year = $50k; total = $60k."""
    resp = client.post(
        f"{BASE}/penalty-calculator",
        json={"years_not_filed": 1, "continued_failure_periods": 5},
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["base_penalty_usd"] == 10_000
    assert data["continuation_penalty_usd"] == 50_000
    assert data["total_penalty_usd"] == 60_000
    assert data["criminal_risk_flag"] is True


def test_penalty_one_year_zero_continuation_no_criminal_risk(auth_token: str) -> None:
    resp = client.post(
        f"{BASE}/penalty-calculator",
        json={"years_not_filed": 1, "continued_failure_periods": 0},
        headers=auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_penalty_usd"] == 10_000
    assert data["criminal_risk_flag"] is False


# ---------------------------------------------------------------------------
# Overview Tests (no auth)
# ---------------------------------------------------------------------------


def test_overview_returns_200_no_auth() -> None:
    resp = client.get(f"{BASE}/overview")
    assert resp.status_code == 200


def test_overview_has_form_name_key() -> None:
    resp = client.get(f"{BASE}/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "form_name" in data
    assert "Form 8858" in data["form_name"]


# ---------------------------------------------------------------------------
# Authentication / 401 Tests
# ---------------------------------------------------------------------------


def test_filing_requirement_without_token_returns_401() -> None:
    resp = client.post(
        f"{BASE}/filing-requirement",
        json={
            "ownership_type": "direct_fde",
            "ownership_percentage": 100.0,
            "is_us_person": True,
            "entity_country": "Germany",
            "tax_year": 2024,
        },
    )
    assert resp.status_code == 401


def test_income_summary_without_token_returns_401() -> None:
    resp = client.post(
        f"{BASE}/income-summary",
        json={
            "gross_receipts_usd": 100_000.0,
            "cost_of_goods_sold_usd": 50_000.0,
            "operating_expenses_usd": 20_000.0,
            "depreciation_usd": 5_000.0,
            "other_income_usd": 0.0,
            "other_deductions_usd": 0.0,
        },
    )
    assert resp.status_code == 401


def test_penalty_calculator_without_token_returns_401() -> None:
    resp = client.post(
        f"{BASE}/penalty-calculator",
        json={"years_not_filed": 1, "continued_failure_periods": 0},
    )
    assert resp.status_code == 401
