"""
Form 8843 — Statement for Exempt Individuals and Individuals with a Medical Condition.

Business logic for determining exempt individual status under IRC §7701(b)(5)
and the Substantial Presence Test under IRC §7701(b)(1)-(3).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ExemptIndividualInput:
    """Input for exempt individual status check."""
    us_days_present: int
    foreign_days_present: int
    tax_year: int
    visa_type: Literal["F", "J", "M", "Q", "P", "H", "L", "O", "B", "E", "other"]
    is_student: bool = False
    is_teacher: bool = False
    is_trainee: bool = False
    is_researcher: bool = False


@dataclass
class ExemptIndividualResult:
    """Result of exempt individual status check."""
    exempt_status: bool
    days_counted: int
    substantial_presence_test: dict
    required_forms: list[str]
    explanation: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Visa types that qualify for exempt individual status
EXEMPT_VISA_TYPES = {"F", "J", "M", "Q", "P"}

# Days threshold for Substantial Presence Test
SPT_DAYS_THRESHOLD = 183

# Minimum days in current year to trigger SPT
SPT_MIN_CURRENT_YEAR_DAYS = 31


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------

def check_exempt_status(inp: ExemptIndividualInput) -> ExemptIndividualResult:
    """
    Determine if an individual qualifies as an Exempt Individual under IRC §7701(b)(5).

    Exempt Individuals include:
    - Students (F, J, M, Q visas)
    - Teachers/Trainees (J, Q visas)
    - Researchers (J, Q visas)
    - Athletes (P visas)

    Exempt Individuals are NOT counted as US residents for tax purposes
    under the Substantial Presence Test.
    """
    # Check if visa type qualifies for exempt status
    visa_qualifies = inp.visa_type in EXEMPT_VISA_TYPES

    # Check if individual has a qualifying role
    has_qualifying_role = (
        inp.is_student or
        inp.is_teacher or
        inp.is_trainee or
        inp.is_researcher
    )

    # Determine exempt status
    exempt_status = visa_qualifies and has_qualifying_role

    # Calculate days counted (exempt individuals don't count days)
    days_counted = 0 if exempt_status else inp.us_days_present

    # Run Substantial Presence Test
    spt_result = _calculate_substantial_presence_test(
        us_days=inp.us_days_present,
        foreign_days=inp.foreign_days_present,
        tax_year=inp.tax_year,
        is_exempt=exempt_status,
    )

    # Determine required forms
    required_forms = _determine_required_forms(exempt_status, inp)

    # Generate explanation
    explanation = _generate_explanation(exempt_status, inp, spt_result)

    return ExemptIndividualResult(
        exempt_status=exempt_status,
        days_counted=days_counted,
        substantial_presence_test=spt_result,
        required_forms=required_forms,
        explanation=explanation,
    )


def _calculate_substantial_presence_test(
    us_days: int,
    foreign_days: int,
    tax_year: int,
    is_exempt: bool,
) -> dict:
    """
    Calculate the Substantial Presence Test under IRC §7701(b)(1)-(3).

    Formula:
    - Current year days: 1 day each
    - Prior year days: 1/3 day each
    - Year before prior: 1/6 day each

    Threshold: 183 days

    Note: Exempt Individuals are NOT subject to the SPT.
    """
    # For exempt individuals, SPT does not apply
    if is_exempt:
        return {
            "applies": False,
            "current_year_days": us_days,
            "prior_year_days_weighted": 0,
            "two_years_ago_days_weighted": 0,
            "total_days_counted": 0,
            "threshold": SPT_DAYS_THRESHOLD,
            "meets_threshold": False,
            "explanation": (
                "Substantial Presence Test does not apply to Exempt Individuals "
                "under IRC §7701(b)(5)."
            ),
        }

    # For non-exempt individuals, calculate weighted days
    # Note: In a real implementation, we would need prior year data
    # Here we use the current year days as a simplified calculation
    current_year_days = us_days
    prior_year_days_weighted = 0  # Would need prior year data
    two_years_ago_days_weighted = 0  # Would need two years ago data

    total_days_counted = (
        current_year_days +
        prior_year_days_weighted +
        two_years_ago_days_weighted
    )

    meets_threshold = total_days_counted >= SPT_DAYS_THRESHOLD

    return {
        "applies": True,
        "current_year_days": current_year_days,
        "prior_year_days_weighted": prior_year_days_weighted,
        "two_years_ago_days_weighted": two_years_ago_days_weighted,
        "total_days_counted": total_days_counted,
        "threshold": SPT_DAYS_THRESHOLD,
        "meets_threshold": meets_threshold,
        "explanation": (
            f"Total days counted: {total_days_counted}. "
            f"Threshold: {SPT_DAYS_THRESHOLD} days. "
            f"{'Meets' if meets_threshold else 'Does not meet'} the Substantial Presence Test."
        ),
    }


def _determine_required_forms(exempt_status: bool, inp: ExemptIndividualInput) -> list[str]:
    """Determine which forms are required based on exempt status."""
    forms = []

    if exempt_status:
        forms.append("Form 8843 — Statement for Exempt Individuals")
        forms.append("Form 1040-NR — U.S. Nonresident Alien Income Tax Return (if applicable)")
    else:
        forms.append("Form 1040 — U.S. Individual Income Tax Return")
        if inp.us_days_present > 0:
            forms.append("Form 8843 — Statement for Exempt Individuals (if applicable)")

    return forms


def _generate_explanation(
    exempt_status: bool,
    inp: ExemptIndividualInput,
    spt_result: dict,
) -> str:
    """Generate a human-readable explanation of the exempt status determination."""
    if exempt_status:
        role = []
        if inp.is_student:
            role.append("Student")
        if inp.is_teacher:
            role.append("Teacher")
        if inp.is_trainee:
            role.append("Trainee")
        if inp.is_researcher:
            role.append("Researcher")

        role_str = "/".join(role) if role else "Exempt Individual"

        return (
            f"You qualify as an Exempt Individual under IRC §7701(b)(5) "
            f"as a {role_str} on a {inp.visa_type} visa. "
            f"You are NOT considered a US resident for tax purposes "
            f"under the Substantial Presence Test. "
            f"You must file Form 8843 to claim this status."
        )
    else:
        return (
            f"You do NOT qualify as an Exempt Individual. "
            f"Your {inp.visa_type} visa does not meet the requirements "
            f"for exempt status under IRC §7701(b)(5). "
            f"You may be considered a US resident for tax purposes "
            f"if you meet the Substantial Presence Test."
        )
