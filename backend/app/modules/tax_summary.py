"""
Tax Summary – Gesamtbilanz aller Steuerformulare.

Aggregiert die Berechnungshistorie und erstellt eine Übersicht über
alle gespeicherten Steuerberechnungen pro Mandant.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.history import get_calculations

# Standardpfad zur History-Datei
_HISTORY_FILE = Path(__file__).parent.parent.parent / "data" / "history.json"


def get_tax_summary(tenant_id: str, *, data_file: Path | None = None) -> dict[str, Any]:
    """
    Erstellt eine Gesamtbilanz aller Steuerberechnungen für einen Mandanten.

    Args:
        tenant_id: Die Mandanten-ID
        data_file: Optionaler Pfad zur History-Datei (für Tests)

    Returns:
        Ein Dictionary mit der Zusammenfassung aller Berechnungen
    """
    file_path = data_file or _HISTORY_FILE
    entries = get_calculations(tenant_id=tenant_id, data_file=file_path)

    if not entries:
        return {
            "tenant_id": tenant_id,
            "total_calculations": 0,
            "total_income_usd": "0",
            "total_tax_paid_usd": "0",
            "total_us_tax_liability_usd": "0",
            "recommended_path": None,
            "last_calculation": None,
            "calculations": [],
        }

    # Aggregiere die Daten
    total_income = 0.0
    total_tax_paid = 0.0
    total_us_tax_liability = 0.0
    recommended_paths: list[str] = []

    for entry in entries:
        input_data = entry.get("input_data", {})
        result_data = entry.get("result_data", {})

        # Extrahiere Einkommen
        income_str = input_data.get("foreign_earned_income_usd", "0")
        try:
            income = float(income_str)
        except (ValueError, TypeError):
            income = 0.0
        total_income += income

        # Extrahiere gezahlte deutsche Steuern
        tax_paid_str = input_data.get("german_income_tax_paid_usd", "0")
        try:
            tax_paid = float(tax_paid_str)
        except (ValueError, TypeError):
            tax_paid = 0.0
        total_tax_paid += tax_paid

        # Extrahiere US-Steuerpflicht
        us_tax_str = input_data.get("us_tax_liability_before_credits_usd", "0")
        try:
            us_tax = float(us_tax_str)
        except (ValueError, TypeError):
            us_tax = 0.0
        total_us_tax_liability += us_tax

        # Sammle empfohlene Pfade
        path = result_data.get("recommended_path")
        if path:
            recommended_paths.append(path)

    # Bestimme den häufigsten empfohlenen Pfad
    recommended_path = None
    if recommended_paths:
        from collections import Counter
        path_counts = Counter(recommended_paths)
        recommended_path = path_counts.most_common(1)[0][0]

    # Letzte Berechnierung
    last_calc = entries[0] if entries else None
    last_calculation = None
    if last_calc:
        last_calculation = {
            "id": last_calc.get("id"),
            "timestamp": last_calc.get("timestamp"),
            "recommended_path": last_calc.get("result_data", {}).get("recommended_path"),
        }

    return {
        "tenant_id": tenant_id,
        "total_calculations": len(entries),
        "total_income_usd": str(total_income),
        "total_tax_paid_usd": str(total_tax_paid),
        "total_us_tax_liability_usd": str(total_us_tax_liability),
        "recommended_path": recommended_path,
        "last_calculation": last_calculation,
        "calculations": [
            {
                "id": e.get("id"),
                "timestamp": e.get("timestamp"),
                "recommended_path": e.get("result_data", {}).get("recommended_path"),
                "income_usd": e.get("input_data", {}).get("foreign_earned_income_usd", "0"),
            }
            for e in entries
        ],
    }


def export_tax_summary_json(
    tenant_id: str,
    *,
    data_file: Path | None = None,
    output_file: Path | None = None,
) -> Path:
    """
    Exportiert die Steuerübersicht als JSON-Datei.

    Args:
        tenant_id: Die Mandanten-ID
        data_file: Optionaler Pfad zur History-Datei
        output_file: Optionaler Pfad für die Ausgabedatei

    Returns:
        Pfad zur exportierten JSON-Datei
    """
    summary = get_tax_summary(tenant_id, data_file=data_file)

    if output_file is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = Path(__file__).parent.parent.parent / "data" / f"tax_summary_{tenant_id}_{timestamp}.json"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    return output_file
