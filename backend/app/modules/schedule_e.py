"""
Schedule E — Supplemental Income and Loss.

Business logic for Schedule E calculations under IRC §469.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class ScheduleEInput:
    """Input for Schedule E calculation."""
    rental_income: Decimal = Decimal("0")
    royalty_income: Decimal = Decimal("0")
    rental_expenses: Decimal = Decimal("0")
    royalty_expenses: Decimal = Decimal("0")
    passive_loss_carryforward: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class ScheduleEResult:
    """Result of Schedule E calculation."""
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal
    passive_loss: Decimal
    suspended_loss: Decimal
    explanation: str


def calculate_schedule_e(inp: ScheduleEInput) -> ScheduleEResult:
    """Calculate Schedule E supplemental income and loss."""
    total_income = inp.rental_income + inp.royalty_income
    total_expenses = inp.rental_expenses + inp.royalty_expenses
    net_income = total_income - total_expenses
    
    # Passive loss calculation
    if net_income < 0:
        passive_loss = abs(net_income)
        suspended_loss = passive_loss + inp.passive_loss_carryforward
    else:
        passive_loss = Decimal("0")
        suspended_loss = inp.passive_loss_carryforward
    
    explanation = (
        f"Schedule E: Income ${total_income:,.2f}, "
        f"Expenses ${total_expenses:,.2f}, "
        f"Net ${net_income:,.2f}"
    )
    
    return ScheduleEResult(
        total_income=total_income,
        total_expenses=total_expenses,
        net_income=net_income,
        passive_loss=passive_loss,
        suspended_loss=suspended_loss,
        explanation=explanation,
    )


def get_schedule_e_overview() -> dict:
    """Returns a structured explanation of Schedule E."""
    return {
        "form": "Schedule E",
        "title": "Supplemental Income and Loss",
        "purpose": "Schedule E is used to report income or loss from rental real estate, royalties, partnerships, S-corporations, estates, and trusts.",
        "who_must_file": [
            "Taxpayers with rental income",
            "Taxpayers with royalty income",
            "Partners in partnerships",
            "Shareholders in S-corporations",
        ],
        "key_rules": [
            "Passive loss rules apply to rental real estate",
            "Special $25,000 allowance for active participants",
            "Real estate professionals can deduct losses against other income",
            "Each property reported separately",
        ],
        "statutory_references": ["IRC §469", "IRC §162"],
        "related_forms": ["Form 1040", "Form 8582", "Form 8825"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-schedule-e-form-1040",
    }
