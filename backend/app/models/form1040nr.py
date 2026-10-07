"""
Form 1040-NR Non-Resident Alien Tax Return Models
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ResidentStatus(str, Enum):
    """Resident status for tax purposes"""
    NON_RESIDENT = "non_resident"
    DUAL_STATUS = "dual_status"
    RESIDENT = "resident"
    TREATY_RESIDENT = "treaty_resident"


class IncomeType(str, Enum):
    """Type of income for non-resident aliens"""
    ECI = "eci"  # Effectively Connected Income
    FDAP = "fdap"  # Fixed, Determinable, Annual, Periodic
    CAPITAL_GAINS = "capital_gains"
    RENTAL = "rental"
    OTHER = "other"


class WithholdingType(str, Enum):
    """Type of withholding tax"""
    CHAPTER_3 = "chapter_3"  # Non-resident withholding (30%)
    CHAPTER_4 = "chapter_4"  # FATCA withholding
    BACKUP = "backup"  # Backup withholding


class FilingRequirementRequest(BaseModel):
    """Request to determine filing requirement"""
    tax_year: int = Field(..., ge=2020, le=2030)
    days_in_us_current_year: int = Field(..., ge=0, le=366)
    days_in_us_prior_year_1: int = Field(default=0, ge=0, le=366)
    days_in_us_prior_year_2: int = Field(default=0, ge=0, le=366)
    treaty_country: Optional[str] = Field(default=None)
    is_student: bool = Field(default=False)
    is_teacher: bool = Field(default=False)
    has_us_sourced_income: bool = Field(default=False)
    gross_income: Decimal = Field(default=Decimal("0"), ge=0)
    
    @field_validator('treaty_country')
    @classmethod
    def validate_treaty_country(cls, v):
        if v:
            return v.upper()
        return v


class FilingRequirementResponse(BaseModel):
    """Response with filing requirement determination"""
    tax_year: int
    resident_status: ResidentStatus
    must_file: bool
    substantial_presence_days: Decimal
    passes_substantial_presence_test: bool
    treaty_exemption_applies: bool
    filing_deadline: date
    extension_deadline: Optional[date]
    reasoning: str


class IncomeItem(BaseModel):
    """Single income item"""
    description: str
    income_type: IncomeType
    gross_amount: Decimal = Field(..., ge=0)
    us_sourced: bool
    treaty_exempt: bool = Field(default=False)
    treaty_article: Optional[str] = None
    withheld_amount: Decimal = Field(default=Decimal("0"), ge=0)
    withholding_type: Optional[WithholdingType] = None


class IncomeSummaryRequest(BaseModel):
    """Request for income summary calculation"""
    tax_year: int = Field(..., ge=2020, le=2030)
    income_items: List[IncomeItem]
    standard_deduction_claimed: bool = Field(default=True)
    itemized_deductions: Decimal = Field(default=Decimal("0"), ge=0)


class IncomeSummaryResponse(BaseModel):
    """Response with income summary"""
    tax_year: int
    total_eci: Decimal
    total_fdap: Decimal
    total_capital_gains: Decimal
    total_us_sourced: Decimal
    total_foreign_sourced: Decimal
    total_treaty_exempt: Decimal
    taxable_eci: Decimal
    taxable_fdap: Decimal
    standard_deduction: Decimal
    itemized_deductions: Decimal
    total_tax_before_credits: Decimal
    effective_rate: Decimal


class WithholdingCreditRequest(BaseModel):
    """Request for withholding credit calculation"""
    tax_year: int = Field(..., ge=2020, le=2030)
    chapter_3_withheld: Decimal = Field(default=Decimal("0"), ge=0)
    chapter_4_withheld: Decimal = Field(default=Decimal("0"), ge=0)
    backup_withheld: Decimal = Field(default=Decimal("0"), ge=0)
    estimated_tax_paid: Decimal = Field(default=Decimal("0"), ge=0)
    prior_year_overpayment: Decimal = Field(default=Decimal("0"), ge=0)


class WithholdingCreditResponse(BaseModel):
    """Response with withholding credit"""
    tax_year: int
    total_chapter_3_credit: Decimal
    total_chapter_4_credit: Decimal
    total_backup_credit: Decimal
    total_estimated_tax: Decimal
    total_credits: Decimal
    refundable_amount: Decimal
    non_refundable_amount: Decimal


class PenaltyCalculatorRequest(BaseModel):
    """Request for penalty calculation"""
    tax_year: int = Field(..., ge=2020, le=2030)
    filing_deadline: date
    actual_filing_date: Optional[date] = None
    tax_owed: Decimal = Field(..., ge=0)
    was_extension_filed: bool = Field(default=False)
    reasonable_cause: bool = Field(default=False)


class PenaltyCalculatorResponse(BaseModel):
    """Response with penalty calculation"""
    tax_year: int
    days_late: int
    late_filing_penalty: Decimal
    late_payment_penalty: Decimal
    interest_charges: Decimal
    total_penalties: Decimal
    minimum_penalty_applies: bool
    minimum_penalty_amount: Decimal
    waived_due_to_reasonable_cause: bool
    total_amount_due: Decimal


class Form1040NROverview(BaseModel):
    """Overview of all Form 1040-NR calculations"""
    tax_year: int
    resident_status: Optional[ResidentStatus] = None
    must_file: Optional[bool] = None
    total_eci: Optional[Decimal] = None
    total_fdap: Optional[Decimal] = None
    total_us_sourced: Optional[Decimal] = None
    total_treaty_exempt: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    total_credits: Optional[Decimal] = None
    refund_or_owed: Optional[Decimal] = None
    penalties: Optional[Decimal] = None
    filing_deadline: Optional[date] = None
    created_at: datetime
    updated_at: datetime
