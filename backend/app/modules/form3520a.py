"""
Form 3520-A: Annual Information Return of Foreign Trust With a U.S. Owner.

Implements:
- Filing requirement determination (Owner vs Beneficiary, Foreign Grantor Trust vs Non-Grantor Trust)
- Income distribution calculations for U.S. beneficiaries
- Foreign Grantor Trust Statement requirements
- Penalty calculations under IRC §6677

References:
- IRC §6048(b) - Foreign trust reporting
- IRC §679 - Foreign trusts having one or more U.S. beneficiaries
- IRC §6677 - Failure to file information with respect to foreign trusts
- Form 3520-A Instructions (2024)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

TrustType = Literal["FOREIGN_GRANTOR", "NON_GRANTOR"]
FilerRole = Literal["OWNER", "BENEFICIARY"]
IncomeType = Literal["INTEREST", "DIVIDENDS", "CAPITAL_GAINS", "RENTAL", "OTHER"]


# ---------------------------------------------------------------------------
# Filing Requirement
# ---------------------------------------------------------------------------


def determine_filing_requirement(
    is_us_owner: bool,
    is_us_beneficiary: bool,
    trust_type: TrustType,
    received_distribution: bool,
    distribution_amount_usd: float = 0.0,
) -> dict:
    """
    Determine whether Form 3520-A must be filed and by whom.

    Form 3520-A is filed BY the foreign trust (or its U.S. agent), but the
    filing requirement depends on whether there are U.S. owners or beneficiaries.

    Args:
        is_us_owner: Trust has at least one U.S. owner (grantor)
        is_us_beneficiary: Trust has at least one U.S. beneficiary
        trust_type: FOREIGN_GRANTOR or NON_GRANTOR
        received_distribution: Beneficiary received a distribution
        distribution_amount_usd: Amount of distribution (if any)

    Returns:
        Dictionary with filing_required (bool), filer_role, trust_type, and reasons
    """
    reasons = []
    filing_required = False
    filer_role = None

    if is_us_owner and trust_type == "FOREIGN_GRANTOR":
        filing_required = True
        filer_role = "OWNER"
        reasons.append(
            "Foreign grantor trust with U.S. owner must file Form 3520-A annually"
        )
        reasons.append(
            "U.S. owner must provide Foreign Grantor Trust Owner Statement to beneficiaries"
        )

    if is_us_beneficiary and trust_type == "NON_GRANTOR":
        if received_distribution and distribution_amount_usd > 0:
            filing_required = True
            filer_role = "BENEFICIARY"
            reasons.append(
                f"U.S. beneficiary received distribution of ${distribution_amount_usd:,.2f} from foreign non-grantor trust"
            )
            reasons.append("Foreign trust must file Form 3520-A to report distribution")

    if not filing_required:
        reasons.append("No Form 3520-A filing requirement based on provided facts")

    return {
        "filing_required": filing_required,
        "filer_role": filer_role,
        "trust_type": trust_type,
        "reasons": reasons,
        "us_owner": is_us_owner,
        "us_beneficiary": is_us_beneficiary,
    }


# ---------------------------------------------------------------------------
# Income Distribution
# ---------------------------------------------------------------------------


class IncomeDistributionItem:
    """Represents a single income distribution from foreign trust to U.S. beneficiary."""

    def __init__(
        self,
        income_type: IncomeType,
        gross_amount_usd: float,
        withholding_tax_usd: float,
        distribution_date: str,
        source_country: str,
    ):
        self.income_type = income_type
        self.gross_amount_usd = Decimal(str(gross_amount_usd))
        self.withholding_tax_usd = Decimal(str(withholding_tax_usd))
        self.distribution_date = distribution_date
        self.source_country = source_country

    @property
    def net_amount_usd(self) -> Decimal:
        return self.gross_amount_usd - self.withholding_tax_usd

    def to_dict(self) -> dict:
        return {
            "income_type": self.income_type,
            "gross_amount_usd": float(self.gross_amount_usd),
            "withholding_tax_usd": float(self.withholding_tax_usd),
            "net_amount_usd": float(self.net_amount_usd),
            "distribution_date": self.distribution_date,
            "source_country": self.source_country,
        }


def calculate_income_distribution(
    distributions: list[IncomeDistributionItem],
    trust_type: TrustType,
) -> dict:
    """
    Calculate total income distribution from foreign trust to U.S. beneficiaries.

    For non-grantor trusts, distributions are taxable to the beneficiary.
    For grantor trusts, income is taxed to the grantor regardless of distributions.

    Returns:
        Summary of distributions by type, total gross, total withholding, net amount
    """
    total_gross = Decimal("0")
    total_withholding = Decimal("0")
    by_type = {}

    for dist in distributions:
        total_gross += dist.gross_amount_usd
        total_withholding += dist.withholding_tax_usd

        if dist.income_type not in by_type:
            by_type[dist.income_type] = {
                "count": 0,
                "gross": Decimal("0"),
                "withholding": Decimal("0"),
            }

        by_type[dist.income_type]["count"] += 1
        by_type[dist.income_type]["gross"] += dist.gross_amount_usd
        by_type[dist.income_type]["withholding"] += dist.withholding_tax_usd

    total_net = total_gross - total_withholding

    # Convert by_type to serializable format
    by_type_serialized = {}
    for income_type, data in by_type.items():
        by_type_serialized[income_type] = {
            "count": data["count"],
            "gross_usd": float(data["gross"]),
            "withholding_usd": float(data["withholding"]),
            "net_usd": float(data["gross"] - data["withholding"]),
        }

    tax_treatment = (
        "Distributions taxable to U.S. beneficiary"
        if trust_type == "NON_GRANTOR"
        else "Income taxable to U.S. grantor/owner (not beneficiary)"
    )

    return {
        "trust_type": trust_type,
        "total_distributions": len(distributions),
        "total_gross_usd": float(total_gross),
        "total_withholding_usd": float(total_withholding),
        "total_net_usd": float(total_net),
        "by_income_type": by_type_serialized,
        "tax_treatment": tax_treatment,
        "distributions": [d.to_dict() for d in distributions],
    }


# ---------------------------------------------------------------------------
# Foreign Grantor Trust Statement
# ---------------------------------------------------------------------------


def generate_foreign_grantor_statement(
    trust_name: str,
    trust_ein: str,
    trust_country: str,
    us_owner_name: str,
    us_owner_ssn: str,
    tax_year: int,
    trust_assets_usd: float,
    trust_income_usd: float,
    trust_distributions_usd: float,
) -> dict:
    """
    Generate Foreign Grantor Trust Owner Statement.

    A U.S. owner of a foreign grantor trust must:
    1. Ensure the trust files Form 3520-A
    2. Provide a Foreign Grantor Trust Owner Statement to all beneficiaries
    3. Report the trust's income on their personal return

    Returns:
        Statement data for the U.S. owner to attach to their Form 1040
    """
    statement_date = datetime.now().strftime("%Y-%m-%d")

    return {
        "statement_type": "FOREIGN_GRANTOR_TRUST_OWNER_STATEMENT",
        "trust_name": trust_name,
        "trust_ein": trust_ein,
        "trust_country": trust_country,
        "tax_year": tax_year,
        "us_owner_name": us_owner_name,
        "us_owner_ssn": us_owner_ssn,
        "trust_assets_usd": trust_assets_usd,
        "trust_income_usd": trust_income_usd,
        "trust_distributions_usd": trust_distributions_usd,
        "statement_date": statement_date,
        "owner_obligations": [
            "File Form 3520-A (or ensure trust files via U.S. agent)",
            "Report trust income on Form 1040 as if earned directly",
            "Provide this statement to all trust beneficiaries",
            "Attach this statement to Form 1040",
        ],
        "grantor_trust_rules": "Under IRC §679, a foreign trust with a U.S. beneficiary is treated as having a U.S. owner if a U.S. person transferred property to the trust.",
    }


# ---------------------------------------------------------------------------
# Penalty Calculator (IRC §6677)
# ---------------------------------------------------------------------------


def calculate_form3520a_penalties(
    filing_deadline: str,
    actual_filing_date: str | None,
    trust_gross_value_usd: float,
    is_initial_failure: bool = True,
) -> dict:
    """
    Calculate penalties for failure to file Form 3520-A under IRC §6677.

    Penalties:
    - Initial failure: 5% of gross value of trust assets for the tax year
    - Continued failure after 90 days: Additional 5% per 30-day period (max 25% total)
    - Maximum penalty: 25% of gross value of trust assets

    Args:
        filing_deadline: Deadline in YYYY-MM-DD format (typically March 15 + extension)
        actual_filing_date: Actual filing date (None if not yet filed)
        trust_gross_value_usd: Gross value of trust assets for the tax year
        is_initial_failure: Whether this is the initial failure to file

    Returns:
        Penalty calculation breakdown
    """
    deadline = datetime.strptime(filing_deadline, "%Y-%m-%d")
    initial_penalty_rate = Decimal("0.05")  # 5%
    continuing_penalty_rate = Decimal("0.05")  # 5% per 30-day period
    max_penalty_rate = Decimal("0.25")  # 25% maximum

    trust_value = Decimal(str(trust_gross_value_usd))

    if actual_filing_date:
        filed = datetime.strptime(actual_filing_date, "%Y-%m-%d")
        days_late = max(0, (filed - deadline).days)
    else:
        # Not yet filed - calculate from today
        days_late = max(0, (datetime.now() - deadline).days)

    penalties = []
    total_penalty = Decimal("0")

    if days_late > 0:
        # Initial 5% penalty
        initial_penalty = trust_value * initial_penalty_rate
        penalties.append(
            {
                "type": "INITIAL_FAILURE",
                "rate": "5%",
                "amount_usd": float(initial_penalty),
                "description": "Initial failure to file Form 3520-A on time",
            }
        )
        total_penalty += initial_penalty

        # Continuing penalty after 90 days
        if days_late > 90:
            days_beyond_90 = days_late - 90
            # Calculate number of 30-day periods (rounded up)
            periods = (days_beyond_90 + 29) // 30

            continuing_penalty = min(
                trust_value * continuing_penalty_rate * Decimal(periods),
                trust_value * (max_penalty_rate - initial_penalty_rate),
            )

            penalties.append(
                {
                    "type": "CONTINUING_FAILURE",
                    "rate": f"5% per 30-day period (×{periods})",
                    "amount_usd": float(continuing_penalty),
                    "description": f"Continued failure for {days_beyond_90} days beyond initial 90-day period",
                    "periods": periods,
                }
            )
            total_penalty += continuing_penalty

    # Cap at 25% maximum
    max_penalty = trust_value * max_penalty_rate
    if total_penalty > max_penalty:
        total_penalty = max_penalty

    return {
        "filing_deadline": filing_deadline,
        "actual_filing_date": actual_filing_date,
        "days_late": days_late if days_late > 0 else 0,
        "trust_gross_value_usd": float(trust_value),
        "penalties": penalties,
        "total_penalty_usd": float(total_penalty),
        "penalty_rate": f"{float(total_penalty / trust_value * 100):.2f}%" if trust_value > 0 else "0%",
        "maximum_penalty_usd": float(max_penalty),
        "penalty_capped": total_penalty >= max_penalty,
        "statute": "IRC §6677",
        "notes": [
            "Penalties may be waived for reasonable cause",
            "Form 3520-A due date: 15th day of 3rd month after tax year end (March 15 for calendar year)",
            "Automatic 6-month extension available by filing Form 7004",
        ],
    }


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------


def get_form3520a_overview() -> dict:
    """Return static overview of Form 3520-A requirements."""
    return {
        "form": "3520-A",
        "title": "Annual Information Return of Foreign Trust With a U.S. Owner",
        "purpose": "Report information about a foreign trust that has a U.S. owner under the grantor trust rules",
        "who_must_file": [
            "Foreign trust with at least one U.S. owner (grantor)",
            "U.S. agent of foreign trust (if appointed)",
            "U.S. owner if trust fails to file",
        ],
        "filing_deadline": "15th day of 3rd month after tax year end (March 15 for calendar year trusts)",
        "extension_available": "6-month automatic extension via Form 7004",
        "trust_types": {
            "FOREIGN_GRANTOR": {
                "name": "Foreign Grantor Trust",
                "description": "Foreign trust treated as owned by U.S. person under IRC §§671-679",
                "tax_treatment": "Income taxed to U.S. grantor/owner",
                "reporting": "Must file Form 3520-A; owner reports income on Form 1040",
            },
            "NON_GRANTOR": {
                "name": "Foreign Non-Grantor Trust",
                "description": "Foreign trust not treated as owned by U.S. person",
                "tax_treatment": "Distributions taxed to U.S. beneficiaries",
                "reporting": "Trust files Form 3520-A if it has U.S. beneficiaries who receive distributions",
            },
        },
        "penalties": {
            "initial_failure": {
                "rate": "5%",
                "base": "Gross value of trust assets",
                "statute": "IRC §6677(a)",
            },
            "continuing_failure": {
                "rate": "5% per 30-day period after initial 90 days",
                "max_rate": "25%",
                "base": "Gross value of trust assets",
                "statute": "IRC §6677(b)",
            },
        },
        "related_forms": [
            "Form 3520: Annual Return To Report Transactions With Foreign Trusts",
            "Form 1040: U.S. Individual Income Tax Return (for owner to report trust income)",
            "Form 1116: Foreign Tax Credit (for crediting foreign taxes paid by trust)",
            "Form 7004: Application for Automatic Extension of Time To File",
        ],
        "key_references": [
            "IRC §6048(b): Information with respect to foreign trusts",
            "IRC §679: Foreign trusts having one or more U.S. beneficiaries",
            "IRC §§671-678: Grantor trust rules",
            "IRC §6677: Failure to file information returns",
        ],
    }
