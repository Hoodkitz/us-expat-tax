"""
Form 1040-X — Amended U.S. Individual Income Tax Return.

Business logic for Form 1040-X calculations under IRC §6213.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form1040XInput:
    """Input for Form 1040-X calculation."""
    original_tax: Decimal
    corrected_tax: Decimal
    original_payments: Decimal
    corrected_payments: Decimal
    explanation: str
    tax_year: int = 2025


@dataclass
class Form1040XResult:
    """Result of Form 1040-X calculation."""
    additional_tax_due: Decimal
    refund_due: Decimal
    penalty: Decimal
    interest: Decimal
    total_due: Decimal
    explanation: str


def calculate_form1040x(inp: Form1040XInput) -> Form1040XResult:
    """Calculate Form 1040-X amended return."""
    tax_difference = inp.corrected_tax - inp.original_tax
    payment_difference = inp.corrected_payments - inp.original_payments
    
    additional_tax_due = max(tax_difference - payment_difference, Decimal("0"))
    refund_due = max(payment_difference - tax_difference, Decimal("0"))
    
    # Simplified penalty/interest calculation
    penalty = (additional_tax_due * Decimal("0.05")).quantize(Decimal("0.01")) if additional_tax_due > 0 else Decimal("0")
    interest = (additional_tax_due * Decimal("0.08")).quantize(Decimal("0.01")) if additional_tax_due > 0 else Decimal("0")
    
    total_due = additional_tax_due + penalty + interest
    
    explanation = (
        f"Amended return: Additional tax ${additional_tax_due:,.2f}, "
        f"Penalty ${penalty:,.2f}, Interest ${interest:,.2f}"
    )
    
    return Form1040XResult(
        additional_tax_due=additional_tax_due,
        refund_due=refund_due,
        penalty=penalty,
        interest=interest,
        total_due=total_due,
        explanation=explanation,
    )


def get_form1040x_overview() -> dict:
    """Returns a structured explanation of Form 1040-X."""
    return {
        "form": "Form 1040-X",
        "title": "Amended U.S. Individual Income Tax Return",
        "purpose": "Form 1040-X is used to amend a previously filed Form 1040, 1040-SR, or 1040-NR.",
        "who_must_file": [
            "Taxpayers who need to correct errors on a previously filed return",
            "Taxpayers who need to claim additional deductions or credits",
            "Taxpayers who need to report additional income",
        ],
        "key_rules": [
            "Must be filed within 3 years of original filing date",
            "Cannot be e-filed; must be paper filed",
            "Include explanation of changes in Part III",
            "Attach supporting documentation for changes",
        ],
        "statutory_references": ["IRC §6213", "IRC §6501"],
        "related_forms": ["Form 1040", "Form 1040-SR", "Form 1040-NR"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-1040x",
    }
