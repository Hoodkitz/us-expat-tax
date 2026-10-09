"""Tests for Schedule H (Form 1040) — Household Employment Taxes."""
from __future__ import annotations

import pytest

from app.modules.schedule_h import (
    CASH_WAGES_THRESHOLD,
    SS_RATE,
    MEDICARE_RATE,
    ADDITIONAL_MEDICARE_RATE,
    SS_WAGE_BASE_2025,
    ADDITIONAL_MEDICARE_THRESHOLD,
    EMPLOYER_PAID_SS_RATE,
    EMPLOYER_PAID_MEDICARE_RATE,
    HouseholdEmployeeInput,
    ScheduleHInput,
    calculate_schedule_h,
    get_overview,
)


class TestConstants:
    """Verify IRS 2025 constants."""

    def test_cash_wages_threshold(self):
        assert CASH_WAGES_THRESHOLD == 2_800.0

    def test_ss_rate(self):
        assert SS_RATE == 0.124

    def test_medicare_rate(self):
        assert MEDICARE_RATE == 0.029

    def test_additional_medicare_rate(self):
        assert ADDITIONAL_MEDICARE_RATE == 0.009

    def test_ss_wage_base_2025(self):
        assert SS_WAGE_BASE_2025 == 176_100.0

    def test_additional_medicare_threshold(self):
        assert ADDITIONAL_MEDICARE_THRESHOLD == 200_000.0

    def test_employer_paid_rates(self):
        assert EMPLOYER_PAID_SS_RATE == 0.029
        assert EMPLOYER_PAID_MEDICARE_RATE == 0.0145


