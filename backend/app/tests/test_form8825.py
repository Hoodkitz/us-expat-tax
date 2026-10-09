"""
Tests for Form 8825 Rental Real Estate Income and Expenses.

Covers:
- Filing requirement checks (income threshold, entity types)
- Passive loss limitation (active participation, phase-out, real estate professional)
- Income summary calculation (rents, advance rents, security deposits, tenant-paid)
- Expense calculation (all categories)
- Overview endpoint
- API endpoints return 200
- Edge cases: zero income, negative net income, high AGI phase-out
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import get_current_tenant
from app.modules.form8825 import (
    FilingRequirementInput,
    IncomeSummaryInput,
    ExpenseCalculationInput,
    check_filing_requirement,
    calculate_income_summary,
    calculate_expenses,
    get_overview,
    PASSIVE_LOSS_LIMIT,
    PASSIVE_LOSS_PHASE_OUT_START,
    PASSIVE_LOSS_PHASE_OUT_END,
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

# ---------------------------------------------------------------------------
# 1. Filing Requirement Tests
# ---------------------------------------------------------------------------

def test_filing_required_with_rental_income():
    """Filing required when rental income > 0."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=12000.0,
        rental_expenses=8000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is True
    assert result.rental_income == 12000.0
    assert result.net_rental_income == 4000.0
    assert len(result.reasons) > 0

def test_filing_not_required_zero_income():
    """No rental income → filing not required."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=0.0,
        rental_expenses=0.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is False

def test_filing_required_llc_entity():
    """LLC entity type also triggers filing requirement."""
    inp = FilingRequirementInput(
        entity_type="llc",
        rental_income=5000.0,
        rental_expenses=3000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="passive",
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is True
    assert result.entity_type == "llc"

def test_net_rental_income_positive():
    """Net rental income = income - expenses (positive case)."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=20000.0,
        rental_expenses=15000.0,
        tax_year=2025,
        filing_status="married_filing_jointly",
        participation_level="active",
    )
    result = check_filing_requirement(inp)
    assert result.net_rental_income == 5000.0

def test_net_rental_income_negative():
    """Net rental income = income - expenses (negative case = loss)."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=10000.0,
        rental_expenses=15000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
    )
    result = check_filing_requirement(inp)
    assert result.net_rental_income == -5000.0

# ---------------------------------------------------------------------------
# 2. Passive Loss Limitation Tests
# ---------------------------------------------------------------------------

def test_passive_loss_full_deduction_low_agi():
    """Active participation, AGI below phase-out → full $25,000 deduction."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=10000.0,
        rental_expenses=25000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
        modified_agi=80000.0,
    )
    result = check_filing_requirement(inp)
    assert result.passive_loss_limit == PASSIVE_LOSS_LIMIT
    assert result.allowed_passive_loss == 15000.0
    assert result.suspended_passive_loss == 0.0

def test_passive_loss_phase_out_mid_agi():
    """Active participation, AGI in phase-out range → partial deduction."""
    # AGI = 125,000 → 50% through phase-out → limit = 12,500
    # Net rental loss = 30,000 - 10,000 = 20,000
    # Allowed = min(20000, 12500) = 12500, suspended = 20000 - 12500 = 7500
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=10000.0,
        rental_expenses=30000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
        modified_agi=125000.0,
    )
    result = check_filing_requirement(inp)
    assert result.passive_loss_limit == 12500.0
    assert result.allowed_passive_loss == 12500.0
    assert result.suspended_passive_loss == 7500.0

def test_passive_loss_no_deduction_high_agi():
    """Active participation, AGI above phase-out → no passive loss deduction."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=10000.0,
        rental_expenses=30000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
        modified_agi=200000.0,
    )
    result = check_filing_requirement(inp)
    assert result.passive_loss_limit == 0.0
    assert result.allowed_passive_loss == 0.0
    assert result.suspended_passive_loss == 20000.0

def test_real_estate_professional_full_deduction():
    """Real estate professional → full deduction regardless of AGI."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=10000.0,
        rental_expenses=50000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="real_estate_professional",
        modified_agi=300000.0,
    )
    result = check_filing_requirement(inp)
    assert result.allowed_passive_loss == 40000.0
    assert result.suspended_passive_loss == 0.0

