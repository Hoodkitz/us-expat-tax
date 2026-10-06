"""
History-Router: POST/GET /api/v1/history

Speichert und liefert Steuerberechnungen pro Mandant.
Mandanten-Isolation ist durch JWT-Claims (tenant_id) sichergestellt.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.utils import get_current_tenant
from app.modules.history import get_calculations, save_calculation

router = APIRouter(tags=["history"])


# ---------------------------------------------------------------------------
# Pydantic-Modelle
# ---------------------------------------------------------------------------


class SaveCalculationRequest(BaseModel):
    input_data: dict
    result_data: dict


class SaveCalculationResponse(BaseModel):
    calc_id: str


# ---------------------------------------------------------------------------
# Endpunkte
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SaveCalculationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Steuerberechnung speichern",
)
async def save_calculation_endpoint(
    body: SaveCalculationRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SaveCalculationResponse:
    """
    Speichert eine Steuerberechnung für den authentifizierten Mandanten
    und gibt die neue Berechnungs-ID zurück.
    """
    tenant_id: str = current_tenant["tenant_id"]
    try:
        calc_id = save_calculation(
            tenant_id=tenant_id,
            input_data=body.input_data,
            result_data=body.result_data,
        )
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Berechnungshistorie konnte nicht gespeichert werden: {exc}",
        ) from exc
    return SaveCalculationResponse(calc_id=calc_id)


@router.get(
    "",
    summary="Berechnungshistorie abrufen",
)
async def get_calculations_endpoint(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[dict]:
    """
    Gibt alle gespeicherten Steuerberechnungen des authentifizierten Mandanten
    zurück, sortiert nach Datum (neueste zuerst).
    """
    tenant_id: str = current_tenant["tenant_id"]
    return get_calculations(tenant_id=tenant_id)
