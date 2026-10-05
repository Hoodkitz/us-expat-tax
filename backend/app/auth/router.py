"""
Auth-Router: Registrierung, Login, aktueller Mandant.
Tenant-Daten werden in backend/app/data/tenants.json gespeichert.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.models import TenantLogin, TenantOut, TenantRegister, TokenResponse
from app.auth.utils import (
    create_access_token,
    get_current_tenant,
    hash_password,
    verify_password,
)

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

# --------------------------------------------------------------------------
# Persistenz: JSON-Datei
# --------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent / "data"
TENANTS_FILE = DATA_DIR / "tenants.json"


def _load_tenants() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TENANTS_FILE.exists():
        return {}
    with TENANTS_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_tenants(tenants: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with TENANTS_FILE.open("w", encoding="utf-8") as fh:
        json.dump(tenants, fh, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------
# Endpunkte
# --------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=TenantOut,
    status_code=status.HTTP_201_CREATED,
    summary="Neuen Mandanten registrieren",
)
async def register(body: TenantRegister) -> TenantOut:
    tenants = _load_tenants()
    if body.email in tenants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-Mail bereits registriert.",
        )
    tenant_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    tenants[body.email] = {
        "email": body.email,
        "tenant_name": body.tenant_name,
        "tenant_id": tenant_id,
        "password_hash": hash_password(body.password),
        "created_at": created_at,
    }
    _save_tenants(tenants)
    logger.info("Neuer Mandant registriert: email=%s tenant_id=%s", body.email, tenant_id)
    return TenantOut(
        email=body.email,
        tenant_name=body.tenant_name,
        tenant_id=uuid.UUID(tenant_id),
        created_at=datetime.fromisoformat(created_at),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login und JWT-Token erhalten",
)
async def login(body: TenantLogin) -> TokenResponse:
    tenants = _load_tenants()
    record = tenants.get(body.email)
    if record is None or not verify_password(body.password, record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige E-Mail oder Passwort.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        {"sub": record["email"], "tenant_id": record["tenant_id"]}
    )
    logger.info("Mandant angemeldet: email=%s tenant_id=%s", record["email"], record["tenant_id"])
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=TenantOut,
    summary="Aktuellen Mandanten abrufen",
)
async def me(current: dict = Depends(get_current_tenant)) -> TenantOut:
    tenants = _load_tenants()
    record = tenants.get(current["email"])
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mandant nicht gefunden.",
        )
    return TenantOut(
        email=record["email"],
        tenant_name=record["tenant_name"],
        tenant_id=uuid.UUID(record["tenant_id"]),
        created_at=datetime.fromisoformat(record["created_at"]),
    )
