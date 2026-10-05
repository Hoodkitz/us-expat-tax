"""
Modul 2 - PSD2/Tink-API Interface (Read-Only).

Ruft ausschließlich Kontoumsätze im Read-Only-Scope ab (kein
Zahlungsauslöse-Scope!). Kategorisiert Werbungskosten deterministisch
über eine Merchant-Kategorie-Zuordnungstabelle; das LLM ist hier NICHT
beteiligt (Kategorisierung ist eine Lookup-Operation, kein NLP-Problem).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

import httpx

logger = logging.getLogger("psd2.tink")

TINK_API_BASE = "https://api.tink.com/data/v2"

# Read-Only Scopes -- explizit KEIN "payments:write" oder ähnliches
REQUIRED_SCOPES = [
    "accounts:read",
    "transactions:read",
    "provider-consents:read",
]


class WerbungskostenKategorie(str, Enum):
    ARBEITSMITTEL = "Arbeitsmittel"
    FAHRTKOSTEN = "Fahrtkosten"
    FORTBILDUNG = "Fortbildung"
    HOMEOFFICE = "Homeoffice-Pauschale"
    FACHLITERATUR = "Fachliteratur"
    SONSTIGE = "Sonstige Werbungskosten"
    NICHT_ABZUGSFAEHIG = "Nicht abzugsfähig"


# Deterministische Merchant-Category-Code (MCC) -> Kategorie-Zuordnung.
# In Produktion aus versionierter Konfigurationsdatei laden.
MCC_TO_KATEGORIE: dict[str, WerbungskostenKategorie] = {
    "5942": WerbungskostenKategorie.FACHLITERATUR,   # Buchhandlungen
    "5734": WerbungskostenKategorie.ARBEITSMITTEL,   # Computersoftware
    "4111": WerbungskostenKategorie.FAHRTKOSTEN,     # Nahverkehr
    "8299": WerbungskostenKategorie.FORTBILDUNG,     # Bildungsdienstleistungen
    "5411": WerbungskostenKategorie.NICHT_ABZUGSFAEHIG,  # Supermärkte
}


@dataclass(frozen=True)
class TinkTransaction:
    transaction_id: str
    booking_date: date
    amount_eur: Decimal
    merchant_category_code: str | None
    description: str


@dataclass(frozen=True)
class KategorisierteTransaktion:
    transaction: TinkTransaction
    kategorie: WerbungskostenKategorie
    automatisch_kategorisiert: bool


class TinkReadOnlyClient:
    """
    Read-Only Wrapper um die Tink-API. Der OAuth-Token wird über Vault
    bezogen (nicht in diesem Modul verwaltet) und hier nur konsumiert.
    """

    def __init__(self, access_token: str, timeout_s: float = 10.0):
        self._token = access_token
        self._client = httpx.AsyncClient(
            base_url=TINK_API_BASE,
            timeout=timeout_s,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def fetch_transactions(
        self, account_id: str, from_date: date, to_date: date
    ) -> list[TinkTransaction]:
        """Read-Only Abruf. Wirft bei Nicht-2xx-Status, kein stilles Verschlucken."""
        response = await self._client.get(
            "/transactions",
            params={
                "accountIdIn": account_id,
                "bookedDateGte": from_date.isoformat(),
                "bookedDateLte": to_date.isoformat(),
            },
        )
        response.raise_for_status()
        payload = response.json()

        transactions: list[TinkTransaction] = []
        for item in payload.get("transactions", []):
            transactions.append(
                TinkTransaction(
                    transaction_id=item["id"],
                    booking_date=date.fromisoformat(item["dates"]["booked"]),
                    amount_eur=Decimal(str(item["amount"]["value"]["unscaledValue"]))
                    / Decimal(10) ** int(item["amount"]["value"]["scale"]),
                    merchant_category_code=item.get("merchantInformation", {}).get(
                        "categoryCode"
                    ),
                    description=item.get("descriptions", {}).get(
                        "display", ""
                    ),
                )
            )
        return transactions

    async def aclose(self) -> None:
        await self._client.aclose()


def kategorisiere_transaktion(tx: TinkTransaction) -> KategorisierteTransaktion:
    """Rein deterministisches Lookup, kein LLM."""
    if tx.merchant_category_code and tx.merchant_category_code in MCC_TO_KATEGORIE:
        return KategorisierteTransaktion(
            transaction=tx,
            kategorie=MCC_TO_KATEGORIE[tx.merchant_category_code],
            automatisch_kategorisiert=True,
        )
    return KategorisierteTransaktion(
        transaction=tx,
        kategorie=WerbungskostenKategorie.SONSTIGE,
        automatisch_kategorisiert=False,  # -> UI muss manuelle Zuordnung anfordern
    )
