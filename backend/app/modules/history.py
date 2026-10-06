"""
Berechnungshistorie – persistente Speicherung und Abfrage von
Steuerberechnungen pro Mandant.

Datei: backend/data/history.json
Format: {"entries": [{id, tenant_id, timestamp, input_data, result_data}, ...]}
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Standardpfad – kann in Tests über Modul-Monkey-Patching überschrieben werden
_DEFAULT_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "history.json"


def _get_data_file() -> Path:
    """Gibt den aktuellen Pfad zur History-Datei zurück (überschreibbar in Tests)."""
    return _DEFAULT_DATA_FILE


def _load(data_file: Path | None = None) -> dict[str, list]:
    path = data_file or _get_data_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return {"entries": []}
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if "entries" not in raw:
        raw["entries"] = []
    return raw


def _save(data: dict[str, list], data_file: Path | None = None) -> None:
    path = data_file or _get_data_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def save_calculation(
    tenant_id: str,
    input_data: dict[str, Any],
    result_data: dict[str, Any],
    *,
    data_file: Path | None = None,
) -> str:
    """
    Speichert eine Steuerberechnung für den angegebenen Mandanten.

    Gibt die neue Berechnungs-ID (UUID4-String) zurück.
    """
    calc_id = str(uuid.uuid4())
    entry: dict[str, Any] = {
        "id": calc_id,
        "tenant_id": tenant_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_data": input_data,
        "result_data": result_data,
    }
    data = _load(data_file)
    data["entries"].append(entry)
    _save(data, data_file)
    return calc_id


def get_calculations(
    tenant_id: str,
    *,
    data_file: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Gibt alle Berechnungen für den angegebenen Mandanten zurück,
    sortiert nach Zeitstempel (neueste zuerst).
    """
    data = _load(data_file)
    tenant_entries = [e for e in data["entries"] if e["tenant_id"] == tenant_id]
    # Neueste zuerst
    tenant_entries.sort(key=lambda e: e["timestamp"], reverse=True)
    return tenant_entries
