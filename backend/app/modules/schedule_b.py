"""
Schedule B — Interest and Ordinary Dividends.

Business logic for Schedule B calculations under IRC §61.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class ScheduleBInput:
    """Input for Schedule B calculation."""
    interest_income: Decimal
    ordinary_dividends: Decimal
    foreign_accounts: bool = False
    foreign_trusts: bool = False
    tax_year: int = 2025


@dataclass
class ScheduleBResult:
    """Result of Schedule B calculation."""
    total_interest: Decimal
    total_dividends: Decimal
    total_income: Decimal
    filing_required: bool
    explanation: str


FILING_THRESHOLD = Decimal("1500")


def calculate_schedule_b(inp: ScheduleBInput) -> ScheduleBResult:
    """Calculate Schedule B interest and dividends."""
    total_interest = inp.interest_income
    total_dividends = inp.ordinary_dividends
    total_income = total_interest + total_dividends
    
    # Filing required if over threshold or foreign accounts
    filing_required = (
        total_interest > FILING_THRESHOLD or
        total_dividends > FILING_THRESHOLD or
        inp.foreign_accounts or
        inp.foreign_trusts
    )
    
    explanation = (
        f"Schedule B: Interest ${total_interest:,.2f}, "
        f"Dividends ${total_dividends:,.2f}, "
        f"Filing required: {filing_required}"
    )
    
    return ScheduleBResult(
        total_interest=total_interest,
        total_dividends=total_dividends,
        total_income=total_income,
        filing_required=filing_required,
        explanation=explanation,
    )


def get_schedule_b_overview() -> dict:
    """Returns a structured explanation of Schedule B."""
    return {
        "form": "Schedule B",
        "title": "Interest and Ordinary Dividends",
        "purpose": "Schedule B is used to report interest and ordinary dividend income.",
        "who_must_file": [
            "Taxpayers with interest income over $1,500",
            "Taxpayers with ordinary dividends over $1,500",
            "Taxpayers with foreign accounts or trusts",
        ],
        "key_rules": [
            "Required if interest or dividends exceed $1,500",
            "Must list each payer separately",
            "Foreign accounts require FBAR and/or Form 8938",
            "Ordinary dividends reported separately from qualified dividends",
        ],
        "statutory_references": ["IRC §61", "IRC §6042"],
        "related_forms": ["Form 1040", "Form 8938"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-schedule-b-form-1040",
    }
