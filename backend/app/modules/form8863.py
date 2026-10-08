"""
Form 8863 — Education Credits.

Business logic for Form 8863 calculations under IRC §25A.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8863Input:
    """Input for Form 8863 calculation."""
    credit_type: str  # 'aotc' or 'llc'
    qualified_expenses: Decimal
    agi: Decimal
    filing_status: str
    tax_year: int = 2025


@dataclass
class Form8863Result:
    """Result of Form 8863 calculation."""
    credit_amount: Decimal
    refundable_amount: Decimal
    nonrefundable_amount: Decimal
    explanation: str


AOTC_MAX_CREDIT = Decimal("2500")
LLC_MAX_CREDIT = Decimal("2000")

# Phase-out thresholds
AOTC_PHASEOUT_SINGLE = (Decimal("80000"), Decimal("90000"))
AOTC_PHASEOUT_MARRIED = (Decimal("160000"), Decimal("180000"))
LLC_PHASEOUT_SINGLE = (Decimal("80000"), Decimal("90000"))
LLC_PHASEOUT_MARRIED = (Decimal("160000"), Decimal("180000"))


def calculate_form8863(inp: Form8863Input) -> Form8863Result:
    """Calculate Form 8863 education credits."""
    if inp.credit_type == "aotc":
        # American Opportunity Tax Credit
        max_credit = AOTC_MAX_CREDIT
        phaseout = AOTC_PHASEOUT_MARRIED if inp.filing_status == "married_joint" else AOTC_PHASEOUT_SINGLE
        
        # Calculate base credit
        if inp.qualified_expenses <= Decimal("2000"):
            credit_amount = inp.qualified_expenses * Decimal("1.0")
        else:
            credit_amount = Decimal("2000") + (inp.qualified_expenses - Decimal("2000")) * Decimal("0.25")
        
        credit_amount = min(credit_amount, max_credit)
        
        # Phase-out
        if inp.agi > phaseout[1]:
            credit_amount = Decimal("0")
        elif inp.agi > phaseout[0]:
            phaseout_ratio = (inp.agi - phaseout[0]) / (phaseout[1] - phaseout[0])
            credit_amount = (credit_amount * (Decimal("1") - phaseout_ratio)).quantize(Decimal("0.01"))
        
        # 40% refundable
        refundable_amount = (credit_amount * Decimal("0.40")).quantize(Decimal("0.01"))
        nonrefundable_amount = credit_amount - refundable_amount
        
    else:
        # Lifetime Learning Credit
        max_credit = LLC_MAX_CREDIT
        phaseout = LLC_PHASEOUT_MARRIED if inp.filing_status == "married_joint" else LLC_PHASEOUT_SINGLE
        
        # Calculate base credit
        credit_amount = (inp.qualified_expenses * Decimal("0.20")).quantize(Decimal("0.01"))
        credit_amount = min(credit_amount, max_credit)
        
        # Phase-out
        if inp.agi > phaseout[1]:
            credit_amount = Decimal("0")
        elif inp.agi > phaseout[0]:
            phaseout_ratio = (inp.agi - phaseout[0]) / (phaseout[1] - phaseout[0])
            credit_amount = (credit_amount * (Decimal("1") - phaseout_ratio)).quantize(Decimal("0.01"))
        
        refundable_amount = Decimal("0")
        nonrefundable_amount = credit_amount
    
    explanation = (
        f"Education credit: ${credit_amount:,.2f} "
        f"(Refundable: ${refundable_amount:,.2f}, Nonrefundable: ${nonrefundable_amount:,.2f})"
    )
    
    return Form8863Result(
        credit_amount=credit_amount,
        refundable_amount=refundable_amount,
        nonrefundable_amount=nonrefundable_amount,
        explanation=explanation,
    )


def get_form8863_overview() -> dict:
    """Returns a structured explanation of Form 8863."""
    return {
        "form": "Form 8863",
        "title": "Education Credits",
        "purpose": "Form 8863 is used to claim the American Opportunity Tax Credit and Lifetime Learning Credit.",
        "who_must_file": [
            "Taxpayers with qualified education expenses",
            "Students or parents paying for college",
            "Taxpayers with 1098-T forms",
        ],
        "key_rules": [
            "American Opportunity Credit: up to $2,500 per student (40% refundable)",
            "Lifetime Learning Credit: up to $2,000 per return",
            "AOTC limited to first 4 years of post-secondary education",
            "Phase-out begins at $80,000 (single), $160,000 (married)",
        ],
        "statutory_references": ["IRC §25A", "IRC §25A(i)"],
        "related_forms": ["Form 1040", "Form 8917"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8863",
    }
