"""
Form 8995 — Qualified Business Income Deduction.

Business logic for Form 8995 calculations under IRC §199A.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8995Input:
    """Input for Form 8995 calculation."""
    qualified_business_income: Decimal
    agi: Decimal
    filing_status: str
    specified_service_business: bool = False
    w2_wages: Decimal = Decimal("0")
    ubia: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Form8995Result:
    """Result of Form 8995 calculation."""
    qbi_deduction: Decimal
    phaseout_applied: bool
    wage_limit_applied: bool
    explanation: str


QBI_RATE = Decimal("0.20")

# Thresholds
THRESHOLDS = {
    "single": Decimal("197300"),
    "married_joint": Decimal("394600"),
    "married_separate": Decimal("197300"),
    "head_of_household": Decimal("197300"),
}

THRESHOLD_RANGE = Decimal("50000")  # Phase-out range


def calculate_form8995(inp: Form8995Input) -> Form8995Result:
    """Calculate Form 8995 QBI deduction."""
    threshold = THRESHOLDS.get(inp.filing_status, Decimal("197300"))
    
    # Base QBI deduction
    qbi_deduction = (inp.qualified_business_income * QBI_RATE).quantize(Decimal("0.01"))
    
    phaseout_applied = False
    wage_limit_applied = False
    
    # Check if above threshold
    if inp.agi > threshold:
        phaseout_applied = True
        
        # Specified service business: fully phased out
        if inp.specified_service_business:
            if inp.agi > threshold + THRESHOLD_RANGE:
                qbi_deduction = Decimal("0")
                explanation = (
                    f"QBI deduction: $0 (specified service business fully phased out)"
                )
                return Form8995Result(
                    qbi_deduction=qbi_deduction,
                    phaseout_applied=phaseout_applied,
                    wage_limit_applied=wage_limit_applied,
                    explanation=explanation,
                )
        
        # Wage/UBIA limitation
        wage_limit = max(
            inp.w2_wages * Decimal("0.50"),
            inp.w2_wages * Decimal("0.25") + inp.ubia * Decimal("0.025")
        )
        
        # Phase-out ratio
        if inp.agi > threshold + THRESHOLD_RANGE:
            phaseout_ratio = Decimal("1")
        else:
            phaseout_ratio = (inp.agi - threshold) / THRESHOLD_RANGE
        
        # Apply limitation
        limited_deduction = min(qbi_deduction, wage_limit)
        qbi_deduction = (qbi_deduction * (Decimal("1") - phaseout_ratio) + 
                        limited_deduction * phaseout_ratio).quantize(Decimal("0.01"))
        
        wage_limit_applied = True
    
    explanation = (
        f"QBI deduction: ${qbi_deduction:,.2f} "
        f"(Phaseout: {phaseout_applied}, Wage limit: {wage_limit_applied})"
    )
    
    return Form8995Result(
        qbi_deduction=qbi_deduction,
        phaseout_applied=phaseout_applied,
        wage_limit_applied=wage_limit_applied,
        explanation=explanation,
    )


def get_form8995_overview() -> dict:
    """Returns a structured explanation of Form 8995."""
    return {
        "form": "Form 8995",
        "title": "Qualified Business Income Deduction",
        "purpose": "Form 8995 is used to calculate the 20% Qualified Business Income (QBI) deduction for pass-through entities.",
        "who_must_file": [
            "Owners of pass-through entities (S-corporations, partnerships, sole proprietorships)",
            "Taxpayers with qualified business income",
            "Taxpayers with REIT dividends or PTP income",
        ],
        "key_rules": [
            "Deduction: 20% of qualified business income",
            "Thresholds: $197,300 (single), $394,600 (married) for 2025",
            "Phase-out for specified service businesses",
            "W-2 wage and UBIA limitations apply above thresholds",
        ],
        "statutory_references": ["IRC §199A", "IRC §199A(b)"],
        "related_forms": ["Form 1040", "Schedule C", "Schedule E"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8995",
    }
