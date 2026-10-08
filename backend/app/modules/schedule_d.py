"""
Schedule D — Capital Gains and Losses.

Business logic for Schedule D calculations under IRC §1221.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class ScheduleDInput:
    """Input for Schedule D calculation."""
    short_term_gains: Decimal = Decimal("0")
    short_term_losses: Decimal = Decimal("0")
    long_term_gains: Decimal = Decimal("0")
    long_term_losses: Decimal = Decimal("0")
    capital_loss_carryforward: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class ScheduleDResult:
    """Result of Schedule D calculation."""
    net_short_term: Decimal
    net_long_term: Decimal
    net_capital_gain: Decimal
    deductible_loss: Decimal
    carryforward: Decimal
    tax_rate: Decimal
    tax: Decimal
    explanation: str


CAPITAL_LOSS_DEDUCTION_LIMIT = Decimal("3000")

# Long-term capital gains rates (2025)
LTCG_RATES = {
    "single": [
        (Decimal("0"), Decimal("48350"), Decimal("0")),
        (Decimal("48350"), Decimal("533400"), Decimal("0.15")),
        (Decimal("533400"), Decimal("999999999"), Decimal("0.20")),
    ],
    "married_joint": [
        (Decimal("0"), Decimal("96700"), Decimal("0")),
        (Decimal("96700"), Decimal("600050"), Decimal("0.15")),
        (Decimal("600050"), Decimal("999999999"), Decimal("0.20")),
    ],
}


def calculate_schedule_d(inp: ScheduleDInput) -> ScheduleDResult:
    """Calculate Schedule D capital gains and losses."""
    # Net short-term and long-term
    net_short_term = inp.short_term_gains - inp.short_term_losses
    net_long_term = inp.long_term_gains - inp.long_term_losses
    
    # Net capital gain
    net_capital_gain = net_short_term + net_long_term
    
    # Capital loss deduction
    if net_capital_gain < 0:
        deductible_loss = min(abs(net_capital_gain), CAPITAL_LOSS_DEDUCTION_LIMIT)
        carryforward = abs(net_capital_gain) - deductible_loss + inp.capital_loss_carryforward
        tax = Decimal("0")
        tax_rate = Decimal("0")
    else:
        deductible_loss = Decimal("0")
        carryforward = inp.capital_loss_carryforward
        
        # Determine tax rate (simplified - assumes single filer)
        tax_rate = Decimal("0.15")
        for low, high, rate in LTCG_RATES["single"]:
            if low <= net_capital_gain < high:
                tax_rate = rate
                break
        
        # Tax on long-term gains (short-term taxed as ordinary income)
        tax = (net_long_term * tax_rate).quantize(Decimal("0.01")) if net_long_term > 0 else Decimal("0")
    
    explanation = (
        f"Capital gains: Net ${net_capital_gain:,.2f}, "
        f"Tax ${tax:,.2f}, Rate {tax_rate*100:.0f}%"
    )
    
    return ScheduleDResult(
        net_short_term=net_short_term,
        net_long_term=net_long_term,
        net_capital_gain=net_capital_gain,
        deductible_loss=deductible_loss,
        carryforward=carryforward,
        tax_rate=tax_rate,
        tax=tax,
        explanation=explanation,
    )


def get_schedule_d_overview() -> dict:
    """Returns a structured explanation of Schedule D."""
    return {
        "form": "Schedule D",
        "title": "Capital Gains and Losses",
        "purpose": "Schedule D is used to report capital gains and losses from the sale of capital assets.",
        "who_must_file": [
            "Taxpayers who sold capital assets",
            "Taxpayers with capital gains or losses",
            "Taxpayers who received capital gain distributions",
        ],
        "key_rules": [
            "Short-term gains taxed as ordinary income",
            "Long-term gains taxed at 0%, 15%, or 20%",
            "Capital losses can offset capital gains plus $3,000 of ordinary income",
            "Excess losses carried forward to future years",
        ],
        "statutory_references": ["IRC §1221", "IRC §1222", "IRC §1211"],
        "related_forms": ["Form 1040", "Form 8949"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-schedule-d-form-1040",
    }
