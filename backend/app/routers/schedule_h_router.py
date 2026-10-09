"""
Schedule H API Router.
POST /api/v1/schedule-h/calculate — Calculate household employment taxes
GET /api/v1/schedule-h/overview — Get Schedule H law summary
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_h import (
    HouseholdEmployeeInput,
    ScheduleHInput,
    ScheduleHResult,
    calculate_schedule_h,
    get_overview,
)

router = APIRouter(tags=["schedule-h"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class HouseholdEmployeeRequest(BaseModel):
    """A single household employee."""

    employee_name: str = Field(
        ...,
        min_length=1,
        description="Name of household employee",
        examples=["Jane Doe"],
    )
    cash_wages: float = Field(
        ...,
        ge=0,
        description="Total cash wages paid to this employee in 2025",
        examples=[5000.0],
    )


class ScheduleHCalculateRequest(BaseModel):
    """Request for Schedule H calculation."""

    employees: list[HouseholdEmployeeRequest] = Field(
        ...,
        description="List of household employees",
    )
    tax_year: int = Field(
        default=2025,
        ge=2000,
        le=2099,
        description="Tax year",
        examples=[2025],
    )
    employer_pays_employee_share: bool = Field(
        default=False,
        description="Whether employer elects to pay the employee's share of SS/Medicare",
        examples=[False],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate", response_model=ScheduleHResult)
async def schedule_h_calculate(
    req: ScheduleHCalculateRequest,
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> ScheduleHResult:
    """
    Calculate Schedule H household employment taxes.

    Applies IRS Schedule H rules:
    - Filing required if any employee's cash wages exceed $2,800 (2025)
    - SS tax: 12.4% on wages up to $176,100 (2025)
    - Medicare tax: 2.9% on all wages
    - Additional Medicare: 0.9% on wages over $200,000
    - If employer pays employee share: 2.9% SS + 1.45% Medicare

    **Authentication**: JWT required
    """
    input_data = ScheduleHInput(
        employees=[
            HouseholdEmployeeInput(
                employee_name=emp.employee_name,
                cash_wages=emp.cash_wages,
            )
            for emp in req.employees
        ],
        tax_year=req.tax_year,
        employer_pays_employee_share=req.employer_pays_employee_share,
    )
    return calculate_schedule_h(input_data)


@router.get("/overview")
async def schedule_h_overview(
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> dict:
    """
    Get Schedule H law summary and calculation overview.

    Returns filing thresholds, tax rates, and recommendations for
    Schedule H (Household Employment Taxes).

    **Authentication**: JWT required
    """
    return get_overview().model_dump()
