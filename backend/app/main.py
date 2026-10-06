"""
FastAPI-Entrypoint. Verdrahtet Module 1-5. Bindet NUR an
127.0.0.1 innerhalb des Containers - der Linkerd-Proxy-Sidecar
übernimmt TLS-Termination und mTLS zu anderen Mesh-Teilnehmern
(siehe docker-compose.yml).

JWT Mandanten-Authentifizierung ist für alle /api/v1/ Routen aktiv.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth.router import router as auth_router
from app.auth.utils import get_current_tenant
from app.routers.history_router import router as history_router
from app.routers.fbar_router import router as fbar_router
from app.routers.totalization_router import router as totalization_router
from app.routers.fbar_penalties_router import router as fbar_penalties_router
from app.routers.feie_router import router as feie_router
from app.modules.logic_engine import TaxpayerInput, evaluate as evaluate_tax
from app.modules.compliance_state import compute_compliance_flags
from app.modules.submission_saga import (
    create_liability_waiver,
    TollgateError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="US-Expat-Tax-App Backend",
    description="Interne API - nur via Linkerd-mTLS-Mesh erreichbar.",
    version="0.2.0",
)

# ---------------------------------------------------------------------------
# CORS (Lokale Frontend-Entwicklung auf localhost:3000)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Auth-Router einbinden
# ---------------------------------------------------------------------------
app.include_router(auth_router)

# ---------------------------------------------------------------------------
# History-Router einbinden
# ---------------------------------------------------------------------------
app.include_router(history_router, prefix="/api/v1/history")
app.include_router(fbar_router, prefix="/api/v1/fbar")
app.include_router(totalization_router, prefix="/api/v1/totalization")
app.include_router(fbar_penalties_router, prefix="/api/v1/fbar")
app.include_router(feie_router, prefix="/api/v1/feie")

# ---------------------------------------------------------------------------
# Request-Modelle
# ---------------------------------------------------------------------------

class TaxEvaluationRequest(BaseModel):
    foreign_earned_income_usd: str = Field(..., examples=["90000"])
    german_income_tax_paid_usd: str = Field(..., examples=["18000"])
    us_tax_liability_before_credits_usd: str = Field(..., examples=["15000"])
    num_qualifying_children: int = Field(0, ge=0, le=20)


class TollgateRequest(BaseModel):
    user_id: str
    totp_code: str


# ---------------------------------------------------------------------------
# Hilfsfunktion: Audit-Log pro Mandant
# ---------------------------------------------------------------------------

def _audit(tenant: dict, endpoint: str) -> None:
    logger.info(
        "AUDIT tenant_id=%s endpoint=%s timestamp=%s",
        tenant["tenant_id"],
        endpoint,
        datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Öffentliche Endpunkte
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Geschützte Endpunkte (JWT-Pflicht)
# ---------------------------------------------------------------------------

@app.post("/api/v1/tax/evaluate")
async def evaluate_tax_endpoint(
    payload: TaxEvaluationRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Reiner Delegations-Endpunkt an die deterministische Steuer-Engine.
    Kein LLM beteiligt.
    """
    import sympy as sp

    _audit(current_tenant, "/api/v1/tax/evaluate")

    try:
        inp = TaxpayerInput(
            foreign_earned_income_usd=sp.Rational(payload.foreign_earned_income_usd),
            german_income_tax_paid_usd=sp.Rational(payload.german_income_tax_paid_usd),
            us_tax_liability_before_credits_usd=sp.Rational(
                payload.us_tax_liability_before_credits_usd
            ),
            num_qualifying_children=payload.num_qualifying_children,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = evaluate_tax(inp)
    return {
        "recommended_path": result.recommended_path.value,
        "recommendation_reason": result.recommendation_reason,
        "ftc": {
            "credit_usd": str(result.ftc_result.credit_or_exclusion_amount_usd),
            "resulting_tax_usd": str(result.ftc_result.resulting_us_tax_liability_usd),
            "ctc_unlocked": result.ftc_result.ctc_unlocked,
            "actc_refundable_usd": str(result.ftc_result.actc_refundable_amount_usd),
        },
        "feie": {
            "exclusion_usd": str(result.feie_result.credit_or_exclusion_amount_usd),
            "resulting_tax_usd": str(result.feie_result.resulting_us_tax_liability_usd),
            "ctc_unlocked": result.feie_result.ctc_unlocked,
            "actc_refundable_usd": str(result.feie_result.actc_refundable_amount_usd),
        },
    }


@app.get("/api/v1/compliance/flags")
async def compliance_flags_endpoint(
    max_account_balance_usd: str,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    _audit(current_tenant, "/api/v1/compliance/flags")
    flags = compute_compliance_flags(max_account_balance_usd)
    return flags.__dict__


@app.post("/api/v1/submission/tollgate")
async def tollgate_endpoint(
    payload: TollgateRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Muss erfolgreich durchlaufen werden, BEVOR /submission/submit
    aufgerufen werden darf. Server-Secret kommt aus Vault, hier als
    Platzhalter-Injektion markiert.
    """
    _audit(current_tenant, "/api/v1/submission/tollgate")
    server_secret = b"REPLACE_WITH_VAULT_INJECTED_SECRET"  # TODO: Vault-Anbindung

    try:
        waiver = create_liability_waiver(payload.user_id, payload.totp_code, server_secret)
    except TollgateError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc

    return {
        "waiver_hash": waiver.waiver_text_hash,
        "timestamp": waiver.timestamp_unix,
        "signature": waiver.signature,
    }
