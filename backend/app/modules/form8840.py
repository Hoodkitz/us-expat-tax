"""
Form 8840 — Closer Connection Exception
=======================================

Form 8840 is used by foreign nationals to claim the "Closer Connection Exception"
to the Substantial Presence Test (SPT). If a foreign national has a closer connection
to the United States than to a foreign country, they may be treated as a U.S. Resident
Alien even if they do not meet the 183-day threshold of the SPT.

Key rules:
- If days_in_us >= 183 → Resident Alien (SPT met)
- If closer_connection=True and days_in_us < 183 → Resident Alien (Closer Connection Exception)
- If exempt_individual=True → NOT a Resident Alien (exempt from SPT)
"""

from pydantic import BaseModel, Field


class Form8840Input(BaseModel):
    """Input model for Form 8840 Closer Connection Exception calculation."""

    days_in_us: int = Field(
        ...,
        ge=0,
        le=366,
        description="Number of days present in the United States during the tax year",
    )
    tax_year: int = Field(
        ...,
        ge=2000,
        le=2099,
        description="Tax year for which the calculation is performed",
    )
    closer_connection: bool = Field(
        ...,
        description="Whether the individual has a closer connection to the US than to a foreign country",
    )
    exempt_individual: bool = Field(
        ...,
        description="Whether the individual qualifies as an exempt individual (e.g., student, teacher, trainee)",
    )


class Form8840Result(BaseModel):
    """Result model for Form 8840 Closer Connection Exception calculation."""

    resident_alien: bool = Field(
        ...,
        description="Whether the individual is classified as a U.S. Resident Alien",
    )
    days_in_us: int = Field(
        ...,
        description="Number of days present in the United States",
    )
    closer_connection: bool = Field(
        ...,
        description="Whether a closer connection to the US was claimed",
    )
    exempt_individual: bool = Field(
        ...,
        description="Whether the individual qualifies as an exempt individual",
    )
    explanation: str = Field(
        ...,
        description="Detailed explanation of the determination",
    )


def calculate_form8840(data: Form8840Input) -> Form8840Result:
    """
    Calculate Form 8840 Closer Connection Exception.

    Rules:
    1. If exempt_individual=True → NOT a Resident Alien (exempt from SPT)
    2. If days_in_us >= 183 → Resident Alien (Substantial Presence Test met)
    3. If closer_connection=True and days_in_us < 183 → Resident Alien (Closer Connection Exception)
    4. Otherwise → NOT a Resident Alien

    Args:
        data: Form8840Input with days_in_us, tax_year, closer_connection, exempt_individual

    Returns:
        Form8840Result with resident_alien determination and explanation
    """
    # Rule 1: Exempt individuals are not subject to SPT
    if data.exempt_individual:
        return Form8840Result(
            resident_alien=False,
            days_in_us=data.days_in_us,
            closer_connection=data.closer_connection,
            exempt_individual=data.exempt_individual,
            explanation=(
                f"You qualify as an exempt individual for tax year {data.tax_year}. "
                "Exempt individuals (such as students, teachers, trainees, and certain "
                "other categories) are not subject to the Substantial Presence Test. "
                "Therefore, you are NOT classified as a U.S. Resident Alien for tax "
                "purposes, regardless of your days present in the United States."
            ),
        )

    # Rule 2: Substantial Presence Test (183-day threshold)
    if data.days_in_us >= 183:
        return Form8840Result(
            resident_alien=True,
            days_in_us=data.days_in_us,
            closer_connection=data.closer_connection,
            exempt_individual=data.exempt_individual,
            explanation=(
                f"You were present in the United States for {data.days_in_us} days during "
                f"tax year {data.tax_year}, which meets or exceeds the 183-day threshold "
                "of the Substantial Presence Test. You are classified as a U.S. Resident "
                "Alien for tax purposes."
            ),
        )

    # Rule 3: Closer Connection Exception
    if data.closer_connection:
        return Form8840Result(
            resident_alien=True,
            days_in_us=data.days_in_us,
            closer_connection=data.closer_connection,
            exempt_individual=data.exempt_individual,
            explanation=(
                f"Although you were present in the United States for only {data.days_in_us} days "
                f"(less than the 183-day threshold), you have claimed a closer connection to "
                "the United States than to a foreign country. Under the Closer Connection "
                "Exception (Form 8840), you are classified as a U.S. Resident Alien for tax "
                f"purposes for tax year {data.tax_year}."
            ),
        )

    # Rule 4: Not a resident alien
    return Form8840Result(
        resident_alien=False,
        days_in_us=data.days_in_us,
        closer_connection=data.closer_connection,
        exempt_individual=data.exempt_individual,
        explanation=(
            f"You were present in the United States for {data.days_in_us} days during "
            f"tax year {data.tax_year}, which is less than the 183-day threshold of the "
            "Substantial Presence Test. You have not claimed a closer connection to the "
            "United States. Therefore, you are NOT classified as a U.S. Resident Alien "
            "for tax purposes."
        ),
    )


def get_form8840_overview() -> dict:
    """
    Return an overview of Form 8840 Closer Connection Exception.

    Returns:
        Dictionary with purpose, who must file, key rules, and IRS reference.
    """
    return {
        "form": "Form 8840",
        "title": "Closer Connection Exception Statement for Aliens",
        "purpose": (
            "Form 8840 is used by foreign nationals who are present in the United States "
            "but do not meet the Substantial Presence Test (SPT) threshold of 183 days. "
            "It allows them to claim the Closer Connection Exception, which treats them as "
            "U.S. Resident Aliens if they can demonstrate a closer connection to the United "
            "States than to any foreign country."
        ),
        "who_must_file": [
            "Foreign nationals present in the United States for fewer than 183 days",
            "Individuals who do not meet the Substantial Presence Test",
            "Individuals who have a closer connection to the US than to a foreign country",
            "Foreign students, teachers, and trainees who are exempt individuals but wish to claim resident status",
        ],
        "key_rules": [
            "Substantial Presence Test: 183 days or more in the US → Resident Alien",
            "Closer Connection Exception: Fewer than 183 days but closer connection to US → Resident Alien",
            "Exempt Individuals: Students, teachers, trainees, and certain others are exempt from SPT",
            "Closer Connection Factors: Location of family, personal belongings, home, social ties, business interests",
            "Tax Year: The determination is made separately for each tax year",
        ],
        "closer_connection_factors": [
            "Location of permanent home",
            "Location of family (spouse, children)",
            "Location of personal belongings (cars, furniture, clothing)",
            "Location of social, cultural, religious, and political organizations",
            "Location of business interests (bank accounts, investments)",
            "Country of driver's license",
            "Country of voter registration",
            "Country of residence declared on official documents",
        ],
        "exempt_individual_categories": [
            "F visa students (academic)",
            "J visa exchange visitors",
            "M visa vocational students",
            "Q visa cultural exchange participants",
            "Certain teachers and trainees",
            "Professional athletes temporarily in the US for charitable events",
        ],
        "filing_deadline": (
            "Form 8840 should be filed with the individual's U.S. tax return (Form 1040-NR "
            "or Form 1040) by the tax filing deadline, typically April 15 of the following year."
        ),
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8840",
    }
