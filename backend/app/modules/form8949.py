"""
Form 8949 — Sales and Other Dispositions of Capital Assets.

Business logic for calculating short-term and long-term capital gains/losses.
Used by US expats to report stock sales, crypto dispositions, and other capital asset transactions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Transaction:
    """A single capital asset disposition transaction."""
    purchase_date: str       # ISO format YYYY-MM-DD
    purchase_price: Decimal  # Cost basis in USD
    sale_date: str           # ISO format YYYY-MM-DD
    sale_price: Decimal      # Proceeds in USD
    description: str = ""    # Asset description (e.g., "AAPL", "BTC")


@dataclass
class Form8949Input:
    """Input for Form 8949 calculation."""
    transactions: list[Transaction]


@dataclass
class Form8949Transaction:
    """A processed transaction with computed gain/loss and holding period."""
    description: str
    purchase_date: str
    sale_date: str
    purchase_price: Decimal
    sale_price: Decimal
    gain_loss: Decimal
    holding_period: str  # "short-term" or "long-term"
    holding_days: int


@dataclass
class Form8949Result:
    """Result of Form 8949 calculation."""
    short_term_transactions: list[Form8949Transaction] = field(default_factory=list)
    long_term_transactions: list[Form8949Transaction] = field(default_factory=list)
    short_term_total: Decimal = Decimal("0")
    long_term_total: Decimal = Decimal("0")
    net_gain_loss: Decimal = Decimal("0")
    short_term_count: int = 0
    long_term_count: int = 0
    explanation: str = ""


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> date:
    """Parse ISO date string to date object."""
    return datetime.fromisoformat(date_str).date()


def _is_long_term(purchase_date: date, sale_date: date) -> bool:
    """
    Determine if a transaction is long-term (held more than 1 year).

    IRS rule: Short-term = 1 year or less; Long-term = more than 1 year.
    """
    try:
        one_year_after = purchase_date.replace(year=purchase_date.year + 1)
    except ValueError:
        # Feb 29 case — use Mar 1 of next year
        one_year_after = date(purchase_date.year + 1, 3, 1)
    return sale_date > one_year_after


def _calculate_holding_days(purchase_date: date, sale_date: date) -> int:
    """Calculate the number of days the asset was held."""
    return (sale_date - purchase_date).days


def calculate_form8949(inp: Form8949Input) -> Form8949Result:
    """
    Calculate Form 8949 short-term and long-term capital gains/losses.

    For each transaction:
    - Gain/Loss = Sale Price - Purchase Price
    - Short-term: held <= 1 year
    - Long-term: held > 1 year
    """
    result = Form8949Result()

    for tx in inp.transactions:
        purchase_date = _parse_date(tx.purchase_date)
        sale_date = _parse_date(tx.sale_date)

        # Calculate gain/loss
        gain_loss = tx.sale_price - tx.purchase_price
        gain_loss = gain_loss.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Determine holding period
        is_long = _is_long_term(purchase_date, sale_date)
        holding_period = "long-term" if is_long else "short-term"
        holding_days = _calculate_holding_days(purchase_date, sale_date)

        processed = Form8949Transaction(
            description=tx.description,
            purchase_date=tx.purchase_date,
            sale_date=tx.sale_date,
            purchase_price=tx.purchase_price,
            sale_price=tx.sale_price,
            gain_loss=gain_loss,
            holding_period=holding_period,
            holding_days=holding_days,
        )

        if is_long:
            result.long_term_transactions.append(processed)
            result.long_term_total += gain_loss
            result.long_term_count += 1
        else:
            result.short_term_transactions.append(processed)
            result.short_term_total += gain_loss
            result.short_term_count += 1

    # Round totals
    result.short_term_total = result.short_term_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    result.long_term_total = result.long_term_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    result.net_gain_loss = (result.short_term_total + result.long_term_total).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Generate explanation
    parts = []
    if result.short_term_count > 0:
        parts.append(
            f"Short-term: {result.short_term_count} transaction(s), "
            f"net {'gain' if result.short_term_total >= 0 else 'loss'} of ${abs(result.short_term_total):,.2f}"
        )
    if result.long_term_count > 0:
        parts.append(
            f"Long-term: {result.long_term_count} transaction(s), "
            f"net {'gain' if result.long_term_total >= 0 else 'loss'} of ${abs(result.long_term_total):,.2f}"
        )
    if not parts:
        parts.append("No transactions provided.")

    result.explanation = "Form 8949 Summary: " + "; ".join(parts) + "."

    return result


def get_form8949_overview() -> dict:
    """Returns a structured explanation of Form 8949."""
    return {
        "form": "Form 8949",
        "title": "Sales and Other Dispositions of Capital Assets",
        "purpose": (
            "Form 8949 is used to report sales and other dispositions of capital assets, "
            "including stocks, bonds, cryptocurrency, and other investment property. "
            "It separates short-term (held 1 year or less) and long-term (held more than 1 year) "
            "transactions, which are taxed at different rates."
        ),
        "who_must_file": [
            "Taxpayers who sold stocks, bonds, or other securities",
            "Taxpayers who disposed of cryptocurrency",
            "Taxpayers with capital asset dispositions reportable on Schedule D",
        ],
        "key_rules": [
            "Short-term gains: taxed as ordinary income (up to 37%)",
            "Long-term gains: taxed at preferential rates (0%, 15%, or 20%)",
            "Net capital losses can offset up to $3,000 of ordinary income per year",
            "Excess capital losses carry forward to future years",
            "Wash sale rules apply to substantially identical securities",
        ],
        "statutory_references": [
            "IRC §1221 — Capital asset defined",
            "IRC §1222 — Short-term and long-term gains and losses",
            "IRC §1211 — Limitation on capital losses",
        ],
        "related_forms": ["Schedule D", "Form 1040", "Form 8949"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8949",
    }
