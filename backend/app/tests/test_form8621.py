"""
Tests for Form 8621 PFIC Reporting.

Covers:
- Filing requirement check (ownership, sale, distribution)
- MTM election: unrealized gains/losses as ordinary income/loss
- QEF election: pro-rata ordinary earnings + capital gains
- Excess distribution: deferred tax + interest charge
- Default regime allocation over holding period
- Edge cases: zero distributions, no prior distributions
- Penalty amounts for non-filing
- All endpoints return 200
- Calculation accuracy for all three regimes
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.form8621 import (
    FilingRequirementInput,
    MTMCalculationInput,
    QEFCalculationInput,
    ExcessDistributionInput,
    check_filing_requirement,
    calculate_mtm,
    calculate_qef,
    calculate_excess_distribution,
    PENALTY_FAILURE_TO_FILE,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# 1. Filing Requirement Tests
# ---------------------------------------------------------------------------

def test_filing_required_pfic_interest():
    """Filing required if taxpayer holds PFIC interest."""
    inp = FilingRequirementInput(
        has_pfic_interest=True,
        had_sale_or_distribution=False,
        received_excess_distribution=False,
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is True
    assert "hold a direct or indirect interest" in result.reasons[0]
    assert result.penalty_if_not_filed == PENALTY_FAILURE_TO_FILE

def test_filing_required_sale_or_distribution():
    """Filing required if taxpayer sold PFIC or received distribution."""
    inp = FilingRequirementInput(
        has_pfic_interest=False,
        had_sale_or_distribution=True,
        received_excess_distribution=False,
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is True
    assert "sold PFIC shares or received a distribution" in result.reasons[0]

def test_filing_required_excess_distribution():
    """Filing required if taxpayer received excess distribution."""
    inp = FilingRequirementInput(
        has_pfic_interest=False,
        had_sale_or_distribution=False,
        received_excess_distribution=True,
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is True
    assert "excess distribution" in result.reasons[0]

def test_filing_not_required():
    """No filing requirement if no PFIC activity."""
    inp = FilingRequirementInput(
        has_pfic_interest=False,
        had_sale_or_distribution=False,
        received_excess_distribution=False,
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is False
    assert result.penalty_if_not_filed == 0.0
    assert "not required" in result.recommendation

def test_filing_endpoint():
    """POST /filing-requirement returns 200."""
    response = client.post(
        "/api/v1/form8621/filing-requirement",
        json={
            "has_pfic_interest": True,
            "had_sale_or_distribution": False,
            "received_excess_distribution": False,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filing_required"] is True

# ---------------------------------------------------------------------------
# 2. Mark-to-Market (MTM) Election Tests
# ---------------------------------------------------------------------------

def test_mtm_unrealized_gain():
    """MTM election: unrealized gain → ordinary income."""
    inp = MTMCalculationInput(
        beginning_fmv=100_000.0,
        ending_fmv=115_000.0,
        tax_year=2024,
    )
    result = calculate_mtm(inp)
    assert result.unrealized_gain_or_loss == 15_000.0
    assert result.ordinary_income_or_loss == 15_000.0
    assert result.tax_treatment == "Ordinary Income"
    assert "ORDINARY INCOME" in result.explanation

def test_mtm_unrealized_loss():
    """MTM election: unrealized loss → ordinary loss."""
    inp = MTMCalculationInput(
        beginning_fmv=100_000.0,
        ending_fmv=85_000.0,
        tax_year=2024,
    )
    result = calculate_mtm(inp)
    assert result.unrealized_gain_or_loss == -15_000.0
    assert result.ordinary_income_or_loss == -15_000.0
    assert result.tax_treatment == "Ordinary Loss"
    assert "ORDINARY LOSS" in result.explanation

def test_mtm_no_change():
    """MTM election: no FMV change → no gain/loss."""
    inp = MTMCalculationInput(
        beginning_fmv=100_000.0,
        ending_fmv=100_000.0,
        tax_year=2024,
    )
    result = calculate_mtm(inp)
    assert result.unrealized_gain_or_loss == 0.0
    assert result.ordinary_income_or_loss == 0.0

def test_mtm_endpoint():
    """POST /mtm-calculation returns 200."""
    response = client.post(
        "/api/v1/form8621/mtm-calculation",
        json={
            "beginning_fmv": 100_000.0,
            "ending_fmv": 115_000.0,
            "tax_year": 2024,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unrealized_gain_or_loss"] == 15_000.0

# ---------------------------------------------------------------------------
# 3. QEF Election Tests
# ---------------------------------------------------------------------------

def test_qef_ordinary_and_capital():
    """QEF election: include pro-rata ordinary earnings + capital gains."""
    inp = QEFCalculationInput(
        ordinary_earnings=5_000.0,
        net_capital_gain=2_000.0,
        ownership_percentage=10.0,
        tax_year=2024,
    )
    result = calculate_qef(inp)
    # 10% ownership
    assert result.ordinary_earnings_includible == 500.0
    assert result.capital_gain_includible == 200.0
    assert result.total_inclusion == 700.0
    assert "pro-rata share" in result.explanation

def test_qef_100_percent_ownership():
    """QEF election: 100% ownership → full inclusion."""
    inp = QEFCalculationInput(
        ordinary_earnings=10_000.0,
        net_capital_gain=3_000.0,
        ownership_percentage=100.0,
        tax_year=2024,
    )
    result = calculate_qef(inp)
    assert result.ordinary_earnings_includible == 10_000.0
    assert result.capital_gain_includible == 3_000.0
    assert result.total_inclusion == 13_000.0

def test_qef_zero_capital_gain():
    """QEF election: only ordinary earnings, no capital gain."""
    inp = QEFCalculationInput(
        ordinary_earnings=8_000.0,
        net_capital_gain=0.0,
        ownership_percentage=25.0,
        tax_year=2024,
    )
    result = calculate_qef(inp)
    assert result.ordinary_earnings_includible == 2_000.0
    assert result.capital_gain_includible == 0.0
    assert result.total_inclusion == 2_000.0

def test_qef_endpoint():
    """POST /qef-calculation returns 200."""
    response = client.post(
        "/api/v1/form8621/qef-calculation",
        json={
            "ordinary_earnings": 5_000.0,
            "net_capital_gain": 2_000.0,
            "ownership_percentage": 10.0,
            "tax_year": 2024,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_inclusion"] == 700.0

# ---------------------------------------------------------------------------
# 4. Excess Distribution Tests (Default Regime)
# ---------------------------------------------------------------------------

def test_excess_distribution_exceeds_threshold():
    """Excess distribution: distribution > 125% of average → excess."""
    inp = ExcessDistributionInput(
        total_distribution=20_000.0,
        holding_period_years=5,
        prior_distributions=[8_000.0, 7_500.0, 9_000.0],
        tax_year=2024,
    )
    result = calculate_excess_distribution(inp)
    
    # Average = (8000 + 7500 + 9000) / 3 = 8166.67
    # Threshold = 8166.67 * 1.25 = 10208.33
    # Excess = 20000 - 10208.33 = 9791.67
    assert result.average_distribution == pytest.approx(8166.67, rel=0.01)
    assert result.excess_amount > 0
    assert result.deferred_tax_amount > 0
    assert result.interest_charge > 0
    assert len(result.allocation_by_year) == 5

def test_excess_distribution_below_threshold():
    """No excess distribution if below 125% threshold."""
    inp = ExcessDistributionInput(
        total_distribution=9_000.0,
        holding_period_years=5,
        prior_distributions=[8_000.0, 7_500.0, 9_000.0],
        tax_year=2024,
    )
    result = calculate_excess_distribution(inp)
    
    # Average = 8166.67, Threshold = 10208.33
    # 9000 < 10208.33 → no excess
    assert result.excess_amount == 0.0
    assert result.deferred_tax_amount == 0.0
    assert result.interest_charge == 0.0

def test_excess_distribution_no_prior_distributions():
    """No prior distributions → entire distribution is excess."""
    inp = ExcessDistributionInput(
        total_distribution=15_000.0,
        holding_period_years=3,
        prior_distributions=[],
        tax_year=2024,
    )
    result = calculate_excess_distribution(inp)
    
    # Average = 0, Threshold = 0
    # Entire distribution is excess
    assert result.average_distribution == 0.0
    assert result.excess_amount == 15_000.0
    assert result.deferred_tax_amount > 0
    assert result.interest_charge > 0

def test_excess_distribution_allocation():
    """Excess distribution is allocated pro-rata over holding period."""
    inp = ExcessDistributionInput(
        total_distribution=20_000.0,
        holding_period_years=4,
        prior_distributions=[5_000.0, 6_000.0],
        tax_year=2024,
    )
    result = calculate_excess_distribution(inp)
    
    # Verify allocation breakdown
    assert len(result.allocation_by_year) == 4
    # Each year should have equal allocation
    allocations = [item["allocated_amount"] for item in result.allocation_by_year]
    assert len(set(allocations)) == 1  # All allocations equal

def test_excess_distribution_endpoint():
    """POST /excess-distribution returns 200."""
    response = client.post(
        "/api/v1/form8621/excess-distribution",
        json={
            "total_distribution": 20_000.0,
            "holding_period_years": 5,
            "prior_distributions": [8_000.0, 7_500.0, 9_000.0],
            "tax_year": 2024,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "excess_amount" in data
    assert "deferred_tax_amount" in data

# ---------------------------------------------------------------------------
# 5. Overview Endpoint
# ---------------------------------------------------------------------------

def test_overview_endpoint():
    """GET /overview returns 200 with regime descriptions."""
    response = client.get("/api/v1/form8621/overview")
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "regimes" in data
    assert "default" in data["regimes"]
    assert "qef" in data["regimes"]
    assert "mtm" in data["regimes"]
    assert "penalties" in data

# ---------------------------------------------------------------------------
# 6. Edge Cases and Validation
# ---------------------------------------------------------------------------

def test_mtm_zero_beginning_fmv():
    """MTM with zero beginning FMV."""
    inp = MTMCalculationInput(
        beginning_fmv=0.0,
        ending_fmv=50_000.0,
        tax_year=2024,
    )
    result = calculate_mtm(inp)
    assert result.unrealized_gain_or_loss == 50_000.0

def test_qef_zero_ownership():
    """QEF with zero ownership → zero inclusion."""
    inp = QEFCalculationInput(
        ordinary_earnings=10_000.0,
        net_capital_gain=5_000.0,
        ownership_percentage=0.0,
        tax_year=2024,
    )
    result = calculate_qef(inp)
    assert result.total_inclusion == 0.0

def test_excess_distribution_single_year_holding():
    """Excess distribution with 1-year holding period."""
    inp = ExcessDistributionInput(
        total_distribution=10_000.0,
        holding_period_years=1,
        prior_distributions=[],
        tax_year=2024,
    )
    result = calculate_excess_distribution(inp)
    assert len(result.allocation_by_year) == 1
    assert result.allocation_by_year[0]["allocated_amount"] == 10_000.0

def test_penalty_amount_constant():
    """Penalty for failure to file is $10,000."""
    assert PENALTY_FAILURE_TO_FILE == 10_000.0

# ---------------------------------------------------------------------------
# 7. Integration Tests
# ---------------------------------------------------------------------------

def test_all_endpoints_accessible():
    """Verify all 5 endpoints are accessible."""
    endpoints = [
        ("/api/v1/form8621/filing-requirement", "POST", {
            "has_pfic_interest": True,
            "had_sale_or_distribution": False,
            "received_excess_distribution": False,
        }),
        ("/api/v1/form8621/mtm-calculation", "POST", {
            "beginning_fmv": 100_000.0,
            "ending_fmv": 110_000.0,
            "tax_year": 2024,
        }),
        ("/api/v1/form8621/qef-calculation", "POST", {
            "ordinary_earnings": 5_000.0,
            "net_capital_gain": 2_000.0,
            "ownership_percentage": 10.0,
            "tax_year": 2024,
        }),
        ("/api/v1/form8621/excess-distribution", "POST", {
            "total_distribution": 15_000.0,
            "holding_period_years": 3,
            "prior_distributions": [5_000.0],
            "tax_year": 2024,
        }),
        ("/api/v1/form8621/overview", "GET", None),
    ]
    
    for endpoint, method, payload in endpoints:
        if method == "POST":
            response = client.post(endpoint, json=payload)
        else:
            response = client.get(endpoint)
        assert response.status_code == 200, f"{endpoint} failed with {response.status_code}"

def test_mtm_large_numbers():
    """MTM calculation with large numbers."""
    inp = MTMCalculationInput(
        beginning_fmv=1_000_000.0,
        ending_fmv=1_500_000.0,
        tax_year=2024,
    )
    result = calculate_mtm(inp)
    assert result.unrealized_gain_or_loss == 500_000.0

def test_excess_distribution_interest_charge_positive():
    """Interest charge is positive when excess exists."""
    inp = ExcessDistributionInput(
        total_distribution=30_000.0,
        holding_period_years=10,
        prior_distributions=[5_000.0, 6_000.0, 5_500.0],
        tax_year=2024,
    )
    result = calculate_excess_distribution(inp)
    if result.excess_amount > 0:
        assert result.interest_charge > 0
        assert result.total_tax_and_interest > result.deferred_tax_amount
