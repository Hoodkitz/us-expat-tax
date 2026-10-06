"""
Schedule SE Self-Employment Tax Calculation Module.
IRC §1401 (Self-Employment Tax) and IRC §1402 (Definitions).
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


# 2025 Tax Constants
SOCIAL_SECURITY_BASE_2025 = 168_600.0
ADDITIONAL_MEDICARE_THRESHOLD_SINGLE = 200_000.0
ADDITIONAL_MEDICARE_THRESHOLD_MARRIED = 250_000.0
SE_TAX_RATE = 0.153  # 15.3% (12.4% SS + 2.9% Medicare)
MEDICARE_ONLY_RATE = 0.029  # 2.9% Medicare only (above SS base)
ADDITIONAL_MEDICARE_RATE = 0.009  # 0.9% Additional Medicare
NET_EARNINGS_FACTOR = 0.9235  # 92.35% of net self-employment income


FilingStatus = Literal["single", "married_filing_jointly", "married_filing_separately"]


class ScheduleSEInput(BaseModel):
    """Input for Schedule SE calculation."""
    net_self_employment_income: float = Field(..., description="Net profit from self-employment (Schedule C/F)")
    filing_status: FilingStatus = Field(default="single")
    tax_year: int = Field(default=2025, ge=2025, le=2025)  # Only 2025 supported for now


class ScheduleSEResult(BaseModel):
    """Schedule SE calculation result."""
    net_self_employment_income: float
    net_earnings_subject_to_se_tax: float  # 92.35% of net income
    social_security_tax: float
    medicare_tax: float
    additional_medicare_tax: float
    total_self_employment_tax: float
    deductible_se_tax: float  # 50% of SE tax for 1040 Schedule 1


def calculate_schedule_se(input_data: ScheduleSEInput) -> ScheduleSEResult:
    """
    Calculate self-employment tax per IRC §1401.
    
    Steps:
    1. Net earnings = 92.35% of net self-employment income (IRC §1401(b))
    2. Social Security tax = 12.4% on earnings up to $168,600 (2025)
    3. Medicare tax = 2.9% on all net earnings
    4. Additional Medicare = 0.9% on earnings above threshold ($200k single, $250k married)
    5. Deductible SE tax = 50% of total SE tax (IRC §164(f))
    """
    net_income = input_data.net_self_employment_income
    
    # Handle zero or negative income
    if net_income <= 0:
        return ScheduleSEResult(
            net_self_employment_income=net_income,
            net_earnings_subject_to_se_tax=0.0,
            social_security_tax=0.0,
            medicare_tax=0.0,
            additional_medicare_tax=0.0,
            total_self_employment_tax=0.0,
            deductible_se_tax=0.0,
        )
    
    # Step 1: Calculate net earnings (92.35% of net income)
    net_earnings = net_income * NET_EARNINGS_FACTOR
    
    # Step 2: Social Security tax (12.4% up to base)
    ss_taxable = min(net_earnings, SOCIAL_SECURITY_BASE_2025)
    social_security_tax = ss_taxable * 0.124
    
    # Step 3: Medicare tax (2.9% on all earnings)
    medicare_tax = net_earnings * MEDICARE_ONLY_RATE
    
    # Step 4: Additional Medicare tax (0.9% above threshold)
    threshold = (
        ADDITIONAL_MEDICARE_THRESHOLD_MARRIED
        if input_data.filing_status == "married_filing_jointly"
        else ADDITIONAL_MEDICARE_THRESHOLD_SINGLE
    )
    additional_medicare_base = max(0.0, net_earnings - threshold)
    additional_medicare_tax = additional_medicare_base * ADDITIONAL_MEDICARE_RATE
    
    # Step 5: Total SE tax and deduction
    total_se_tax = social_security_tax + medicare_tax + additional_medicare_tax
    deductible_se_tax = total_se_tax * 0.5
    
    return ScheduleSEResult(
        net_self_employment_income=net_income,
        net_earnings_subject_to_se_tax=round(net_earnings, 2),
        social_security_tax=round(social_security_tax, 2),
        medicare_tax=round(medicare_tax, 2),
        additional_medicare_tax=round(additional_medicare_tax, 2),
        total_self_employment_tax=round(total_se_tax, 2),
        deductible_se_tax=round(deductible_se_tax, 2),
    )


def calculate_se_deduction(total_self_employment_tax: float) -> float:
    """
    Calculate the deductible portion of self-employment tax (IRC §164(f)).
    This is exactly 50% of the total SE tax.
    """
    return round(total_self_employment_tax * 0.5, 2)


def get_schedule_se_overview() -> dict:
    """
    Return a summary of Schedule SE law and calculation rules.
    """
    return {
        "title": "Schedule SE: Self-Employment Tax",
        "statutory_authority": [
            "IRC §1401 - Tax on self-employment income",
            "IRC §1402 - Definitions of self-employment income",
            "IRC §164(f) - Deduction for one-half of self-employment tax",
        ],
        "tax_year": 2025,
        "rates": {
            "social_security": {
                "rate": "12.4%",
                "base": f"${SOCIAL_SECURITY_BASE_2025:,.0f}",
                "description": "OASDI (Old-Age, Survivors, and Disability Insurance)",
            },
            "medicare": {
                "rate": "2.9%",
                "base": "Unlimited",
                "description": "Hospital Insurance (HI) on all net earnings",
            },
            "additional_medicare": {
                "rate": "0.9%",
                "threshold_single": f"${ADDITIONAL_MEDICARE_THRESHOLD_SINGLE:,.0f}",
                "threshold_married_jointly": f"${ADDITIONAL_MEDICARE_THRESHOLD_MARRIED:,.0f}",
                "description": "Additional Medicare Tax (ACA provision)",
            },
        },
        "calculation_steps": [
            "1. Calculate net earnings: 92.35% of net self-employment income (IRC §1401(b))",
            "2. Social Security tax: 12.4% on earnings up to $168,600",
            "3. Medicare tax: 2.9% on all net earnings",
            "4. Additional Medicare: 0.9% on earnings above threshold ($200k/$250k)",
            "5. Deductible SE tax: 50% of total SE tax (Schedule 1, Line 15)",
        ],
        "notes": [
            "Self-employed individuals pay both employer and employee portions of FICA taxes",
            "The 92.35% factor approximates the employer deduction for payroll taxes",
            "Additional Medicare Tax applies to high earners (ACA §9015)",
            "The deductible portion reduces adjusted gross income (AGI) on Form 1040",
        ],
    }
