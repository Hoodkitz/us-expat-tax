"""
Form 5471 — Controlled Foreign Corporation (CFC) Reporting Module.

Pydantic models and business logic for:
- Filing requirement determination (Categories 1–5)
- Subpart F income calculation
- GILTI inclusion calculation
- Combined income calculation endpoint
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "1": "Category 1 — U.S. shareholder of a foreign corporation that was a CFC at any time during the tax year.",
    "2": "Category 2 — Officer or director of a foreign corporation when a U.S. person acquired 10%+ of stock.",
    "3": "Category 3 — U.S. person who acquired (or disposed of) stock in a foreign corporation that is or becomes a CFC, reaching 10% ownership.",
    "4": "Category 4 — U.S. person who had control (>50% ownership by vote or value) of a foreign corporation at any point during the tax year.",
    "5": "Category 5 — U.S. shareholder of a CFC at any point during the tax year (directly or indirectly owning ≥10%).",
}

BASE_PENALTY_USD = 10_000
CONTINUATION_PENALTY_PER_30_DAYS = 10_000
MAX_CONTINUATION_PENALTIES = 5

GILTI_HIGH_TAX_THRESHOLD_PCT = 18.9
SUBPART_F_HIGH_TAX_THRESHOLD_PCT = 18.9


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

CategoryOfFiler = Literal["1", "2", "3", "4", "5"]


class FilingRequirementRequest(BaseModel):
    category_of_filer: CategoryOfFiler = Field(..., examples=["4"])
    ownership_percentage: float = Field(..., ge=0.0, le=100.0, examples=[51.0])
    is_officer_or_director: bool = Field(..., examples=[False])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class SubpartFIncomeRequest(BaseModel):
    passive_income_usd: float = Field(..., ge=0.0, examples=[50_000.0])
    sales_income_usd: float = Field(..., ge=0.0, examples=[20_000.0])
    services_income_usd: float = Field(..., ge=0.0, examples=[10_000.0])
    foreign_base_company_income_usd: float = Field(..., ge=0.0, examples=[30_000.0])
    total_cfc_income_usd: float = Field(..., ge=0.0, examples=[200_000.0])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class GiltiCalculatorRequest(BaseModel):
    net_tested_income_usd: float = Field(..., ge=0.0, examples=[500_000.0])
    qualified_business_asset_investment_usd: float = Field(..., ge=0.0, examples=[1_000_000.0])
    deemed_tangible_income_return_pct: float = Field(10.0, ge=0.0, le=100.0, examples=[10.0])
    ownership_pct: float = Field(..., ge=0.0, le=100.0, examples=[100.0])


class IncomeCalculationRequest(BaseModel):
    """Combined income calculation: Subpart F + GILTI."""
    # Subpart F inputs
    passive_income_usd: float = Field(..., ge=0.0, examples=[50_000.0])
    sales_income_usd: float = Field(..., ge=0.0, examples=[20_000.0])
    services_income_usd: float = Field(..., ge=0.0, examples=[10_000.0])
    foreign_base_company_income_usd: float = Field(..., ge=0.0, examples=[30_000.0])
    total_cfc_income_usd: float = Field(..., ge=0.0, examples=[200_000.0])
    # GILTI inputs
    net_tested_income_usd: float = Field(..., ge=0.0, examples=[500_000.0])
    qualified_business_asset_investment_usd: float = Field(..., ge=0.0, examples=[1_000_000.0])
    deemed_tangible_income_return_pct: float = Field(10.0, ge=0.0, le=100.0, examples=[10.0])
    ownership_pct: float = Field(..., ge=0.0, le=100.0, examples=[100.0])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------


def determine_filing_requirement(req: FilingRequirementRequest) -> dict:
    """Determine whether a U.S. person must file Form 5471."""
    must_file = False
    categories_triggered: list[str] = []
    reasons: list[str] = []

    cat = req.category_of_filer

    if cat == "1":
        must_file = True
        categories_triggered.append("1")
        reasons.append(
            "Category 1 filer: you are a U.S. shareholder of a foreign corporation that was a CFC. "
            "Filing is required under IRC §6038 to report constructive ownership and CFC status."
        )

    if cat == "2":
        if req.is_officer_or_director:
            must_file = True
            categories_triggered.append("2")
            reasons.append(
                "Category 2 filer: as an officer or director of the foreign corporation at the time a "
                "U.S. person acquired ≥10% of the stock, you must file Form 5471."
            )
        elif req.ownership_percentage >= 10.0:
            must_file = True
            categories_triggered.append("2")
            reasons.append(
                f"Category 2 filer: a U.S. person acquired stock bringing ownership to "
                f"{req.ownership_percentage:.1f}% (≥10%), triggering the officer/director reporting requirement."
            )
        else:
            reasons.append(
                "Category 2: no filing triggered — neither officer/director status confirmed nor "
                "sufficient ownership change occurred."
            )

    if cat == "3":
        if req.ownership_percentage >= 10.0:
            must_file = True
            categories_triggered.append("3")
            reasons.append(
                f"Category 3 filer: you acquired stock to reach {req.ownership_percentage:.1f}% ownership "
                f"(≥10%) in a foreign corporation that is or became a CFC."
            )
        else:
            reasons.append(
                f"Category 3: ownership is {req.ownership_percentage:.1f}%, below the 10% threshold. "
                "No filing required under Category 3."
            )

    if cat == "4":
        if req.ownership_percentage > 50.0:
            must_file = True
            categories_triggered.append("4")
            reasons.append(
                f"Category 4 filer: you controlled {req.ownership_percentage:.1f}% of the foreign "
                "corporation (>50% by vote or value), triggering Form 5471 filing under IRC §6038."
            )
        elif req.ownership_percentage == 50.0:
            must_file = True
            categories_triggered.append("4")
            reasons.append(
                "Category 4 filer: 50% ownership may constitute control when combined with constructive "
                "ownership rules. Consult a tax professional to confirm Category 4 applicability."
            )
        else:
            reasons.append(
                f"Category 4: ownership is {req.ownership_percentage:.1f}%, which is ≤50%. "
                "Control threshold not met — no Category 4 filing required based solely on ownership."
            )

    if cat == "5":
        if req.ownership_percentage >= 10.0:
            must_file = True
            categories_triggered.append("5")
            reasons.append(
                f"Category 5 filer: you own {req.ownership_percentage:.1f}% (≥10%) of the CFC. "
                "U.S. shareholders of CFCs must file Form 5471 including schedules for Subpart F and GILTI."
            )
        else:
            reasons.append(
                f"Category 5: ownership is {req.ownership_percentage:.1f}%, below the 10% U.S. shareholder "
                "threshold. No Category 5 filing required."
            )

    if not reasons:
        reasons.append("No Form 5471 filing obligation identified based on provided information.")

    penalty_if_not_filed = (
        f"Failure to file Form 5471: initial penalty of ${BASE_PENALTY_USD:,} per year per CFC. "
        f"If non-compliance continues, an additional ${CONTINUATION_PENALTY_PER_30_DAYS:,} per 30-day period "
        f"(up to {MAX_CONTINUATION_PENALTIES} additional periods = up to $60,000 total). "
        "IRC §6038(b). Criminal penalties may also apply for willful failure."
    )

    due_date = (
        f"April 15, {req.tax_year + 1} (attached to Form 1040 or Form 1120); "
        "automatic extension to October 15 if Form 4868 filed (individuals)."
    )

    return {
        "must_file": must_file,
        "categories_triggered": categories_triggered,
        "reasons": reasons,
        "penalty_if_not_filed": penalty_if_not_filed,
        "due_date": due_date,
    }


def calculate_subpart_f(req: SubpartFIncomeRequest) -> dict:
    """Calculate Subpart F income inclusions for a CFC."""
    subpart_f_total_usd = round(req.passive_income_usd + req.foreign_base_company_income_usd, 2)
    inclusion_required = subpart_f_total_usd > 0

    de_minimis_rule_applies = (
        req.total_cfc_income_usd > 0
        and subpart_f_total_usd <= req.total_cfc_income_usd * 0.05
    )

    high_tax_exception_may_apply = False
    if req.total_cfc_income_usd > 0 and subpart_f_total_usd > 0:
        active_income = req.sales_income_usd + req.services_income_usd
        high_tax_exception_may_apply = active_income > subpart_f_total_usd

    recommendations: list[str] = []

    if inclusion_required:
        recommendations.append(
            f"Subpart F income of ${subpart_f_total_usd:,.2f} must be included in your gross income "
            "for the current tax year, even if not distributed (IRC §951)."
        )

    if de_minimis_rule_applies and req.total_cfc_income_usd > 0:
        recommendations.append(
            "The de minimis rule may apply: Subpart F income is ≤5% of total CFC gross income. "
            "Consult Treas. Reg. §1.954-1(b) to confirm eligibility."
        )

    if high_tax_exception_may_apply:
        recommendations.append(
            f"High-tax exception may apply if the CFC's effective foreign tax rate is ≥{SUBPART_F_HIGH_TAX_THRESHOLD_PCT}%. "
            "Document actual foreign taxes paid to support this position (Treas. Reg. §1.954-1(d))."
        )

    if not inclusion_required:
        recommendations.append(
            "No Subpart F income identified. Verify that passive income, FBCI, and insurance income "
            "items have been correctly classified."
        )

    if req.sales_income_usd > 0:
        recommendations.append(
            f"Sales income of ${req.sales_income_usd:,.2f} noted. Determine whether this qualifies as "
            "Foreign Base Company Sales Income under IRC §954(d) based on buy-sell transaction facts."
        )

    if req.services_income_usd > 0:
        recommendations.append(
            f"Services income of ${req.services_income_usd:,.2f} noted. Determine whether this qualifies as "
            "Foreign Base Company Services Income under IRC §954(e)."
        )

    return {
        "subpart_f_total_usd": subpart_f_total_usd,
        "inclusion_required": inclusion_required,
        "high_tax_exception_may_apply": high_tax_exception_may_apply,
        "effective_foreign_rate_threshold_pct": SUBPART_F_HIGH_TAX_THRESHOLD_PCT,
        "recommendations": recommendations,
    }


def calculate_gilti(req: GiltiCalculatorRequest) -> dict:
    """Calculate GILTI inclusion amount under IRC §951A."""
    ownership_fraction = req.ownership_pct / 100.0

    net_cfc_tested_income_usd = round(req.net_tested_income_usd * ownership_fraction, 2)

    dtir_rate = req.deemed_tangible_income_return_pct / 100.0
    dtir_usd = round(req.qualified_business_asset_investment_usd * dtir_rate * ownership_fraction, 2)

    gilti_inclusion_usd = round(max(0.0, net_cfc_tested_income_usd - dtir_usd), 2)

    deduction_80pct_corporations = round(gilti_inclusion_usd * 0.50, 2)

    if req.ownership_pct < 100.0:
        ownership_note = (
            f" (pro-rated at {req.ownership_pct:.1f}% ownership: "
            f"${req.net_tested_income_usd:,.2f} × {ownership_fraction:.4f})"
        )
    else:
        ownership_note = ""

    explanation = (
        f"Net CFC Tested Income{ownership_note}: ${net_cfc_tested_income_usd:,.2f}. "
        f"DTIR (QBAI × {req.deemed_tangible_income_return_pct:.1f}%): ${dtir_usd:,.2f}. "
        f"GILTI Inclusion (Tested Income − DTIR): ${gilti_inclusion_usd:,.2f}. "
    )

    if gilti_inclusion_usd == 0.0:
        explanation += (
            "GILTI inclusion is $0 because the Deemed Tangible Income Return equals or exceeds "
            "the net tested income. No GILTI inclusion required."
        )
    else:
        explanation += (
            f"C-corporations may claim a §250 deduction of 50% (${deduction_80pct_corporations:,.2f}), "
            "reducing the effective GILTI rate. Individuals are not eligible for the §250 deduction "
            "unless a §962 election is made."
        )

    return {
        "gilti_inclusion_usd": gilti_inclusion_usd,
        "dtir_usd": dtir_usd,
        "net_cfc_tested_income_usd": net_cfc_tested_income_usd,
        "deduction_80pct_corporations": deduction_80pct_corporations,
        "explanation": explanation,
    }


def calculate_income(req: IncomeCalculationRequest) -> dict:
    """Combined income calculation: Subpart F + GILTI."""
    subpart_f_req = SubpartFIncomeRequest(
        passive_income_usd=req.passive_income_usd,
        sales_income_usd=req.sales_income_usd,
        services_income_usd=req.services_income_usd,
        foreign_base_company_income_usd=req.foreign_base_company_income_usd,
        total_cfc_income_usd=req.total_cfc_income_usd,
        tax_year=req.tax_year,
    )
    gilti_req = GiltiCalculatorRequest(
        net_tested_income_usd=req.net_tested_income_usd,
        qualified_business_asset_investment_usd=req.qualified_business_asset_investment_usd,
        deemed_tangible_income_return_pct=req.deemed_tangible_income_return_pct,
        ownership_pct=req.ownership_pct,
    )

    subpart_f_result = calculate_subpart_f(subpart_f_req)
    gilti_result = calculate_gilti(gilti_req)

    total_inclusion_usd = round(
        subpart_f_result["subpart_f_total_usd"] + gilti_result["gilti_inclusion_usd"], 2
    )

    return {
        "subpart_f": subpart_f_result,
        "gilti": gilti_result,
        "total_inclusion_usd": total_inclusion_usd,
        "tax_year": req.tax_year,
    }
