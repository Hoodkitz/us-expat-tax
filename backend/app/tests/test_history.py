"""
Tests für das History-Modul und den zugehörigen Router.

- Speichern und Abrufen von Berechnungen
- Mandanten-Isolation (Tenant A sieht nicht Tenant Bs Daten)
- tmp_path-Fixture für Datei-Isolation zwischen Tests
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.modules.history import get_calculations, save_calculation


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _make_input(income: int = 90_000) -> dict:
    return {
        "foreign_earned_income_usd": str(income),
        "german_income_tax_paid_usd": "18000",
        "us_tax_liability_before_credits_usd": "15000",
        "num_qualifying_children": 0,
    }


def _make_result(path: str = "FTC") -> dict:
    return {
        "recommended_path": path,
        "recommendation_reason": "Testresultat",
        "ftc": {
            "credit_usd": "15000",
            "resulting_tax_usd": "0",
            "ctc_unlocked": False,
            "actc_refundable_usd": "0",
        },
        "feie": {
            "exclusion_usd": "90000",
            "resulting_tax_usd": "0",
            "ctc_unlocked": False,
            "actc_refundable_usd": "0",
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_save_and_retrieve_calculation(tmp_path: Path) -> None:
    """Gespeicherte Berechnung kann zurückgelesen werden."""
    data_file = tmp_path / "history.json"
    tenant_id = "tenant-abc-123"

    calc_id = save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(),
        result_data=_make_result(),
        data_file=data_file,
    )

    assert isinstance(calc_id, str)
    assert len(calc_id) > 0

    entries = get_calculations(tenant_id=tenant_id, data_file=data_file)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["id"] == calc_id
    assert entry["tenant_id"] == tenant_id
    assert entry["input_data"]["foreign_earned_income_usd"] == "90000"
    assert entry["result_data"]["recommended_path"] == "FTC"
    assert "timestamp" in entry


def test_save_multiple_calculations_returns_newest_first(tmp_path: Path) -> None:
    """Mehrere Berechnungen werden neueste zuerst zurückgegeben."""
    data_file = tmp_path / "history.json"
    tenant_id = "tenant-order-test"

    id1 = save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=50_000),
        result_data=_make_result("FEIE"),
        data_file=data_file,
    )
    id2 = save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=80_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )

    entries = get_calculations(tenant_id=tenant_id, data_file=data_file)
    assert len(entries) == 2
    # Neueste zuerst – id2 wurde als letztes gespeichert
    assert entries[0]["id"] == id2
    assert entries[1]["id"] == id1


def test_tenant_isolation(tmp_path: Path) -> None:
    """
    Mandanten-Isolation: Tenant A sieht ausschließlich eigene Berechnungen,
    nicht die von Tenant B (und umgekehrt).
    """
    data_file = tmp_path / "history.json"
    tenant_a = "tenant-A-uuid"
    tenant_b = "tenant-B-uuid"

    save_calculation(
        tenant_id=tenant_a,
        input_data=_make_input(income=90_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )
    save_calculation(
        tenant_id=tenant_b,
        input_data=_make_input(income=200_000),
        result_data=_make_result("FEIE"),
        data_file=data_file,
    )
    save_calculation(
        tenant_id=tenant_a,
        input_data=_make_input(income=95_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )

    entries_a = get_calculations(tenant_id=tenant_a, data_file=data_file)
    entries_b = get_calculations(tenant_id=tenant_b, data_file=data_file)

    # Tenant A hat 2 Einträge, Tenant B hat 1 Eintrag
    assert len(entries_a) == 2
    assert len(entries_b) == 1

    # Kein Eintrag von B in As Liste
    for entry in entries_a:
        assert entry["tenant_id"] == tenant_a

    # Kein Eintrag von A in Bs Liste
    for entry in entries_b:
        assert entry["tenant_id"] == tenant_b


def test_empty_history_returns_empty_list(tmp_path: Path) -> None:
    """Keine gespeicherten Berechnungen -> leere Liste, kein Fehler."""
    data_file = tmp_path / "history.json"
    entries = get_calculations(tenant_id="ghost-tenant", data_file=data_file)
    assert entries == []


def test_history_file_created_on_first_save(tmp_path: Path) -> None:
    """Die JSON-Datei wird automatisch angelegt, wenn sie noch nicht existiert."""
    data_file = tmp_path / "subdir" / "history.json"
    assert not data_file.exists()

    save_calculation(
        tenant_id="new-tenant",
        input_data=_make_input(),
        result_data=_make_result(),
        data_file=data_file,
    )

    assert data_file.exists()
    with data_file.open() as fh:
        raw = json.load(fh)
    assert "entries" in raw
    assert len(raw["entries"]) == 1


def test_history_entry_has_required_fields(tmp_path: Path) -> None:
    """Jeder Eintrag enthält die Pflichtfelder id, tenant_id, timestamp, input_data, result_data."""
    data_file = tmp_path / "history.json"
    save_calculation(
        tenant_id="field-check-tenant",
        input_data=_make_input(),
        result_data=_make_result(),
        data_file=data_file,
    )
    entries = get_calculations(tenant_id="field-check-tenant", data_file=data_file)
    assert len(entries) == 1
    entry = entries[0]
    for field in ("id", "tenant_id", "timestamp", "input_data", "result_data"):
        assert field in entry, f"Pflichtfeld '{field}' fehlt im History-Eintrag"
