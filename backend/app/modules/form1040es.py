"""
Form 1040-ES — Estimated Tax for Individuals.

Business logic for calculating estimated tax payments, safe harbor rules,
and underpayment penalties under IRC §6654.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class EstimatedTaxInput:
    """Input for estimated tax calculation."""
    filing_status: str
    annual_income: Decimal
    withholding: Decimal
    deductions: Decimal
    credits: Decimal
    prior_year_tax: Decimal
    current_year_tax: Decimal | None = None
    quarters_paid: int = 0
    amount_paid: Decimal = Decimal("0")


@dataclass
class EstimatedTaxResult:
    """Result of estimated tax calculation."""
    total_tax_liability: Decimal
    total_payments: Decimal
    balance_due: Decimal
    quarterly_payment: Decimal
    safe_harbor_met: bool
    safe_harbor_amount: Decimal
    underpayment_penalty: Decimal
    underpayment_quarters: int
    effective_tax_rate: Decimal
    marginal_tax_rate: Decimal
    explanation: str


@dataclass
class QuarterlyPayment:
    """Single quarterly payment details."""
    quarter: int
    due_date: str
    amount_due: Decimal
    cumulative_due: Decimal
    paid: Decimal
    balance: Decimal


@dataclass
class QuarterlySchedule:
    """Full quarterly payment schedule."""
    payments: list[QuarterlyPayment]
    total_due: Decimal
    total_paid: Decimal
    remaining_balance: Decimal


# ---------------------------------------------------------------------------
# Constants — 2025 Tax Year
# ---------------------------------------------------------------------------

# 2025 Federal Tax Brackets (Single)
TAX_BRACKETS_SINGLE = [
    (Decimal("0"), Decimal("11925"), Decimal("0.10")),
    (Decimal("11925"), Decimal("48475"), Decimal("0.12")),
    (Decimal("48475"), Decimal("103350"), Decimal("0.22")),
    (Decimal("103350"), Decimal("197300"), Decimal("0.24")),
    (Decimal("197300"), Decimal("250525"), Decimal("0.32")),
    (Decimal("250525"), Decimal("626350"), Decimal("0.35")),
    (Decimal("626350"), Decimal("999999999"), Decimal("0.37")),
]

# 2025 Federal Tax Brackets (Married Filing Jointly)
TAX_BRACKETS_MARRIED_JOINT = [
    (Decimal("0"), Decimal("23850"), Decimal("0.10")),
    (Decimal("23850"), Decimal("96950"), Decimal("0.12")),
    (Decimal("96950"), Decimal("206700"), Decimal("0.22")),
    (Decimal("206700"), Decimal("394600"), Decimal("0.24")),
    (Decimal("394600"), Decimal("501050"), Decimal("0.32")),
    (Decimal("501050"), Decimal("751600"), Decimal("0.35")),
    (Decimal("751600"), Decimal("999999999"), Decimal("0.37")),
]

# 2025 Federal Tax Brackets (Married Filing Separately)
TAX_BRACKETS_MARRIED_SEPARATE = [
    (Decimal("0"), Decimal("11925"), Decimal("0.10")),
    (Decimal("11925"), Decimal("48475"), Decimal("0.12")),
    (Decimal("48475"), Decimal("103350"), Decimal("0.22")),
    (Decimal("103350"), Decimal("197300"), Decimal("0.24")),
    (Decimal("197300"), Decimal("250525"), Decimal("0.32")),
    (Decimal("250525"), Decimal("375800"), Decimal("0.35")),
    (Decimal("375800"), Decimal("999999999"), Decimal("0.37")),
]

# 2025 Federal Tax Brackets (Head of Household)
TAX_BRACKETS_HEAD_OF_HOUSEHOLD = [
    (Decimal("0"), Decimal("17000"), Decimal("0.10")),
    (Decimal("17000"), Decimal("64850"), Decimal("0.12")),
    (Decimal("64850"), Decimal("103350"), Decimal("0.22")),
    (Decimal("103350"), Decimal("197300"), Decimal("0.24")),
    (Decimal("197300"), Decimal("250500"), Decimal("0.32")),
    (Decimal("250500"), Decimal("626350"), Decimal("0.35")),
    (Decimal("626350"), Decimal("999999999"), Decimal("0.37")),
]

# Standard Deductions (2025)
STANDARD_DEDUCTIONS = {
    "single": Decimal("15000"),
    "married_joint": Decimal("30000"),
    "married_separate": Decimal("15000"),
    "head_of_household": Decimal("22500"),
}

# Safe Harbor Rules
SAFE_HARBOR_PERCENTAGE = Decimal("0.90")  # 90% of current year
SAFE_HARBOR_PRIOR_PERCENTAGE = Decimal("1.00")  # 100% of prior year
SAFE_HARBOR_PRIOR_HIGH_PERCENTAGE = Decimal("1.10")  # 110% if AGI > $150k

# Underpayment Penalty Rate (2025, quarterly)
UNDERPAYMENT_PENALTY_RATE = Decimal("0.0025")  # ~1% annual (varies by quarter)

# Quarterly Due Dates
QUARTERLY_DUE_DATES = {
    1: "April 15",
    2: "June 15",
    3: "September 15",
    4: "January 15 (following year)",
}

# High AGI threshold for 110% safe harbor
HIGH_AGI_THRESHOLD = Decimal("150000")


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------

def _get_brackets(filing_status: str) -> list[tuple[Decimal, Decimal, Decimal]]:
    """Get tax brackets for filing status."""
    brackets = {
        "single": TAX_BRACKETS_SINGLE,
        "married_joint": TAX_BRACKETS_MARRIED_JOINT,
        "married_separate": TAX_BRACKETS_MARRIED_SEPARATE,
        "head_of_household": TAX_BRACKETS_HEAD_OF_HOUSEHOLD,
    }
    return brackets.get(filing_status, TAX_BRACKETS_SINGLE)


def _calculate_tax_from_brackets(taxable_income: Decimal, brackets: list[tuple[Decimal, Decimal, Decimal]]) -> Decimal:
    """Calculate tax using progressive brackets."""
    tax = Decimal("0")
    for lower, upper, rate in brackets:
        if taxable_income > lower:
            taxable_at_rate = min(taxable_income, upper) - lower
            if taxable_at_rate > 0:
                tax += taxable_at_rate * rate
        else:
            break
    return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get_marginal_rate(taxable_income: Decimal, brackets: list[tuple[Decimal, Decimal, Decimal]]) -> Decimal:
    """Get the marginal tax rate for the given taxable income."""
    for lower, upper, rate in brackets:
        if taxable_income <= upper:
            return rate
    return brackets[-1][2] if brackets else Decimal("0")


def calculate_estimated_tax(inp: EstimatedTaxInput) -> EstimatedTaxResult:
    """
    Calculate estimated tax liability and quarterly payments.

    Applies 2025 tax rules:
    - Progressive tax brackets
    - Safe harbor rules (90% current year or 100%/110% prior year)
    - Underpayment penalty calculation
    """
    # Determine standard deduction
    std_deduction = STANDARD_DEDUCTIONS.get(inp.filing_status, Decimal("15000"))
    total_deductions = max(inp.deductions, std_deduction)

    # Calculate taxable income
    taxable_income = max(Decimal("0"), inp.annual_income - total_deductions)

    # Get brackets and calculate tax
    brackets = _get_brackets(inp.filing_status)
    total_tax = _calculate_tax_from_brackets(taxable_income, brackets)

    # Apply credits
    tax_after_credits = max(Decimal("0"), total_tax - inp.credits)

    # Total payments (withholding + estimated paid)
    total_payments = inp.withholding + inp.amount_paid

    # Balance due
    balance_due = max(Decimal("0"), tax_after_credits - total_payments)

    # Quarterly payment (divide remaining by remaining quarters)
    remaining_quarters = max(1, 4 - inp.quarters_paid)
    quarterly_payment = (balance_due / remaining_quarters).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Safe harbor calculation
    safe_harbor_amount = _calculate_safe_harbor(inp, tax_after_credits)
    safe_harbor_met = total_payments >= safe_harbor_amount

    # Underpayment penalty
    underpayment_penalty = _calculate_underpayment_penalty(
        inp, tax_after_credits, total_payments, safe_harbor_met
    )

    # Effective and marginal rates
    effective_rate = (tax_after_credits / inp.annual_income) if inp.annual_income > 0 else Decimal("0")
    marginal_rate = _get_marginal_rate(taxable_income, brackets)

    # Generate explanation
    explanation = _generate_explanation(
        inp, taxable_income, total_tax, tax_after_credits, total_payments,
        balance_due, safe_harbor_met, safe_harbor_amount, underpayment_penalty
    )

    return EstimatedTaxResult(
        total_tax_liability=tax_after_credits,
        total_payments=total_payments,
        balance_due=balance_due,
        quarterly_payment=quarterly_payment,
        safe_harbor_met=safe_harbor_met,
        safe_harbor_amount=safe_harbor_amount,
        underpayment_penalty=underpayment_penalty,
        underpayment_quarters=inp.quarters_paid if not safe_harbor_met else 0,
        effective_tax_rate=effective_rate,
        marginal_tax_rate=marginal_rate,
        explanation=explanation,
    )


def calculate_quarterly_schedule(inp: EstimatedTaxInput) -> QuarterlySchedule:
    """
    Calculate the full quarterly payment schedule.

    Shows cumulative due dates and remaining balance.
    """
    result = calculate_estimated_tax(inp)
    remaining = result.balance_due
    payments = []

    for q in range(1, 5):
        # Each quarter's payment is 1/4 of total estimated tax
        quarterly_due = (result.total_tax_liability / 4).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        cumulative_due = quarterly_due * q

        # Amount paid through this quarter
        if q <= inp.quarters_paid:
            paid = (quarterly_due * q).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            paid = (quarterly_due * inp.quarters_paid).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        balance = max(Decimal("0"), cumulative_due - paid)

        payments.append(QuarterlyPayment(
            quarter=q,
            due_date=QUARTERLY_DUE_DATES[q],
            amount_due=quarterly_due,
            cumulative_due=cumulative_due,
            paid=paid,
            balance=balance,
        ))

    total_due = result.total_tax_liability
    total_paid = result.total_payments
    remaining_balance = max(Decimal("0"), total_due - total_paid)

    return QuarterlySchedule(
        payments=payments,
        total_due=total_due,
        total_paid=total_paid,
        remaining_balance=remaining_balance,
    )


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _calculate_safe_harbor(inp: EstimatedTaxInput, current_year_tax: Decimal) -> Decimal:
    """
    Calculate safe harbor amount.

    Safe harbor is the LESSER of:
    - 90% of current year tax
    - 100% of prior year tax (110% if AGI > $150k)
    """
    # 90% of current year
    current_year_safe = current_year_tax * SAFE_HARBOR_PERCENTAGE

    # Prior year safe harbor
    if inp.annual_income > HIGH_AGI_THRESHOLD:
        prior_year_safe = inp.prior_year_tax * SAFE_HARBOR_PRIOR_HIGH_PERCENTAGE
    else:
        prior_year_safe = inp.prior_year_tax * SAFE_HARBOR_PRIOR_PERCENTAGE

    return min(current_year_safe, prior_year_safe).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calculate_underpayment_penalty(
    inp: EstimatedTaxInput,
    tax_after_credits: Decimal,
    total_payments: Decimal,
    safe_harbor_met: bool,
) -> Decimal:
    """
    Calculate underpayment penalty under IRC §6654.

    Penalty applies if:
    - Total payments < 90% of current year tax AND
    - Total payments < 100%/110% of prior year tax
    """
    if safe_harbor_met:
        return Decimal("0")

    # Required annual payment
    required = min(
        tax_after_credits * SAFE_HARBOR_PERCENTAGE,
        inp.prior_year_tax * SAFE_HARBOR_PRIOR_PERCENTAGE
    )

    if total_payments >= required:
        return Decimal("0")

    underpayment = required - total_payments
    # Simplified: penalty = underpayment * quarterly rate * quarters underpaid
    quarters_underpaid = max(1, 4 - inp.quarters_paid)
    penalty = underpayment * UNDERPAYMENT_PENALTY_RATE * quarters_underpaid

    return penalty.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _generate_explanation(
    inp: EstimatedTaxInput,
    taxable_income: Decimal,
    total_tax: Decimal,
    tax_after_credits: Decimal,
    total_payments: Decimal,
    balance_due: Decimal,
    safe_harbor_met: bool,
    safe_harbor_amount: Decimal,
    underpayment_penalty: Decimal,
) -> str:
    """Generate human-readable explanation."""
    parts = []

    parts.append(f"Taxable income: ${taxable_income:,.2f}")
    parts.append(f"Total tax before credits: ${total_tax:,.2f}")
    parts.append(f"Tax after credits: ${tax_after_credits:,.2f}")
    parts.append(f"Total payments (withholding + estimated): ${total_payments:,.2f}")

    if balance_due > 0:
        parts.append(f"Balance due: ${balance_due:,.2f}")
    else:
        parts.append(f"Refund/overpayment: ${abs(balance_due):,.2f}")

    if safe_harbor_met:
        parts.append(f"✅ Safe harbor met (${safe_harbor_amount:,.2f}) — no underpayment penalty.")
    else:
        parts.append(f"⚠️ Safe harbor NOT met (required: ${safe_harbor_amount:,.2f}).")
        if underpayment_penalty > 0:
            parts.append(f"Estimated underpayment penalty: ${underpayment_penalty:,.2f}")

    return " | ".join(parts)


def get_form1040es_overview() -> dict:
    """Return static overview of Form 1040-ES."""
    return {
        "form": "Form 1040-ES",
        "title": "Estimated Tax for Individuals",
        "purpose": (
            "Form 1040-ES is used to calculate and pay estimated tax on income "
            "that is not subject to withholding, such as self-employment income, "
            "interest, dividends, rental income, and other sources. Taxpayers "
            "generally must pay estimated tax if they expect to owe $1,000 or more."
        ),
        "who_must_file": [
            "Self-employed individuals with net earnings ≥ $400",
            "Taxpayers with significant non-wage income (interest, dividends, capital gains)",
            "Taxpayers whose withholding is insufficient",
            "Individuals expecting to owe ≥ $1,000 in tax after withholding",
        ],
        "safe_harbor_rules": {
            "rule_1": "Pay 90% of current year tax liability",
            "rule_2": "Pay 100% of prior year tax (110% if AGI > $150,000)",
            "description": "Meeting either rule avoids underpayment penalties",
        },
        "quarterly_due_dates": {
            "Q1": "April 15",
            "Q2": "June 15",
            "Q3": "September 15",
            "Q4": "January 15 (following year)",
        },
        "underpayment_penalty": {
            "applies_when": "Total payments < 90% of current year AND < 100%/110% of prior year",
            "rate": "Federal short-term rate + 3 percentage points (varies quarterly)",
            "irc_reference": "IRC §6654",
        },
        "key_rules": [
            "Estimated tax is paid in 4 equal quarterly installments",
            "Safe harbor protects against underpayment penalties",
            "Annualized income method may help with uneven income",
            "Farmers and fishermen have special rules (2/3 threshold)",
        ],
        "statutory_references": [
            "IRC §6654 — Failure by individual to pay estimated tax",
            "IRC §6655 — Failure by corporation to pay estimated tax",
            "IRC §6154 — Payment of estimated tax",
        ],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-1040-es",
    }
