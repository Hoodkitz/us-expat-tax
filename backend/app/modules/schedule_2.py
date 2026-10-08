"""
Schedule 2 — Additional Taxes.

Business logic for Schedule 2 calculations under IRC §55.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Schedule2Input:
    """Input for Schedule 2 calculation."""
    alternative_minimum_tax: Decimal = Decimal("0")
    excess_advance_premium_tax_credit: Decimal = Decimal("0")
    self_employment_tax: Decimal = Decimal("0")
    additional_medicare_tax: Decimal = Decimal("0")
    net_investment_income_tax: Decimal = Decimal("0")
    recapture_taxes: Decimal = Decimal("0")
    other_taxes: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Schedule2Result:
    """Result of Schedule 2 calculation."""
    total_additional_taxes: Decimal
    explanation: str


def calculate_schedule_2(inp: Schedule2Input) -> Schedule2Result:
    """Calculate Schedule 2 additional taxes."""
    total_additional_taxes = (
        inp.alternative_minimum_tax + inp.excess_advance_premium_tax_credit +
        inp.self_employment_tax + inp.additional_medicare_tax +
        inp.net_investment_income_tax + inp.recapture_taxes + inp.other_taxes
    )
    
    explanation = f"Schedule 2: Total additional taxes ${total_additional_taxes:,.2f}"
    
    return Schedule2Result(
        total_additional_taxes=total_additional_taxes,
        explanation=explanation,
    )


def get_schedule_2_overview() -> dict:
    """Returns a structured explanation of Schedule 2."""
    return {
        "form": "Schedule 2",
        "title": "Additional Taxes",
        "purpose": "Schedule 2 is used to report additional taxes owed.",
        "who_must_file": [
            "Taxpayers who owe alternative minimum tax",
            "Taxpayers with self-employment tax",
            "Taxpayers with additional Medicare tax",
            "Taxpayers with net investment income tax",
        ],
        "key_rules": [
            "Reports taxes not included in Form 1040",
            "Includes AMT, self-employment tax, and NIIT",
            "Excess advance premium tax credit repayment",
            "Recapture taxes from prior year credits",
        ],
        "statutory_references": ["IRC §55", "IRC §1401", "IRC §1411"],
        "related_forms": ["Form 1040", "Form 6251", "Form 8959"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-schedule-2-form-1040",
    }
