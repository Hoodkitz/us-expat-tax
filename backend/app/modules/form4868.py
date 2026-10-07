"""
Form 4868 — Application for Automatic Extension of Time to File.

Business logic for extension eligibility, deadline calculation,
and payment estimation under IRC §6081.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ExtensionInput:
    """Input for extension calculation."""
    filing_status: str
    tax_year: int
    original_deadline: date
    extension_months: int = 6
    estimated_tax_liability: Decimal = Decimal("0")
    amount_paid: Decimal = Decimal("0")
    reason: str = "automatic"


@dataclass
class ExtensionResult:
    """Result of extension calculation."""
    extended_deadline: date
    days_extended: int
    extension_granted: bool
    balance_due: Decimal
    payment_deadline: date
    penalty_if_not_filed: Decimal
    interest_if_not_paid: Decimal
    explanation: str


@dataclass
class ExtensionStatus:
    """Status of an extension request."""
    extension_filed: bool
    original_deadline: date
    extended_deadline: date
    days_remaining: int
    filing_status: str
    payment_status: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Standard extension period
STANDARD_EXTENSION_MONTHS = 6

# Original filing deadlines by tax year (simplified — actual dates vary)
# For most individual taxpayers: April 15
ORIGINAL_DEADLINES = {
    2025: date(2025, 4, 15),
    2024: date(2024, 4, 15),
    2023: date(2023, 4, 15),
    2022: date(2022, 4, 15),
}

# Extended deadlines (6 months from original)
EXTENDED_DEADLINES = {
    2025: date(2025, 10, 15),
    2024: date(2024, 10, 15),
    2023: date(2023, 10, 15),
    2022: date(2022, 10, 15),
}

# Failure to file penalty: 5% per month, max 25%
FAILURE_TO_FILE_RATE = Decimal("0.05")
FAILURE_TO_FILE_MAX = Decimal("0.25")

# Failure to pay penalty: 0.5% per month, max 25%
FAILURE_TO_PAY_RATE = Decimal("0.005")
FAILURE_TO_PAY_MAX = Decimal("0.25")

# Interest rate (simplified — actual rate varies quarterly)
INTEREST_RATE = Decimal("0.08")  # 8% annual

# Special rules for taxpayers living abroad
ABROAD_EXTENSION_MONTHS = 2  # Automatic 2-month extension to June 15
ABROAD_EXTENDED_DEADLINE = date(2025, 10, 15)  # Still Oct 15 with Form 4868


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------

def calculate_extension(inp: ExtensionInput) -> ExtensionResult:
    """
    Calculate extension deadline and associated penalties.

    Under IRC §6081:
    - Automatic 6-month extension available
    - Extension to file is NOT extension to pay
    - Taxes owed must still be paid by original deadline
    """
    # Calculate extended deadline
    extended_deadline = _calculate_extended_deadline(inp.original_deadline, inp.extension_months)
    days_extended = (extended_deadline - inp.original_deadline).days

    # Extension is automatically granted if filed by original deadline
    extension_granted = True

    # Balance due
    balance_due = max(Decimal("0"), inp.estimated_tax_liability - inp.amount_paid)

    # Payment deadline is ALWAYS the original deadline
    payment_deadline = inp.original_deadline

    # Penalties (if not filed by extended deadline)
    penalty_if_not_filed = _calculate_failure_to_file_penalty(
        inp.estimated_tax_liability, inp.extension_months
    )

    # Interest (if not paid by original deadline)
    interest_if_not_paid = _calculate_interest(
        balance_due, inp.original_deadline, extended_deadline
    )

    explanation = _generate_explanation(
        inp, extended_deadline, days_extended, balance_due,
        penalty_if_not_filed, interest_if_not_paid
    )

    return ExtensionResult(
        extended_deadline=extended_deadline,
        days_extended=days_extended,
        extension_granted=extension_granted,
        balance_due=balance_due,
        payment_deadline=payment_deadline,
        penalty_if_not_filed=penalty_if_not_filed,
        interest_if_not_paid=interest_if_not_paid,
        explanation=explanation,
    )


def get_extension_status(
    extension_filed: bool,
    tax_year: int,
    today: date | None = None,
) -> ExtensionStatus:
    """
    Get current status of extension request.

    Returns days remaining and filing/payment status.
    """
    if today is None:
        today = date.today()

    original = ORIGINAL_DEADLINES.get(tax_year, date(tax_year, 4, 15))
    extended = EXTENDED_DEADLINES.get(tax_year, date(tax_year, 10, 15))

    if extension_filed:
        days_remaining = (extended - today).days
        filing_status = "Extension filed" if days_remaining > 0 else "Extension expired"
        payment_status = "Payment due by original deadline"
    else:
        days_remaining = (original - today).days
        filing_status = "No extension filed" if days_remaining > 0 else "Past original deadline"
        payment_status = "Payment overdue" if days_remaining < 0 else "Payment due"

    return ExtensionStatus(
        extension_filed=extension_filed,
        original_deadline=original,
        extended_deadline=extended,
        days_remaining=days_remaining,
        filing_status=filing_status,
        payment_status=payment_status,
    )


def check_abroad_extension_eligible(
    country: str,
    tax_year: int,
    living_abroad: bool,
) -> dict:
    """
    Check if taxpayer qualifies for special abroad extension.

    Under IRC §6081 and §7508:
    - Taxpayers living outside the US get automatic 2-month extension to June 15
    - Can also file Form 4868 for additional extension to October 15
    - Must attach statement explaining why they qualify
    """
    if not living_abroad:
        return {
            "eligible": False,
            "reason": "Taxpayer must be living outside the United States",
            "automatic_extension": None,
            "extended_deadline": None,
        }

    # Automatic 2-month extension to June 15
    automatic_deadline = date(tax_year, 6, 15)

    # With Form 4868, extended to October 15
    extended_deadline = date(tax_year, 10, 15)

    return {
        "eligible": True,
        "reason": f"Taxpayer living in {country} qualifies for automatic 2-month extension",
        "automatic_extension": {
            "deadline": automatic_deadline.isoformat(),
            "months": 2,
        },
        "extended_deadline": extended_deadline.isoformat(),
        "requirements": [
            "Must be living outside the United States on the original due date",
            "Must be a US citizen or resident alien",
            "Must attach statement to return explaining qualification",
        ],
    }


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _calculate_extended_deadline(original: date, months: int) -> date:
    """Calculate extended deadline by adding months to original deadline."""
    year = original.year
    month = original.month + months

    # Handle year rollover
    while month > 12:
        month -= 12
        year += 1

    # Handle day overflow (e.g., March 31 + 1 month = April 30)
    day = original.day
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1


def _calculate_failure_to_file_penalty(tax_liability: Decimal, months: int) -> Decimal:
    """Calculate failure to file penalty (5% per month, max 25%)."""
    penalty_rate = min(FAILURE_TO_FILE_RATE * months, FAILURE_TO_FILE_MAX)
    penalty = tax_liability * penalty_rate
    return penalty.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calculate_interest(balance: Decimal, start_date: date, end_date: date) -> Decimal:
    """Calculate interest on unpaid tax."""
    days = (end_date - start_date).days
    daily_rate = INTEREST_RATE / Decimal("365")
    interest = balance * daily_rate * days
    return interest.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _generate_explanation(
    inp: ExtensionInput,
    extended_deadline: date,
    days_extended: int,
    balance_due: Decimal,
    penalty_if_not_filed: Decimal,
    interest_if_not_paid: Decimal,
) -> str:
    """Generate human-readable explanation."""
    parts = []

    parts.append(f"Original deadline: {inp.original_deadline.isoformat()}")
    parts.append(f"Extended deadline: {extended_deadline.isoformat()}")
    parts.append(f"Extension period: {days_extended} days ({inp.extension_months} months)")

    if balance_due > 0:
        parts.append(f"Balance due: ${balance_due:,.2f}")
        parts.append(f"Payment deadline: {inp.original_deadline.isoformat()} (NOT extended)")
    else:
        parts.append("No balance due — extension is for filing only")

    if penalty_if_not_filed > 0:
        parts.append(f"⚠️ Failure to file penalty if not filed by extended deadline: ${penalty_if_not_filed:,.2f}")

    if interest_if_not_paid > 0:
        parts.append(f"⚠️ Interest on unpaid tax: ${interest_if_not_paid:,.2f}")

    return " | ".join(parts)


def get_form4868_overview() -> dict:
    """Return static overview of Form 4868."""
    return {
        "form": "Form 4868",
        "title": "Application for Automatic Extension of Time to File",
        "purpose": (
            "Form 4868 is used to request an automatic 6-month extension "
            "to file your individual income tax return. The extension is "
            "automatically granted if filed by the original due date."
        ),
        "key_facts": [
            "Automatic 6-month extension (April 15 → October 15)",
            "Extension to file is NOT an extension to pay",
            "Taxes owed must still be paid by the original deadline",
            "No reason required for automatic extension",
            "Can be filed electronically or by mail",
        ],
        "deadlines": {
            "original": "April 15 (or next business day if weekend/holiday)",
            "extended": "October 15 (6 months from original)",
            "abroad_automatic": "June 15 (automatic 2-month for taxpayers abroad)",
        },
        "penalties": {
            "failure_to_file": "5% per month, max 25% of unpaid tax",
            "failure_to_pay": "0.5% per month, max 25% of unpaid tax",
            "interest": "Federal short-term rate + 3 percentage points",
        },
        "special_rules": {
            "taxpayers_abroad": "Automatic 2-month extension to June 15",
            "combat_zone": "Additional extension for service members in combat zones",
            "disaster_areas": "IRS may grant additional extensions for disaster victims",
        },
        "how_to_file": [
            "File electronically through IRS Free File or tax software",
            "Mail Form 4868 to IRS",
            "Pay estimated tax with extension request",
        ],
        "statutory_references": [
            "IRC §6081 — Extension of time for filing",
            "IRC §6651 — Failure to file or pay",
            "IRC §7508 — Extension for taxpayers in combat zones",
        ],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-4868",
    }
