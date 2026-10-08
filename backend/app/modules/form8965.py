"""
Form 8965 — Health Coverage Exemptions.

Business logic for Form 8965 calculations under IRC §5000A.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8965Input:
    """Input for Form 8965 calculation."""
    exemption_type: str
    months_without_coverage: int
    household_income: Decimal
    filing_threshold: Decimal
    tax_year: int = 2025


@dataclass
class Form8965Result:
    """Result of Form 8965 calculation."""
    exemption_approved: bool
    penalty: Decimal
    explanation: str


def calculate_form8965(inp: Form8965Input) -> Form8965Result:
    """Calculate Form 8965 health coverage exemptions."""
    # Individual mandate penalty suspended after 2018
    # But some states have their own mandates
    penalty = Decimal("0")
    
    # Check if exemption applies
    exemption_approved = False
    
    if inp.exemption_type in ["hardship", "religious_conscience", "health_care_sharing_ministry", "incarceration", "native_american"]:
        exemption_approved = True
    elif inp.exemption_type == "income_below_filing_threshold":
        if inp.household_income < inp.filing_threshold:
            exemption_approved = True
    
    explanation = (
        f"Exemption: {inp.exemption_type}, "
        f"Approved: {exemption_approved}, "
        f"Penalty: ${penalty:,.2f}"
    )
    
    return Form8965Result(
        exemption_approved=exemption_approved,
        penalty=penalty,
        explanation=explanation,
    )


def get_form8965_overview() -> dict:
    """Returns a structured explanation of Form 8965."""
    return {
        "form": "Form 8965",
        "title": "Health Coverage Exemptions",
        "purpose": "Form 8965 is used to claim exemptions from the individual shared responsibility provision.",
        "who_must_file": [
            "Taxpayers who were unqualified for health coverage for part of the year",
            "Taxpayers who qualify for an exemption from the coverage requirement",
            "Taxpayers who need to reconcile advance premium tax credit",
        ],
        "key_rules": [
            "Exemptions include hardship, religious conscience, membership in health care sharing ministry",
            "Exemptions can be claimed on the return or granted by the Marketplace",
            "Individual mandate penalty suspended after 2018",
            "Some states have their own mandates",
        ],
        "statutory_references": ["IRC §5000A", "IRC §5000A(d)"],
        "related_forms": ["Form 1040", "Form 8962"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8965",
    }