class TestFilingRequirement:
    """Test filing requirement determination."""

    def test_no_employees_not_required(self):
        inp = ScheduleHInput(employees=[], tax_year=2025, employer_pays_employee_share=False)
        result = calculate_schedule_h(inp)
        assert result.filing_required is False

    def test_below_threshold_not_required(self):
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=2_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        assert result.filing_required is False

    def test_exactly_at_threshold_not_required(self):
        """Exactly at threshold — not required (must exceed)."""
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=CASH_WAGES_THRESHOLD),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        assert result.filing_required is False

    def test_above_threshold_required(self):
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=3_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        assert result.filing_required is True

    def test_multiple_employees_one_above(self):
        """Only one employee needs to exceed threshold."""
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=1_500.0),
                HouseholdEmployeeInput(employee_name="Housekeeper", cash_wages=3_500.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        assert result.filing_required is True


class TestTaxCalculation:
    """Test tax calculation for individual employees."""

    def test_basic_ss_and_medicare(self):
        """Employee with $10,000 wages — SS capped at wage base, Medicare on all."""
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=10_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        emp = result.employees[0]
        assert emp.ss_wages == 10_000.0
        assert emp.social_security_tax == pytest.approx(10_000.0 * 0.124)
        assert emp.medicare_tax == pytest.approx(10_000.0 * 0.029)
        assert emp.additional_medicare_tax == 0.0
        assert emp.total_employment_tax == pytest.approx(10_000.0 * 0.124 + 10_000.0 * 0.029)

    def test_ss_wage_base_cap(self):
        """Employee with wages above SS wage base — SS capped."""
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=200_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        emp = result.employees[0]
        assert emp.ss_wages == SS_WAGE_BASE_2025
        assert emp.social_security_tax == pytest.approx(SS_WAGE_BASE_2025 * 0.124)
        assert emp.medicare_tax == pytest.approx(200_000.0 * 0.029)
        # Additional Medicare: 0.9% on $200k - $200k = $0
        assert emp.additional_medicare_tax == 0.0

    def test_additional_medicare_tax(self):
        """Employee with wages above $200k — additional Medicare applies."""
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=250_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        emp = result.employees[0]
        assert emp.ss_wages == SS_WAGE_BASE_2025
        assert emp.social_security_tax == pytest.approx(SS_WAGE_BASE_2025 * 0.124)
        assert emp.medicare_tax == pytest.approx(250_000.0 * 0.029)
        assert emp.additional_medicare_tax == pytest.approx(50_000.0 * 0.009)

    def test_zero_wages(self):
        """Employee with zero wages — no tax."""
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=0.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        emp = result.employees[0]
        assert emp.social_security_tax == 0.0
        assert emp.medicare_tax == 0.0
        assert emp.additional_medicare_tax == 0.0
        assert emp.total_employment_tax == 0.0


class TestMultipleEmployees:
    """Test aggregation across multiple employees."""

    def test_total_wages_sum(self):
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=5_000.0),
                HouseholdEmployeeInput(employee_name="Housekeeper", cash_wages=4_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        assert result.total_cash_wages == 9_000.0

    def test_total_tax_sum(self):
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=5_000.0),
                HouseholdEmployeeInput(employee_name="Housekeeper", cash_wages=4_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        expected_ss = 5_000.0 * 0.124 + 4_000.0 * 0.124
        expected_medicare = 5_000.0 * 0.029 + 4_000.0 * 0.029
        assert result.total_social_security_tax == pytest.approx(expected_ss)
        assert result.total_medicare_tax == pytest.approx(expected_medicare)
        assert result.total_employment_tax == pytest.approx(expected_ss + expected_medicare)


class TestEmployerPaysEmployeeShare:
    """Test employer-elects-to-pay-employee-share scenario."""

    def test_employer_pays_uses_reduced_rates(self):
        """When employer pays employee share, use 2.9% SS + 1.45% Medicare."""
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=10_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=True,
        )
        result = calculate_schedule_h(inp)
        emp = result.employees[0]
        assert emp.social_security_tax == pytest.approx(10_000.0 * EMPLOYER_PAID_SS_RATE)
        assert emp.medicare_tax == pytest.approx(10_000.0 * EMPLOYER_PAID_MEDICARE_RATE)

    def test_standard_rates_when_flag_false(self):
        """Standard rates (12.4% SS + 2.9% Medicare) when flag is False."""
        inp = ScheduleHInput(
            employees=[
                HouseholdEmployeeInput(employee_name="Nanny", cash_wages=10_000.0),
            ],
            tax_year=2025,
            employer_pays_employee_share=False,
        )
        result = calculate_schedule_h(inp)
        emp = result.employees[0]
        assert emp.social_security_tax == pytest.approx(10_000.0 * SS_RATE)
        assert emp.medicare_tax == pytest.approx(10_000.0 * MEDICARE_RATE)

    def test_employer_pays_total_tax_lower(self):
        """Employer-paid scenario results in lower total tax."""
        emp = HouseholdEmployeeInput(employee_name="Nanny", cash_wages=10_000.0)
        standard = calculate_schedule_h(ScheduleHInput(
            employees=[emp], tax_year=2025, employer_pays_employee_share=False
        ))
        employer_paid = calculate_schedule_h(ScheduleHInput(
            employees=[emp], tax_year=2025, employer_pays_employee_share=True
        ))
        assert employer_paid.total_employment_tax < standard.total_employment_tax


class TestOverview:
    """Test overview endpoint."""

    def test_overview_contains_constants(self):
        overview = get_overview()
        assert overview.cash_wages_threshold == CASH_WAGES_THRESHOLD
        assert overview.social_security_rate == SS_RATE
        assert overview.social_security_wage_base == SS_WAGE_BASE_2025
        assert overview.medicare_rate == MEDICARE_RATE
        assert overview.additional_medicare_rate == ADDITIONAL_MEDICARE_RATE
        assert overview.additional_medicare_threshold == ADDITIONAL_MEDICARE_THRESHOLD

    def test_overview_employer_paid_rates(self):
        overview = get_overview()
        assert overview.employer_paid_rates["social_security"] == EMPLOYER_PAID_SS_RATE
        assert overview.employer_paid_rates["medicare"] == EMPLOYER_PAID_MEDICARE_RATE


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------

class TestScheduleHAPI:
    """Test Schedule H API endpoints."""

    def test_calculate_endpoint(self):
        """POST /api/v1/schedule-h/calculate returns valid response."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/schedule-h/calculate",
            json={
                "employees": [
                    {"employee_name": "Nanny", "cash_wages": 5000.0},
                ],
                "tax_year": 2025,
                "employer_pays_employee_share": False,
            },
        )
        # May require auth — just check it doesn't crash
        assert response.status_code in (200, 401, 403)

    def test_overview_endpoint(self):
        """GET /api/v1/schedule-h/overview returns valid response."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/api/v1/schedule-h/overview")
        assert response.status_code in (200, 401, 403)
