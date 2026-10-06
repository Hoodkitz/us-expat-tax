"""
Form 8621 PFIC (Passive Foreign Investment Company) module.

Implements three tax regimes for PFIC holdings per IRC:
1. Default regime (§1291): Excess distribution method with deferred tax + interest charge
2. QEF election (§1293): Qualified Electing Fund - report pro-rata ordinary earnings + capital gains
3. MTM election (§1296): Mark-to-Market - recognize annual FMV changes as ordinary income

Filing requirement: Any US person with direct/indirect PFIC interest, or sale/distribution/excess distribution.
Penalties: $10,000 per year for failure to file, plus potential criminal penalties.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# IRS interest rate for excess distributions (§6621(a)(2))
# Using approximate rate for calculation purposes
IRS_UNDERPAYMENT_RATE = 0.07  # 7% (simplified; actual rate varies quarterly)

# PFIC filing thresholds
PFIC_OWNERSHIP_THRESHOLD = 0.0  # Any ownership triggers filing requirement

# Penalty amounts
PENALTY_FAILURE_TO_FILE = 10_000.0  # Per year, per Form 8621

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

RegimeLiteral = Literal["default", "qef", "mtm"]

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class FilingRequirementInput(BaseModel):
    """Input for checking Form 8621 filing requirement."""
    has_pfic_interest: bool = Field(..., description="Do you hold any PFIC interest?")
    had_sale_or_distribution: bool = Field(..., description="Did you sell PFIC shares or receive distribution?")
    received_excess_distribution: bool = Field(..., description="Did you receive excess distribution?")
    
class MTMCalculationInput(BaseModel):
    """Input for Mark-to-Market election calculation (§1296)."""
    beginning_fmv: float = Field(..., ge=0, description="Fair market value at beginning of tax year")
    ending_fmv: float = Field(..., ge=0, description="Fair market value at end of tax year")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")

class QEFCalculationInput(BaseModel):
    """Input for QEF election calculation (§1293)."""
    ordinary_earnings: float = Field(..., ge=0, description="Pro-rata share of ordinary earnings")
    net_capital_gain: float = Field(..., ge=0, description="Pro-rata share of net capital gains")
    ownership_percentage: float = Field(..., ge=0, le=100, description="Percentage ownership of PFIC")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")

class ExcessDistributionInput(BaseModel):
    """Input for excess distribution calculation under default regime (§1291)."""
    total_distribution: float = Field(..., ge=0, description="Total distribution received")
    holding_period_years: int = Field(..., ge=1, description="Number of years holding PFIC shares")
    prior_distributions: list[float] = Field(default_factory=list, description="Distributions from prior 3 years")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")

# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class FilingRequirementResult(BaseModel):
    """Result of filing requirement check."""
    filing_required: bool
    reasons: list[str]
    penalty_if_not_filed: float
    recommendation: str

class MTMCalculationResult(BaseModel):
    """Result of Mark-to-Market calculation."""
    unrealized_gain_or_loss: float
    ordinary_income_or_loss: float
    beginning_fmv: float
    ending_fmv: float
    tax_treatment: str
    explanation: str

class QEFCalculationResult(BaseModel):
    """Result of QEF election calculation."""
    ordinary_earnings_includible: float
    capital_gain_includible: float
    total_inclusion: float
    ownership_percentage: float
    explanation: str

class ExcessDistributionResult(BaseModel):
    """Result of excess distribution calculation under default regime."""
    total_distribution: float
    average_distribution: float
    excess_amount: float
    deferred_tax_amount: float
    interest_charge: float
    total_tax_and_interest: float
    allocation_by_year: list[dict]
    explanation: str

class Form8621Overview(BaseModel):
    """Overview of Form 8621 requirements and regimes."""
    title: str
    filing_requirement: str
    regimes: dict[str, str]
    penalties: str
    recommendation: str

# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def check_filing_requirement(inp: FilingRequirementInput) -> FilingRequirementResult:
    """
    Determine if Form 8621 filing is required.
    
    Filing required if:
    - Taxpayer holds any direct or indirect PFIC interest
    - Taxpayer sold PFIC shares
    - Taxpayer received distribution or excess distribution
    """
    reasons = []
    filing_required = False
    
    if inp.has_pfic_interest:
        filing_required = True
        reasons.append("You hold a direct or indirect interest in a PFIC")
    
    if inp.had_sale_or_distribution:
        filing_required = True
        reasons.append("You sold PFIC shares or received a distribution during the tax year")
    
    if inp.received_excess_distribution:
        filing_required = True
        reasons.append("You received an excess distribution subject to §1291")
    
    if not filing_required:
        return FilingRequirementResult(
            filing_required=False,
            reasons=["No PFIC activity detected"],
            penalty_if_not_filed=0.0,
            recommendation="Form 8621 is not required based on your responses. However, verify with a tax professional if you hold any foreign mutual funds or pooled investments."
        )
    
    return FilingRequirementResult(
        filing_required=True,
        reasons=reasons,
        penalty_if_not_filed=PENALTY_FAILURE_TO_FILE,
        recommendation="Form 8621 is REQUIRED. Failure to file can result in a $10,000 penalty per year, plus potential criminal penalties. Consult a tax professional specializing in PFIC reporting."
    )

def calculate_mtm(inp: MTMCalculationInput) -> MTMCalculationResult:
    """
    Calculate Mark-to-Market election (§1296).
    
    Under MTM election:
    - Taxpayer recognizes unrealized gain/loss annually
    - Gain is treated as ordinary income
    - Loss is treated as ordinary loss (limited to prior MTM gains)
    """
    unrealized_gain_or_loss = inp.ending_fmv - inp.beginning_fmv
    
    if unrealized_gain_or_loss >= 0:
        tax_treatment = "Ordinary Income"
        explanation = (
            f"Under Mark-to-Market election (§1296), the unrealized gain of "
            f"${unrealized_gain_or_loss:,.2f} is recognized as ORDINARY INCOME in tax year {inp.tax_year}. "
            f"This gain is reported on Form 8621 Part II and included in your taxable income. "
            f"No deferral or interest charge applies under MTM election."
        )
    else:
        tax_treatment = "Ordinary Loss"
        explanation = (
            f"Under Mark-to-Market election (§1296), the unrealized loss of "
            f"${abs(unrealized_gain_or_loss):,.2f} is recognized as ORDINARY LOSS in tax year {inp.tax_year}. "
            f"This loss is deductible to the extent of prior MTM gains. Any excess loss carries forward. "
            f"Report on Form 8621 Part II."
        )
    
    return MTMCalculationResult(
        unrealized_gain_or_loss=unrealized_gain_or_loss,
        ordinary_income_or_loss=unrealized_gain_or_loss,
        beginning_fmv=inp.beginning_fmv,
        ending_fmv=inp.ending_fmv,
        tax_treatment=tax_treatment,
        explanation=explanation
    )

def calculate_qef(inp: QEFCalculationInput) -> QEFCalculationResult:
    """
    Calculate QEF (Qualified Electing Fund) election (§1293).
    
    Under QEF election:
    - Taxpayer includes pro-rata share of PFIC's ordinary earnings
    - Taxpayer includes pro-rata share of PFIC's net capital gain
    - No deferral or interest charge
    - PFIC must provide annual information statement
    """
    # QEF income is already pro-rata, but we apply ownership percentage for clarity
    ownership_factor = inp.ownership_percentage / 100.0
    
    ordinary_includible = inp.ordinary_earnings * ownership_factor
    capital_includible = inp.net_capital_gain * ownership_factor
    total_inclusion = ordinary_includible + capital_includible
    
    explanation = (
        f"Under QEF election (§1293), you must include your pro-rata share of the PFIC's earnings "
        f"in tax year {inp.tax_year}, regardless of whether distributions were received. "
        f"Ordinary earnings: ${ordinary_includible:,.2f} (taxed at ordinary rates). "
        f"Net capital gain: ${capital_includible:,.2f} (taxed at capital gains rates). "
        f"Total inclusion: ${total_inclusion:,.2f}. "
        f"Report on Form 8621 Part III. The PFIC must provide an annual PFIC Annual Information Statement."
    )
    
    return QEFCalculationResult(
        ordinary_earnings_includible=ordinary_includible,
        capital_gain_includible=capital_includible,
        total_inclusion=total_inclusion,
        ownership_percentage=inp.ownership_percentage,
        explanation=explanation
    )

def calculate_excess_distribution(inp: ExcessDistributionInput) -> ExcessDistributionResult:
    """
    Calculate excess distribution under default regime (§1291).
    
    Default regime (no election):
    - Distribution exceeding 125% of average of prior 3 years is "excess"
    - Excess amount is allocated pro-rata over holding period
    - Tax on each year's allocation is computed at highest marginal rate
    - Interest charge applies under §1291(c) using IRS underpayment rate
    
    This is a SIMPLIFIED calculation. Actual Form 8621 requires detailed
    allocation to each year of the holding period and application of highest
    marginal tax rates for each year.
    """
    # Calculate average distribution from prior 3 years
    if len(inp.prior_distributions) == 0:
        # If no prior distributions, entire distribution is excess
        average_distribution = 0.0
    else:
        average_distribution = sum(inp.prior_distributions) / len(inp.prior_distributions)
    
    # Excess distribution threshold = 125% of average
    excess_threshold = average_distribution * 1.25
    
    # Calculate excess amount
    if inp.total_distribution > excess_threshold:
        excess_amount = inp.total_distribution - excess_threshold
    else:
        excess_amount = 0.0
    
    # Allocate excess amount pro-rata over holding period
    allocation_per_year = excess_amount / inp.holding_period_years
    
    # Simplified tax calculation (assumes 37% highest marginal rate)
    # In reality, need to apply the highest rate for each year in holding period
    highest_marginal_rate = 0.37
    deferred_tax_amount = excess_amount * highest_marginal_rate
    
    # Interest charge on deferred tax (simplified)
    # Interest is calculated from the due date of each prior year's return to current year
    # Simplified: assume average deferral period = holding_period_years / 2
    average_deferral_years = inp.holding_period_years / 2.0
    interest_charge = deferred_tax_amount * IRS_UNDERPAYMENT_RATE * average_deferral_years
    
    total_tax_and_interest = deferred_tax_amount + interest_charge
    
    # Build allocation breakdown by year
    allocation_by_year = []
    for year_idx in range(inp.holding_period_years):
        year = inp.tax_year - inp.holding_period_years + year_idx + 1
        allocation_by_year.append({
            "year": year,
            "allocated_amount": round(allocation_per_year, 2),
            "tax_on_allocation": round(allocation_per_year * highest_marginal_rate, 2)
        })
    
    if excess_amount == 0:
        explanation = (
            f"Your distribution of ${inp.total_distribution:,.2f} does NOT exceed 125% of the average "
            f"prior distribution (${average_distribution:,.2f}), so NO excess distribution exists. "
            f"The entire distribution is taxed as ordinary income in the current year under normal rules."
        )
    else:
        explanation = (
            f"Your distribution of ${inp.total_distribution:,.2f} exceeds 125% of the average prior distribution "
            f"(${average_distribution:,.2f}), creating an excess distribution of ${excess_amount:,.2f}. "
            f"Under §1291 default regime, this excess is allocated pro-rata over your {inp.holding_period_years}-year "
            f"holding period (${allocation_per_year:,.2f} per year), taxed at the highest marginal rate (37%), "
            f"and subject to an interest charge of ${interest_charge:,.2f} under §1291(c). "
            f"Total tax + interest: ${total_tax_and_interest:,.2f}. "
            f"This punitive treatment is why QEF or MTM elections are strongly recommended."
        )
    
    return ExcessDistributionResult(
        total_distribution=inp.total_distribution,
        average_distribution=average_distribution,
        excess_amount=excess_amount,
        deferred_tax_amount=deferred_tax_amount,
        interest_charge=interest_charge,
        total_tax_and_interest=total_tax_and_interest,
        allocation_by_year=allocation_by_year,
        explanation=explanation
    )

def get_overview() -> Form8621Overview:
    """Return overview of Form 8621 PFIC reporting requirements."""
    return Form8621Overview(
        title="Form 8621: Passive Foreign Investment Company (PFIC) Reporting",
        filing_requirement=(
            "Form 8621 is required for ANY US person (citizen, resident, or domestic entity) who holds "
            "a direct or indirect interest in a PFIC, or who receives a distribution or recognizes a gain "
            "on a disposition of PFIC shares. Common PFICs include foreign mutual funds, ETFs, and certain "
            "foreign corporations with passive income ≥75% or passive assets ≥50%."
        ),
        regimes={
            "default": (
                "Default Regime (§1291): Excess distributions and gains on sale are allocated over the holding period "
                "and taxed at the highest marginal rate for each year, PLUS an interest charge under §1291(c). "
                "This is the most PUNITIVE regime and should be avoided if possible."
            ),
            "qef": (
                "QEF Election (§1293): Qualified Electing Fund election allows you to include your pro-rata share of "
                "the PFIC's ordinary earnings and net capital gain annually (similar to pass-through treatment). "
                "No deferral or interest charge. Requires annual PFIC information statement from the fund."
            ),
            "mtm": (
                "Mark-to-Market Election (§1296): Available for marketable PFIC stock. Recognize unrealized gains/losses "
                "annually as ordinary income/loss. Gains are taxed each year; losses are deductible (limited to prior MTM gains). "
                "No deferral or interest charge. Simpler than QEF but requires marketable stock."
            )
        },
        penalties=(
            "Failure to file Form 8621 can result in a penalty of $10,000 per year per form, extended statute of limitations, "
            "and potential criminal penalties. The IRS has increased PFIC enforcement in recent years."
        ),
        recommendation=(
            "If you hold foreign mutual funds or pooled investments, consult a tax professional specializing in PFIC reporting. "
            "QEF or MTM elections can significantly reduce your tax burden compared to the default regime. "
            "Elections must be made timely and are generally irrevocable without IRS consent."
        )
    )
