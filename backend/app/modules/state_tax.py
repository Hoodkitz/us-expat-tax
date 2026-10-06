"""
State Tax Filing Obligations Module.
Helps US expats understand state income tax filing requirements based on
residency, physical presence, and domicile rules for all 50 US states.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# State Knowledge Base
# ---------------------------------------------------------------------------

STATE_DATA: dict[str, dict] = {
    "AK": {"name": "Alaska",          "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No state income tax."},
    "AL": {"name": "Alabama",         "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day statutory residency rule."},
    "AR": {"name": "Arkansas",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule; domicile controls."},
    "AZ": {"name": "Arizona",         "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "CA": {"name": "California",      "has_income_tax": True,  "safe_harbor_days": 546, "statutory_resident_days": 183, "notes": "Highly aggressive. Safe harbor: 546 days over 2 consecutive years outside CA. 9 domicile factors. FTB scrutinizes. Form 3840 for multi-state."},
    "CO": {"name": "Colorado",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "CT": {"name": "Connecticut",     "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183+ days AND permanent place of abode triggers statutory residency."},
    "DE": {"name": "Delaware",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "FL": {"name": "Florida",         "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No state income tax. Popular expat destination state for domicile."},
    "GA": {"name": "Georgia",         "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "HI": {"name": "Hawaii",          "has_income_tax": True,  "safe_harbor_days": 200, "statutory_resident_days": 200, "notes": "200+ days considered resident."},
    "IA": {"name": "Iowa",            "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "ID": {"name": "Idaho",           "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "IL": {"name": "Illinois",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "High-risk state. Aggressive nexus. 183+ days triggers full residency."},
    "IN": {"name": "Indiana",         "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "KS": {"name": "Kansas",          "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "KY": {"name": "Kentucky",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "LA": {"name": "Louisiana",       "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "MA": {"name": "Massachusetts",   "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "High-risk. 183+ days AND maintained a home = statutory resident."},
    "MD": {"name": "Maryland",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183+ days AND permanent place of abode."},
    "ME": {"name": "Maine",           "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "MI": {"name": "Michigan",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "MN": {"name": "Minnesota",       "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule; very active enforcement."},
    "MO": {"name": "Missouri",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "MS": {"name": "Mississippi",     "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "MT": {"name": "Montana",         "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "NC": {"name": "North Carolina",  "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "ND": {"name": "North Dakota",    "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "NE": {"name": "Nebraska",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "NH": {"name": "New Hampshire",   "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No earned income tax (interest/dividends only)."},
    "NJ": {"name": "New Jersey",      "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "High-risk. 183+ days triggers statutory residency. Aggressive enforcement."},
    "NM": {"name": "New Mexico",      "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "NV": {"name": "Nevada",          "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No state income tax."},
    "NY": {"name": "New York",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "High-risk. 183+ days AND maintained permanent place of abode = statutory resident even if domiciled abroad."},
    "OH": {"name": "Ohio",            "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "OK": {"name": "Oklahoma",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "OR": {"name": "Oregon",          "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule; high income tax rate."},
    "PA": {"name": "Pennsylvania",    "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule. Domicile very important."},
    "RI": {"name": "Rhode Island",    "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "SC": {"name": "South Carolina",  "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "SD": {"name": "South Dakota",    "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No state income tax."},
    "TN": {"name": "Tennessee",       "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No earned income tax."},
    "TX": {"name": "Texas",           "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No state income tax. Expat-friendly domicile state."},
    "UT": {"name": "Utah",            "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "VA": {"name": "Virginia",        "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "High-risk. Very aggressive domicile rules. Military exemptions may apply."},
    "VT": {"name": "Vermont",         "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "WA": {"name": "Washington",      "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No state income tax (no capital gains tax for most)."},
    "WI": {"name": "Wisconsin",       "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "WV": {"name": "West Virginia",   "has_income_tax": True,  "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "183-day rule."},
    "WY": {"name": "Wyoming",         "has_income_tax": False, "safe_harbor_days": 183, "statutory_resident_days": 183, "notes": "No state income tax."},
}

HIGH_RISK_STATES = {"CA", "NY", "NJ", "IL", "MA", "VA"}

NO_INCOME_TAX_STATES = {"AK", "FL", "NH", "NV", "SD", "TN", "TX", "WA", "WY"}

STATES_WITH_ABODE_RULE = {"NY", "CT", "MA", "MD", "NJ"}

CA_SAFE_HARBOR_DAYS = 546  # over 2 consecutive years


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ObligationsRequest(BaseModel):
    state: str = Field(..., min_length=2, max_length=2, description="2-letter state code")
    days_in_state: int = Field(..., ge=0, le=366)
    domicile_state: str = Field(..., min_length=2, max_length=2, description="State of domicile")
    income_source: str = Field(..., description="employment|self_employment|investment|rental")
    moved_abroad_year: int = Field(..., ge=1900, le=2100)
    maintained_home: bool
    driver_license_state: Optional[str] = Field(None, min_length=2, max_length=2)
    voter_reg_state: Optional[str] = Field(None, min_length=2, max_length=2)


class ObligationsResult(BaseModel):
    filing_required: bool
    reason: str
    nexus_type: str  # domicile | statutory_resident | nonresident | none
    safe_harbor_days: int
    days_remaining_safe_harbor: int
    filing_deadline: str
    estimated_form: str
    recommendations: list[str]
    warning_flags: list[str]


class StateInfo(BaseModel):
    code: str
    name: str
    has_income_tax: bool
    safe_harbor_days: int
    statutory_resident_days: int
    notes: str


class DomicileAnalysisRequest(BaseModel):
    original_state: str = Field(..., min_length=2, max_length=2)
    years_abroad: float = Field(..., ge=0)
    maintained_home: bool
    voter_registered_in_state: bool
    driver_license_in_state: bool
    bank_accounts_in_state: bool
    family_in_state: bool
    returned_to_state_days_per_year: int = Field(..., ge=0, le=366)
    intent_to_return: bool
    business_ties_in_state: bool
    vehicle_registered_in_state: bool


class DomicileAnalysisResult(BaseModel):
    domicile_abandoned: bool
    risk_score: int  # 0-100
    factors_for: list[str]
    factors_against: list[str]
    summary: str


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------

def analyze_obligations(req: ObligationsRequest) -> ObligationsResult:
    state = req.state.upper()
    domicile = req.domicile_state.upper()

    state_info = STATE_DATA.get(state)
    if not state_info:
        raise ValueError(f"Unknown state code: {state}")

    recommendations: list[str] = []
    warning_flags: list[str] = []

    # No income tax states
    if not state_info["has_income_tax"]:
        return ObligationsResult(
            filing_required=False,
            reason=f"{state_info['name']} has no state income tax.",
            nexus_type="none",
            safe_harbor_days=state_info["safe_harbor_days"],
            days_remaining_safe_harbor=max(0, state_info["safe_harbor_days"] - req.days_in_state),
            filing_deadline="N/A",
            estimated_form="N/A",
            recommendations=[f"No state income tax filing required for {state_info['name']}."],
            warning_flags=[],
        )

    safe_harbor = state_info["safe_harbor_days"]
    statutory_days = state_info["statutory_resident_days"]
    days_remaining = max(0, safe_harbor - req.days_in_state)

    # Determine nexus type
    nexus_type = "none"
    filing_required = False
    reason = ""

    # Domicile nexus
    if domicile == state:
        nexus_type = "domicile"
        filing_required = True
        reason = f"Your domicile is in {state_info['name']}. Domiciliaries must file regardless of days present."
        recommendations.append("Consider formally establishing domicile in a no-income-tax state before moving abroad.")
        if state in HIGH_RISK_STATES:
            warning_flags.append(f"{state_info['name']} is a high-risk state for expats — domicile is difficult to abandon.")

    # CA special: 546-day safe harbor over 2 years
    elif state == "CA":
        if req.days_in_state > CA_SAFE_HARBOR_DAYS:
            nexus_type = "statutory_resident"
            filing_required = True
            reason = f"CA: Exceeded {CA_SAFE_HARBOR_DAYS}-day safe harbor over 2 consecutive years."
        elif req.days_in_state >= statutory_days and req.maintained_home:
            nexus_type = "statutory_resident"
            filing_required = True
            reason = "CA: 183+ days with maintained California home creates statutory residency."
        elif req.days_in_state > 0:
            nexus_type = "nonresident"
            filing_required = True  # CA taxes nonresident CA-source income
            reason = f"CA nonresident: CA-source income is taxable even as nonresident."
            recommendations.append("File CA Form 540NR as a nonresident for CA-source income only.")
        warning_flags.append("California FTB aggressively audits former residents. Document your departure carefully.")
        recommendations.append("Maintain records proving you were not in CA more than 546 days over any 2 consecutive years.")
        safe_harbor = CA_SAFE_HARBOR_DAYS
        days_remaining = max(0, CA_SAFE_HARBOR_DAYS - req.days_in_state)

    # NY special: 183+ days AND permanent place of abode
    elif state == "NY" and req.days_in_state >= statutory_days and req.maintained_home:
        nexus_type = "statutory_resident"
        filing_required = True
        reason = "NY: 183+ days AND maintained permanent place of abode = statutory resident, even if domiciled abroad."
        warning_flags.append("New York will tax you as a full resident even if domiciled abroad if you have 183+ days AND a NY abode.")
        recommendations.append("If you plan to keep a NY apartment, limit NY days to under 183 per year.")

    # States with abode rule (CT, MA, MD, NJ)
    elif state in STATES_WITH_ABODE_RULE and req.days_in_state >= statutory_days and req.maintained_home:
        nexus_type = "statutory_resident"
        filing_required = True
        reason = f"{state_info['name']}: 183+ days AND maintained home creates statutory residency."
        warning_flags.append(f"{state_info['name']} uses 'permanent place of abode' rule — maintaining a home here is high-risk.")

    # General 183-day rule
    elif req.days_in_state >= statutory_days:
        nexus_type = "statutory_resident"
        filing_required = True
        reason = f"{state_info['name']}: {req.days_in_state} days exceeds {statutory_days}-day statutory residency threshold."

    # Source income (rental/investment/employment) — nonresident filing
    elif req.income_source in ("rental", "employment") and req.days_in_state > 0:
        nexus_type = "nonresident"
        filing_required = True
        reason = f"{state_info['name']}: {req.income_source} income sourced from this state requires nonresident filing."
        recommendations.append(f"File {state_info['name']} nonresident return for state-source income only.")
    else:
        nexus_type = "none"
        filing_required = False
        reason = f"No filing obligation for {state_info['name']}: days below threshold, no domicile, no source income."

    # Warning flags
    if req.driver_license_state == state:
        warning_flags.append(f"Driver's license in {state} creates evidence of residency. Consider updating it.")
    if req.voter_reg_state == state:
        warning_flags.append(f"Voter registration in {state} is a strong domicile indicator. Update if domicile has changed.")
    if req.maintained_home and state in HIGH_RISK_STATES:
        warning_flags.append(f"Maintaining a home in {state_info['name']} is a significant nexus risk.")
    if days_remaining < 30 and days_remaining > 0:
        warning_flags.append(f"Warning: Only {days_remaining} days remaining in safe harbor for {state_info['name']}.")

    # Recommendations
    if not filing_required:
        recommendations.append(f"No state filing required for {state_info['name']} based on current facts.")
    if state in HIGH_RISK_STATES and filing_required:
        recommendations.append("Consult a CPA familiar with this state's aggressive residency rules.")
    if req.income_source == "rental":
        recommendations.append("Rental income from state property is always taxable by that state as source income.")

    # Filing deadline and form
    filing_deadline = "April 15 (same as federal, or state extension)"
    if state == "CA":
        estimated_form = "CA Form 540 (resident) or 540NR (nonresident)"
        filing_deadline = "April 15 (CA allows automatic 6-month extension)"
    elif state == "NY":
        estimated_form = "NY Form IT-201 (resident) or IT-203 (nonresident/part-year)"
    elif nexus_type == "nonresident":
        estimated_form = f"{state_info['name']} Nonresident/Part-Year Resident Return"
    elif filing_required:
        estimated_form = f"{state_info['name']} Resident Income Tax Return"
    else:
        estimated_form = "N/A"

    if not filing_required:
        filing_deadline = "N/A"

    return ObligationsResult(
        filing_required=filing_required,
        reason=reason,
        nexus_type=nexus_type,
        safe_harbor_days=safe_harbor,
        days_remaining_safe_harbor=days_remaining,
        filing_deadline=filing_deadline,
        estimated_form=estimated_form,
        recommendations=recommendations,
        warning_flags=warning_flags,
    )


def list_states() -> list[StateInfo]:
    return [
        StateInfo(
            code=code,
            name=data["name"],
            has_income_tax=data["has_income_tax"],
            safe_harbor_days=data["safe_harbor_days"],
            statutory_resident_days=data["statutory_resident_days"],
            notes=data["notes"],
        )
        for code, data in sorted(STATE_DATA.items())
    ]


def analyze_domicile(req: DomicileAnalysisRequest) -> DomicileAnalysisResult:
    factors_for: list[str] = []    # factors supporting domicile abandonment
    factors_against: list[str] = []  # factors indicating domicile retained

    # Factors FOR abandonment (supporting expat's claim)
    if not req.maintained_home:
        factors_for.append("No home maintained in original state")
    if not req.voter_registered_in_state:
        factors_for.append("Voter registration updated (not in original state)")
    if not req.driver_license_in_state:
        factors_for.append("Driver's license not in original state")
    if req.years_abroad >= 2:
        factors_for.append(f"Extended time abroad ({req.years_abroad:.1f} years)")
    if not req.bank_accounts_in_state:
        factors_for.append("No primary bank accounts in original state")
    if not req.vehicle_registered_in_state:
        factors_for.append("Vehicle not registered in original state")
    if req.returned_to_state_days_per_year < 30:
        factors_for.append(f"Limited return visits ({req.returned_to_state_days_per_year} days/year)")
    if not req.intent_to_return:
        factors_for.append("No expressed intent to return to original state")
    if not req.business_ties_in_state:
        factors_for.append("No active business ties in original state")

    # Factors AGAINST abandonment (risks)
    if req.maintained_home:
        factors_against.append("Home maintained in original state (strong nexus indicator)")
    if req.voter_registered_in_state:
        factors_against.append("Still registered to vote in original state")
    if req.driver_license_in_state:
        factors_against.append("Driver's license still in original state")
    if req.bank_accounts_in_state:
        factors_against.append("Primary bank accounts still in original state")
    if req.family_in_state:
        factors_against.append("Family (spouse/dependents) still in original state")
    if req.returned_to_state_days_per_year >= 60:
        factors_against.append(f"Frequent return visits ({req.returned_to_state_days_per_year} days/year)")
    if req.intent_to_return:
        factors_against.append("Expressed intent to return to original state")
    if req.business_ties_in_state:
        factors_against.append("Active business ties in original state")
    if req.vehicle_registered_in_state:
        factors_against.append("Vehicle still registered in original state")
    if req.years_abroad < 1:
        factors_against.append("Less than 1 year abroad — domicile change not yet clearly established")

    # Risk score (0=fully abandoned, 100=definitely retained)
    risk_points = 0
    weights = {
        "maintained_home": 25,
        "voter_registered": 15,
        "driver_license": 10,
        "bank_accounts": 10,
        "family": 15,
        "frequent_visits": 10,
        "intent_to_return": 10,
        "business_ties": 5,
    }
    if req.maintained_home: risk_points += weights["maintained_home"]
    if req.voter_registered_in_state: risk_points += weights["voter_registered"]
    if req.driver_license_in_state: risk_points += weights["driver_license"]
    if req.bank_accounts_in_state: risk_points += weights["bank_accounts"]
    if req.family_in_state: risk_points += weights["family"]
    if req.returned_to_state_days_per_year >= 60: risk_points += weights["frequent_visits"]
    if req.intent_to_return: risk_points += weights["intent_to_return"]
    if req.business_ties_in_state: risk_points += weights["business_ties"]

    # Additional penalty for CA/NY/VA (aggressive states)
    if req.original_state.upper() in HIGH_RISK_STATES:
        risk_points = min(100, int(risk_points * 1.2))

    risk_score = min(100, risk_points)
    domicile_abandoned = risk_score < 40

    if domicile_abandoned:
        summary = f"Based on {len(factors_for)} supporting factors, domicile appears to be abandoned (risk score: {risk_score}/100). Continue documenting your ties to your new country of residence."
    else:
        summary = f"Domicile may NOT be fully abandoned (risk score: {risk_score}/100). {len(factors_against)} factors indicate retained state ties. Review and address risk factors."

    return DomicileAnalysisResult(
        domicile_abandoned=domicile_abandoned,
        risk_score=risk_score,
        factors_for=factors_for,
        factors_against=factors_against,
        summary=summary,
    )
