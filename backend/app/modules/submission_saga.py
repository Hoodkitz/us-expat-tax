"""
Modul 5 - Orchestrierung & "One-Click"-Submission.

Enthält:
  1. Ein kryptografisch geloggtes Haftungsfreistellungs-"Tollgate" mit
     Mock-2FA (TOTP), das VOR jeder Übermittlung durchlaufen werden muss.
  2. Ein Saga-Pattern mit idempotentem Polling für die asynchrone
     ELSTER-Übermittlung via Erica-Service (kein synchroner ERiC-Call).
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger("submission.saga")


# ---------------------------------------------------------------------------
# Tollgate: Haftungsfreistellung + Mock-2FA
# ---------------------------------------------------------------------------

class TollgateError(RuntimeError):
    pass


@dataclass(frozen=True)
class LiabilityWaiverRecord:
    user_id: str
    waiver_text_hash: str
    timestamp_unix: int
    totp_verified: bool
    signature: str  # HMAC über (user_id, hash, timestamp) mit Server-Secret


WAIVER_TEXT = (
    "Ich bestätige, dass ich die berechneten Werte geprüft habe und die "
    "Übermittlung an ELSTER und den US-IRS eigenverantwortlich freigebe. "
    "Diese App leistet keine Steuerberatung."
)


def _mock_verify_totp(user_id: str, submitted_code: str, server_secret: bytes) -> bool:
    """
    MOCK-Funktion für FIDO2/TOTP-Verifikation. In Produktion durch
    echte WebAuthn/FIDO2-Assertion-Verifikation oder eine RFC-6238-
    konforme TOTP-Bibliothek (z.B. pyotp) mit Zeitfenster-Toleranz
    ersetzen. Hier: einfache deterministische Simulation für Tests.
    """
    window = int(time.time() // 30)
    expected = hmac.new(
        server_secret, f"{user_id}:{window}".encode(), hashlib.sha256
    ).hexdigest()[:6]
    return hmac.compare_digest(expected, submitted_code)


def create_liability_waiver(
    user_id: str,
    totp_code: str,
    server_secret: bytes,
) -> LiabilityWaiverRecord:
    """
    Erzeugt einen kryptografisch signierten, unveränderlichen Log-Eintrag
    der Haftungsfreistellung. Wirft TollgateError, wenn 2FA fehlschlägt -
    KEINE Übermittlung ohne erfolgreiche Verifikation möglich.
    """
    if not _mock_verify_totp(user_id, totp_code, server_secret):
        raise TollgateError("2FA-Verifikation fehlgeschlagen. Übermittlung blockiert.")

    waiver_hash = hashlib.sha256(WAIVER_TEXT.encode()).hexdigest()
    timestamp = int(time.time())
    signature = hmac.new(
        server_secret,
        f"{user_id}:{waiver_hash}:{timestamp}".encode(),
        hashlib.sha256,
    ).hexdigest()

    record = LiabilityWaiverRecord(
        user_id=user_id,
        waiver_text_hash=waiver_hash,
        timestamp_unix=timestamp,
        totp_verified=True,
        signature=signature,
    )
    logger.info(
        "Haftungsfreistellung erstellt: user=%s hash=%s ts=%s sig=%s...",
        user_id, waiver_hash, timestamp, signature[:12],
    )
    return record


# ---------------------------------------------------------------------------
# Saga: Idempotentes Polling der ELSTER-Übermittlung
# ---------------------------------------------------------------------------

class SubmissionState(str, Enum):
    PENDING = "PENDING"
    ELSTER_SENT = "ELSTER_SENT"
    ELSTER_TIMEOUT_POLLING = "ELSTER_TIMEOUT_POLLING"
    ELSTER_TRANSFERTICKET_RECEIVED = "ELSTER_TRANSFERTICKET_RECEIVED"
    US_FORMS_GENERATED = "US_FORMS_GENERATED"
    FAILED = "FAILED"


class SagaError(RuntimeError):
    pass


@dataclass
class SubmissionSagaState:
    submission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: SubmissionState = SubmissionState.PENDING
    elster_transferticket: str | None = None
    history: list[str] = field(default_factory=list)

    def transition(self, new_state: SubmissionState, note: str = "") -> None:
        logger.info("Saga %s: %s -> %s (%s)", self.submission_id, self.state, new_state, note)
        self.state = new_state
        self.history.append(f"{new_state.value}: {note}")


class ElsterSubmissionSaga:
    """
    Implementiert: Payload verschlüsselt senden -> bei 504 asynchron per
    UUID pollen, bis Transferticket vorliegt -> erst danach US-Formulare
    entriegeln. Jeder Schritt ist idempotent über die submission_id.
    """

    def __init__(
        self,
        erica_client: httpx.AsyncClient,
        max_poll_attempts: int = 30,
        poll_interval_s: float = 5.0,
    ):
        self._client = erica_client
        self._max_poll_attempts = max_poll_attempts
        self._poll_interval_s = poll_interval_s

    async def submit(
        self,
        encrypted_payload: bytes,
        waiver: LiabilityWaiverRecord,
    ) -> SubmissionSagaState:
        if not waiver.totp_verified:
            raise SagaError("Übermittlung ohne verifizierte Haftungsfreistellung blockiert.")

        saga = SubmissionSagaState()

        try:
            response = await self._client.post(
                "/eric/submit",
                content=encrypted_payload,
                headers={
                    "Idempotency-Key": saga.submission_id,
                    "Content-Type": "application/octet-stream",
                },
                timeout=10.0,
            )
        except httpx.TimeoutException:
            saga.transition(
                SubmissionState.ELSTER_TIMEOUT_POLLING,
                "Initialer Request timeout - starte Polling-Schleife",
            )
            return await self._poll_until_ticket(saga)

        if response.status_code == 504:
            saga.transition(
                SubmissionState.ELSTER_TIMEOUT_POLLING,
                "HTTP 504 vom Erica-Service - starte Polling-Schleife",
            )
            return await self._poll_until_ticket(saga)

        response.raise_for_status()
        payload = response.json()
        ticket = payload.get("transferticket")
        if ticket:
            saga.elster_transferticket = ticket
            saga.transition(
                SubmissionState.ELSTER_TRANSFERTICKET_RECEIVED,
                "Synchron erhalten",
            )
            return saga

        # Kein Ticket, kein Timeout -> asynchron angenommen, UUID vorhanden
        saga.transition(SubmissionState.ELSTER_SENT, "Async angenommen, polle Status")
        return await self._poll_until_ticket(saga)

    async def _poll_until_ticket(self, saga: SubmissionSagaState) -> SubmissionSagaState:
        for attempt in range(1, self._max_poll_attempts + 1):
            try:
                status_resp = await self._client.get(
                    f"/eric/status/{saga.submission_id}", timeout=10.0
                )
            except httpx.TransportError as exc:
                logger.warning("Polling-Versuch %d fehlgeschlagen: %s", attempt, exc)
                await asyncio.sleep(self._poll_interval_s)
                continue

            if status_resp.status_code == 200:
                data = status_resp.json()
                ticket = data.get("transferticket")
                if ticket:
                    saga.elster_transferticket = ticket
                    saga.transition(
                        SubmissionState.ELSTER_TRANSFERTICKET_RECEIVED,
                        f"Nach {attempt} Poll-Versuchen erhalten",
                    )
                    return saga

            await asyncio.sleep(self._poll_interval_s)

        saga.transition(
            SubmissionState.FAILED,
            f"Kein Transferticket nach {self._max_poll_attempts} Versuchen",
        )
        raise SagaError(
            f"Submission {saga.submission_id}: ELSTER-Transferticket nicht erhalten. "
            "US-Logik bleibt verriegelt."
        )

    def unlock_us_forms(self, saga: SubmissionSagaState) -> None:
        """
        Harte Vorbedingung: darf NUR nach erfolgreichem DE-Transferticket
        aufgerufen werden. Wird hier zusätzlich zur Aufrufer-Disziplin
        defensiv im Code selbst erzwungen.
        """
        if saga.state != SubmissionState.ELSTER_TRANSFERTICKET_RECEIVED:
            raise SagaError(
                "US-Formulare (1040/1116) dürfen erst nach erfolgreichem "
                f"ELSTER-Transferticket generiert werden. Aktueller Status: {saga.state}"
            )
        saga.transition(
            SubmissionState.US_FORMS_GENERATED,
            "Form 1040/1116 PDF-Generierung entriegelt",
        )
