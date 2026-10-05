"""
Pydantic-Modelle für die Mandanten-Authentifizierung (JWT).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TenantRegister(BaseModel):
    """Registrierungsanfrage für einen neuen Mandanten."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    tenant_name: str = Field(..., min_length=1, description="Firmen- oder Privatname")


class TenantLogin(BaseModel):
    """Login-Anfrage."""
    email: EmailStr
    password: str


class TenantOut(BaseModel):
    """Öffentliche Mandanten-Darstellung (kein Passwort)."""
    email: EmailStr
    tenant_name: str
    tenant_id: uuid.UUID
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT-Token-Antwort."""
    access_token: str
    token_type: str = "bearer"
