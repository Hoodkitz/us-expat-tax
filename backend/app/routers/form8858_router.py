"""
Form 8858 Foreign Disregarded Entities (FDE) and Foreign Branches (FB) Router.

POST /api/v1/form8858/filing-requirement  – JWT-protected: determine Form 8858 filing obligation
POST /api/v1/form8858/income-summary      – JWT-protected: FDE income summary
POST /api/v1/form8858/penalty-calculator  – JWT-protected: IRC §6038 penalty calculator
GET  /api/v1/form8858/overview            – static overview of Form 8858 / FDE rules
"""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant

router = APIRouter(tags=["form8858"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FORM_DUE_DATE = "Same as your income tax return due date (typically April 15 / Oct 15 extended)"
BASE_PENALTY_USD = 10_000
MAX_CONTINUATION_PERIODS = 5

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

OwnershipType = Literal["direct_fde", "indirect_fde", "foreign_branch", "cfc_fde"]


class FilingRequirementRequest(BaseModel):
    ownership_type: OwnershipType = Field(..., examples=["direct_fde"])
    ownership_percentage: float = Field(..., ge=0.0, le=100.0, examples=[100.0])
    is_us_person: bool = Field(..., examples=[True])
    entity_country: str = Field(..., examples=["Germany"])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class FilingRequirementResponse(BaseModel):
    must_file: bool
    reason: str
    form_due_date: str
    penalty_if_not_filed_usd: int
    filing_instructions: str


class IncomeSummaryRequest(BaseModel):
    gross_receipts_usd: float = Field(..., ge=0.0, examples=[500_000.0])
    cost_of_goods_sold_usd: float = Field(..., ge=0.0, examples=[200_000.0])
    operating_expenses_usd: float = Field(..., ge=0.0, examples=[100_000.0])
    depreciation_usd: float = Field(..., ge=0.0, examples=[20_000.0])
    other_income_usd: float = Field(..., ge=0.0, examples=[10_000.0])
    other_deductions_usd: float = Field(..., ge=0.0, examples=[5_000.0])


class IncomeSummaryResponse(BaseModel):
    gross_income_usd: float
    total_deductions_usd: float
    net_income_loss_usd: float
    is_profitable: bool
    us_tax_implications: str


class PenaltyCalculatorRequest(BaseModel):
    years_not_filed: int = Field(..., ge=1, le=10, examples=[2])
    continued_failure_periods: int = Field(..., ge=0, le=5, examples=[3])


class PenaltyCalculatorResponse(BaseModel):
    base_penalty_usd: int
    continuation_penalty_usd: int
    total_penalty_usd: int
    criminal_risk_flag: bool
    mitigation_options: list[str]


# ---------------------------------------------------------------------------
# Business logic helpers
# ---------------------------------------------------------------------------


def _determine_filing_requirement(req: FilingRequirementRequest) -> FilingRequirementResponse:
    ownership_type = req.ownership_type
    is_us = req.is_us_person
    pct = req.ownership_percentage

    if ownership_type == "direct_fde":
        must_file = is_us
        if must_file:
            reason = (
                "As a U.S. person who directly owns a foreign disregarded entity (FDE), "
                "you are required to file Form 8858 under IRC §6038(a) and Treas. Reg. §1.6038-3."
            )
        else:
            reason = (
                "Non-U.S. persons are not required to file Form 8858 for directly owned FDEs."
            )
    elif ownership_type == "indirect_fde":
        must_file = is_us and pct >= 10.0
        if must_file:
            reason = (
                f"As a U.S. person indirectly owning {pct:.1f}% of the FDE (≥10% threshold met), "
                "you must file Form 8858 per IRC §6038(a)."
            )
        elif is_us and pct < 10.0:
            reason = (
                f"Your indirect ownership of {pct:.1f}% is below the 10% threshold required "
                "for Form 8858 filing of indirect FDE owners."
            )
        else:
            reason = "Non-U.S. persons are not required to file Form 8858."
    elif ownership_type == "foreign_branch":
        must_file = is_us
        if must_file:
            reason = (
                "U.S. persons operating a foreign branch must file Form 8858 (Schedule G and FB "
                "schedules) per the Tax Cuts and Jobs Act (TCJA) 2017 expansion to foreign branches."
            )
        else:
            reason = "Non-U.S. persons do not file Form 8858 for foreign branches."
    else:  # cfc_fde
        must_file = True
        reason = (
            "A foreign disregarded entity owned by a Controlled Foreign Corporation (CFC) always "
            "requires Form 8858 as an attachment to Form 5471. The U.S. shareholders of the CFC "
            "must include Form 8858 per IRC §6038 regardless of direct ownership."
        )

    filing_instructions = (
        "Complete all applicable schedules of Form 8858 including the income statement (Schedule C), "
        "balance sheet (Schedule F), and transactions with related parties (Schedule G). "
        "Attach to Form 1040 (individuals), Form 1065 (partnerships), or Form 1120 (corporations) "
        "as applicable. File by the due date of your annual return including extensions."
    ) if must_file else (
        "No Form 8858 filing is required based on the information provided. "
        "Consult a U.S. international tax professional if your circumstances change."
    )

    return FilingRequirementResponse(
        must_file=must_file,
        reason=reason,
        form_due_date=FORM_DUE_DATE,
        penalty_if_not_filed_usd=BASE_PENALTY_USD,
        filing_instructions=filing_instructions,
    )


def _calculate_income_summary(req: IncomeSummaryRequest) -> IncomeSummaryResponse:
    gross_income = req.gross_receipts_usd - req.cost_of_goods_sold_usd + req.other_income_usd
    total_deductions = req.operating_expenses_usd + req.depreciation_usd + req.other_deductions_usd
    net_income_loss = gross_income - total_deductions
    is_profitable = net_income_loss > 0

    if is_profitable:
        us_tax_implications = (
            f"The FDE generated net income of ${net_income_loss:,.2f}. As a disregarded entity, "
            "its income flows directly to the U.S. owner and is subject to U.S. taxation. "
            "Consider Subpart F income and GILTI implications if the FDE is owned by a CFC."
        )
    elif net_income_loss < 0:
        us_tax_implications = (
            f"The FDE reported a net loss of ${abs(net_income_loss):,.2f}. Losses may be "
            "deductible on the U.S. owner's return, subject to at-risk and passive activity rules. "
            "Consult a U.S. tax professional regarding loss utilization."
        )
    else:
        us_tax_implications = (
            "The FDE broke even with zero net income or loss. No immediate U.S. tax liability "
            "arises from FDE operations, but Form 8858 filing is still required if applicable."
        )

    return IncomeSummaryResponse(
        gross_income_usd=gross_income,
        total_deductions_usd=total_deductions,
        net_income_loss_usd=net_income_loss,
        is_profitable=is_profitable,
        us_tax_implications=us_tax_implications,
    )


def _calculate_penalty(req: PenaltyCalculatorRequest) -> PenaltyCalculatorResponse:
    base_penalty = BASE_PENALTY_USD * req.years_not_filed
    continuation_per_year = min(req.continued_failure_periods, MAX_CONTINUATION_PERIODS) * BASE_PENALTY_USD
    total_continuation = continuation_per_year * req.years_not_filed
    total_penalty = base_penalty + total_continuation
    criminal_risk_flag = total_penalty > 50_000

    mitigation_options = [
        "Voluntary disclosure via IRS Streamlined Procedures",
        "Reasonable cause statement with Form 8858",
        "Seek competent US international tax counsel",
    ]

    return PenaltyCalculatorResponse(
        base_penalty_usd=base_penalty,
        continuation_penalty_usd=total_continuation,
        total_penalty_usd=total_penalty,
        criminal_risk_flag=criminal_risk_flag,
        mitigation_options=mitigation_options,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/filing-requirement", response_model=FilingRequirementResponse)
async def filing_requirement(
    req: FilingRequirementRequest,
    _tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FilingRequirementResponse:
    """Determine Form 8858 filing obligation for an FDE or foreign branch."""
    return _determine_filing_requirement(req)


@router.post("/income-summary", response_model=IncomeSummaryResponse)
async def income_summary(
    req: IncomeSummaryRequest,
    _tenant: Annotated[dict, Depends(get_current_tenant)],
) -> IncomeSummaryResponse:
    """Calculate FDE income summary per Form 8858 Schedule C."""
    return _calculate_income_summary(req)


@router.post("/penalty-calculator", response_model=PenaltyCalculatorResponse)
async def penalty_calculator(
    req: PenaltyCalculatorRequest,
    _tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PenaltyCalculatorResponse:
    """Calculate IRC §6038 penalties for failure to file Form 8858."""
    return _calculate_penalty(req)


@router.get("/overview")
async def overview() -> dict:
    """Static overview of Form 8858 requirements — no authentication required."""
    return {
        "form_name": "Form 8858 - Information Return of U.S. Persons With Respect to Foreign Disregarded Entities (FDEs) and Foreign Branches (FBs)",
        "purpose": (
            "Form 8858 is used to satisfy the reporting requirements of IRC §6038 for U.S. persons "
            "who are tax owners of foreign disregarded entities (FDEs) or operate foreign branches (FBs). "
            "It provides the IRS with information about the FDE's/FB's income, assets, and transactions."
        ),
        "who_must_file": [
            "U.S. persons who are tax owners of foreign disregarded entities (direct ownership)",
            "U.S. persons who indirectly own ≥10% of an FDE through a foreign entity",
            "U.S. persons operating foreign branches (post-TCJA 2017 expansion)",
            "U.S. shareholders of CFCs that own FDEs (attach to Form 5471)",
            "U.S. partners of foreign partnerships that own FDEs (attach to Form 8865)",
        ],
        "key_deadlines": {
            "individual_return": "April 15 (or October 15 with extension)",
            "corporate_return": "April 15 (or October 15 with extension for calendar-year corps)",
            "partnership_return": "March 15 (or September 15 with extension)",
            "note": "Form 8858 is due with the filer's annual income tax return",
        },
        "penalties": {
            "base_penalty_usd": 10_000,
            "continuation_penalty": "$10,000 per 30-day period (up to 5 periods = $50,000 max additional)",
            "criminal_exposure": "Potential criminal penalties under IRC §7203 for willful failure",
            "statute_of_limitations": "Failure to file Form 8858 can toll the statute of limitations for the entire tax return",
        },
        "related_forms": [
            "Form 5471 (Information Return for CFCs that own FDEs)",
            "Form 8865 (Foreign Partnerships that own FDEs)",
            "FinCEN 114 (FBAR — foreign bank accounts)",
            "Form 926 (Transfer of assets to foreign corporations)",
            "Form 8938 (FATCA — Statement of Foreign Financial Assets)",
        ],
    }
