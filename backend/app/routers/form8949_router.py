"""
Form 8949 Router — Sales and Other Dispositions of Capital Assets.

POST /api/v1/form8949/calculate – JWT-protected: calculate gains/losses
GET  /api/v1/form8949/overview  – JWT-protected: static overview of Form 8949
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8949 import (
    Transaction,
    Form8949Input,
    calculate_form8949,
    get_form8949_overview,
)

router = APIRouter(tags=["form8949"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class TransactionRequest(BaseModel):
    """A single capital asset transaction."""
    purchase_date: str = Field(
        ...,
        examples=["2024-01-15"],
        description="Purchase date in YYYY-MM-DD format",
    )
    purchase_price: str = Field(
        ...,
        examples=["10000.00"],
        description="Purchase price (cost basis) in USD",
    )
    sale_date: str = Field(
        ...,
        examples=["2024-06-20"],
        description="Sale date in YYYY-MM-DD format",
    )
    sale_price: str = Field(
        ...,
        examples=["12500.00"],
        description="Sale price (proceeds) in USD",
    )
    description: str = Field(
        default="",
        examples=["AAPL"],
        description="Asset description",
    )


class Form8949Request(BaseModel):
    """Request to calculate Form 8949 capital gains/losses."""
    transactions: list[TransactionRequest] = Field(
        ...,
        description="List of capital asset transactions",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_transaction(tx) -> dict:
    """Convert a Form8949Transaction to a JSON-serializable dict."""
    return {
        "description": tx.description,
        "purchase_date": tx.purchase_date,
        "sale_date": tx.sale_date,
        "purchase_price": str(tx.purchase_price),
        "sale_price": str(tx.sale_price),
        "gain_loss": str(tx.gain_loss),
        "holding_period": tx.holding_period,
        "holding_days": tx.holding_days,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate")
async def calculate(
    payload: Form8949Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate Form 8949 short-term and long-term capital gains/losses.

    Requires a valid JWT (Bearer token).
    """
    try:
        transactions = [
            Transaction(
                purchase_date=tx.purchase_date,
                purchase_price=Decimal(tx.purchase_price),
                sale_date=tx.sale_date,
                sale_price=Decimal(tx.sale_price),
                description=tx.description,
            )
            for tx in payload.transactions
        ]
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid transaction data: {exc}") from exc

    inp = Form8949Input(transactions=transactions)
    result = calculate_form8949(inp)

    return {
        "short_term_transactions": [
            _serialize_transaction(tx) for tx in result.short_term_transactions
        ],
        "long_term_transactions": [
            _serialize_transaction(tx) for tx in result.long_term_transactions
        ],
        "short_term_total": str(result.short_term_total),
        "long_term_total": str(result.long_term_total),
        "net_gain_loss": str(result.net_gain_loss),
        "short_term_count": result.short_term_count,
        "long_term_count": result.long_term_count,
        "explanation": result.explanation,
    }


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8949 overview. Requires a valid JWT."""
    return get_form8949_overview()
