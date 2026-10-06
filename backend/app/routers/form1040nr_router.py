"""
Form 1040-NR Router: U.S. Nonresident Alien Income Tax Return
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.utils import get_current_tenant
from app.modules.form1040nr import (
    FilingRequirementRequest,
    FilingRequirementResponse,
    TaxCalculationRequest,
    TaxCalculationResponse,
    OverviewResponse,
    check_filing_requirement,
    calculate_tax,
    get_overview,
)

logger = logging.getLogger("app.form1040nr")

router = APIRouter(prefix="/form1040nr", tags=["form1040nr"])


@router.post(
    "/filing-requirement",
    response_model=FilingRequirementResponse,
    summary="Prüfen, ob Form 1040-NR Pflicht ist",
)
async def filing_requirement(
    body: FilingRequirementRequest,
    current_tenant: dict = Depends(get_current_tenant),
) -> FilingRequirementResponse:
    """
    Prüft, ob ein Nonresident Alien Form 1040-NR einreichen muss.
    """
    logger.info(
        "Filing requirement check: tenant=%s tax_year=%s",
        current_tenant.get("email"),
        body.tax_year,
    )
    try:
        result = check_filing_requirement(body)
        return result
    except Exception as e:
        logger.error("Filing requirement check failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Berechnung fehlgeschlagen: {str(e)}",
        )


@router.post(
    "/calculate",
    response_model=TaxCalculationResponse,
    summary="Steuerschuld für Nonresident Aliens berechnen",
)
async def calculate(
    body: TaxCalculationRequest,
    current_tenant: dict = Depends(get_current_tenant),
) -> TaxCalculationResponse:
    """
    Berechnet die Steuerschuld für Nonresident Aliens.
    """
    logger.info(
        "Tax calculation: tenant=%s tax_year=%s",
        current_tenant.get("email"),
        body.tax_year,
    )
    try:
        result = calculate_tax(body)
        return result
    except Exception as e:
        logger.error("Tax calculation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Berechnung fehlgeschlagen: {str(e)}",
        )


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Übersicht über Form 1040-NR",
)
async def overview(
    current_tenant: dict = Depends(get_current_tenant),
) -> OverviewResponse:
    """
    Gibt eine Übersicht über Form 1040-NR zurück.
    """
    logger.info("Overview requested: tenant=%s", current_tenant.get("email"))
    try:
        result = get_overview()
        return result
    except Exception as e:
        logger.error("Overview failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Übersicht fehlgeschlagen: {str(e)}",
        )
