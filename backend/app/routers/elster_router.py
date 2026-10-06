"""
ELSTER Router für us-expat-tax API.

Stellt Mock-Endpoints für ELSTER-Integration bereit.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.utils import get_current_tenant
from app.modules.elster_mock import test_elster_connection, get_elster_info


router = APIRouter(tags=["elster"])


@router.post("/test-connection")
async def elster_test_connection_endpoint(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Testet die ELSTER-Verbindung (Mock-Implementierung).
    
    TODO: Ersetzen durch echten ELSTER-API-Aufruf mit Zertifikats-Authentifizierung.
    
    Returns:
        Dict mit Verbindungs-Status, Zertifikat-Info und Test-Steuernummer
    """
    return test_elster_connection()


@router.get("/info")
async def elster_info_endpoint(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Gibt Informationen über verfügbare ELSTER-Endpoints zurück.
    
    Returns:
        Dict mit Endpoint-Liste und Integrations-Status
    """
    return get_elster_info()
