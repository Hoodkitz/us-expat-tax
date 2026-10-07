"""
Form 8915 — Qualified Disaster Retirement Plan Distributions and Repayments.

Business logic for determining eligibility for qualified disaster distributions,
penalty waivers, and repayment schedules under IRC §72(t)(2)(G) and §1400Q.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class FilingRequirementInput:
    """Input for filing requirement check."""
    disaster_area: str
    distribution_date: str  # ISO format YYYY-MM-DD
    home_destroyed: bool
    economic_loss_amt: Decimal


@dataclass
class FilingRequirementResult:
    """Result of filing requirement check."""
    eligible: bool
    disaster_type: str
    distribution_within_window: bool
    economic_loss_threshold_met: bool
    max_distribution_limit: Decimal
    explanation: str


@dataclass
class RepaymentScheduleInput:
    """Input for repayment schedule calculation."""
    distribution_amt: Decimal
    repayment_years: int


@dataclass
class RepaymentScheduleResult:
    """Result of repayment schedule calculation."""
    total_distribution: Decimal
    annual_repayment: Decimal
    repayment_schedule: list[dict]
    tax_spread_per_year: Decimal
    explanation: str


@dataclass
class PenaltyWaiverInput:
    """Input for penalty waiver check."""
    age: int
    distribution_amt: Decimal


@dataclass
class PenaltyWaiverResult:
    """Result of penalty waiver check."""
    waiver_eligible: bool
    standard_penalty_rate: Decimal
    waived_penalty_amount: Decimal
    explanation: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Qualified disaster types (simplified list)
QUALIFIED_DISASTER_TYPES = {
    "hurricane": "Hurricane",
    "wildfire": "Wildfire",
    "flood": "Flood",
    "tornado": "Tornado",
    "earthquake": "Earthquake",
    "pandemic": "Pandemic (COVID-19)",
}

# Maximum distribution limit for qualified disasters
MAX_DISTRIBUTION_LIMIT = Decimal("100000")

# Early withdrawal penalty rate (under age 59½)
EARLY_WITHDRAWAL_PENALTY_RATE = Decimal("0.10")

# Standard repayment period
STANDARD_REPAYMENT_YEARS = 3

# Tax spread denominator (1/3 per year over 3 years)
TAX_SPREAD_DENOMINATOR = Decimal("3")

# Economic loss threshold (simplified)
ECONOMIC_LOSS_THRESHOLD = Decimal("1000")


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------

def check_filing_requirement(inp: FilingRequirementInput) -> FilingRequirementResult:
    """
    Determine if a taxpayer is eligible for qualified disaster distribution treatment
    under IRC §72(t)(2)(G) and §1400Q.

    Requirements:
    1. Distribution from a qualified retirement plan
    2. Disaster declared by federal government
    3. Principal residence or economic loss in disaster area
    4. Distribution within qualified disaster period (typically incident date + 180 days)
    5. Total distributions ≤ $100,000
    """
    # Normalize disaster area to disaster type
    disaster_type = _normalize_disaster_area(inp.disaster_area)
    
    # Check if disaster type is qualified
    qualified_disaster = disaster_type in QUALIFIED_DISASTER_TYPES
    
    # Parse distribution date
    try:
        dist_date = datetime.fromisoformat(inp.distribution_date).date()
    except ValueError:
        return FilingRequirementResult(
            eligible=False,
            disaster_type="Unknown",
            distribution_within_window=False,
            economic_loss_threshold_met=False,
            max_distribution_limit=MAX_DISTRIBUTION_LIMIT,
            explanation="Invalid distribution date format. Use YYYY-MM-DD.",
        )
    
    # Check if distribution is within qualified disaster period
    # Simplified: check if distribution is within reasonable disaster response window
    # In production, would check against IRS-published disaster dates
    current_year = datetime.now().year
    distribution_year = dist_date.year
    # Allow distributions from current year and prior 2 years
    distribution_within_window = (current_year - distribution_year) <= 2
    
    # Check economic loss threshold
    economic_loss_met = (
        inp.home_destroyed or 
        inp.economic_loss_amt >= ECONOMIC_LOSS_THRESHOLD
    )
    
    # Determine eligibility
    eligible = (
        qualified_disaster and
        distribution_within_window and
        economic_loss_met
    )
    
    # Generate explanation
    explanation = _generate_filing_explanation(
        eligible=eligible,
        disaster_type=disaster_type,
        qualified_disaster=qualified_disaster,
        distribution_within_window=distribution_within_window,
        economic_loss_met=economic_loss_met,
        home_destroyed=inp.home_destroyed,
        economic_loss_amt=inp.economic_loss_amt,
    )
    
    return FilingRequirementResult(
        eligible=eligible,
        disaster_type=QUALIFIED_DISASTER_TYPES.get(disaster_type, "Unknown"),
        distribution_within_window=distribution_within_window,
        economic_loss_threshold_met=economic_loss_met,
        max_distribution_limit=MAX_DISTRIBUTION_LIMIT,
        explanation=explanation,
    )


def calculate_repayment_schedule(inp: RepaymentScheduleInput) -> RepaymentScheduleResult:
    """
    Calculate the repayment schedule for a qualified disaster distribution.

    Under IRC §1400Q:
    - Taxpayer has 3 years to repay the distribution
    - If NOT repaid, income is spread equally over 3 years (1/3 per year)
    - No 10% early withdrawal penalty applies
    """
    # Validate repayment years
    if inp.repayment_years < 1 or inp.repayment_years > STANDARD_REPAYMENT_YEARS:
        repayment_years = STANDARD_REPAYMENT_YEARS
    else:
        repayment_years = inp.repayment_years
    
    # Calculate annual repayment
    annual_repayment = inp.distribution_amt / repayment_years
    
    # Calculate tax spread per year if NOT repaid
    tax_spread_per_year = inp.distribution_amt / TAX_SPREAD_DENOMINATOR
    
    # Generate repayment schedule
    schedule = []
    current_year = datetime.now().year
    
    for i in range(repayment_years):
        year = current_year + i
        schedule.append({
            "year": year,
            "repayment_due": str(annual_repayment.quantize(Decimal("0.01"))),
            "tax_if_not_repaid": str(tax_spread_per_year.quantize(Decimal("0.01"))),
        })
    
    explanation = (
        f"You may repay up to ${inp.distribution_amt:,.2f} over {repayment_years} years. "
        f"Annual repayment: ${annual_repayment:,.2f}. "
        f"If NOT repaid, income is spread over 3 years at ${tax_spread_per_year:,.2f} per year. "
        f"No 10% early withdrawal penalty applies to qualified disaster distributions."
    )
    
    return RepaymentScheduleResult(
        total_distribution=inp.distribution_amt,
        annual_repayment=annual_repayment,
        repayment_schedule=schedule,
        tax_spread_per_year=tax_spread_per_year,
        explanation=explanation,
    )


def check_penalty_waiver(inp: PenaltyWaiverInput) -> PenaltyWaiverResult:
    """
    Determine if the 10% early withdrawal penalty is waived for a qualified disaster distribution.

    Under IRC §72(t)(2)(G):
    - The 10% early withdrawal penalty does NOT apply to qualified disaster distributions
    - Applies regardless of taxpayer age
    - Waiver is automatic for distributions meeting Form 8915 requirements
    """
    # Standard penalty calculation (for comparison)
    standard_penalty = inp.distribution_amt * EARLY_WITHDRAWAL_PENALTY_RATE
    
    # For qualified disaster distributions, penalty is waived
    waiver_eligible = True
    waived_penalty = standard_penalty
    
    explanation = (
        f"The 10% early withdrawal penalty is WAIVED for qualified disaster distributions "
        f"under IRC §72(t)(2)(G). "
        f"Standard penalty would have been ${standard_penalty:,.2f}. "
        f"Age: {inp.age} (waiver applies regardless of age). "
        f"You save ${waived_penalty:,.2f} in penalties."
    )
    
    return PenaltyWaiverResult(
        waiver_eligible=waiver_eligible,
        standard_penalty_rate=EARLY_WITHDRAWAL_PENALTY_RATE,
        waived_penalty_amount=waived_penalty,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _normalize_disaster_area(disaster_area: str) -> str:
    """Normalize disaster area string to disaster type."""
    area_lower = disaster_area.lower()
    
    for disaster_type in QUALIFIED_DISASTER_TYPES.keys():
        if disaster_type in area_lower:
            return disaster_type
    
    # Default fallback
    return "unknown"


def _generate_filing_explanation(
    eligible: bool,
    disaster_type: str,
    qualified_disaster: bool,
    distribution_within_window: bool,
    economic_loss_met: bool,
    home_destroyed: bool,
    economic_loss_amt: Decimal,
) -> str:
    """Generate a human-readable explanation of filing requirement determination."""
    if eligible:
        loss_reason = "home destroyed" if home_destroyed else f"economic loss of ${economic_loss_amt:,.2f}"
        disaster_name = QUALIFIED_DISASTER_TYPES.get(disaster_type, "Unknown")
        
        return (
            f"You are ELIGIBLE for qualified disaster distribution treatment under Form 8915. "
            f"Disaster type: {disaster_name}. "
            f"Reason: {loss_reason}. "
            f"Distribution within qualified disaster period: Yes. "
            f"Maximum distribution limit: ${MAX_DISTRIBUTION_LIMIT:,.2f}. "
            f"You may avoid the 10% early withdrawal penalty and spread income over 3 years."
        )
    else:
        reasons = []
        
        if not qualified_disaster:
            disaster_name = QUALIFIED_DISASTER_TYPES.get(disaster_type, disaster_type)
            reasons.append(f"'{disaster_name}' is not a federally-declared qualified disaster")
        
        if not distribution_within_window:
            reasons.append("distribution not within qualified disaster period")
        
        if not economic_loss_met:
            reasons.append(f"economic loss (${economic_loss_amt:,.2f}) below threshold or no home destruction")
        
        reasons_str = "; ".join(reasons)
        
        return (
            f"You are NOT ELIGIBLE for qualified disaster distribution treatment. "
            f"Reason(s): {reasons_str}. "
            f"Standard early withdrawal penalties and immediate tax recognition apply."
        )