def test_passive_participation_no_deduction():
    """Passive participation → all losses suspended."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=10000.0,
        rental_expenses=20000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="passive",
        modified_agi=50000.0,
    )
    result = check_filing_requirement(inp)
    assert result.allowed_passive_loss == 0.0
    assert result.suspended_passive_loss == 10000.0

# ---------------------------------------------------------------------------
# 3. Income Summary Tests
# ---------------------------------------------------------------------------

def test_income_summary_basic():
    """Basic income summary with rents received only."""
    inp = IncomeSummaryInput(
        rents_received=12000.0,
        advance_rents=0.0,
        security_deposits_retained=0.0,
        rental_expenses_paid_by_tenant=0.0,
        tax_year=2025,
    )
    result = calculate_income_summary(inp)
    assert result.total_rental_income == 12000.0
    assert result.gross_rental_income == 12000.0

def test_income_summary_all_sources():
    """Income summary with all income sources."""
    inp = IncomeSummaryInput(
        rents_received=10000.0,
        advance_rents=2000.0,
        security_deposits_retained=500.0,
        rental_expenses_paid_by_tenant=300.0,
        tax_year=2025,
    )
    result = calculate_income_summary(inp)
    assert result.total_rental_income == 12800.0

def test_income_summary_zero():
    """Zero income summary."""
    inp = IncomeSummaryInput(
        rents_received=0.0,
        advance_rents=0.0,
        security_deposits_retained=0.0,
        rental_expenses_paid_by_tenant=0.0,
        tax_year=2025,
    )
    result = calculate_income_summary(inp)
    assert result.total_rental_income == 0.0

# ---------------------------------------------------------------------------
# 4. Expense Calculation Tests
# ---------------------------------------------------------------------------

def test_expenses_basic():
    """Basic expense calculation with common categories."""
    inp = ExpenseCalculationInput(
        advertising=500.0,
        auto_travel=0.0,
        cleaning_maintenance=1200.0,
        commissions=0.0,
        insurance=1800.0,
        legal_professional_fees=0.0,
        management_fees=960.0,
        mortgage_interest=4800.0,
        repairs=600.0,
        supplies=0.0,
        taxes=2400.0,
        utilities=0.0,
        depreciation=3600.0,
        other_expenses=0.0,
        tax_year=2025,
    )
    result = calculate_expenses(inp)
    assert result.total_expenses == 15860.0
    assert result.deductible_expenses == 15860.0
    assert result.non_deductible_expenses == 0.0

def test_expenses_all_categories():
    """Expense calculation with all categories populated."""
    inp = ExpenseCalculationInput(
        advertising=100.0,
        auto_travel=200.0,
        cleaning_maintenance=300.0,
        commissions=400.0,
        insurance=500.0,
        legal_professional_fees=600.0,
        management_fees=700.0,
        mortgage_interest=800.0,
        repairs=900.0,
        supplies=1000.0,
        taxes=1100.0,
        utilities=1200.0,
        depreciation=1300.0,
        other_expenses=1400.0,
        tax_year=2025,
    )
    result = calculate_expenses(inp)
    # Sum: 100+200+300+400+500+600+700+800+900+1000+1100+1200+1300+1400 = 10500
    assert result.total_expenses == 10500.0
    assert result.expense_breakdown["advertising"] == 100.0
    assert result.expense_breakdown["other"] == 1400.0

def test_expenses_zero():
    """Zero expenses."""
    inp = ExpenseCalculationInput(
        advertising=0.0,
        auto_travel=0.0,
        cleaning_maintenance=0.0,
        commissions=0.0,
        insurance=0.0,
        legal_professional_fees=0.0,
        management_fees=0.0,
        mortgage_interest=0.0,
        repairs=0.0,
        supplies=0.0,
        taxes=0.0,
        utilities=0.0,
        depreciation=0.0,
        other_expenses=0.0,
        tax_year=2025,
    )
    result = calculate_expenses(inp)
    assert result.total_expenses == 0.0

# ---------------------------------------------------------------------------
# 5. Overview Tests
# ---------------------------------------------------------------------------

def test_overview_structure():
    """Overview should include all required fields."""
    result = get_overview()
    assert result.title
    assert result.description
    assert len(result.who_must_file) > 0
    assert len(result.income_types) > 0
    assert len(result.expense_categories) > 0
    assert result.passive_loss_rules
    assert result.filing_deadline
    assert len(result.related_forms) > 0
    assert result.recommendation

def test_overview_passive_loss_rules():
    """Overview passive loss rules should mention $25,000 limit."""
    result = get_overview()
    assert "25,000" in result.passive_loss_rules or "25000" in result.passive_loss_rules

def test_overview_income_types():
    """Overview should list key income types."""
    result = get_overview()
    income_types_lower = [x.lower() for x in result.income_types]
    assert any("rent" in x for x in income_types_lower)
    assert any("security deposit" in x for x in income_types_lower)

# ---------------------------------------------------------------------------
# 6. API Endpoint Tests
# ---------------------------------------------------------------------------

def test_api_filing_requirement_endpoint():
    """Test /filing-requirement endpoint."""
    response = client.post(
        "/api/v1/form8825/filing-requirement",
        json={
            "entity_type": "individual",
            "rental_income": 12000.0,
            "rental_expenses": 8000.0,
            "tax_year": 2025,
            "filing_status": "single",
            "participation_level": "active",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filing_required"] is True
    assert data["net_rental_income"] == 4000.0

def test_api_income_summary_endpoint():
    """Test /income-summary endpoint."""
    response = client.post(
        "/api/v1/form8825/income-summary",
        json={
            "rents_received": 10000.0,
            "advance_rents": 2000.0,
            "security_deposits_retained": 500.0,
            "rental_expenses_paid_by_tenant": 300.0,
            "tax_year": 2025,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rental_income"] == 12800.0

def test_api_expenses_endpoint():
    """Test /expenses endpoint."""
    response = client.post(
        "/api/v1/form8825/expense-calculation",
        json={
            "advertising": 500.0,
            "auto_travel": 0.0,
            "cleaning_maintenance": 1200.0,
            "commissions": 0.0,
            "insurance": 1800.0,
            "legal_professional_fees": 0.0,
            "management_fees": 960.0,
            "mortgage_interest": 4800.0,
            "repairs": 600.0,
            "supplies": 0.0,
            "taxes": 2400.0,
            "utilities": 0.0,
            "depreciation": 3600.0,
            "other_expenses": 0.0,
            "tax_year": 2025,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_expenses"] == 15860.0

def test_api_overview_endpoint():
    """Test /overview endpoint."""
    response = client.get("/api/v1/form8825/overview")
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "description" in data
    assert "who_must_file" in data
    assert "expense_categories" in data

# ---------------------------------------------------------------------------
# 7. Edge Cases
# ---------------------------------------------------------------------------

def test_filing_requirement_partnership():
    """Partnership entity type."""
    inp = FilingRequirementInput(
        entity_type="partnership",
        rental_income=5000.0,
        rental_expenses=2000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is True
    assert result.entity_type == "partnership"

def test_filing_requirement_trust():
    """Trust entity type."""
    inp = FilingRequirementInput(
        entity_type="trust",
        rental_income=5000.0,
        rental_expenses=2000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
    )
    result = check_filing_requirement(inp)
    assert result.filing_required is True
    assert result.entity_type == "trust"

def test_related_forms_included():
    """Related forms should be included when filing required."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=12000.0,
        rental_expenses=8000.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
    )
    result = check_filing_requirement(inp)
    assert "Schedule E" in result.related_forms
    assert "Form 4562" in result.related_forms

def test_related_forms_empty_when_not_required():
    """Related forms should be empty when filing not required."""
    inp = FilingRequirementInput(
        entity_type="individual",
        rental_income=0.0,
        rental_expenses=0.0,
        tax_year=2025,
        filing_status="single",
        participation_level="active",
    )
    result = check_filing_requirement(inp)
    assert result.related_forms == []
