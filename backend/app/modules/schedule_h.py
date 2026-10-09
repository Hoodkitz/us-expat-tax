"""
Schedule H (Form 1040) — Household Employment Taxes.

Schedule H is used by U.S. taxpayers to report household employment taxes
for workers such as nannies, housekeepers, and caregivers.

Key concepts:
- Cash wages threshold: $2,800 (2025) — required if total cash wages paid
  to any one household employee exceed this amount
- Social Security tax: 12.4% on wages up to the SS wage base ($176,100 in 2025)
- Medicare tax: 2.9% on all wages
- Additional Medicare tax: 0.9% on wages over $200,000
- Employer may elect to pay the employee's share (optional)
- Total household employment tax = SS + Medicare + Additional Medicare
- Credit reduction states increase SS rate (not applicable here)

Source: IRS Schedule H (Form 1040) Instructions, tax year 2025.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants — IRS 2025
# ---------------------------------------------------------------------------

# Cash wages filing threshold (per household employee)
# 2025: $2,800 (2024: $2,700)
CASH_WAGES_THRESHOLD = 2_800.0

# Social Security tax rate
SS_RATE = 0.124  # 12.4%

# Medicare tax rate
MEDICARE_RATE = 0.029  # 2.9%

# Additional Medicare tax rate
ADDITIONAL_MEDICARE_RATE = 0.009  # 0.9%

# Social Security wage base (2025)
# 2025: $176,100 (2024: $168,600)
SS_WAGE_BASE_2025 = 176_100.0

# Additional Medicare threshold (all filers — same for single and joint)
ADDITIONAL_MEDICARE_THRESHOLD = 200_000.0

# Employer-elects-to-pay-employee-share rates
# When employer pays employee share: 2.9% SS + 1.45% Medicare
EMPLOYER_PAID_SS_RATE = 0.029  # 2.9%
EMPLOYER_PAID_MEDICARE_RATE = 0.0145  # 1.45%

FilingStatusLiteral = Literal["single", "married_filing_jointly", "married_filing_separately", "head_of_household"]


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class HouseholdEmployeeInput(BaseModel):
    """A single household employee."""
    employee_name: str = Field(..., min_length=1, description="Name of household employee")
    cash_wages: float = Field(..., ge=0, description="Total cash wages paid to this employee in 2025")

class ScheduleHInput(BaseModel):
    """Input for Schedule H calculation."""
    employees: list[HouseholdEmployeeInput] = Field(..., description="List of household employees")
    tax_year: int = Field(2025, ge=2000, le=2099, description="Tax year")
    employer_pays_employee_share: bool = Field(
        False,
        description="Whether employer elects to pay the employee's share of SS/Medicare"
    )

# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class EmployeeTaxResult(BaseModel):
    """Tax breakdown for a single household employee."""
    employee_name: str
    cash_wages: float
    ss_wages: float
    social_security_tax: float
    medicare_tax: float
    additional_medicare_tax: float
    total_employment_tax: float

class ScheduleHResult(BaseModel):
    """Result of Schedule H calculation."""
    filing_required: bool
    threshold: float
    total_cash_wages: float
    total_social_security_tax: float
    total_medicare_tax: float
    total_additional_medicare_tax: float
    total_employment_tax: float
    employees: list[EmployeeTaxResult]
    notes: list[str]

class ScheduleHOverview(BaseModel):
    """Overview of Schedule H requirements."""
    title: str
    filing_requirement: str
    cash_wages_threshold: float
    social_security_rate: float
    social_security_wage_base: float
    medicare_rate: float
    additional_medicare_rate: float
    additional_medicare_threshold: float
    employer_paid_rates: dict[str, float]
    recommendation: str


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def _get_ss_wage_base(tax_year: int) -> float:
    """Return the Social Security wage base for the given tax year."""
    # Known values per IRS
    wage_bases = {
        2020: 137_700.0,
        2021: 142_800.0,
        2022: 147_000.0,
        2023: 160_200.0,
        2024: 168_600.0,
        2025: 176_100.0,
    }
    return wage_bases.get(tax_year, SS_WAGE_BASE_2025)


def calculate_schedule_h(inp: ScheduleHInput) -> ScheduleHResult:
    """
    Calculate Schedule H household employment taxes.

    For each employee:
    - SS tax: 12.4% on wages up to the SS wage base
    - Medicare tax: 2.9% on all wages
    - Additional Medicare: 0.9% on wages over $200,000
    """
    notes: list[str] = []
    threshold = CASH_WAGES_THRESHOLD
    wage_base = _get_ss_wage_base(inp.tax_year)

    # Filing required if any single employee's cash wages exceed threshold
    filing_required = any(emp.cash_wages > threshold for emp in inp.employees)

    total_ss = 0.0
    total_medicare = 0.0
    total_additional = 0.0
    total_wages = 0.0

    results = []
    for emp in inp.employees:
        total_wages += emp.cash_wages
        ss_wages = min(emp.cash_wages, wage_base)

        if inp.employer_pays_employee_share:
            # Employer pays both shares: 2.9% SS + 1.45% Medicare
            ss_tax = ss_wages * EMPLOYER_PAID_SS_RATE
            medicare_tax = emp.cash_wages * EMPLOYER_PAID_MEDICARE_RATE
        else:
            # Standard: 12.4% SS + 2.9% Medicare
            ss_tax = ss_wages * SS_RATE
            medicare_tax = emp.cash_wages * MEDICARE_RATE

        additional_tax = max(0.0, emp.cash_wages - ADDITIONAL_MEDICARE_THRESHOLD) * ADDITIONAL_MEDICARE_RATE

        total_ss += ss_tax
        total_medicare += medicare_tax
        total_additional += additional_tax

        results.append(EmployeeTaxResult(
            employee_name=emp.employee_name,
            cash_wages=emp.cash_wages,
            ss_wages=ss_wages,
            social_security_tax=ss_tax,
            medicare_tax=medicare_tax,
            additional_medicare_tax=additional_tax,
            total_employment_tax=ss_tax + medicare_tax + additional_tax,
        ))

    total_tax = total_ss + total_medicare + total_additional

    if not filing_required:
        notes.append(
            f"No employee's cash wages exceed the ${threshold:,.0f} threshold. "
            "Schedule H is not required."
        )
    else:
        notes.append(
            f"At least one employee's cash wages exceed the ${threshold:,.0f} threshold. "
            "Schedule H is required."
        )

    if inp.employer_pays_employee_share:
        notes.append(
            "Employer has elected to pay the employee's share of Social Security "
            "and Medicare. The employee's share is included in the total."
        )

    if inp.tax_year not in [2020, 2021, 2022, 2023, 2024, 2025]:
        notes.append(
            f"Tax year {inp.tax_year} uses the 2025 SS wage base of ${wage_base:,.0f}. "
            "Verify with IRS for the correct year."
        )

    return ScheduleHResult(
        filing_required=filing_required,
        threshold=threshold,
        total_cash_wages=total_wages,
        total_social_security_tax=total_ss,
        total_medicare_tax=total_medicare,
        total_additional_medicare_tax=total_additional,
        total_employment_tax=total_tax,
        employees=results,
        notes=notes,
    )


def get_overview() -> ScheduleHOverview:
    """Return overview of Schedule H requirements."""
    return ScheduleHOverview(
        title="Schedule H (Form 1040): Household Employment Taxes",
        filing_requirement=(
            "Schedule H is required if you paid cash wages of $2,800 or more in 2025 "
            "to any one household employee. This includes nannies, housekeepers, "
            "caregivers, and other household workers."
        ),
        cash_wages_threshold=CASH_WAGES_THRESHOLD,
        social_security_rate=SS_RATE,
        social_security_wage_base=SS_WAGE_BASE_2025,
        medicare_rate=MEDICARE_RATE,
        additional_medicare_rate=ADDITIONAL_MEDICARE_RATE,
        additional_medicare_threshold=ADDITIONAL_MEDICARE_THRESHOLD,
        employer_paid_rates={
            "social_security": EMPLOYER_PAID_SS_RATE,
            "medicare": EMPLOYER_PAID_MEDICARE_RATE,
        },
        recommendation=(
            "If you employ household workers, you must withhold and pay Social Security "
            "and Medicare taxes if cash wages exceed $2,800 per employee in 2025. "
            "File Schedule H with your Form 1040. Consult a tax professional if you "
            "are unsure about your obligations."
        ),
    )
