"""
Tests for Form 8825 – Rental Real Estate Income and Expenses.

Covers:
- Filing requirement checks
- Income summary calculations
- Expense calculations
- Passive activity loss limitations
- API router endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
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


@pytest.fixture
def override_auth_dependency():
    """Override get_current_tenant for tests that need it."""
    from app.auth.utils import get_current_tenant

    async def mock_get_current_tenant():
        return {
            "tenant_id": "test-tenant-123",
            "email": "test@example.com",
            "tenant_name": "Test Tenant",
        }

    app.dependency_overrides[get_current_tenant] = mock_get_current_tenant
    yield
    app.dependency_overrides.clear()


# ===========================================================================
# Unit Tests – check_filing_requirement
# ===========================================================================

class TestCheckFilingRequirement:
    """Tests for check_filing_requirement function."""

    def test_no_rental_income_not_required(self):
        """No rental income → filing not required."""
        inp = FilingRequirementInput(
            entity_type="individual",
            rental_income=0,
            rental_expenses=0,
            tax_year=2024,
            filing_status="single",
            participation_level="active",
            modified_agi=0,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False
        assert result.net_rental_income == 0
        assert len(result.reasons) > 0

    def test_rental_income_positive_required(self):
        """Positive rental income → filing required."""
        inp = FilingRequirementInput(
            entity_type="individual",
            rental_income=12000,
            rental_expenses=8000,
            tax_year=2024,
            filing_status="single",
            participation_level="active",
            modified_agi=50000,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.net_rental_income == 4000
        assert result.related_forms == ["Schedule E", "Form 4562"]

    def test_rental_income_with_loss_active_participation(self):
        """Rental loss with active participation → partial deduction."""
        inp = FilingRequirementInput(
            entity_type="individual",
            rental_income=10000,
            rental_expenses=30000,
            tax_year=2024,
            filing_status="single",
            participation_level="active",
            modified_agi=50000,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.net_rental_income == -20000
        # Loss is 20000, which is less than PASSIVE_LOSS_LIMIT (25000)
        assert result.allowed_passive_loss == 20000
        assert result.suspended_passive_loss == 0

    def test_rental_loss_passive_participation_suspended(self):
        """Rental loss with passive participation → all suspended."""
        inp = FilingRequirementInput(
            entity_type="individual",
            rental_income=5000,
            rental_expenses=20000,
            tax_year=2024,
            filing_status="single",
            participation_level="passive",
            modified_agi=50000,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.net_rental_income == -15000
        assert result.allowed_passive_loss == 0
        assert result.suspended_passive_loss == 15000

    def test_real_estate_professional_full_deduction(self):
        """Real estate professional → full loss deduction."""
        inp = FilingRequirementInput(
            entity_type="individual",
            rental_income=5000,
            rental_expenses=50000,
            tax_year=2024,
            filing_status="single",
            participation_level="real_estate_professional",
            modified_agi=200000,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.net_rental_income == -45000
        assert result.allowed_passive_loss == 45000
        assert result.suspended_passive_loss == 0

    def test_phase_out_midpoint(self):
        """AGI at phase-out midpoint → reduced passive loss limit."""
        mid_agi = (PASSIVE_LOSS_PHASE_OUT_START + PASSIVE_LOSS_PHASE_OUT_END) / 2
        inp = FilingRequirementInput(
            entity_type="individual",
            rental_income=0,
            rental_expenses=30000,
            tax_year=2024,
            filing_status="single",
            participation_level="active",
            modified_agi=mid_agi,
        )
        result = check_filing_requirement(inp)
        expected_limit = PASSIVE_LOSS_LIMIT * 0.5
        assert result.passive_loss_limit == pytest.approx(expected_limit, rel=1e-2)

    def test_phase_out_complete(self):
        """AGI above phase-out end → no passive loss deduction."""
        inp = FilingRequirementInput(
            entity_type="individual",
            rental_income=0,
            rental_expenses=30000,
            tax_year=2024,
            filing_status="single",
            participation_level="active",
            modified_agi=PASSIVE_LOSS_PHASE_OUT_END + 10000,
        )
        result = check_filing_requirement(inp)
        assert result.passive_loss_limit == 0
        assert result.allowed_passive_loss == 0
        assert result.suspended_passive_loss == 30000

    def test_partnership_entity_type(self):
        """Partnership entity type works correctly."""
        inp = FilingRequirementInput(
            entity_type="partnership",
            rental_income=50000,
            rental_expenses=30000,
            tax_year=2024,
            filing_status="single",
            participation_level="active",
            modified_agi=50000,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.entity_type == "partnership"
        assert result.net_rental_income == 20000


# ===========================================================================
# Unit Tests – calculate_income_summary
# ===========================================================================

class TestCalculateIncomeSummary:
    """Tests for calculate_income_summary function."""

    def test_basic_income(self):
        """Basic rental income calculation."""
        inp = IncomeSummaryInput(
            rents_received=12000,
            advance_rents=0,
            security_deposits_retained=0,
            rental_expenses_paid_by_tenant=0,
            tax_year=2024,
        )
        result = calculate_income_summary(inp)
        assert result.gross_rental_income == 12000
        assert result.total_rental_income == 12000

    def test_income_with_advance_rents(self):
        """Income including advance rents."""
        inp = IncomeSummaryInput(
            rents_received=12000,
            advance_rents=2000,
            security_deposits_retained=0,
            rental_expenses_paid_by_tenant=0,
            tax_year=2024,
        )
        result = calculate_income_summary(inp)
        assert result.total_rental_income == 14000
        assert result.advance_rents == 2000

    def test_income_with_security_deposits(self):
        """Income including retained security deposits."""
        inp = IncomeSummaryInput(
            rents_received=12000,
            advance_rents=0,
            security_deposits_retained=1500,
            rental_expenses_paid_by_tenant=0,
            tax_year=2024,
        )
        result = calculate_income_summary(inp)
        assert result.total_rental_income == 13500
        assert result.security_deposits_retained == 1500

    def test_income_with_tenant_paid_expenses(self):
        """Income including tenant-paid expenses."""
        inp = IncomeSummaryInput(
            rents_received=12000,
            advance_rents=0,
            security_deposits_retained=0,
            rental_expenses_paid_by_tenant=800,
            tax_year=2024,
        )
        result = calculate_income_summary(inp)
        assert result.total_rental_income == 12800
        assert result.tenant_paid_expenses == 800

    def test_all_income_sources(self):
        """All income sources combined."""
        inp = IncomeSummaryInput(
            rents_received=24000,
            advance_rents=3000,
            security_deposits_retained=1000,
            rental_expenses_paid_by_tenant=500,
            tax_year=2024,
        )
        result = calculate_income_summary(inp)
        assert result.total_rental_income == 28500
        assert "28,500" in result.explanation


# ===========================================================================
# Unit Tests – calculate_expenses
# ===========================================================================

class TestCalculateExpenses:
    """Tests for calculate_expenses function."""

    def test_basic_expenses(self):
        """Basic expense calculation."""
        inp = ExpenseCalculationInput(
            advertising=500,
            auto_travel=0,
            cleaning_maintenance=1200,
            commissions=0,
            insurance=1800,
            legal_professional_fees=0,
            management_fees=0,
            mortgage_interest=8000,
            repairs=2000,
            supplies=300,
            taxes=2500,
            utilities=1500,
            depreciation=5000,
            other_expenses=0,
            tax_year=2024,
        )
        result = calculate_expenses(inp)
        assert result.total_expenses == 22800
        assert result.deductible_expenses == 22800
        assert result.non_deductible_expenses == 0

    def test_zero_expenses(self):
        """All zero expenses."""
        inp = ExpenseCalculationInput(
            advertising=0,
            auto_travel=0,
            cleaning_maintenance=0,
            commissions=0,
            insurance=0,
            legal_professional_fees=0,
            management_fees=0,
            mortgage_interest=0,
            repairs=0,
            supplies=0,
            taxes=0,
            utilities=0,
            depreciation=0,
            other_expenses=0,
            tax_year=2024,
        )
        result = calculate_expenses(inp)
        assert result.total_expenses == 0
        assert result.deductible_expenses == 0

    def test_expense_breakdown(self):
        """Expense breakdown contains all categories."""
        inp = ExpenseCalculationInput(
            advertising=100,
            auto_travel=200,
            cleaning_maintenance=300,
            commissions=400,
            insurance=500,
            legal_professional_fees=600,
            management_fees=700,
            mortgage_interest=800,
            repairs=900,
            supplies=1000,
            taxes=1100,
            utilities=1200,
            depreciation=1300,
            other_expenses=1400,
            tax_year=2024,
        )
        result = calculate_expenses(inp)
        assert len(result.expense_breakdown) == 14
        assert result.expense_breakdown["advertising"] == 100
        assert result.expense_breakdown["depreciation"] == 1300
        assert result.total_expenses == 10500


# ===========================================================================
# Unit Tests – get_overview
# ===========================================================================

class TestGetOverview:
    """Tests for get_overview function."""

    def test_overview_structure(self):
        """Overview has all required fields."""
        result = get_overview()
        assert result.title == "Form 8825: Rental Real Estate Income and Expenses"
        assert len(result.who_must_file) > 0
        assert len(result.income_types) > 0
        assert len(result.expense_categories) > 0
        assert "active participants" in result.passive_loss_rules.lower()
        assert len(result.related_forms) > 0
        assert len(result.recommendation) > 0

    def test_overview_expense_categories(self):
        """Overview includes all expense categories."""
        result = get_overview()
        expected_categories = [
            "advertising", "auto_travel", "cleaning_maintenance", "commissions",
            "insurance", "legal_professional_fees", "management_fees",
            "mortgage_interest", "repairs", "supplies", "taxes", "utilities",
            "depreciation", "other",
        ]
        for cat in expected_categories:
            assert cat in result.expense_categories


# ===========================================================================
# API Router Tests
# ===========================================================================

class TestForm8825Router:
    """Tests for Form 8825 API router endpoints."""

    def test_filing_requirement_endpoint(self, override_auth_dependency):
        """POST /filing-requirement returns correct result."""
        response = client.post(
            "/api/v1/form8825/filing-requirement",
            json={
                "entity_type": "individual",
                "rental_income": 15000,
                "rental_expenses": 10000,
                "tax_year": 2024,
                "filing_status": "single",
                "participation_level": "active",
                "modified_agi": 60000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_required"] is True
        assert data["net_rental_income"] == 5000
        assert "reasons" in data

    def test_income_summary_endpoint(self, override_auth_dependency):
        """POST /income-summary returns correct result."""
        response = client.post(
            "/api/v1/form8825/income-summary",
            json={
                "rents_received": 18000,
                "advance_rents": 1000,
                "security_deposits_retained": 500,
                "rental_expenses_paid_by_tenant": 300,
                "tax_year": 2024,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rental_income"] == 19800
        assert data["gross_rental_income"] == 18000

    def test_expense_calculation_endpoint(self, override_auth_dependency):
        """POST /expense-calculation returns correct result."""
        response = client.post(
            "/api/v1/form8825/expense-calculation",
            json={
                "advertising": 600,
                "auto_travel": 0,
                "cleaning_maintenance": 1500,
                "commissions": 0,
                "insurance": 2000,
                "legal_professional_fees": 500,
                "management_fees": 0,
                "mortgage_interest": 9000,
                "repairs": 2500,
                "supplies": 400,
                "taxes": 3000,
                "utilities": 1800,
                "depreciation": 6000,
                "other_expenses": 0,
                "tax_year": 2024,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_expenses"] == 27300
        assert data["deductible_expenses"] == 27300
        assert "expense_breakdown" in data

    def test_overview_endpoint(self):
        """GET /overview returns overview data."""
        response = client.get("/api/v1/form8825/overview")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "who_must_file" in data
        assert "expense_categories" in data

    def test_filing_requirement_invalid_entity_type(self, override_auth_dependency):
        """Invalid entity type returns 422."""
        response = client.post(
            "/api/v1/form8825/filing-requirement",
            json={
                "entity_type": "invalid_type",
                "rental_income": 10000,
                "rental_expenses": 5000,
                "tax_year": 2024,
            },
        )
        assert response.status_code == 422

    def test_filing_requirement_negative_income(self, override_auth_dependency):
        """Negative rental income returns 422."""
        response = client.post(
            "/api/v1/form8825/filing-requirement",
            json={
                "entity_type": "individual",
                "rental_income": -1000,
                "rental_expenses": 5000,
                "tax_year": 2024,
            },
        )
        assert response.status_code == 422

    def test_income_summary_missing_required_field(self, override_auth_dependency):
        """Missing required field returns 422."""
        response = client.post(
            "/api/v1/form8825/income-summary",
            json={
                "rents_received": 10000,
                # missing tax_year
            },
        )
        assert response.status_code == 422

    def test_expense_calculation_defaults(self, override_auth_dependency):
        """Expense calculation with defaults (all zeros)."""
        response = client.post(
            "/api/v1/form8825/expense-calculation",
            json={
                "tax_year": 2024,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_expenses"] == 0
        assert data["deductible_expenses"] == 0
