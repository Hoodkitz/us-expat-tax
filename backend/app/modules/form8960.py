"""
Form 8960 — Net Investment Income Tax.

Business logic for Form 8960 calculations under IRC §1411.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8960Input:
    """Input for Form 8960 calculation."""
    filing_status: str
    magi: Decimal
    net_investment_income: Decimal
    tax_year: int = 2025


@dataclass
class Form8960Result:
    """Result of Form 8960 calculation."""
    threshold: Decimal
    excess_magi: Decimal
    niit: Decimal
    explanation: str


NIIT_RATE = Decimal("0.038")

# Thresholds
THRESHOLDS = {
    "single": Decimal("200000"),
    "married_joint": Decimal("250000"),
    "married_separate": Decimal("125000"),
    "head_of_household": Decimal("200000"),
}


def calculate_form8960(inp: Form8960Input) -> Form8960Result:
    """Calculate Form 8960 Net Investment Income Tax."""
    threshold = THRESHOLDS.get(inp.filing_status, Decimal("200000"))
    
    # Excess MAGI
    excess_magi = max(inp.magi - threshold, Decimal("0"))
    
    # NIIT is lesser of NII or excess MAGI
    niit_base = min(inp.net_investment_income, excess_magi)
    niit = (niit_base * NIIT_RATE).quantize(Decimal("0.01"))
    
    explanation = (
        f"NIIT: ${niit:,.2f} on NII of ${niit_base:,.2f} "
        f"(MAGI excess: ${excess_magi:,.2f})"
    )
    
    return Form8960Result(
        threshold=threshold,
        excess_magi=excess_magi,
        niit=niit,
        explanation=explanation,
    )


def get_form8960_overview() -> dict:
    """Returns a structured explanation of Form 8960."""
    return {
        "form": "Form 8960",
        "title": "Net Investment Income Tax",
        "purpose": "Form 8960 is used to calculate the 3.8% Net Investment Income Tax on high-income taxpayers.",
        "who_must_file": [
            "Taxpayers with net investment income and MAGI above thresholds",
            "Single taxpayers with MAGI above $200,000",
            "Married taxpayers with MAGI above $250,000",
        ],
        "key_rules": [
            "3.8% tax on lesser of NII or MAGI above threshold",
            "Thresholds: $200,000 (single), $250,000 (married), $125,000 (married separate)",
            "NII includes interest, dividends, capital gains, rental income",
            "Does not include distributions from retirement accounts",
        ],
        "statutory_references": ["IRC §1411", "IRC §1411(c)"],
        "related_forms": ["Form 1040", "Schedule D"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8960",
    }
