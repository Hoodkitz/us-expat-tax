"""
Social Security Totalization Agreements helper.

Covers the ~30 countries the US has Totalization Agreements with.
Determines which country's Social Security system applies and whether
FICA taxes may be avoided.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Data: countries with US Totalization Agreements
# (Source: SSA.gov – active as of 2024)
# ---------------------------------------------------------------------------

TOTALIZATION_COUNTRIES: dict[str, dict] = {
    "italy": {
        "name": "Italy",
        "effective_year": 1978,
        "notes": "First US totalization agreement.",
    },
    "germany": {
        "name": "Germany",
        "effective_year": 1979,
        "notes": "Covers employees and self-employed.",
    },
    "switzerland": {
        "name": "Switzerland",
        "effective_year": 1980,
        "notes": "",
    },
    "belgium": {
        "name": "Belgium",
        "effective_year": 1984,
        "notes": "",
    },
    "norway": {
        "name": "Norway",
        "effective_year": 1984,
        "notes": "",
    },
    "canada": {
        "name": "Canada",
        "effective_year": 1984,
        "notes": "",
    },
    "united kingdom": {
        "name": "United Kingdom",
        "effective_year": 1985,
        "notes": "Covers Great Britain and Northern Ireland.",
    },
    "uk": {
        "name": "United Kingdom",
        "effective_year": 1985,
        "notes": "Covers Great Britain and Northern Ireland.",
    },
    "sweden": {
        "name": "Sweden",
        "effective_year": 1987,
        "notes": "",
    },
    "spain": {
        "name": "Spain",
        "effective_year": 1988,
        "notes": "",
    },
    "france": {
        "name": "France",
        "effective_year": 1988,
        "notes": "",
    },
    "portugal": {
        "name": "Portugal",
        "effective_year": 1989,
        "notes": "",
    },
    "netherlands": {
        "name": "Netherlands",
        "effective_year": 1990,
        "notes": "",
    },
    "austria": {
        "name": "Austria",
        "effective_year": 1991,
        "notes": "",
    },
    "finland": {
        "name": "Finland",
        "effective_year": 1992,
        "notes": "",
    },
    "ireland": {
        "name": "Ireland",
        "effective_year": 1993,
        "notes": "",
    },
    "luxembourg": {
        "name": "Luxembourg",
        "effective_year": 1993,
        "notes": "",
    },
    "greece": {
        "name": "Greece",
        "effective_year": 1994,
        "notes": "",
    },
    "south korea": {
        "name": "South Korea",
        "effective_year": 2001,
        "notes": "",
    },
    "korea": {
        "name": "South Korea",
        "effective_year": 2001,
        "notes": "",
    },
    "chile": {
        "name": "Chile",
        "effective_year": 2001,
        "notes": "",
    },
    "australia": {
        "name": "Australia",
        "effective_year": 2002,
        "notes": "",
    },
    "japan": {
        "name": "Japan",
        "effective_year": 2005,
        "notes": "",
    },
    "denmark": {
        "name": "Denmark",
        "effective_year": 2008,
        "notes": "",
    },
    "czech republic": {
        "name": "Czech Republic",
        "effective_year": 2009,
        "notes": "",
    },
    "poland": {
        "name": "Poland",
        "effective_year": 2009,
        "notes": "",
    },
    "slovakia": {
        "name": "Slovakia",
        "effective_year": 2014,
        "notes": "",
    },
    "hungary": {
        "name": "Hungary",
        "effective_year": 2016,
        "notes": "",
    },
    "brazil": {
        "name": "Brazil",
        "effective_year": 2018,
        "notes": "Limited coverage.",
    },
    "uruguay": {
        "name": "Uruguay",
        "effective_year": 2016,
        "notes": "",
    },
    "iceland": {
        "name": "Iceland",
        "effective_year": 2016,
        "notes": "",
    },
    "india": {
        "name": "India",
        "effective_year": 2009,
        "notes": "Covers employees on temporary assignment.",
    },
}

# Countries where self-employed are covered differently
SELF_EMPLOYED_EXCEPTIONS = {"canada", "australia"}

# Canonical list for the GET endpoint (deduplicated display names)
_CANONICAL_NAMES: list[str] = sorted(
    {v["name"] for v in TOTALIZATION_COUNTRIES.values()}
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TotalizationRequest(BaseModel):
    country: str
    employment_type: Literal["employee", "self_employed"]
    years_in_us: float
    years_in_country: float
    us_citizen: bool


class TotalizationResult(BaseModel):
    agreement_exists: bool
    agreement_countries: list[str]
    applicable_system: str
    avoid_double_taxation: bool
    fica_exempt: bool
    explanation: str


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

# Minimum years required to be eligible for SS benefits in each system
_MIN_YEARS_US = 10.0          # 40 quarters
_MIN_YEARS_FOREIGN = 1.0      # at least some coverage abroad (varies; 1yr is conservative)


def check_totalization(req: TotalizationRequest) -> TotalizationResult:
    """
    Evaluate whether a US Totalization Agreement applies and what it means.
    """
    country_key = req.country.strip().lower()
    country_data = TOTALIZATION_COUNTRIES.get(country_key)

    agreement_exists = country_data is not None
    country_display = country_data["name"] if country_data else req.country

    if not agreement_exists:
        return TotalizationResult(
            agreement_exists=False,
            agreement_countries=_CANONICAL_NAMES,
            applicable_system="Both (no agreement – double taxation risk)",
            avoid_double_taxation=False,
            fica_exempt=False,
            explanation=(
                f"The US does not have a Totalization Agreement with {country_display}. "
                "You may owe Social Security taxes in BOTH countries simultaneously. "
                "Consult a tax professional to explore treaty or domestic exemptions."
            ),
        )

    # --- Determine which system applies ---
    # General rule: work is covered by the country where you're working.
    # Exception: temporary assignments (typically ≤5 years) can remain covered
    # by the home country system.

    is_temporary = req.years_in_country <= 5 and req.years_in_us >= 1

    # For employees on temporary assignment to the foreign country,
    # they may stay under US system if sent by a US employer.
    # For self-employed, most agreements cover the country of residence.
    if req.employment_type == "self_employed" and country_key in SELF_EMPLOYED_EXCEPTIONS:
        applicable_system = "US (self-employed – special rule applies)"
        fica_exempt = False
        system_note = (
            f"As a self-employed person, the US-{country_display} agreement uses a special "
            "residency-based rule. You pay US SE tax and are exempt from foreign SS contributions."
        )
    elif is_temporary and req.employment_type == "employee":
        applicable_system = "US (temporary assignment – home-country coverage)"
        fica_exempt = False
        system_note = (
            f"Because your assignment to {country_display} is temporary (≤5 years) and you "
            "were previously covered by the US system, you remain under the US Social Security "
            "system and are exempt from paying into {country_display}'s system."
        )
    else:
        applicable_system = f"{country_display} (country of employment)"
        fica_exempt = True
        system_note = (
            f"You are covered by {country_display}'s Social Security system. "
            "Under the Totalization Agreement, you are exempt from US FICA taxes "
            "(Social Security and Medicare) on your foreign employment income."
        )

    # --- Benefit eligibility estimate ---
    us_eligible = req.years_in_us >= _MIN_YEARS_US
    foreign_eligible = req.years_in_country >= _MIN_YEARS_FOREIGN

    benefit_note: str
    if us_eligible and foreign_eligible:
        benefit_note = (
            "You may qualify for benefits under BOTH systems. "
            "The Totalization Agreement allows combining work credits from both countries "
            "to meet minimum eligibility thresholds."
        )
    elif us_eligible:
        benefit_note = (
            "You have sufficient US work credits (≥10 years / 40 quarters) to qualify "
            f"for US Social Security. You may also accumulate {country_display} credits "
            "for future eligibility there."
        )
    elif foreign_eligible:
        benefit_note = (
            f"You have some coverage in {country_display}. "
            "You may not yet meet the 40-quarter (10-year) US threshold, but totalized "
            "credits from both countries may help you qualify."
        )
    else:
        benefit_note = (
            "You have limited coverage in both systems so far. "
            "Totalization lets you combine credits from both countries to reach eligibility thresholds."
        )

    explanation = (
        f"The US has a Totalization Agreement with {country_display} "
        f"(in effect since {country_data['effective_year']}). "
        f"{system_note} "
        f"{benefit_note}"
    )

    if country_data.get("notes"):
        explanation += f" Note: {country_data['notes']}"

    return TotalizationResult(
        agreement_exists=True,
        agreement_countries=_CANONICAL_NAMES,
        applicable_system=applicable_system,
        avoid_double_taxation=True,
        fica_exempt=fica_exempt,
        explanation=explanation,
    )
