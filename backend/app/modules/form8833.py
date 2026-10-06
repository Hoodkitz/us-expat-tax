"""
Form 8833 Treaty-Based Return Position Disclosure.

Required when a U.S. taxpayer takes a position that a tax treaty overrides or modifies 
U.S. tax law, resulting in reduced or eliminated tax liability.

Key requirements per IRC §6114:
- Must be attached to tax return for the year treaty position is taken
- Required for positions under income tax treaties (NOT totalization agreements)
- Penalty: $1,000 per failure to disclose (IRC §6712)
- Exception: Certain pension/benefit positions under totalization agreements exempt

Common treaty positions requiring disclosure:
1. Treaty residence (different from citizenship/green card status)
2. Reduced withholding on dividends, interest, royalties
3. Business profits exemption (permanent establishment rules)
4. Pension distribution treatment
5. Social security/government service exemptions
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Penalty for failure to file Form 8833 (IRC §6712)
PENALTY_FAILURE_TO_DISCLOSE = 1_000.0

# Common treaty countries with US tax treaties
TREATY_COUNTRIES = {
    "DE": "Germany",
    "GB": "United Kingdom",
    "CA": "Canada",
    "FR": "France",
    "JP": "Japan",
    "AU": "Australia",
    "CH": "Switzerland",
    "NL": "Netherlands",
    "IE": "Ireland",
    "IN": "India",
}

# Position types requiring disclosure
POSITION_TYPES = [
    "RESIDENCE",              # Treaty residence claim
    "BUSINESS_PROFITS",       # Permanent establishment exemption
    "DIVIDENDS",              # Reduced withholding on dividends
    "INTEREST",               # Reduced withholding on interest
    "ROYALTIES",              # Reduced withholding on royalties
    "PENSIONS",               # Pension distribution treatment
    "GOVERNMENT_SERVICE",     # Government service exemption
    "STUDENTS_TEACHERS",      # Student/teacher exemption
    "OTHER_INCOME",           # Other income article claims
    "TOTALIZATION",           # Social security totalization (often EXEMPT from 8833)
]

# Positions exempt from Form 8833 requirement
EXEMPT_POSITIONS = {
    "TOTALIZATION",  # Social security totalization agreements are NOT tax treaties
}

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

PositionType = Literal[
    "RESIDENCE",
    "BUSINESS_PROFITS",
    "DIVIDENDS",
    "INTEREST",
    "ROYALTIES",
    "PENSIONS",
    "GOVERNMENT_SERVICE",
    "STUDENTS_TEACHERS",
    "OTHER_INCOME",
    "TOTALIZATION",
]

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class FilingRequirementInput(BaseModel):
    """Input for checking Form 8833 filing requirement."""
    treaty_country: str = Field(..., description="ISO 2-letter country code (e.g., 'DE', 'GB', 'CA')")
    treaty_article: str = Field(..., description="Treaty article or provision number (e.g., 'Article 15', 'Article 4')")
    position_type: PositionType = Field(..., description="Type of treaty position taken")
    
class DisclosureInput(BaseModel):
    """Input for creating Form 8833 disclosure."""
    treaty_country: str = Field(..., description="ISO 2-letter country code")
    treaty_article: str = Field(..., description="Treaty article or provision")
    treaty_provision: str = Field(..., description="Specific treaty text or provision relied upon")
    taxpayer_position: str = Field(..., description="Taxpayer's position and interpretation")
    law_overruled: str = Field(..., description="U.S. Code section overruled or modified by treaty")

# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class FilingRequirementResult(BaseModel):
    """Result of filing requirement check."""
    required: bool
    reason: str
    filing_deadline: str
    penalty_if_not_filed: float
    treaty_country_name: str
    position_type: str

class DisclosureResult(BaseModel):
    """Result of disclosure creation."""
    disclosure_summary: str
    reporting_requirements: list[str]
    treaty_reference: str
    penalty_warning: str

class OverviewResult(BaseModel):
    """Overview of Form 8833 and common treaty positions."""
    description: str
    common_countries: dict[str, str]
    common_articles: dict[str, str]
    filing_threshold: str
    penalty_amount: float

# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------

def check_filing_requirement(inp: FilingRequirementInput) -> FilingRequirementResult:
    """
    Check if Form 8833 filing is required for a treaty position.
    
    Returns filing requirement status with reason and deadline.
    """
    # Check if position is exempt
    is_exempt = inp.position_type in EXEMPT_POSITIONS
    
    # Get country name
    country_name = TREATY_COUNTRIES.get(inp.treaty_country.upper(), inp.treaty_country)
    
    # Determine filing requirement
    if is_exempt:
        required = False
        reason = (
            f"{inp.position_type} positions under totalization agreements are generally "
            f"exempt from Form 8833 disclosure requirements. However, verify with IRS "
            f"Publication 519 for your specific situation."
        )
    else:
        required = True
        reason = (
            f"Form 8833 disclosure is REQUIRED when claiming a {inp.position_type} position "
            f"under the U.S.-{country_name} tax treaty ({inp.treaty_article}) that reduces "
            f"or eliminates U.S. tax liability."
        )
    
    # Filing deadline is same as tax return deadline (typically April 15, or October 15 with extension)
    # For illustration, using current year + 1, April 15
    current_year = date.today().year
    filing_deadline_date = date(current_year + 1, 4, 15)
    filing_deadline = filing_deadline_date.strftime("%Y-%m-%d")
    
    return FilingRequirementResult(
        required=required,
        reason=reason,
        filing_deadline=filing_deadline,
        penalty_if_not_filed=PENALTY_FAILURE_TO_DISCLOSE if required else 0.0,
        treaty_country_name=country_name,
        position_type=inp.position_type,
    )

def create_disclosure(inp: DisclosureInput) -> DisclosureResult:
    """
    Create a treaty position disclosure for Form 8833.
    
    Returns disclosure summary and reporting requirements.
    """
    country_name = TREATY_COUNTRIES.get(inp.treaty_country.upper(), inp.treaty_country)
    
    # Generate disclosure summary
    disclosure_summary = (
        f"Treaty Position Disclosure: U.S.-{country_name} Tax Treaty, {inp.treaty_article}. "
        f"Taxpayer claims treaty provision overrides or modifies {inp.law_overruled}. "
        f"Position: {inp.taxpayer_position[:200]}..."
    )
    
    # Reporting requirements
    reporting_requirements = [
        "Attach Form 8833 to your Form 1040 or 1040-NR for the tax year",
        "Complete all required lines including treaty article and U.S. Code section affected",
        "Provide detailed explanation of your treaty position in Part III",
        f"Ensure disclosure is made by filing deadline (typically April 15 + extensions)",
        "Keep supporting documentation (treaty text, residency certificates, etc.)",
        "If position changes, file updated Form 8833 with amended return",
    ]
    
    treaty_reference = f"U.S.-{country_name} Income Tax Treaty, {inp.treaty_article}"
    
    penalty_warning = (
        f"IMPORTANT: Failure to properly disclose this treaty position may result in a "
        f"${PENALTY_FAILURE_TO_DISCLOSE:,.0f} penalty per IRC §6712. Penalties may be "
        f"higher if the position is determined to be frivolous or fraudulent."
    )
    
    return DisclosureResult(
        disclosure_summary=disclosure_summary,
        reporting_requirements=reporting_requirements,
        treaty_reference=treaty_reference,
        penalty_warning=penalty_warning,
    )

def get_overview() -> OverviewResult:
    """
    Get overview of Form 8833 requirements and common treaty positions.
    """
    description = (
        "Form 8833 (Treaty-Based Return Position Disclosure) is required when a U.S. taxpayer "
        "takes a position that a tax treaty overrides or modifies U.S. tax law. Common situations "
        "include claiming treaty residence, reduced withholding rates, or business profits exemptions. "
        "The form must be attached to your tax return, and failure to disclose can result in penalties."
    )
    
    common_articles = {
        "Article 4": "Residence - Claiming treaty residence status different from citizenship",
        "Article 7": "Business Profits - Permanent establishment exemptions",
        "Article 10": "Dividends - Reduced withholding rates (typically 15% or 0%)",
        "Article 11": "Interest - Reduced or eliminated withholding on interest income",
        "Article 12": "Royalties - Reduced withholding on royalty payments",
        "Article 18": "Pensions - Taxation of pension and annuity distributions",
        "Article 19": "Government Service - Exemptions for government employees",
        "Article 20": "Students/Teachers - Exemptions for students and educators",
    }
    
    filing_threshold = (
        "Required whenever you take a treaty position that reduces or eliminates U.S. tax. "
        "No dollar threshold - even $1 of tax savings requires disclosure."
    )
    
    return OverviewResult(
        description=description,
        common_countries=TREATY_COUNTRIES,
        common_articles=common_articles,
        filing_threshold=filing_threshold,
        penalty_amount=PENALTY_FAILURE_TO_DISCLOSE,
    )
