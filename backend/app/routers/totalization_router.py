"""
Totalization Agreement API Router.
GET  /api/v1/totalization/countries  – list all countries with US agreements
POST /api/v1/totalization/check      – check agreement for a specific country
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.utils import get_current_tenant
from app.modules.totalization import (
    TotalizationRequest,
    TotalizationResult,
    check_totalization,
    _CANONICAL_NAMES,
)

router = APIRouter(tags=["totalization"])


@router.get("/countries")
async def list_totalization_countries(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Returns the list of countries that have a US Totalization Agreement.
    """
    return {
        "count": len(_CANONICAL_NAMES),
        "countries": _CANONICAL_NAMES,
        "source": "SSA.gov – US International Social Security Agreements",
        "note": (
            "These agreements eliminate dual Social Security taxation for workers "
            "who would otherwise owe contributions to both countries."
        ),
    }


@router.post("/check")
async def check_totalization_endpoint(
    payload: TotalizationRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> TotalizationResult:
    """
    Checks whether a US Totalization Agreement applies for the given country
    and employment situation, and determines which system's SS taxes apply.
    """
    return check_totalization(payload)
