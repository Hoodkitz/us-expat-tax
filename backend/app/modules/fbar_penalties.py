"""
Enhanced FBAR Penalties Calculator.

Covers non-willful, willful, and fraud violations with inflation
adjustment, Streamlined Procedure discounts, and criminal risk flags.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Penalty constants (2024 inflation-adjusted)
# ---------------------------------------------------------------------------

# Non-willful: up to $10,000 per account per year (CPI-adjusted ≈ $14,489 for 2024)
NON_WILLFUL_BASE = 10_000.0
NON_WILLFUL_ADJUSTED_2024 = 14_489.0  # 31 CFR 1010.821 – FinCEN 2024 update

# Willful: greater of $100,000 or 50% of max account balance, per year
WILLFUL_BASE_MIN = 100_000.0
WILLFUL_PCT_OF_BALANCE = 0.50

# Fraud / criminal: up to $250,000 fine + up to 5 years imprisonment (31 U.S.C. § 5322(b))
FRAUD_MAX_FINE = 250_000.0
FRAUD_IMPRISONMENT_YEARS = 5

# Streamlined Foreign Offshore Procedures: 5% of highest aggregate balance
STREAMLINED_PENALTY_PCT = 0.05

# FBAR filing thresholds (2024)
FBAR_FILING_THRESHOLD = 10_000.0
FBAR_DUE_DATE = "April 15 (automatic extension to October 15)"

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class FBARPenaltyRequest(BaseModel):
    violation_type: Literal["non_willful", "willful", "fraud"]
    years_of_violation: int
    max_account_balance: float
    filed_late: bool
    voluntary_disclosure: bool


class PenaltyBreakdownItem(BaseModel):
    description: str
    amount: float


class FBARPenaltyResult(BaseModel):
    min_penalty: float
    max_penalty: float
    criminal_risk: bool
    streamlined_eligible: bool
    penalty_breakdown: list[PenaltyBreakdownItem]
    recommendation: str


# ---------------------------------------------------------------------------
# FBAR filing thresholds data (for GET endpoint)
# ---------------------------------------------------------------------------

FBAR_THRESHOLDS_INFO: dict = {
    "filing_required_if_balance_exceeds_usd": FBAR_FILING_THRESHOLD,
    "aggregation_rule": (
        "All foreign financial accounts are aggregated. If the combined maximum "
        "balance at any point during the year exceeds $10,000, ALL accounts must be reported."
    ),
    "due_date": FBAR_DUE_DATE,
    "form": "FinCEN Form 114",
    "filing_system": "BSA E-Filing System (bsaefiling.fincen.treas.gov)",
    "who_must_file": (
        "US persons (citizens, residents, entities) with a financial interest in or "
        "signature authority over foreign financial accounts."
    ),
    "penalty_tiers": {
        "non_willful_max_per_year_2024": NON_WILLFUL_ADJUSTED_2024,
        "willful_min_per_year": WILLFUL_BASE_MIN,
        "willful_pct_of_balance": f"{int(WILLFUL_PCT_OF_BALANCE * 100)}%",
        "fraud_criminal_fine_max": FRAUD_MAX_FINE,
        "fraud_imprisonment_max_years": FRAUD_IMPRISONMENT_YEARS,
    },
    "streamlined_procedure": {
        "penalty_rate": f"{int(STREAMLINED_PENALTY_PCT * 100)}%",
        "basis": "Highest aggregate balance over the 6-year lookback period",
        "eligibility": "Non-willful violations; taxpayer must not be under IRS examination",
    },
}

# ---------------------------------------------------------------------------
# Core penalty logic
# ---------------------------------------------------------------------------


def calculate_fbar_penalties(req: FBARPenaltyRequest) -> FBARPenaltyResult:
    """
    Calculate FBAR penalties based on violation type, years, and account balance.
    """
    years = max(1, req.years_of_violation)
    balance = max(0.0, req.max_account_balance)
    breakdown: list[PenaltyBreakdownItem] = []
    criminal_risk = False
    streamlined_eligible = False
    min_penalty = 0.0
    max_penalty = 0.0

    if req.violation_type == "non_willful":
        # Non-willful: IRS typically assesses $0–$14,489 per year (per account).
        # We treat each year as one account occurrence (single account assumed for simplicity).
        per_year_max = NON_WILLFUL_ADJUSTED_2024
        max_penalty = per_year_max * years
        min_penalty = 0.0  # IRS has discretion; could be $0 with explanation

        breakdown.append(PenaltyBreakdownItem(
            description=f"Non-willful penalty: up to ${per_year_max:,.2f}/year × {years} year(s)",
            amount=max_penalty,
        ))

        # Streamlined eligible if voluntary disclosure and not under examination
        if req.voluntary_disclosure:
            streamlined_amount = balance * STREAMLINED_PENALTY_PCT
            streamlined_eligible = True
            breakdown.append(PenaltyBreakdownItem(
                description=(
                    f"Streamlined Foreign Offshore Procedure: "
                    f"{int(STREAMLINED_PENALTY_PCT*100)}% × ${balance:,.2f} balance"
                ),
                amount=streamlined_amount,
            ))
            # Streamlined is usually better than the full non-willful penalty
            min_penalty = min(streamlined_amount, max_penalty)

        criminal_risk = False
        recommendation = _non_willful_recommendation(req, streamlined_eligible)

    elif req.violation_type == "willful":
        # Willful: greater of $100,000 or 50% of max balance, per year
        per_year = max(WILLFUL_BASE_MIN, balance * WILLFUL_PCT_OF_BALANCE)
        max_penalty = per_year * years
        min_penalty = WILLFUL_BASE_MIN * years  # floor: $100k/year even with low balance

        breakdown.append(PenaltyBreakdownItem(
            description=(
                f"Willful penalty: max(${WILLFUL_BASE_MIN:,.0f}, "
                f"50% × ${balance:,.2f}) = ${per_year:,.2f}/year × {years} year(s)"
            ),
            amount=max_penalty,
        ))

        if balance >= 1_000_000:
            breakdown.append(PenaltyBreakdownItem(
                description="High-balance surcharge risk: IRS may seek 100% forfeiture",
                amount=balance,
            ))
            criminal_risk = True

        # Streamlined NOT available for willful violations
        streamlined_eligible = False

        if req.voluntary_disclosure:
            # OVDP/SDOP mitigation – rough estimate: ~25% reduction via disclosure program
            disclosure_reduction = max_penalty * 0.25
            breakdown.append(PenaltyBreakdownItem(
                description="Voluntary Disclosure Program estimated reduction (~25%)",
                amount=-disclosure_reduction,
            ))
            min_penalty = max_penalty - disclosure_reduction

        criminal_risk = criminal_risk or (years >= 3 and balance >= 500_000)
        recommendation = _willful_recommendation(req, max_penalty, criminal_risk)

    else:  # fraud
        # Criminal fraud: up to $250,000 fine + 5 years imprisonment per count
        # Civil fraud penalty is separate: up to 75% of underpayment
        # Here we model the criminal exposure
        max_penalty = FRAUD_MAX_FINE * years
        min_penalty = WILLFUL_BASE_MIN * years  # at minimum treated as willful

        breakdown.append(PenaltyBreakdownItem(
            description=(
                f"Fraud – criminal fine: up to ${FRAUD_MAX_FINE:,.0f}/count × {years} year(s)"
            ),
            amount=max_penalty,
        ))
        breakdown.append(PenaltyBreakdownItem(
            description=(
                f"Imprisonment risk: up to {FRAUD_IMPRISONMENT_YEARS} years per count"
            ),
            amount=0.0,  # not a monetary amount; informational
        ))
        civil_fraud = balance * 0.75
        breakdown.append(PenaltyBreakdownItem(
            description=f"Civil fraud penalty (75% of balance): ${civil_fraud:,.2f}",
            amount=civil_fraud,
        ))

        criminal_risk = True
        streamlined_eligible = False
        recommendation = _fraud_recommendation(req)

    return FBARPenaltyResult(
        min_penalty=round(min_penalty, 2),
        max_penalty=round(max_penalty, 2),
        criminal_risk=criminal_risk,
        streamlined_eligible=streamlined_eligible,
        penalty_breakdown=breakdown,
        recommendation=recommendation,
    )


# ---------------------------------------------------------------------------
# Recommendation text helpers
# ---------------------------------------------------------------------------


def _non_willful_recommendation(req: FBARPenaltyRequest, streamlined: bool) -> str:
    parts = [
        "Non-willful FBAR violations carry penalties up to $14,489 per year (2024). "
    ]
    if streamlined:
        parts.append(
            "Because you indicated voluntary disclosure, you may qualify for the "
            "Streamlined Foreign Offshore Procedures (5% penalty on highest aggregate balance), "
            "which is often significantly less than the standard penalty. "
            "Act promptly—streamlined is unavailable once an IRS examination begins. "
        )
    else:
        parts.append(
            "Consider filing amended FBARs with an explanation. "
            "The IRS has discretion to assess $0 for first-time non-willful violations "
            "(see Bittner v. United States, 2023 Supreme Court ruling). "
        )
    parts.append("Consult a tax attorney specializing in international compliance before filing.")
    return " ".join(parts)


def _willful_recommendation(
    req: FBARPenaltyRequest, max_penalty: float, criminal_risk: bool
) -> str:
    parts = [
        f"Willful violations expose you to penalties of ${max_penalty:,.2f}. "
    ]
    if criminal_risk:
        parts.append(
            "⚠️ The combination of high balance and multiple years creates CRIMINAL PROSECUTION RISK. "
            "Retain a tax attorney immediately before any contact with the IRS. "
        )
    if req.voluntary_disclosure:
        parts.append(
            "Voluntary disclosure through the IRS OVDP or modified streamlined programs may "
            "reduce penalties but willful violations cannot use the Streamlined procedure. "
        )
    else:
        parts.append(
            "Voluntary disclosure now—before the IRS contacts you—may significantly reduce exposure. "
        )
    parts.append("This situation requires specialized legal counsel.")
    return " ".join(parts)


def _fraud_recommendation(req: FBARPenaltyRequest) -> str:
    return (
        "⚠️ FRAUD-LEVEL VIOLATIONS: This carries both civil and criminal exposure, "
        f"including fines up to ${FRAUD_MAX_FINE:,.0f} per count and up to "
        f"{FRAUD_IMPRISONMENT_YEARS} years imprisonment per count under 31 U.S.C. § 5322(b). "
        "DO NOT contact the IRS without legal representation. "
        "Retain a tax attorney with criminal defense experience immediately. "
        "Voluntary disclosure prior to IRS contact may still be possible and could "
        "substantially reduce criminal exposure."
    )
