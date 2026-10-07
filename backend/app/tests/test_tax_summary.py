"""
Tests für das Tax Summary Modul und den zugehörigen Router.

- Gesamtbilanz mit leerer History
- Aggregation mehrerer Berechnungen
- Empfohlene Strategie wird korrekt bestimmt
- Tenant-Isolation
- JSON-Export
- Router-Endpunkte (GET /overview, POST /export)
- Auth-Pflicht (401 ohne Token)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.tax_summary import export_tax_summary_json, get_tax_summary
from app.modules.history import save_calculation


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _make_input(income: int = 90_000, tax_paid: int = 18_000, us_tax: int = 15_000) -> dict:
    return {
        "foreign_earned_income_usd": str(income),
        "german_income_tax_paid_usd": str(tax_paid),
        "us_tax_liability_before_credits_usd": str(us_tax),
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


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def override_auth():
    """Override get_current_tenant for tests."""
    from app.auth.utils import get_current_tenant

    async def mock_get_current_tenant():
        return {
            "tenant_id": "test-tenant-123",
            "email": "test@example.com",
            "tenant_name": "Test Tenant",
        }

    app.dependency_overrides[get_current_tenant] = mock_get_current_tenant
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Modul-Tests
# ---------------------------------------------------------------------------


def test_get_tax_summary_empty_history(tmp_path: Path) -> None:
    """Leere History liefert eine leere Zusammenfassung ohne Fehler."""
    data_file = tmp_path / "history.json"
    summary = get_tax_summary(tenant_id="ghost-tenant", data_file=data_file)

    assert summary["tenant_id"] == "ghost-tenant"
    assert summary["total_calculations"] == 0
    assert summary["total_income_usd"] == "0"
    assert summary["total_tax_paid_usd"] == "0"
    assert summary["total_us_tax_liability_usd"] == "0"
    assert summary["recommended_path"] is None
    assert summary["last_calculation"] is None
    assert summary["calculations"] == []


def test_get_tax_summary_single_calculation(tmp_path: Path) -> None:
    """Eine Berechnung wird korrekt aggregiert."""
    data_file = tmp_path / "history.json"
    tenant_id = "tenant-single"

    save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=90_000, tax_paid=18_000, us_tax=15_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )

    summary = get_tax_summary(tenant_id=tenant_id, data_file=data_file)

    assert summary["tenant_id"] == tenant_id
    assert summary["total_calculations"] == 1
    assert summary["total_income_usd"] == "90000.0"
    assert summary["total_tax_paid_usd"] == "18000.0"
    assert summary["total_us_tax_liability_usd"] == "15000.0"
    assert summary["recommended_path"] == "FTC"
    assert summary["last_calculation"] is not None
    assert summary["last_calculation"]["recommended_path"] == "FTC"
    assert len(summary["calculations"]) == 1


def test_get_tax_summary_multiple_calculations(tmp_path: Path) -> None:
    """Mehrere Berechnungen werden korrekt aggregiert."""
    data_file = tmp_path / "history.json"
    tenant_id = "tenant-multi"

    save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=50_000, tax_paid=10_000, us_tax=8_000),
        result_data=_make_result("FEIE"),
        data_file=data_file,
    )
    save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=80_000, tax_paid=16_000, us_tax=12_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )
    save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=100_000, tax_paid=20_000, us_tax=18_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )

    summary = get_tax_summary(tenant_id=tenant_id, data_file=data_file)

    assert summary["total_calculations"] == 3
    assert summary["total_income_usd"] == "230000.0"
    assert summary["total_tax_paid_usd"] == "46000.0"
    assert summary["total_us_tax_liability_usd"] == "38000.0"
    # FTC kommt 2x vor, FEIE 1x -> FTC wird empfohlen
    assert summary["recommended_path"] == "FTC"
    assert len(summary["calculations"]) == 3


def test_get_tax_summary_tenant_isolation(tmp_path: Path) -> None:
    """Mandanten-Isolation: Tenant A sieht nur eigene Berechnungen."""
    data_file = tmp_path / "history.json"
    tenant_a = "tenant-A"
    tenant_b = "tenant-B"

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

    summary_a = get_tax_summary(tenant_id=tenant_a, data_file=data_file)
    summary_b = get_tax_summary(tenant_id=tenant_b, data_file=data_file)

    assert summary_a["total_calculations"] == 1
    assert summary_a["total_income_usd"] == "90000.0"
    assert summary_b["total_calculations"] == 1
    assert summary_b["total_income_usd"] == "200000.0"


def test_get_tax_summary_recommended_path_tie(tmp_path: Path) -> None:
    """Bei Gleichstand wird ein Pfad ausgewählt (FTC bei 1:1)."""
    data_file = tmp_path / "history.json"
    tenant_id = "tenant-tie"

    save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=50_000),
        result_data=_make_result("FEIE"),
        data_file=data_file,
    )
    save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=80_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )

    summary = get_tax_summary(tenant_id=tenant_id, data_file=data_file)

    # Bei 1:1 wird einer der beiden Pfade zurückgegeben (Counter.most_common)
    assert summary["recommended_path"] in ("FTC", "FEIE")


# ---------------------------------------------------------------------------
# Export-Tests
# ---------------------------------------------------------------------------


def test_export_tax_summary_json(tmp_path: Path) -> None:
    """JSON-Export erstellt eine gültige Datei."""
    data_file = tmp_path / "history.json"
    tenant_id = "tenant-export"

    save_calculation(
        tenant_id=tenant_id,
        input_data=_make_input(income=90_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )

    output_file = tmp_path / "export.json"
    result_path = export_tax_summary_json(
        tenant_id=tenant_id,
        data_file=data_file,
        output_file=output_file,
    )

    assert result_path.exists()
    with result_path.open() as fh:
        data = json.load(fh)

    assert data["tenant_id"] == tenant_id
    assert data["total_calculations"] == 1
    assert data["recommended_path"] == "FTC"


def test_export_tax_summary_json_empty(tmp_path: Path) -> None:
    """Export mit leerer History erstellt trotzdem eine gültige Datei."""
    data_file = tmp_path / "history.json"
    output_file = tmp_path / "export_empty.json"

    result_path = export_tax_summary_json(
        tenant_id="ghost-tenant",
        data_file=data_file,
        output_file=output_file,
    )

    assert result_path.exists()
    with result_path.open() as fh:
        data = json.load(fh)

    assert data["total_calculations"] == 0
    assert data["recommended_path"] is None


# ---------------------------------------------------------------------------
# Router-Tests
# ---------------------------------------------------------------------------


def test_router_overview_endpoint(client: TestClient, override_auth, tmp_path: Path) -> None:
    """GET /api/v1/tax-summary/overview liefert die Zusammenfassung."""
    # Berechnung speichern
    data_file = tmp_path / "history.json"
    save_calculation(
        tenant_id="test-tenant-123",
        input_data=_make_input(income=90_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )

    # Monkey-Patch des History-Pfads
    import app.modules.tax_summary as ts_module
    original = ts_module._HISTORY_FILE
    ts_module._HISTORY_FILE = data_file
    try:
        response = client.get("/api/v1/tax-summary/overview")
    finally:
        ts_module._HISTORY_FILE = original

    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "test-tenant-123"
    assert data["total_calculations"] == 1
    assert data["recommended_path"] == "FTC"


def test_router_overview_requires_auth(client: TestClient) -> None:
    """GET /api/v1/tax-summary/overview ohne Token liefert 401."""
    response = client.get("/api/v1/tax-summary/overview")
    assert response.status_code == 401


def test_router_export_endpoint(client: TestClient, override_auth, tmp_path: Path) -> None:
    """POST /api/v1/tax-summary/export erstellt einen JSON-Export."""
    data_file = tmp_path / "history.json"
    save_calculation(
        tenant_id="test-tenant-123",
        input_data=_make_input(income=90_000),
        result_data=_make_result("FTC"),
        data_file=data_file,
    )

    import app.modules.tax_summary as ts_module
    original = ts_module._HISTORY_FILE
    ts_module._HISTORY_FILE = data_file
    try:
        response = client.post(
            "/api/v1/tax-summary/export",
            json={"format": "json"},
        )
    finally:
        ts_module._HISTORY_FILE = original

    assert response.status_code == 200
    data = response.json()
    assert "export_id" in data
    assert "file_path" in data
    assert "summary" in data
    assert data["summary"]["total_calculations"] == 1


def test_router_export_invalid_format(client: TestClient, override_auth) -> None:
    """POST /api/v1/tax-summary/export mit ungültigem Format liefert 400."""
    response = client.post(
        "/api/v1/tax-summary/export",
        json={"format": "xml"},
    )
    assert response.status_code == 400


def test_router_export_requires_auth(client: TestClient) -> None:
    """POST /api/v1/tax-summary/export ohne Token liefert 401."""
    response = client.post(
        "/api/v1/tax-summary/export",
        json={"format": "json"},
    )
    assert response.status_code == 401
