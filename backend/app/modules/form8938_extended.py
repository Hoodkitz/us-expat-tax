"""
Form 8938 FATCA Extended Features.

This module extends Form 8938 with:
1. Foreign trust reporting (IRC §§671-679)
2. Joint filing thresholds for US residents abroad ($400k/$600k)
3. Enhanced penalty scenarios with accuracy-related penalties
4. Statute of limitations extension (6 years vs 3 years)
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants - Joint Filing Thresholds (Living Abroad)
# ---------------------------------------------------------------------------

# Married Filing Jointly — Living Abroad
# Higher thresholds apply to taxpayers living outside the US
THRESHOLD_MFJ_ABROAD_YEAR_END = 400_000.0
THRESHOLD_MFJ_ABROAD_ANY_TIME = 600_000.0

# Single — Living Abroad
THRESHOLD_SINGLE_ABROAD_YEAR_END = 200_000.0
THRESHOLD_SINGLE_ABROAD_ANY_TIME = 300_000.0

# Domestic thresholds (from original module)
THRESHOLD_SINGLE_DOMESTIC_YEAR_END = 50_000.0
THRESHOLD_SINGLE_DOMESTIC_ANY_TIME = 75_000.0
THRESHOLD_MFJ_DOMESTIC_YEAR_END = 100_000.0
THRESHOLD_MFJ_DOMESTIC_ANY_TIME = 150_000.0

# ---------------------------------------------------------------------------
# Constants - Penalties
# ---------------------------------------------------------------------------

# Accuracy-related penalty for undisclosed foreign financial assets
PENALTY_ACCURACY_RELATED = 0.40  # 40% of underpayment attributable to undisclosed assets

# Statute of limitations
STATUTE_NORMAL_YEARS = 3
STATUTE_FOREIGN_ASSET_UNREPORTED_YEARS = 6

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

TrustTypeLiteral = Literal["grantor", "beneficiary", "other"]
ResidencyStatusLiteral = Literal["domestic", "abroad"]

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class ForeignTrustInput(BaseModel):
    """Foreign trust reporting (IRC §§671-679)."""
    trust_name: str = Field(..., min_length=1, description="Name of the foreign trust")
    trust_type: TrustTypeLiteral = Field(..., description="Type: grantor, beneficiary, or other")
    country: str = Field(..., min_length=2, description="Country where trust is established")
    fair_market_value_usd: float = Field(..., ge=0, description="Fair market value in USD")
    distributions_received_usd: float = Field(0.0, ge=0, description="Distributions received during tax year")
    is_grantor: bool = Field(False, description="Whether taxpayer is treated as grantor under IRC §671-679")
    
class JointFilingThresholdInput(BaseModel):
    """Input for joint filing threshold check."""
    filing_status: Literal["single", "mfj", "mfs", "hoh"] = Field(..., description="Filing status")
    residency_status: ResidencyStatusLiteral = Field(..., description="Domestic or abroad")
    year_end_value_usd: float = Field(..., ge=0, description="Total foreign asset value at year-end")
    max_any_time_value_usd: float = Field(..., ge=0, description="Maximum value at any time during year")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")

class AccuracyPenaltyInput(BaseModel):
    """Input for accuracy-related penalty calculation."""
    underpayment_amount_usd: float = Field(..., ge=0, description="Tax underpayment amount")
    total_foreign_assets_usd: float = Field(..., ge=0, description="Total undisclosed foreign assets")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")

class StatuteOfLimitationsInput(BaseModel):
    """Input for statute of limitations determination."""
    foreign_assets_disclosed: bool = Field(..., description="Whether foreign assets were properly disclosed")
    foreign_asset_value_usd: float = Field(0.0, ge=0, description="Total foreign asset value")
    gross_income_usd: float = Field(..., ge=0, description="Gross income for the tax year")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")

# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class ForeignTrustResult(BaseModel):
    """Result of foreign trust reporting check."""
    reporting_required: bool
    trust_type: str
    fair_market_value_usd: float
    is_grantor_trust: bool
    required_forms: list[str]
    explanation: str
    penalties_if_not_reported: str

class JointFilingThresholdResult(BaseModel):
    """Result of joint filing threshold check."""
    filing_required: bool
    applicable_threshold_year_end: float
    applicable_threshold_any_time: float
    year_end_value_usd: float
    max_any_time_value_usd: float
    residency_status: str
    filing_status: str
    reasons: list[str]
    recommendation: str

class AccuracyPenaltyResult(BaseModel):
    """Result of accuracy-related penalty calculation."""
    penalty_rate: float
    underpayment_amount: float
    penalty_amount: float
    total_foreign_assets: float
    explanation: str

class StatuteOfLimitationsResult(BaseModel):
    """Result of statute of limitations determination."""
    statute_years: int
    foreign_assets_disclosed: bool
    assessment_deadline_year: int
    is_extended: bool
    explanation: str
    recommendation: str

# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def check_foreign_trust_reporting(inp: ForeignTrustInput) -> ForeignTrustResult:
    """
    Determine foreign trust reporting requirements under IRC §§671-679.
    
    US persons with interests in foreign trusts must report:
    - Form 3520: Transactions with foreign trusts
    - Form 3520-A: Annual Information Return of Foreign Trust (if grantor)
    - Form 8938: If value exceeds thresholds
    """
    required_forms = ["Form 8938"]
    
    # Grantor trusts require additional reporting
    if inp.is_grantor or inp.trust_type == "grantor":
        required_forms.extend(["Form 3520", "Form 3520-A"])
        explanation = (
            f"As a grantor trust under IRC §§671-679, you are treated as the owner of the trust "
            f"for US tax purposes. You must report all trust income on your personal return and file "
            f"Forms 3520 and 3520-A in addition to Form 8938."
        )
        penalties = (
            "Failure to file Form 3520: Greater of $10,000 or 35% of gross reportable amount. "
            "Failure to file Form 3520-A: $10,000 plus $10,000 for each 30-day period after IRS notice."
        )
    elif inp.trust_type == "beneficiary":
        required_forms.append("Form 3520")
        explanation = (
            f"As a beneficiary of a foreign trust, you must report distributions received "
            f"(${inp.distributions_received_usd:,.2f}) on Form 3520. The trust itself is not "
            f"taxed to you unless you are also treated as a grantor."
        )
        penalties = (
            "Failure to file Form 3520: Greater of $10,000 or 35% of gross reportable amount."
        )
    else:
        explanation = (
            f"You have an interest in a foreign trust valued at ${inp.fair_market_value_usd:,.2f}. "
            f"Report this on Form 8938 if the total foreign asset value exceeds applicable thresholds."
        )
        penalties = (
            "Failure to file Form 8938: $10,000 initial penalty, up to $50,000 for continued failure. "
            "Willful failure: greater of $100,000 or 50% of asset value."
        )
    
    return ForeignTrustResult(
        reporting_required=True,
        trust_type=inp.trust_type,
        fair_market_value_usd=inp.fair_market_value_usd,
        is_grantor_trust=(inp.is_grantor or inp.trust_type == "grantor"),
        required_forms=required_forms,
        explanation=explanation,
        penalties_if_not_reported=penalties,
    )

def check_joint_filing_threshold(inp: JointFilingThresholdInput) -> JointFilingThresholdResult:
    """
    Check filing requirement with proper joint filing thresholds.
    
    Thresholds differ based on residency:
    - Domestic (living in US):
      - Single/MFS/HOH: $50k year-end / $75k any time
      - MFJ: $100k year-end / $150k any time
    
    - Abroad (living outside US):
      - Single/MFS/HOH: $200k year-end / $300k any time
      - MFJ: $400k year-end / $600k any time
    """
    # Determine applicable thresholds
    if inp.residency_status == "abroad":
        if inp.filing_status == "mfj":
            threshold_year_end = THRESHOLD_MFJ_ABROAD_YEAR_END
            threshold_any_time = THRESHOLD_MFJ_ABROAD_ANY_TIME
        else:
            threshold_year_end = THRESHOLD_SINGLE_ABROAD_YEAR_END
            threshold_any_time = THRESHOLD_SINGLE_ABROAD_ANY_TIME
    else:  # domestic
        if inp.filing_status == "mfj":
            threshold_year_end = THRESHOLD_MFJ_DOMESTIC_YEAR_END
            threshold_any_time = THRESHOLD_MFJ_DOMESTIC_ANY_TIME
        else:
            threshold_year_end = THRESHOLD_SINGLE_DOMESTIC_YEAR_END
            threshold_any_time = THRESHOLD_SINGLE_DOMESTIC_ANY_TIME
    
    reasons = []
    filing_required = False
    
    # Check year-end threshold
    if inp.year_end_value_usd > threshold_year_end:
        filing_required = True
        reasons.append(
            f"Year-end value (${inp.year_end_value_usd:,.2f}) exceeds threshold "
            f"(${threshold_year_end:,.2f}) for {inp.filing_status.upper()} "
            f"living {inp.residency_status}"
        )
    
    # Check any-time threshold
    if inp.max_any_time_value_usd > threshold_any_time:
        filing_required = True
        reasons.append(
            f"Maximum value (${inp.max_any_time_value_usd:,.2f}) exceeds any-time threshold "
            f"(${threshold_any_time:,.2f}) for {inp.filing_status.upper()} "
            f"living {inp.residency_status}"
        )
    
    if not filing_required:
        reasons.append(
            f"Foreign asset values below both thresholds for {inp.filing_status.upper()} "
            f"living {inp.residency_status}"
        )
        recommendation = (
            f"Form 8938 is NOT required. Your foreign assets are below the applicable thresholds. "
            f"Year-end threshold: ${threshold_year_end:,.0f}, Any-time threshold: ${threshold_any_time:,.0f}."
        )
    else:
        recommendation = (
            f"Form 8938 is REQUIRED. Your foreign assets exceed the applicable thresholds "
            f"for {inp.filing_status.upper()} taxpayers living {inp.residency_status}. "
            f"Failure to file can result in penalties of $10,000 to $50,000."
        )
    
    return JointFilingThresholdResult(
        filing_required=filing_required,
        applicable_threshold_year_end=threshold_year_end,
        applicable_threshold_any_time=threshold_any_time,
        year_end_value_usd=inp.year_end_value_usd,
        max_any_time_value_usd=inp.max_any_time_value_usd,
        residency_status=inp.residency_status,
        filing_status=inp.filing_status,
        reasons=reasons,
        recommendation=recommendation,
    )

def calculate_accuracy_penalty(inp: AccuracyPenaltyInput) -> AccuracyPenaltyResult:
    """
    Calculate 40% accuracy-related penalty for undisclosed foreign assets.
    
    IRC §6662(j): 40% penalty on underpayment attributable to undisclosed
    foreign financial assets. This is in addition to other Form 8938 penalties.
    """
    penalty_amount = inp.underpayment_amount_usd * PENALTY_ACCURACY_RELATED
    
    explanation = (
        f"Under IRC §6662(j), a 40% accuracy-related penalty applies to the portion of "
        f"any underpayment attributable to undisclosed foreign financial assets. "
        f"Underpayment: ${inp.underpayment_amount_usd:,.2f}. "
        f"Penalty: ${penalty_amount:,.2f} ({PENALTY_ACCURACY_RELATED * 100:.0f}%). "
        f"This penalty is IN ADDITION to Form 8938 filing penalties and may not be "
        f"reduced or waived for reasonable cause."
    )
    
    return AccuracyPenaltyResult(
        penalty_rate=PENALTY_ACCURACY_RELATED,
        underpayment_amount=inp.underpayment_amount_usd,
        penalty_amount=penalty_amount,
        total_foreign_assets=inp.total_foreign_assets_usd,
        explanation=explanation,
    )

def check_statute_of_limitations(inp: StatuteOfLimitationsInput) -> StatuteOfLimitationsResult:
    """
    Determine statute of limitations for IRS assessment.
    
    Normal: 3 years from filing date
    Extended: 6 years if foreign assets omitted and exceed certain thresholds
    
    IRC §6501(e)(1)(A): 6-year statute applies when gross income omissions
    exceed 25% of reported gross income AND involve foreign assets.
    """
    # Calculate 25% threshold
    omission_threshold = inp.gross_income_usd * 0.25
    
    if not inp.foreign_assets_disclosed and inp.foreign_asset_value_usd > omission_threshold:
        statute_years = STATUTE_FOREIGN_ASSET_UNREPORTED_YEARS
        is_extended = True
        assessment_deadline = inp.tax_year + statute_years + 1  # +1 for typical filing year
        
        explanation = (
            f"The statute of limitations is EXTENDED to {statute_years} years because "
            f"undisclosed foreign assets (${inp.foreign_asset_value_usd:,.2f}) exceed "
            f"25% of gross income (${omission_threshold:,.2f}). "
            f"The IRS may assess additional tax until approximately {assessment_deadline}."
        )
        
        recommendation = (
            "Consider filing a delinquent or amended return through the IRS Streamlined Filing "
            "Compliance Procedures or Delinquent FBAR Submission Procedures to mitigate penalties "
            "and start the statute of limitations running."
        )
    else:
        statute_years = STATUTE_NORMAL_YEARS
        is_extended = False
        assessment_deadline = inp.tax_year + statute_years + 1
        
        explanation = (
            f"The normal {statute_years}-year statute of limitations applies. "
            f"Foreign assets were properly disclosed or do not trigger the extended statute. "
            f"The IRS assessment period generally ends around {assessment_deadline}."
        )
        
        recommendation = (
            "The standard 3-year statute of limitations applies. Maintain records for at least "
            "3 years from the filing date, or 6 years for substantial omissions."
        )
    
    return StatuteOfLimitationsResult(
        statute_years=statute_years,
        foreign_assets_disclosed=inp.foreign_assets_disclosed,
        assessment_deadline_year=assessment_deadline,
        is_extended=is_extended,
        explanation=explanation,
        recommendation=recommendation,
    )
