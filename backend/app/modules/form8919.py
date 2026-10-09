"""
Form 8919 — Uncollected Social Security and Medicare Tax on Wages.

Business logic for Form 8919 calculations.
Employee pays 7.65% (6.2% SS up to wage base + 1.45% Medicare).
Employer pays matching 7.65%. Total 15.3%.
Used when employer doesn't withhold.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8919Input:
    """Input for Form 8919 calculation."""
    wages: Decimal
    tax_year: int = 2025


@dataclass
class Form8919Result:
    """Result of Form 8919 calculation."""
    social_security_tax: Decimal
    medicare_tax: Decimal
    total_tax: Decimal
    explanation: str


# 2025 Social Security wage base limit
SS_WAGE_BASE_2025 = Decimal("176100")

# Tax rates
SS_RATE = Decimal("0.062")       # 6.2% Social Security
MEDICARE_RATE = Decimal("0.0145")  # 1.45% Medicare
TOTAL_RATE = Decimal("0.0765")    # 7.65% combined


def calculate_form8919(inp: Form8919Input) -> Form8919Result:
    """Calculate Form 8919 uncollected Social Security and Medicare tax."""
    wages = inp.wages

    # Social Security tax: 6.2% on wages up to the wage base
    ss_wages = min(wages, SS_WAGE_BASE_2025)
    social_security_tax = (ss_wages * SS_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Medicare tax: 1.45% on all wages (no cap)
    medicare_tax = (wages * MEDICARE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Total employee share
    total_tax = social_security_tax + medicare_tax

    explanation = (
        f"Uncollected Social Security and Medicare tax on ${wages:,.2f} wages: "
        f"Social Security tax ${social_security_tax:,.2f} "
        f"(6.2% on ${ss_wages:,.2f} up to ${SS_WAGE_BASE_2025:,.2f} wage base), "
        f"Medicare tax ${medicare_tax:,.2f} (1.45% on all wages). "
        f"Total employee share: ${total_tax:,.2f}."
    )

    return Form8919Result(
        social_security_tax=social_security_tax,
        medicare_tax=medicare_tax,
        total_tax=total_tax,
        explanation=explanation,
    )


def get_form8919_overview() -> dict:
    """Returns a structured explanation of Form 8919."""
    return {
        "form": "Form 8919",
        "title": "Uncollected Social Security and Medicare Tax on Wages",
        "purpose": (
            "Form 8919 is used to figure the uncollected Social Security and Medicare tax "
            "on wages received from an employer who did not withhold these taxes."
        ),
        "who_must_file": [
            "Employees who received wages but employer did not withhold Social Security and Medicare tax",
            "Employees with tips that were not reported to employer or employer did not withhold on",
            "Employees who need to pay the employee share of FICA taxes",
        ],
        "key_rules": [
            "Employee pays 7.65% total: 6.2% Social Security (up to wage base) + 1.45% Medicare (no cap)",
            "Employer pays matching 7.65%",
            "2025 Social Security wage base limit: $176,100",
            "Medicare tax applies to all wages with no limit",
            "Additional Medicare tax of 0.9% may apply to high earners",
        ],
        "statutory_references": ["IRC §3101", "IRC §3111", "IRC §3102"],
        "related_forms": ["Form 1040", "Schedule 2", "Form 4137"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8919",
    }
