"""
State Tax Filing Obligations Router.
GET  /api/v1/state-tax/states          – all 50 states with tax info
POST /api/v1/state-tax/obligations     – analyze filing obligations
POST /api/v1/state-tax/domicile-analysis – domicile abandonment analysis
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.auth.utils import get_current_tenant
from app.modules.state_tax import (
    ObligationsRequest,
    ObligationsResult,
    DomicileAnalysisRequest,
    DomicileAnalysisResult,
    StateInfo,
    analyze_obligations,
    analyze_domicile,
    list_states,
    STATE_DATA,
)

router = APIRouter(tags=["state-tax"])


@router.get("/states")
async def get_states(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Returns all 50 US states with income tax status, safe harbor days,
    and statutory residency day thresholds.
    """
    states = list_states()
    return {
        "count": len(states),
        "states": [s.model_dump() for s in states],
        "note": (
            "Safe harbor days indicate how many days you can spend in a state "
            "before triggering statutory residency. Always consult a tax professional."
        ),
    }


@router.post("/obligations")
async def get_obligations(
    payload: ObligationsRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ObligationsResult:
    """
    Analyzes state income tax filing obligations for a US expat based on
    state, days present, domicile, and income source.
    """
    state = payload.state.upper()
    if state not in STATE_DATA:
        raise HTTPException(status_code=422, detail=f"Unknown state code: {state}")

    domicile = payload.domicile_state.upper()
    if domicile not in STATE_DATA:
        raise HTTPException(status_code=422, detail=f"Unknown domicile state code: {domicile}")

    return analyze_obligations(payload)


@router.post("/domicile-analysis")
async def get_domicile_analysis(
    payload: DomicileAnalysisRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DomicileAnalysisResult:
    """
    Analyzes whether a US expat has successfully abandoned their state domicile
    based on key domicile factors. Returns a risk score and factor breakdown.
    """
    state = payload.original_state.upper()
    if state not in STATE_DATA:
        raise HTTPException(status_code=422, detail=f"Unknown state code: {state}")

    return analyze_domicile(payload)
