"""
Enhanced FBAR Penalties Router.
GET  /api/v1/fbar/thresholds  – current FBAR filing thresholds and deadlines
POST /api/v1/fbar/penalties   – calculate FBAR penalties
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.utils import get_current_tenant
from app.modules.fbar_penalties import (
    FBARPenaltyRequest,
    FBARPenaltyResult,
    calculate_fbar_penalties,
    FBAR_THRESHOLDS_INFO,
)

router = APIRouter(tags=["fbar-penalties"])


@router.get("/thresholds")
async def fbar_thresholds(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Returns current FBAR filing thresholds, deadlines, and penalty tier summary.
    """
    return FBAR_THRESHOLDS_INFO


@router.post("/penalties")
async def fbar_penalties_endpoint(
    payload: FBARPenaltyRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FBARPenaltyResult:
    """
    Calculates estimated FBAR penalties based on violation type, years,
    and maximum account balance.
    """
    return calculate_fbar_penalties(payload)
