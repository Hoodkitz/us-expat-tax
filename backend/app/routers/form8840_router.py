"""
Form 8840 — Closer Connection Exception Router
================================================

Provides API endpoints for Form 8840 calculation and overview.
"""

from fastapi import APIRouter, Depends

from app.modules.form8840 import (
    Form8840Input,
    Form8840Result,
    calculate_form8840,
    get_form8840_overview,
)
from app.auth.utils import get_current_tenant

router = APIRouter(tags=["Form 8840 — Closer Connection Exception"])


@router.post("/calculate", response_model=Form8840Result)
def api_form8840_calculate(
    data: Form8840Input,
    tenant=Depends(get_current_tenant),
):
    """
    Calculate Form 8840 Closer Connection Exception.

    Determines whether a foreign national is classified as a U.S. Resident Alien
    based on days present in the US, closer connection claim, and exempt status.

    **Request body:**
    - `days_in_us` (int): Days present in the US (0-366)
    - `tax_year` (int): Tax year (2000-2099)
    - `closer_connection` (bool): Closer connection to US claimed
    - `exempt_individual` (bool): Qualifies as exempt individual

    **Returns:** Form8840Result with resident_alien determination and explanation.
    """
    return calculate_form8840(data)


@router.get("/overview")
def api_form8840_overview(tenant=Depends(get_current_tenant)):
    """
    Get an overview of Form 8840 Closer Connection Exception.

    Returns information about the form's purpose, who must file, key rules,
    and IRS reference.
    """
    return get_form8840_overview()
