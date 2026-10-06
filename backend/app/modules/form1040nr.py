"""
Form 1040-NR: U.S. Nonresident Alien Income Tax Return
Berechnung der Steuerschuld für Nonresidenten.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ===========================================================================
# Pydantic Models
# ===========================================================================

class FilingRequirementRequest(BaseModel):
    tax_year: int = Field(..., ge=2020, le=2030)
    us_source_income: float = Field(..., ge=0)
    effectively_connected_income: float = Field(0, ge=0)
    fdap_income: float = Field(0, ge=0)
    tax_withheld: float = Field(0, ge=0)
    is_treaty_country_resident: bool = False
    treaty_reduced_rate: Optional[float] = None


class FilingRequirementResponse(BaseModel):
    filing_required: bool
    reasons: List[str]
    recommendation: str
    total_us_income: float
    tax_withheld: float
    estimated_tax_due: float


class TaxCalculationRequest(BaseModel):
    tax_year: int = Field(..., ge=2020, le=2030)
    filing_status: str = Field(default="Single")
    # Income
    wages_salaries: float = Field(0, ge=0)
    interest_income: float = Field(0, ge=0)
    dividend_income: float = Field(0, ge=0)
    capital_gains: float = Field(0, ge=0)
    business_income: float = Field(0, ge=0)
    rental_income: float = Field(0, ge=0)
    other_income: float = Field(0, ge=0)
    # Deductions
    itemized_deductions: float = Field(0, ge=0)
    student_loan_interest: float = Field(0, ge=0)
    ira_deduction: float = Field(0, ge=0)
    # Tax credits
    foreign_tax_credit: float = Field(0, ge=0)
    child_tax_credit: float = Field(0, ge=0)
    other_credits: float = Field(0, ge=0)
    # Withholding
    federal_tax_withheld: float = Field(0, ge=0)
    # Treaty
    is_treaty_country_resident: bool = False
    treaty_reduced_rate: Optional[float] = None


class TaxCalculationResponse(BaseModel):
    tax_year: int
    filing_status: str
    # Income breakdown
    total_income: float
    adjusted_gross_income: float
    # Deductions
    total_deductions: float
    taxable_income: float
    # Tax calculation
    tax_before_credits: float
    total_credits: float
    tax_after_credits: float
    # Withholding
    federal_tax_withheld: float
    # Result
    tax_due: float
    refund: float
    effective_tax_rate: float
    marginal_tax_rate: float
    # Breakdown
    income_breakdown: Dict[str, float]
    tax_bracket_breakdown: List[Dict[str, Any]]
    # Treaty info
    treaty_applied: bool
    treaty_rate: Optional[float]


class OverviewResponse(BaseModel):
    form_name: str
    form_title: str
    description: str
    filing_deadline: str
    who_must_file: List[str]
    income_types: List[str]
    tax_rates: Dict[str, str]
    deductions_available: List[str]
    credits_available: List[str]
    special_rules: List[str]


# ===========================================================================
# Tax Brackets 2024 (Single filer - same for Nonresident aliens)
# ===========================================================================

TAX_BRACKETS_2024_SINGLE = [
    (0, 11600, 0.10),
    (11600, 47150, 0.12),
    (47150, 100525, 0.22),
    (100525, 191950, 0.24),
    (191950, 243725, 0.32),
    (243725, 609350, 0.35),
    (609350, float('inf'), 0.37),
]

TAX_BRACKETS_2024_MARRIED = [
    (0, 23200, 0.10),
    (23200, 94300, 0.12),
    (94300, 201050, 0.22),
    (201050, 383900, 0.24),
    (383900, 487450, 0.32),
    (487450, 731200, 0.35),
    (731200, float('inf'), 0.37),
]

# Standard deduction 2024
STANDARD_DEDUCTION_2024_SINGLE = 14600
STANDARD_DEDUCTION_2024_MARRIED = 29200

# FDAP default withholding rate
FDAP_DEFAULT_RATE = 0.30


# ===========================================================================
# Filing Requirement Check
# ===========================================================================

def check_filing_requirement(data: FilingRequirementRequest) -> FilingRequirementResponse:
    """
    Prüft, ob ein Nonresident Alien Form 1040-NR einreichen muss.
    """
    reasons: List[str] = []
    filing_required = False

    total_income = data.us_source_income + data.effectively_connected_income + data.fdap_income

    # ECI always requires filing
    if data.effectively_connected_income > 0:
        filing_required = True
        reasons.append(
            f"Effectively Connected Income (ECI) von ${data.effectively_connected_income:,.2f} "
            "ist steuerpflichtig und erfordert Form 1040-NR."
        )

    # FDAP income above threshold requires filing
    if data.fdap_income > 0:
        if data.tax_withheld < data.fdap_income * FDAP_DEFAULT_RATE:
            filing_required = True
            reasons.append(
                f"FDAP-Einkommen von ${data.fdap_income:,.2f} mit unzureichender "
                f"Quellensteuer (${data.tax_withheld:,.2f} einbehalten)."
            )
        else:
            reasons.append(
                f"FDAP-Einkommen von ${data.fdap_income:,.2f} wurde mit "
                f"${data.tax_withheld:,.2f} Quellensteuer abgegolten."
            )

    # US source income above personal exemption equivalent
    if data.us_source_income > 0 and not filing_required:
        # Nonresident aliens generally cannot claim personal exemptions
        # but may have treaty benefits
        if data.is_treaty_country_resident:
            reasons.append(
                f"US-Quelleinkommen von ${data.us_source_income:,.2f} - "
                "Steuerabkommen kann Befreiung oder Reduzierung vorsehen."
            )
        else:
            filing_required = True
            reasons.append(
                f"US-Quelleinkommen von ${data.us_source_income:,.2f} ohne "
                "Steuerabkommen - Form 1040-NR erforderlich."
            )

    # Estimate tax due
    estimated_tax = 0.0
    if filing_required:
        # Rough estimate: 22% of ECI + 30% of FDAP not covered by withholding
        estimated_tax = (
            data.effectively_connected_income * 0.22
            + max(0, data.fdap_income * FDAP_DEFAULT_RATE - data.tax_withheld)
        )

    if filing_required:
        recommendation = (
            "Sie müssen Form 1040-NR einreichen. "
            "Reichen Sie bis zum 15. April des Folgejahres ein "
            "oder beantragen Sie eine Fristverlängerung mit Form 4868."
        )
    else:
        recommendation = (
            "Keine Pflicht zur Einreichung von Form 1040-NR. "
            "Prüfen Sie jedoch, ob Sie Anspruch auf Rückerstattung "
            "einbehaltener Steuern haben."
        )

    return FilingRequirementResponse(
        filing_required=filing_required,
        reasons=reasons,
        recommendation=recommendation,
        total_us_income=total_income,
        tax_withheld=data.tax_withheld,
        estimated_tax_due=estimated_tax,
    )


# ===========================================================================
# Tax Calculation
# ===========================================================================

def calculate_tax(data: TaxCalculationRequest) -> TaxCalculationResponse:
    """
    Berechnet die Steuerschuld für Nonresident Aliens.
    """
    # Income breakdown
    income_breakdown = {
        "wages_salaries": data.wages_salaries,
        "interest_income": data.interest_income,
        "dividend_income": data.dividend_income,
        "capital_gains": data.capital_gains,
        "business_income": data.business_income,
        "rental_income": data.rental_income,
        "other_income": data.other_income,
    }

    total_income = sum(income_breakdown.values())

    # Nonresident aliens generally cannot claim standard deduction
    # except in limited cases (e.g., students from India under treaty)
    # For simplicity, we use itemized deductions only
    total_deductions = (
        data.itemized_deductions
        + data.student_loan_interest
        + data.ira_deduction
    )

    # AGI = total income - above-the-line deductions
    adjusted_gross_income = total_income - data.student_loan_interest - data.ira_deduction

    # Taxable income
    taxable_income = max(0, adjusted_gross_income - data.itemized_deductions)

    # Select tax brackets based on filing status
    if data.filing_status in ("Married Filing Jointly", "MFJ"):
        brackets = TAX_BRACKETS_2024_MARRIED
    else:
        brackets = TAX_BRACKETS_2024_SINGLE

    # Calculate tax using progressive brackets
    tax_before_credits = 0.0
    tax_bracket_breakdown: List[Dict[str, Any]] = []
    marginal_rate = 0.0

    for lower, upper, rate in brackets:
        if taxable_income > lower:
            taxable_at_rate = min(taxable_income, upper) - lower
            tax_at_rate = taxable_at_rate * rate
            tax_before_credits += tax_at_rate
            marginal_rate = rate
            tax_bracket_breakdown.append({
                "bracket_lower": lower,
                "bracket_upper": upper if upper != float('inf') else None,
                "rate": rate,
                "taxable_amount": taxable_at_rate,
                "tax_amount": tax_at_rate,
            })
        else:
            break

    # Apply treaty rate if applicable
    treaty_applied = False
    treaty_rate = None
    if data.is_treaty_country_resident and data.treaty_reduced_rate is not None:
        treaty_applied = True
        treaty_rate = data.treaty_reduced_rate
        # Recalculate with treaty rate (simplified: flat rate on taxable income)
        tax_before_credits = taxable_income * treaty_rate
        tax_bracket_breakdown = [{
            "bracket_lower": 0,
            "bracket_upper": None,
            "rate": treaty_rate,
            "taxable_amount": taxable_income,
            "tax_amount": tax_before_credits,
        }]
        marginal_rate = treaty_rate

    # Total credits
    total_credits = (
        data.foreign_tax_credit
        + data.child_tax_credit
        + data.other_credits
    )

    # Tax after credits
    tax_after_credits = max(0, tax_before_credits - total_credits)

    # Withholding
    federal_tax_withheld = data.federal_tax_withheld

    # Tax due or refund
    tax_due = max(0, tax_after_credits - federal_tax_withheld)
    refund = max(0, federal_tax_withheld - tax_after_credits)

    # Effective tax rate
    effective_tax_rate = (tax_after_credits / total_income * 100) if total_income > 0 else 0.0

    return TaxCalculationResponse(
        tax_year=data.tax_year,
        filing_status=data.filing_status,
        total_income=total_income,
        adjusted_gross_income=adjusted_gross_income,
        total_deductions=total_deductions,
        taxable_income=taxable_income,
        tax_before_credits=tax_before_credits,
        total_credits=total_credits,
        tax_after_credits=tax_after_credits,
        federal_tax_withheld=federal_tax_withheld,
        tax_due=tax_due,
        refund=refund,
        effective_tax_rate=round(effective_tax_rate, 2),
        marginal_tax_rate=marginal_rate,
        income_breakdown=income_breakdown,
        tax_bracket_breakdown=tax_bracket_breakdown,
        treaty_applied=treaty_applied,
        treaty_rate=treaty_rate,
    )


# ===========================================================================
# Overview
# ===========================================================================

def get_overview() -> OverviewResponse:
    """
    Gibt eine Übersicht über Form 1040-NR zurück.
    """
    return OverviewResponse(
        form_name="Form 1040-NR",
        form_title="U.S. Nonresident Alien Income Tax Return",
        description=(
            "Form 1040-NR ist die Steuererklärung für Nonresident Aliens, "
            "die in den USA steuerpflichtiges Einkommen erzielen. "
            "Es wird verwendet, um Einkommen aus US-Quellen zu melden "
            "und die Steuerschuld zu berechnen."
        ),
        filing_deadline="15. April des Folgejahres (oder 15. Juni für Ausländer im Ausland)",
        who_must_file=[
            "Nonresident Aliens mit Effectively Connected Income (ECI)",
            "Nonresident Aliens mit FDAP-Einkommen ohne ausreichende Quellensteuer",
            "Nonresident Aliens mit Anspruch auf Rückerstattung",
            "Nonresident Aliens mit Kapitalerträgen aus US-Quellen",
        ],
        income_types=[
            "Wages, salaries, tips (Löhne, Gehälter, Trinkgelder)",
            "Interest income (Zinseinkommen)",
            "Dividend income (Dividendeneinkommen)",
            "Capital gains (Kapitalerträge)",
            "Business income (Gewerbeeinkommen)",
            "Rental income (Mieteinkommen)",
            "Other income (sonstiges Einkommen)",
        ],
        tax_rates={
            "ECI": "Progressiver Tarif (10% - 37%)",
            "FDAP": "30% Quellensteuer (oder niedriger durch Abkommen)",
            "Capital Gains": "0%, 15% oder 20% je nach Einkommen",
        },
        deductions_available=[
            "Itemized deductions (Einzelabzüge)",
            "Student loan interest (Studiokreditzinsen)",
            "IRA deduction (IRA-Einzahlungen)",
            "State and local taxes (Bundes- und Gemeindeuern)",
            "Charitable contributions (Spenden)",
        ],
        credits_available=[
            "Foreign Tax Credit (Ausländische Steuergutschrift)",
            "Child Tax Credit (Kindersteuergutschrift)",
            "Other credits (sonstige Gutschriften)",
        ],
        special_rules=[
            "Kein Standard Deduction für Nonresidenten (außer Ausnahmen)",
            "Keine persönlichen Freibeträge",
            "Steuerabkommen können Steuersätze reduzieren",
            "Quellensteuer wird auf FDAP-Einkommen erhoben",
            "Fristverlängerung mit Form 4868 möglich",
        ],
    )
