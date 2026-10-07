"""
Form 8825 – Information Return by a U.S. Person with Respect to Certain Foreign Partnerships.

Form 8825 is required by U.S. persons who:
- Own ≥10% of a foreign partnership (directly or constructively)
- Own ≥50% of a foreign partnership (control)
- Are a General Partner in a foreign partnership
- Have a reportable event (acquisition/disposition/change in interest)

Penalties (IRC §6679):
- Failure to file: $10,000 per violation
- Maximum penalty: $50,000 per tax year
- Continued failure after IRS notice: additional penalties

Related forms: Form 8865 (Return of U.S. Persons With Respect to Certain Foreign Partnerships)
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Filing thresholds
OWNERSHIP_THRESHOLD = 10.0  # ≥10% ownership
CONTROL_THRESHOLD = 50.0  # ≥50% ownership (control)

# Penalty amounts (IRC §6679)
PENALTY_PER_VIOLATION = 10_000.0
PENALTY_MAX_PER_YEAR = 50_000.0

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

EntityTypeLiteral = Literal["individual", "corporation", "partnership", "trust", "estate", "llc"]
ForeignCorporationLiteral = Literal["yes", "no"]

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class FilingRequirementInput(BaseModel):
    """Input for checking Form 8825 filing requirement."""
    entity_type: EntityTypeLiteral = Field(..., description="Type of U.S. person/entity")
    ownership_percent: float = Field(..., ge=0.0, le=100.0, description="Ownership percentage in foreign partnership (0-100)")
    us_owners: int = Field(..., ge=0, description="Number of U.S. persons with ownership interests")
    foreign_corporation: ForeignCorporationLiteral = Field(..., description="Whether the entity is a foreign corporation")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")


class PenaltyCalculationInput(BaseModel):
    """Input for penalty calculation."""
    entity_type: EntityTypeLiteral = Field(..., description="Type of U.S. person/entity")
    ownership_percent: float = Field(..., ge=0.0, le=100.0, description="Ownership percentage in foreign partnership (0-100)")
    us_owners: int = Field(..., ge=0, description="Number of U.S. persons with ownership interests")
    foreign_corporation: ForeignCorporationLiteral = Field(..., description="Whether the entity is a foreign corporation")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")
    is_general_partner: bool = Field(False, description="Whether the person is a General Partner")
    violations_count: int = Field(1, ge=1, le=10, description="Number of violations (unfiled years)")
    days_unreported: int = Field(0, ge=0, description="Days the failure continues after IRS notice")


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class FilingRequirementResult(BaseModel):
    """Result of filing requirement check."""
    filing_required: bool
    reasons: list[str]
    ownership_percent: float
    entity_type: str
    tax_year: int
    penalty_if_not_filed: float
    related_forms: list[str]
    recommendation: str


class PenaltyResult(BaseModel):
    """Result of penalty calculation."""
    base_penalty: float
    continued_failure_penalty: float
    total_penalty: float
    violations_count: int
    days_unreported: int
    is_general_partner: bool
    explanation: str


class Form8825Overview(BaseModel):
    """Overview of Form 8825 requirements."""
    title: str
    description: str
    who_must_file: list[str]
    ownership_threshold: str
    control_threshold: str
    general_partner_rule: str
    penalties: str
    related_forms: list[str]
    filing_deadline: str
    recommendation: str


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def check_filing_requirement(inp: FilingRequirementInput) -> FilingRequirementResult:
    """
    Check if the taxpayer has a filing requirement for Form 8825.

    Form 8825 is required when:
    1. U.S. person owns ≥10% of a foreign partnership
    2. U.S. person owns ≥50% of a foreign partnership (control)
    3. U.S. person is a General Partner in a foreign partnership
    """
    reasons: list[str] = []
    filing_required = False

    # Check ≥10% ownership threshold
    if inp.ownership_percent >= OWNERSHIP_THRESHOLD:
        filing_required = True
        reasons.append(
            f"You own {inp.ownership_percent:.1f}% of a foreign partnership "
            f"(≥{OWNERSHIP_THRESHOLD:.0f}% threshold). Form 8825 is required."
        )

    # Check ≥50% control threshold
    if inp.ownership_percent >= CONTROL_THRESHOLD:
        reasons.append(
            f"You own {inp.ownership_percent:.1f}% of a foreign partnership "
            f"(≥{CONTROL_THRESHOLD:.0f}% control threshold). "
            f"Enhanced reporting requirements apply."
        )

    # Check if multiple U.S. owners trigger additional requirements
    if inp.us_owners > 1 and inp.ownership_percent >= OWNERSHIP_THRESHOLD:
        reasons.append(
            f"Multiple U.S. owners ({inp.us_owners}) with ≥{OWNERSHIP_THRESHOLD:.0f}% "
            f"aggregate ownership. Each U.S. person may need to file Form 8825."
        )

    # Foreign corporation check
    if inp.foreign_corporation == "yes":
        reasons.append(
            "The entity is a foreign corporation. Additional reporting under "
            "IRC §6038/6038B may apply (Form 5471)."
        )

    if not filing_required:
        reasons.append(
            f"No filing requirement: ownership ({inp.ownership_percent:.1f}%) is below "
            f"the {OWNERSHIP_THRESHOLD:.0f}% threshold and no General Partner status."
        )
        recommendation = (
            "Form 8825 is not required based on the information provided. "
            "However, consult a tax professional to verify constructive ownership "
            "and indirect control rules."
        )
    else:
        recommendation = (
            f"Form 8825 is REQUIRED for {inp.tax_year}. "
            f"Filing deadline: typically April 15 (or October 15 with extension). "
            f"Attach Form 8825 to your Form 1040. "
            f"Also consider Form 8865 for foreign partnership reporting."
        )

    return FilingRequirementResult(
        filing_required=filing_required,
        reasons=reasons,
        ownership_percent=inp.ownership_percent,
        entity_type=inp.entity_type,
        tax_year=inp.tax_year,
        penalty_if_not_filed=PENALTY_PER_VIOLATION if filing_required else 0.0,
        related_forms=["Form 8865", "Form 5471"] if filing_required else [],
        recommendation=recommendation,
    )


def calculate_penalty(inp: PenaltyCalculationInput) -> PenaltyResult:
    """
    Calculate penalties for failure to file Form 8825.

    Penalties (IRC §6679):
    - Base: $10,000 per violation
    - Maximum: $50,000 per tax year
    - Continued failure: additional penalties after IRS notice
    """
    # Check if filing is required
    filing_check = check_filing_requirement(
        FilingRequirementInput(
            entity_type=inp.entity_type,
            ownership_percent=inp.ownership_percent,
            us_owners=inp.us_owners,
            foreign_corporation=inp.foreign_corporation,
            tax_year=inp.tax_year,
        )
    )

    if not filing_check.filing_required and not inp.is_general_partner:
        return PenaltyResult(
            base_penalty=0.0,
            continued_failure_penalty=0.0,
            total_penalty=0.0,
            violations_count=inp.violations_count,
            days_unreported=inp.days_unreported,
            is_general_partner=inp.is_general_partner,
            explanation="No filing requirement; no penalty applies.",
        )

    # Base penalty: $10,000 per violation
    base_penalty = PENALTY_PER_VIOLATION * inp.violations_count

    # Cap at maximum per year
    base_penalty = min(base_penalty, PENALTY_MAX_PER_YEAR)

    # Continued failure penalty: additional $10,000 per 30-day period after IRS notice
    periods_30_days = inp.days_unreported // 30
    continued_penalty = min(
        periods_30_days * PENALTY_PER_VIOLATION,
        PENALTY_MAX_PER_YEAR - base_penalty,
    )
    continued_penalty = max(continued_penalty, 0.0)

    total_penalty = base_penalty + continued_penalty

    explanation = (
        f"Base penalty: ${base_penalty:,.2f} "
        f"(${PENALTY_PER_VIOLATION:,.0f} × {inp.violations_count} violation(s)). "
    )
    if inp.days_unreported > 0:
        explanation += (
            f"Continued failure ({inp.days_unreported} days, {periods_30_days} periods): "
            f"${continued_penalty:,.2f}. "
        )
    if inp.is_general_partner:
        explanation += "General Partner status increases penalty exposure. "
    explanation += f"Total: ${total_penalty:,.2f} (max ${PENALTY_MAX_PER_YEAR:,.0f} per year)."

    return PenaltyResult(
        base_penalty=base_penalty,
        continued_failure_penalty=continued_penalty,
        total_penalty=total_penalty,
        violations_count=inp.violations_count,
        days_unreported=inp.days_unreported,
        is_general_partner=inp.is_general_partner,
        explanation=explanation,
    )


def get_overview() -> Form8825Overview:
    """Return overview of Form 8825 requirements."""
    return Form8825Overview(
        title="Form 8825: Information Return by a U.S. Person with Respect to Certain Foreign Partnerships",
        description=(
            "Form 8825 is required by U.S. persons who have certain interests in "
            "foreign partnerships. The filing requirement depends on the level of "
            "ownership, control, and partnership role."
        ),
        who_must_file=[
            "U.S. persons who own ≥10% of a foreign partnership (directly or constructively)",
            "U.S. persons who own ≥50% of a foreign partnership (control threshold)",
            "U.S. persons who are General Partners in a foreign partnership",
            "U.S. persons with reportable events (acquisition/disposition/change in interest)",
        ],
        ownership_threshold=(
            f"≥{OWNERSHIP_THRESHOLD:.0f}% ownership in a foreign partnership "
            f"(direct, indirect, or constructive)"
        ),
        control_threshold=(
            f"≥{CONTROL_THRESHOLD:.0f}% ownership triggers enhanced reporting requirements"
        ),
        general_partner_rule=(
            "General Partners must file Form 8825 regardless of ownership percentage"
        ),
        penalties=(
            f"Failure to file: ${PENALTY_PER_VIOLATION:,.0f} per violation. "
            f"Maximum: ${PENALTY_MAX_PER_YEAR:,.0f} per tax year. "
            f"Continued failure after IRS notice: additional penalties."
        ),
        related_forms=[
            "Form 8865 (Return of U.S. Persons With Respect to Certain Foreign Partnerships)",
            "Form 5471 (Information Return of U.S. Persons With Respect to Certain Foreign Corporations)",
        ],
        filing_deadline=(
            "Form 8825 is due with your annual tax return (Form 1040). "
            "Deadline: typically April 15, or October 15 with extension."
        ),
        recommendation=(
            "If you own 10% or more of a foreign partnership, or if you are a "
            "General Partner, you likely have a filing requirement. Consult a "
            "tax professional familiar with international tax (IRC §6038/6038B)."
        ),
    )
