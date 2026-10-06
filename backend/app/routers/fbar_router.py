"""
FBAR API Router – FinCEN 114 JSON and PDF endpoints.
All routes require a valid JWT (Depends(get_current_tenant)).
"""
from __future__ import annotations

import tempfile
import os
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.auth.utils import get_current_tenant
from app.modules.fbar import FBARReport, fbar_json, generate_fbar_pdf

router = APIRouter(tags=["fbar"])


@router.post("/generate")
async def generate_fbar_json(
    report: FBARReport,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Returns the FBAR data as JSON.
    """
    data = fbar_json(report)
    return {
        "fbar_data": data,
        "message": (
            "FBAR data generated successfully. "
            "File electronically at bsaefiling.fincen.treas.gov."
        ),
    }


@router.post("/generate/pdf")
async def generate_fbar_pdf_endpoint(
    report: FBARReport,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FileResponse:
    """
    Generates a FinCEN 114 summary PDF and returns it as a file download.
    """
    pdf_bytes = generate_fbar_pdf(report)

    # Write to a named temp file (FileResponse needs a path)
    tmp = tempfile.NamedTemporaryFile(
        suffix=f"_fbar_{report.year}.pdf",
        delete=False,
    )
    try:
        tmp.write(pdf_bytes)
        tmp.flush()
        tmp_path = tmp.name
    finally:
        tmp.close()

    filename = f"fbar_{report.year}.pdf"
    return FileResponse(
        path=tmp_path,
        media_type="application/pdf",
        filename=filename,
        background=None,  # keep file alive until response is sent
    )
