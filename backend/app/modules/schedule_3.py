"""
Schedule 3 — Additional Credits and Payments.

Business logic for Schedule 3 calculations under IRC §36B.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Schedule3Input:
    """Input for Schedule 3 calculation."""
    foreign_tax_credit: Decimal = Decimal("0")
    child_dependent_care_credit: Decimal = Decimal("0")
    education_credits: Decimal = Decimal("0")
    retirement_savings_credit: Decimal = Decimal("0")
    residential_energy_credit: Decimal = Decimal("0")
    other_credits: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Schedule3Result:
    """Result of Schedule 3 calculation."""
    total_credits: Decimal
    explanation: str


def calculate_schedule_3(inp: Schedule3Input) -> Schedule3Result:
    """Calculate Schedule 3 additional credits and payments."""
    total_credits = (
        inp.foreign_tax_credit + inp.child_dependent_care_credit +
        inp.education_credits + inp.retirement_savings_credit +
        inp.residential_energy_credit + inp.other_credits
    )
    
    explanation = f"Schedule 3: Total credits ${total_credits:,.2f}"
    
    return Schedule3Result(
        total_credits=total_credits,
        explanation=explanation,
    )


def get_schedule_3_overview() -> dict:
    """Returns a structured explanation of Schedule 3."""
    return {
        "form": "Schedule 3",
        "title": "Additional Credits and Payments",
        "purpose": "Schedule 3 is used to report additional credits and payments.",
        "who_must_file": [
            "Taxpayers claiming foreign tax credit",
            "Taxpayers with child and dependent care expenses",
            "Taxpayers claiming education credits",
            "Taxpayers with retirement savings contributions",
        ],
        "key_rules": [
            "Reports non-refundable credits",
            "Includes foreign tax credit and education credits",
            "Child and dependent care credit up to $1,050/$2,100",
            "Retirement savings credit up to $1,000",
        ],
        "statutory_references": ["IRC §25A", "IRC §25B", "IRC §36B"],
        "related_forms": ["Form 1040", "Form 1116", "Form 2441"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-schedule-3-form-1040",
    }
