"""
Form 8833 Treaty-Based Return Position Disclosure Router.

POST /api/v1/form8833/filing-requirement  – Check if Form 8833 filing is required
POST /api/v1/form8833/disclosure          – Create treaty position disclosure
GET  /api/v1/form8833/overview            – Form 8833 overview and explanation
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.modules.form8833 import (
    FilingRequirementInput,
    DisclosureInput,
    PositionType,
    check_filing_requirement,
    create_disclosure,
    get_overview,
)

router = APIRouter(tags=["form8833"])

# ---------------------------------------------------------------------------
# Request models (for API documentation)
# ---------------------------------------------------------------------------

class FilingRequirementRequest(BaseModel):
    treaty_country: str = Field(..., examples=["DE"], description="ISO 2-letter country code")
    treaty_article: str = Field(..., examples=["Article 15"], description="Treaty article number")
    position_type: PositionType = Field(..., examples=["RESIDENCE"], description="Type of treaty position")

class DisclosureRequest(BaseModel):
    treaty_country: str = Field(..., examples=["DE"], description="ISO 2-letter country code")
    treaty_article: str = Field(..., examples=["Article 4"], description="Treaty article")
    treaty_provision: str = Field(
        ..., 
        examples=["A person is resident where they have a permanent home available"],
        description="Specific treaty provision text"
    )
    taxpayer_position: str = Field(
        ...,
        examples=["I am a resident of Germany under Article 4 due to permanent home and center of vital interests"],
        description="Taxpayer's position and interpretation"
    )
    law_overruled: str = Field(
        ...,
        examples=["IRC §7701(b) - Substantial Presence Test"],
        description="U.S. Code section overruled by treaty"
    )

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/filing-requirement")
async def filing_requirement(payload: FilingRequirementRequest) -> dict:
    """
    Check if Form 8833 filing is required for a treaty position.
    
    Returns filing requirement status, reason, deadline, and penalty information.
    Public endpoint — no JWT required.
    """
    inp = FilingRequirementInput(
        treaty_country=payload.treaty_country,
        treaty_article=payload.treaty_article,
        position_type=payload.position_type,
    )
    result = check_filing_requirement(inp)
    return result.model_dump()

@router.post("/disclosure")
async def disclosure(payload: DisclosureRequest) -> dict:
    """
    Create a treaty position disclosure for Form 8833.
    
    Returns disclosure summary, reporting requirements, and penalty warnings.
    Public endpoint — no JWT required.
    """
    inp = DisclosureInput(
        treaty_country=payload.treaty_country,
        treaty_article=payload.treaty_article,
        treaty_provision=payload.treaty_provision,
        taxpayer_position=payload.taxpayer_position,
        law_overruled=payload.law_overruled,
    )
    result = create_disclosure(inp)
    return result.model_dump()

@router.get("/overview")
async def overview() -> dict:
    """
    Get overview of Form 8833 requirements and common treaty positions.
    
    Returns description, common countries, articles, and filing requirements.
    Public endpoint — no JWT required.
    """
    result = get_overview()
    return result.model_dump()
