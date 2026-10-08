"""
Schedule 1 — Additional Income and Adjustments to Income.

Business logic for Schedule 1 calculations under IRC §62.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Schedule1Input:
    """Input for Schedule 1 calculation."""
    alimony_received: Decimal = Decimal("0")
    business_income: Decimal = Decimal("0")
    other_gains: Decimal = Decimal("0")
    rental_income: Decimal = Decimal("0")
    farm_income: Decimal = Decimal("0")
    unemployment_compensation: Decimal = Decimal("0")
    other_income: Decimal = Decimal("0")
    educator_expenses: Decimal = Decimal("0")
    hsa_deduction: Decimal = Decimal("0")
    student_loan_interest: Decimal = Decimal("0")
    ira_deduction: Decimal = Decimal("0")
    self_employment_tax_deduction: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Schedule1Result:
    """Result of Schedule 1 calculation."""
    total_additional_income: Decimal
    total_adjustments: Decimal
    net_adjustment: Decimal
    explanation: str


def calculate_schedule_1(inp: Schedule1Input) -> Schedule1Result:
    """Calculate Schedule 1 additional income and adjustments."""
    # Additional income
    total_additional_income = (
        inp.alimony_received + inp.business_income + inp.other_gains +
        inp.rental_income + inp.farm_income + inp.unemployment_compensation +
        inp.other_income
    )
    
    # Adjustments to income
    total_adjustments = (
        inp.educator_expenses + inp.hsa_deduction + inp.student_loan_interest +
        inp.ira_deduction + inp.self_employment_tax_deduction
    )
    
    # Net adjustment
    net_adjustment = total_additional_income - total_adjustments
    
    explanation = (
        f"Schedule 1: Additional income ${total_additional_income:,.2f}, "
        f"Adjustments ${total_adjustments:,.2f}, "
        f"Net ${net_adjustment:,.2f}"
    )
    
    return Schedule1Result(
        total_additional_income=total_additional_income,
        total_adjustments=total_adjustments,
        net_adjustment=net_adjustment,
        explanation=explanation,
    )


def get_schedule_1_overview() -> dict:
    """Returns a structured explanation of Schedule 1."""
    return {
        "form": "Schedule 1",
        "title": "Additional Income and Adjustments to Income",
        "purpose": "Schedule 1 is used to report additional income and adjustments to income.",
        "who_must_file": [
            "Taxpayers with additional income sources",
            "Taxpayers with adjustments to income",
            "Taxpayers with educator expenses or HSA contributions",
        ],
        "key_rules": [
            "Reports income not reported on Form 1040",
            "Includes adjustments to income (above-the-line deductions)",
            "Alimony received is taxable for agreements after 2018",
            "Student loan interest deduction up to $2,500",
        ],
        "statutory_references": ["IRC §62", "IRC §221"],
        "related_forms": ["Form 1040", "Schedule C", "Schedule E"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-schedule-1-form-1040",
    }
