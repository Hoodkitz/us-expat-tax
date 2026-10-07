"""
Form 1040-NR Non-Resident Alien Tax Return Router
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.form1040nr import (
    FilingRequirementRequest,
    FilingRequirementResponse,
    IncomeSummaryRequest,
    IncomeSummaryResponse,
    WithholdingCreditRequest,
    WithholdingCreditResponse,
    PenaltyCalculatorRequest,
    PenaltyCalculatorResponse,
    Form1040NROverview,
    ResidentStatus,
    IncomeType,
    WithholdingType,
)
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/v1/form1040nr", tags=["form1040nr"])


# Tax brackets for non-resident aliens (2024, single filer rates)
NR_TAX_BRACKETS_2024 = [
    (Decimal("11600"), Decimal("0.10")),
    (Decimal("47150"), Decimal("0.12")),
    (Decimal("100525"), Decimal("0.22")),
    (Decimal("191950"), Decimal("0.24")),
    (Decimal("243725"), Decimal("0.32")),
    (Decimal("609350"), Decimal("0.35")),
    (float('inf'), Decimal("0.37")),
]

STANDARD_DEDUCTION_2024 = Decimal("14600")
FDAP_RATE = Decimal("0.30")  # 30% flat rate on FDAP income
INTEREST_RATE_ANNUAL = Decimal("0.08")  # 8% annual interest


def calculate_substantial_presence_days(
    days_current: int, days_prior_1: int, days_prior_2: int
) -> Decimal:
    """
    Calculate substantial presence test days.
    Formula: Current year + (1/3 * prior year) + (1/6 * year before)
    """
    return Decimal(days_current) + (Decimal(days_prior_1) / 3) + (Decimal(days_prior_2) / 6)


def calculate_progressive_tax(income: Decimal) -> Decimal:
    """Calculate tax using progressive brackets"""
    if income <= 0:
        return Decimal("0")
    
    tax = Decimal("0")
    prev_limit = Decimal("0")
    
    for limit, rate in NR_TAX_BRACKETS_2024:
        if income <= prev_limit:
            break
        
        taxable_in_bracket = min(income, Decimal(str(limit))) - prev_limit
        tax += taxable_in_bracket * rate
        prev_limit = Decimal(str(limit))
    
    return tax.quantize(Decimal("0.01"))


@router.post("/filing-requirement", response_model=FilingRequirementResponse)
def determine_filing_requirement(
    request: FilingRequirementRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Determine if non-resident alien must file Form 1040-NR.
    
    Tests:
    1. Substantial Presence Test (183 days weighted)
    2. Treaty tiebreaker
    3. Filing thresholds
    """
    # Calculate substantial presence
    spt_days = calculate_substantial_presence_days(
        request.days_in_us_current_year,
        request.days_in_us_prior_year_1,
        request.days_in_us_prior_year_2,
    )
    
    passes_spt = spt_days >= 183
    
    # Determine resident status
    if passes_spt and request.treaty_country:
        # Treaty tiebreaker - closer connection to treaty country
        resident_status = ResidentStatus.TREATY_RESIDENT
        treaty_exemption = True
    elif passes_spt:
        resident_status = ResidentStatus.RESIDENT
        treaty_exemption = False
    elif request.days_in_us_current_year > 0 and request.days_in_us_current_year < 183:
        # Dual-status if present part of year
        resident_status = ResidentStatus.DUAL_STATUS
        treaty_exemption = False
    else:
        resident_status = ResidentStatus.NON_RESIDENT
        treaty_exemption = False
    
    # Filing requirement logic
    must_file = False
    reasoning_parts = []
    
    if request.has_us_sourced_income:
        must_file = True
        reasoning_parts.append("US-sourced income requires filing")
    
    # Standard deduction for 2024
    filing_threshold = STANDARD_DEDUCTION_2024
    
    if request.gross_income > filing_threshold:
        must_file = True
        reasoning_parts.append(f"Gross income ${request.gross_income} exceeds threshold ${filing_threshold}")
    
    if request.is_student and request.treaty_country:
        reasoning_parts.append(f"Student from treaty country ({request.treaty_country}) may have exemptions")
    
    if request.is_teacher and request.treaty_country:
        reasoning_parts.append(f"Teacher from treaty country ({request.treaty_country}) may have exemptions")
    
    # Filing deadlines
    if resident_status == ResidentStatus.NON_RESIDENT:
        # Non-residents: June 15
        filing_deadline = date(request.tax_year + 1, 6, 15)
        extension_deadline = date(request.tax_year + 1, 10, 15)
    else:
        # Dual-status/resident: April 15
        filing_deadline = date(request.tax_year + 1, 4, 15)
        extension_deadline = date(request.tax_year + 1, 10, 15)
    
    reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No filing requirement"
    
    return FilingRequirementResponse(
        tax_year=request.tax_year,
        resident_status=resident_status,
        must_file=must_file,
        substantial_presence_days=spt_days,
        passes_substantial_presence_test=passes_spt,
        treaty_exemption_applies=treaty_exemption,
        filing_deadline=filing_deadline,
        extension_deadline=extension_deadline,
        reasoning=reasoning,
    )


