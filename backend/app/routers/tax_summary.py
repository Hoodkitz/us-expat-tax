"""
Tax Summary Router: GET/POST /api/v1/tax-summary

Bietet eine Gesamtbilanz aller Steuerformulare und JSON-Export.
Mandanten-Isolation ist durch JWT-Claims (tenant_id) sichergestellt.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.tax_summary import export_tax_summary_json, get_tax_summary

router = APIRouter(tags=["tax-summary"])


# ---------------------------------------------------------------------------
# Pydantic-Modelle
# ---------------------------------------------------------------------------


class TaxSummaryOverviewResponse(BaseModel):
    """Response-Model für die Tax Summary Übersicht."""

    tenant_id: str = Field(..., description="Mandanten-ID")
    total_calculations: int = Field(..., description="Anzahl der Berechnungen")
    total_income_usd: str = Field(..., description="Gesamteinkommen in USD")
    total_tax_paid_usd: str = Field(..., description="Gezahlte Steuern in USD")
    total_us_tax_liability_usd: str = Field(..., description="US-Steuerpflicht in USD")
    recommended_path: str | None = Field(None, description="Empfohlene Strategie")
    last_calculation: dict | None = Field(None, description="Letzte Berechnung")
    calculations: list[dict] = Field(default_factory=list, description="Alle Berechnungen")


class ExportRequest(BaseModel):
    """Request für den JSON-Export."""

    format: str = Field(default="json", description="Export-Format (nur json unterstützt)")


class ExportResponse(BaseModel):
    """Response für den JSON-Export."""

    export_id: str = Field(..., description="ID des Exports")
    file_path: str = Field(..., description="Pfad zur exportierten Datei")
    summary: TaxSummaryOverviewResponse = Field(..., description="Die exportierte Zusammenfassung")


# ---------------------------------------------------------------------------
# Endpunkte
# ---------------------------------------------------------------------------


@router.get(
    "/overview",
    response_model=TaxSummaryOverviewResponse,
    summary="Gesamtbilanz aller Steuerformulare",
)
async def get_overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> TaxSummaryOverviewResponse:
    """
    Gibt eine Gesamtbilanz aller gespeicherten Steuerberechnungen
    für den authentifizierten Mandanten zurück.
    """
    tenant_id: str = current_tenant["tenant_id"]
    try:
        summary = get_tax_summary(tenant_id=tenant_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tax Summary konnte nicht erstellt werden: {exc}",
        ) from exc
    return TaxSummaryOverviewResponse(**summary)


@router.post(
    "/export",
    response_model=ExportResponse,
    summary="Tax Summary als JSON exportieren",
)
async def export_summary(
    body: ExportRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ExportResponse:
    """
    Exportiert die Steuerübersicht als JSON-Datei und gibt
    den Pfad sowie die Zusammenfassung zurück.
    """
    if body.format != "json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nicht unterstütztes Format: {body.format}. Nur 'json' wird unterstützt.",
        )

    tenant_id: str = current_tenant["tenant_id"]
    try:
        output_file = export_tax_summary_json(tenant_id=tenant_id)
        summary = get_tax_summary(tenant_id=tenant_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export fehlgeschlagen: {exc}",
        ) from exc

    return ExportResponse(
        export_id=output_file.stem,
        file_path=str(output_file),
        summary=TaxSummaryOverviewResponse(**summary),
    )
