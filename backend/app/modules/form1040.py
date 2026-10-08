"""
Form 1040 — U.S. Individual Income Tax Return.

Business logic for Form 1040 calculations under IRC §61.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Form1040Input:
    """Input for Form 1040 calculation."""
    filing_status: str
    gross_income: Decimal
    adjustments: Decimal = Decimal("0")
    deductions: Decimal = Decimal("0")
    credits: Decimal = Decimal("0")
    withholding: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Form1040Result:
    """Result of Form 1040 calculation."""
    agi: Decimal
    taxable_income: Decimal
    tax_before_credits: Decimal
    total_tax: Decimal
    effective_tax_rate: Decimal
    marginal_tax_rate: Decimal
    balance_due: Decimal
    refund: Decimal
    explanation: str


# ---------------------------------------------------------------------------
# Constants — 2025 Tax Year
# ---------------------------------------------------------------------------

STANDARD_DEDUCTIONS = {
    "single": Decimal("15000"),
    "married_joint": Decimal("30000"),
    "married_separate": Decimal("15000"),
    "head_of_household": Decimal("22500"),
}

TAX_BRACKETS_SINGLE = [
    (Decimal("0"), Decimal("11925"), Decimal("0.10")),
    (Decimal("11925"), Decimal("48475"), Decimal("0.12")),
    (Decimal("48475"), Decimal("103350"), Decimal("0.22")),
    (Decimal("103350"), Decimal("197300"), Decimal("0.24")),
    (Decimal("197300"), Decimal("250525"), Decimal("0.32")),
    (Decimal("250525"), Decimal("626350"), Decimal("0.35")),
    (Decimal("626350"), Decimal("999999999"), Decimal("0.37")),
]

TAX_BRACKETS_MARRIED_JOINT = [
    (Decimal("0"), Decimal("23850"), Decimal("0.10")),
    (Decimal("23850"), Decimal("96950"), Decimal("0.12")),
    (Decimal("96950"), Decimal("206700"), Decimal("0.22")),
    (Decimal("206700"), Decimal("394600"), Decimal("0.24")),
    (Decimal("394600"), Decimal("501050"), Decimal("0.32")),
    (Decimal("501050"), Decimal("751600"), Decimal("0.35")),
    (Decimal("751600"), Decimal("999999999"), Decimal("0.37")),
]

TAX_BRACKETS_MARRIED_SEPARATE = [
    (Decimal("0"), Decimal("11925"), Decimal("0.10")),
    (Decimal("11925"), Decimal("48475"), Decimal("0.12")),
    (Decimal("48475"), Decimal("103350"), Decimal("0.22")),
    (Decimal("103350"), Decimal("197300"), Decimal("0.24")),
    (Decimal("197300"), Decimal("250525"), Decimal("0.32")),
    (Decimal("250525"), Decimal("375800"), Decimal("0.35")),
    (Decimal("375800"), Decimal("999999999"), Decimal("0.37")),
]

TAX_BRACKETS_HEAD_OF_HOUSEHOLD = [
    (Decimal("0"), Decimal("17000"), Decimal("0.10")),
    (Decimal("17000"), Decimal("64850"), Decimal("0.12")),
    (Decimal("64850"), Decimal("103350"), Decimal("0.22")),
    (Decimal("103350"), Decimal("197300"), Decimal("0.24")),
    (Decimal("197300"), Decimal("250525"), Decimal("0.32")),
    (Decimal("250525"), Decimal("626350"), Decimal("0.35")),
    (Decimal("626350"), Decimal("999999999"), Decimal("0.37")),
]


def _get_brackets(filing_status: str) -> list:
    """Get tax brackets for filing status."""
    brackets = {
        "single": TAX_BRACKETS_SINGLE,
        "married_joint": TAX_BRACKETS_MARRIED_JOINT,
        "married_separate": TAX_BRACKETS_MARRIED_SEPARATE,
        "head_of_household": TAX_BRACKETS_HEAD_OF_HOUSEHOLD,
    }
    return brackets.get(filing_status, TAX_BRACKETS_SINGLE)


def _calculate_tax(taxable_income: Decimal, filing_status: str) -> tuple[Decimal, Decimal]:
    """Calculate tax using progressive brackets. Returns (tax, marginal_rate)."""
    brackets = _get_brackets(filing_status)
    tax = Decimal("0")
    marginal_rate = Decimal("0")
    
    for low, high, rate in brackets:
        if taxable_income > low:
            taxable_at_rate = min(taxable_income, high) - low
            if taxable_at_rate > 0:
                tax += taxable_at_rate * rate
                marginal_rate = rate
        else:
            break
    
    return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), marginal_rate


# ---------------------------------------------------------------------------
# Calculation Functions
# ---------------------------------------------------------------------------

def calculate_form1040(inp: Form1040Input) -> Form1040Result:
    """
    Calculate Form 1040 based on 2025 IRS rules.
    
    Returns:
        Form1040Result with all calculated values.
    """
    # Calculate AGI
    agi = inp.gross_income - inp.adjustments
    
    # Apply standard or itemized deduction
    standard_deduction = STANDARD_DEDUCTIONS.get(inp.filing_status, Decimal("15000"))
    deduction = max(inp.deductions, standard_deduction)
    
    # Calculate taxable income
    taxable_income = max(agi - deduction, Decimal("0"))
    
    # Calculate tax before credits
    tax_before_credits, marginal_rate = _calculate_tax(taxable_income, inp.filing_status)
    
    # Apply credits
    total_tax = max(tax_before_credits - inp.credits, Decimal("0"))
    
    # Calculate effective rate
    effective_rate = (total_tax / inp.gross_income) if inp.gross_income > 0 else Decimal("0")
    
    # Calculate balance due or refund
    net = inp.withholding - total_tax
    balance_due = max(-net, Decimal("0"))
    refund = max(net, Decimal("0"))
    
    explanation = (
        f"Form 1040 calculation for {inp.filing_status}: "
        f"AGI ${agi:,.2f}, Taxable Income ${taxable_income:,.2f}, "
        f"Tax ${total_tax:,.2f}, Effective Rate {effective_rate*100:.2f}%"
    )
    
    return Form1040Result(
        agi=agi.quantize(Decimal("0.01")),
        taxable_income=taxable_income.quantize(Decimal("0.01")),
        tax_before_credits=tax_before_credits,
        total_tax=total_tax.quantize(Decimal("0.01")),
        effective_tax_rate=effective_rate.quantize(Decimal("0.0001")),
        marginal_tax_rate=marginal_rate,
        balance_due=balance_due.quantize(Decimal("0.01")),
        refund=refund.quantize(Decimal("0.01")),
        explanation=explanation,
    )


def get_form1040_overview() -> dict:
    """
    Returns a structured explanation of Form 1040.
    """
    return {
        "form": "Form 1040",
        "title": "U.S. Individual Income Tax Return",
        "purpose": "Form 1040 is the standard federal income tax form used by individuals to file their annual income tax return with the IRS.",
        "who_must_file": [
            "U.S. citizens and residents with gross income above the standard deduction",
            "Self-employed individuals with net earnings of $400 or more",
            "Individuals who owe special taxes (AMT, IRA penalties, etc.)",
        ],
        "key_rules": [
            "Progressive tax rates from 10% to 37%",
            "Standard deduction: $15,000 (single), $30,000 (married filing jointly)",
            "Tax credits can reduce tax liability dollar-for-dollar",
            "Above-the-line deductions reduce AGI",
        ],
        "statutory_references": ["IRC §61", "IRC §63", "IRC §1"],
        "related_forms": ["Schedule 1", "Schedule 2", "Schedule 3", "Form 1040-X"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-1040",
    }