@router.post("/income-summary", response_model=IncomeSummaryResponse)
def calculate_income_summary(
    request: IncomeSummaryRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Calculate income summary for Form 1040-NR.
    
    Separates:
    - ECI (Effectively Connected Income) - taxed at graduated rates
    - FDAP (Fixed, Determinable, Annual, Periodic) - taxed at flat 30%
    - US-sourced vs foreign-sourced
    - Treaty-exempt income
    """
    total_eci = Decimal("0")
    total_fdap = Decimal("0")
    total_capital_gains = Decimal("0")
    total_us_sourced = Decimal("0")
    total_foreign_sourced = Decimal("0")
    total_treaty_exempt = Decimal("0")
    
    for item in request.income_items:
        if item.treaty_exempt:
            total_treaty_exempt += item.gross_amount
            continue
        
        if item.us_sourced:
            total_us_sourced += item.gross_amount
        else:
            total_foreign_sourced += item.gross_amount
        
        if item.income_type == IncomeType.ECI:
            total_eci += item.gross_amount
        elif item.income_type == IncomeType.FDAP:
            total_fdap += item.gross_amount
        elif item.income_type == IncomeType.CAPITAL_GAINS:
            total_capital_gains += item.gross_amount
    
    # Calculate deductions (only for ECI)
    if request.standard_deduction_claimed:
        deduction = STANDARD_DEDUCTION_2024
        itemized = Decimal("0")
    else:
        deduction = request.itemized_deductions
        itemized = request.itemized_deductions
    
    # Taxable ECI after deductions
    taxable_eci = max(total_eci - deduction, Decimal("0"))
    
    # FDAP is taxed at flat 30% (no deductions)
    taxable_fdap = total_fdap
    
    # Calculate tax
    eci_tax = calculate_progressive_tax(taxable_eci)
    fdap_tax = taxable_fdap * FDAP_RATE
    capital_gains_tax = total_capital_gains * Decimal("0.15")  # Simplified 15% rate
    
    total_tax = eci_tax + fdap_tax + capital_gains_tax
    
    # Effective rate
    total_income = total_eci + total_fdap + total_capital_gains
    effective_rate = (total_tax / total_income * 100) if total_income > 0 else Decimal("0")
    
    return IncomeSummaryResponse(
        tax_year=request.tax_year,
        total_eci=total_eci,
        total_fdap=total_fdap,
        total_capital_gains=total_capital_gains,
        total_us_sourced=total_us_sourced,
        total_foreign_sourced=total_foreign_sourced,
        total_treaty_exempt=total_treaty_exempt,
        taxable_eci=taxable_eci,
        taxable_fdap=taxable_fdap,
        standard_deduction=STANDARD_DEDUCTION_2024 if request.standard_deduction_claimed else Decimal("0"),
        itemized_deductions=itemized,
        total_tax_before_credits=total_tax,
        effective_rate=effective_rate.quantize(Decimal("0.01")),
    )


@router.post("/withholding-credit", response_model=WithholdingCreditResponse)
def calculate_withholding_credit(
    request: WithholdingCreditRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Calculate withholding tax credits for Form 1040-NR.
    
    Includes:
    - Chapter 3 withholding (30% on FDAP)
    - Chapter 4 withholding (FATCA)
    - Backup withholding
    - Estimated tax payments
    """
    # All withholding is creditable
    total_chapter_3 = request.chapter_3_withheld
    total_chapter_4 = request.chapter_4_withheld
    total_backup = request.backup_withheld
    total_estimated = request.estimated_tax_paid + request.prior_year_overpayment
    
    total_credits = (
        total_chapter_3 + total_chapter_4 + total_backup + total_estimated
    )
    
    # Chapter 3 and estimated tax are refundable
    refundable = total_chapter_3 + total_estimated
    
    # Chapter 4 and backup are generally refundable too
    refundable += total_chapter_4 + total_backup
    
    non_refundable = Decimal("0")  # For NR aliens, most credits are refundable
    
    return WithholdingCreditResponse(
        tax_year=request.tax_year,
        total_chapter_3_credit=total_chapter_3,
        total_chapter_4_credit=total_chapter_4,
        total_backup_credit=total_backup,
        total_estimated_tax=total_estimated,
        total_credits=total_credits,
        refundable_amount=refundable,
        non_refundable_amount=non_refundable,
    )


@router.post("/penalty-calculator", response_model=PenaltyCalculatorResponse)
def calculate_penalties(
    request: PenaltyCalculatorRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Calculate late filing and payment penalties per §6072.
    
    Penalties:
    - Late filing: 5% per month (max 25%)
    - Late payment: 0.5% per month (max 25%)
    - Minimum penalty: $200 or 100% of tax (whichever is less)
    - Interest: 8% annual
    """
    if request.actual_filing_date is None:
        actual_filing_date = date.today()
    else:
        actual_filing_date = request.actual_filing_date
    
    # Calculate days late
    if actual_filing_date <= request.filing_deadline:
        days_late = 0
    else:
        days_late = (actual_filing_date - request.filing_deadline).days
    
    # Adjust for extension
    if request.was_extension_filed and days_late > 0:
        extension_deadline = request.filing_deadline + timedelta(days=120)
        days_late = max(0, (actual_filing_date - extension_deadline).days)
    
    # Calculate penalties
    if days_late == 0:
        late_filing_penalty = Decimal("0")
        late_payment_penalty = Decimal("0")
        interest_charges = Decimal("0")
    else:
        # Late filing penalty: 5% per month, max 25%
        months_late_filing = (days_late + 29) // 30  # Round up
        filing_penalty_rate = min(Decimal("0.05") * months_late_filing, Decimal("0.25"))
        late_filing_penalty = request.tax_owed * filing_penalty_rate
        
        # Late payment penalty: 0.5% per month, max 25%
        months_late_payment = (days_late + 29) // 30
        payment_penalty_rate = min(Decimal("0.005") * months_late_payment, Decimal("0.25"))
        late_payment_penalty = request.tax_owed * payment_penalty_rate
        
        # Interest charges: 8% annual
        years_late = Decimal(days_late) / Decimal("365")
        interest_charges = request.tax_owed * INTEREST_RATE_ANNUAL * years_late
    
    # Minimum penalty
    minimum_penalty = min(Decimal("200"), request.tax_owed)
    minimum_penalty_applies = False
    
    if days_late > 60 and (late_filing_penalty + late_payment_penalty) < minimum_penalty:
        late_filing_penalty = minimum_penalty
        minimum_penalty_applies = True
    
    total_penalties = late_filing_penalty + late_payment_penalty + interest_charges
    
    # Reasonable cause waiver
    waived = False
    if request.reasonable_cause and total_penalties > 0:
        late_filing_penalty = Decimal("0")
        late_payment_penalty = Decimal("0")
        total_penalties = interest_charges  # Interest is never waived
        waived = True
    
    total_amount_due = request.tax_owed + total_penalties
    
    return PenaltyCalculatorResponse(
        tax_year=request.tax_year,
        days_late=days_late,
        late_filing_penalty=late_filing_penalty.quantize(Decimal("0.01")),
        late_payment_penalty=late_payment_penalty.quantize(Decimal("0.01")),
        interest_charges=interest_charges.quantize(Decimal("0.01")),
        total_penalties=total_penalties.quantize(Decimal("0.01")),
        minimum_penalty_applies=minimum_penalty_applies,
        minimum_penalty_amount=minimum_penalty,
        waived_due_to_reasonable_cause=waived,
        total_amount_due=total_amount_due.quantize(Decimal("0.01")),
    )


@router.get("/overview", response_model=Form1040NROverview)
def get_overview(
    tax_year: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Get overview of Form 1040-NR calculations for a tax year.
    
    This is a simplified overview - in production this would fetch
    from database records.
    """
    return Form1040NROverview(
        tax_year=tax_year,
        resident_status=None,
        must_file=None,
        total_eci=None,
        total_fdap=None,
        total_us_sourced=None,
        total_treaty_exempt=None,
        total_tax=None,
        total_credits=None,
        refund_or_owed=None,
        penalties=None,
        filing_deadline=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
