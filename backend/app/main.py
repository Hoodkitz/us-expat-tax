"""
FastAPI-Entrypoint. Verdrahtet Module 1-5. Bindet NUR an
127.0.0.1 innerhalb des Containers - der Linkerd-Proxy-Sidecar
übernimmt TLS-Termination und mTLS zu anderen Mesh-Teilnehmern
(siehe docker-compose.yml).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

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
    version="0.1.0",
)


class TaxEvaluationRequest(BaseModel):
    foreign_earned_income_usd: str = Field(..., examples=["90000"])
    german_income_tax_paid_usd: str = Field(..., examples=["18000"])
    us_tax_liability_before_credits_usd: str = Field(..., examples=["15000"])
    num_qualifying_children: int = Field(0, ge=0, le=20)


class TollgateRequest(BaseModel):
    user_id: str
    totp_code: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/tax/evaluate")
async def evaluate_tax_endpoint(payload: TaxEvaluationRequest) -> dict:
    """
    Reiner Delegations-Endpunkt an die deterministische Steuer-Engine.
    Kein LLM beteiligt.
    """
    import sympy as sp

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
async def compliance_flags_endpoint(max_account_balance_usd: str) -> dict:
    flags = compute_compliance_flags(max_account_balance_usd)
    return flags.__dict__


@app.post("/api/v1/submission/tollgate")
async def tollgate_endpoint(payload: TollgateRequest) -> dict:
    """
    Muss erfolgreich durchlaufen werden, BEVOR /submission/submit
    aufgerufen werden darf. Server-Secret kommt aus Vault, hier als
    Platzhalter-Injektion markiert.
    """
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
