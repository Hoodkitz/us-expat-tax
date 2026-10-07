"""
Schedule A (Itemized Deductions) Calculation Module.
IRC §63 (Taxable income defined), IRC §67 (2% floor), IRC §68 (Overall limitation).
2025 tax year rules.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# 2025 Tax Constants
MEDICAL_EXPENSE_AGI_FLOOR = 0.075  # 7.5% of AGI
SALT_CAP = 10_000.0  # $10,000 cap ($5,000 if MFS)
SALT_CAP_MFS = 5_000.0  # $5,000 cap for married filing separately
MORTGAGE_INTEREST_DEBT_CAP = 750_000.0  # $750k debt limit (post-2017)
CHARITABLE_CASH_AGI_LIMIT = 0.60  # 60% of AGI for cash contributions

FilingStatus = Literal["single", "married_filing_jointly", "married_filing_separately"]


class ScheduleAInput(BaseModel):
    """Input for Schedule A calculation."""
    adjusted_gross_income: float = Field(..., description="Adjusted Gross Income (AGI)")
    medical_expenses: float = Field(default=0.0, description="Total medical expenses")
    state_local_taxes: float = Field(default=0.0, description="State and local taxes paid (SALT)")
    mortgage_interest: float = Field(default=0.0, description="Mortgage interest paid")
    mortgage_debt: float = Field(default=0.0, description="Total mortgage debt principal")
    charitable_contributions: float = Field(default=0.0, description="Charitable cash contributions")
    casualty_theft_losses: float = Field(default=0.0, description="Casualty/theft losses (federal disasters only)")
    filing_status: FilingStatus = Field(default="single", description="Tax filing status")


class ScheduleAResult(BaseModel):
    """Schedule A calculation result."""
    adjusted_gross_income: float
    medical_expenses_deductible: float
    salt_deductible: float
    mortgage_interest_deductible: float
    charitable_contributions_deductible: float
    casualty_theft_losses_deductible: float
    total_itemized_deductions: float
    standard_deduction: float
    recommended_deduction: float
    use_itemized: bool


# 2025 Standard Deduction amounts
STANDARD_DEDUCTION_2025: dict[str, float] = {
    "single": 15_000.0,
    "married_filing_jointly": 30_000.0,
    "married_filing_separately": 15_000.0,
}


def calculate_schedule_a(input_data: ScheduleAInput) -> ScheduleAResult:
    """
    Calculate Schedule A itemized deductions for 2025.

    Rules:
    1. Medical expenses: Only amount exceeding 7.5% of AGI is deductible
    2. SALT: Capped at $10,000 ($5,000 if married filing separately)
    3. Mortgage interest: Deductible on up to $750,000 of debt (post-2017)
    4. Charitable contributions: Up to 60% of AGI for cash contributions
    5. Casualty/theft losses: Only federally declared disasters (no limitation %)
    """
    agi = input_data.adjusted_gross_income

    # 1. Medical expenses: amount over 7.5% AGI
    medical_floor = agi * MEDICAL_EXPENSE_AGI_FLOOR
    medical_deductible = max(0.0, input_data.medical_expenses - medical_floor)

    # 2. SALT cap
    salt_cap = SALT_CAP_MFS if input_data.filing_status == "married_filing_separately" else SALT_CAP
    salt_deductible = min(input_data.state_local_taxes, salt_cap)

    # 3. Mortgage interest: deductible on up to $750k debt
    if input_data.mortgage_debt > 0 and input_data.mortgage_debt <= MORTGAGE_INTEREST_DEBT_CAP:
        mortgage_deductible = input_data.mortgage_interest
    elif input_data.mortgage_debt > MORTGAGE_INTEREST_DEBT_CAP:
        # Prorate: only interest on first $750k is deductible
        ratio = MORTGAGE_INTEREST_DEBT_CAP / input_data.mortgage_debt
        mortgage_deductible = input_data.mortgage_interest * ratio
    else:
        mortgage_deductible = input_data.mortgage_interest

    # 4. Charitable contributions: up to 60% of AGI
    charitable_limit = agi * CHARITABLE_CASH_AGI_LIMIT
    charitable_deductible = min(input_data.charitable_contributions, charitable_limit)

    # 5. Casualty/theft losses: fully deductible (federal disasters only)
    casualty_deductible = input_data.casualty_theft_losses

    # Total itemized deductions
    total_itemized = (
        medical_deductible
        + salt_deductible
        + mortgage_deductible
        + charitable_deductible
        + casualty_deductible
    )

    # Standard deduction for 2025
    standard = STANDARD_DEDUCTION_2025.get(input_data.filing_status, 15_000.0)

    # Recommend the larger of itemized vs standard
    use_itemized = total_itemized > standard
    recommended = max(total_itemized, standard)

    return ScheduleAResult(
        adjusted_gross_income=agi,
        medical_expenses_deductible=round(medical_deductible, 2),
        salt_deductible=round(salt_deductible, 2),
        mortgage_interest_deductible=round(mortgage_deductible, 2),
        charitable_contributions_deductible=round(charitable_deductible, 2),
        casualty_theft_losses_deductible=round(casualty_deductible, 2),
        total_itemized_deductions=round(total_itemized, 2),
        standard_deduction=standard,
        recommended_deduction=round(recommended, 2),
        use_itemized=use_itemized,
    )


def get_schedule_a_overview() -> dict:
    """
    Return a summary of Schedule A law and calculation rules.
    """
    return {
        "title": "Schedule A: Itemized Deductions",
        "statutory_authority": [
            "IRC §63 - Taxable income defined",
            "IRC §67 - 2% floor on miscellaneous itemized deductions",
            "IRC §68 - Overall limitation on itemized deductions",
            "IRC §213 - Medical and dental expenses",
            "IRC §164 - Taxes (SALT cap)",
            "IRC §163(h) - Mortgage interest deduction",
            "IRC §170 - Charitable contributions",
            "IRC §165 - Casualty and theft losses",
        ],
        "tax_year": 2025,
        "deduction_rules": {
            "medical_expenses": {
                "floor": "7.5% of AGI",
                "description": "Only medical expenses exceeding 7.5% of AGI are deductible",
            },
            "salt": {
                "cap": f"${SALT_CAP:,.0f}",
                "cap_mfs": f"${SALT_CAP_MFS:,.0f}",
                "description": "State and local taxes capped at $10,000 ($5,000 if MFS)",
            },
            "mortgage_interest": {
                "debt_cap": f"${MORTGAGE_INTEREST_DEBT_CAP:,.0f}",
                "description": "Interest deductible on up to $750,000 of mortgage debt",
            },
            "charitable_contributions": {
                "agi_limit": "60%",
                "description": "Cash contributions deductible up to 60% of AGI",
            },
            "casualty_theft_losses": {
                "description": "Only losses from federally declared disasters are deductible",
            },
        },
        "standard_deduction_2025": {
            "single": f"${STANDARD_DEDUCTION_2025['single']:,.0f}",
            "married_filing_jointly": f"${STANDARD_DEDUCTION_2025['married_filing_jointly']:,.0f}",
            "married_filing_separately": f"${STANDARD_DEDUCTION_2025['married_filing_separately']:,.0f}",
        },
        "calculation_steps": [
            "1. Medical expenses: Subtract 7.5% of AGI from total medical expenses",
            "2. SALT: Apply $10,000 cap ($5,000 if MFS)",
            "3. Mortgage interest: Prorate if debt exceeds $750,000",
            "4. Charitable contributions: Apply 60% of AGI limit",
            "5. Casualty/theft losses: Include if federally declared disaster",
            "6. Sum all deductions and compare to standard deduction",
        ],
        "notes": [
            "Taxpayers should itemize only if total itemized deductions exceed the standard deduction",
            "The SALT cap was introduced by the Tax Cuts and Jobs Act of 2017",
            "Medical expense threshold was temporarily lowered to 7.5% for all taxpayers in 2023+",
            "Casualty losses are now only deductible for federally declared disasters",
        ],
    }