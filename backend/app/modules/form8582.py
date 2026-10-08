"""
Form 8582 — Passive Activity Loss Limitations.

Business logic for Form 8582 calculations under IRC §469.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8582Input:
    """Input for Form 8582 calculation."""
    passive_income: Decimal
    passive_losses: Decimal
    agi: Decimal
    active_participation: bool = False
    tax_year: int = 2025


@dataclass
class Form8582Result:
    """Result of Form 8582 calculation."""
    deductible_loss: Decimal
    suspended_loss: Decimal
    special_allowance: Decimal
    explanation: str


SPECIAL_ALLOWANCE = Decimal("25000")
SPECIAL_ALLOWANCE_PHASEOUT_START = Decimal("100000")
SPECIAL_ALLOWANCE_PHASEOUT_END = Decimal("150000")


def calculate_form8582(inp: Form8582Input) -> Form8582Result:
    """Calculate Form 8582 passive activity loss limitations."""
    # Special allowance for active participants in rental real estate
    special_allowance = Decimal("0")
    if inp.active_participation:
        if inp.agi <= SPECIAL_ALLOWANCE_PHASEOUT_START:
            special_allowance = SPECIAL_ALLOWANCE
        elif inp.agi >= SPECIAL_ALLOWANCE_PHASEOUT_END:
            special_allowance = Decimal("0")
        else:
            # Phase-out
            phaseout_ratio = (inp.agi - SPECIAL_ALLOWANCE_PHASEOUT_START) / (SPECIAL_ALLOWANCE_PHASEOUT_END - SPECIAL_ALLOWANCE_PHASEOUT_START)
            special_allowance = (SPECIAL_ALLOWANCE * (Decimal("1") - phaseout_ratio)).quantize(Decimal("0.01"))
    
    # Deductible loss limited to passive income plus special allowance
    max_deduction = inp.passive_income + special_allowance
    deductible_loss = min(inp.passive_losses, max_deduction)
    
    # Suspended loss
    suspended_loss = inp.passive_losses - deductible_loss
    
    explanation = (
        f"Passive loss: Deductible ${deductible_loss:,.2f}, "
        f"Suspended ${suspended_loss:,.2f}, Special allowance ${special_allowance:,.2f}"
    )
    
    return Form8582Result(
        deductible_loss=deductible_loss,
        suspended_loss=suspended_loss,
        special_allowance=special_allowance,
        explanation=explanation,
    )


def get_form8582_overview() -> dict:
    """Returns a structured explanation of Form 8582."""
    return {
        "form": "Form 8582",
        "title": "Passive Activity Loss Limitations",
        "purpose": "Form 8582 is used to calculate the allowable passive activity loss and determine how much can be deducted.",
        "who_must_file": [
            "Taxpayers with passive activity losses",
            "Rental real estate owners with losses",
            "Limited partners with losses",
        ],
        "key_rules": [
            "Passive losses can only offset passive income",
            "Excess losses are suspended and carried forward",
            "Special $25,000 allowance for rental real estate (phases out at $100,000-$150,000 AGI)",
            "Material participation tests determine active vs. passive",
        ],
        "statutory_references": ["IRC §469", "IRC §469(i)"],
        "related_forms": ["Schedule E", "Form 1040"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8582",
    }
