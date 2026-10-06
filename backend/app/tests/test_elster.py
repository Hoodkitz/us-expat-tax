"""
Tests für ELSTER Mock-Integration.
"""

import pytest
from app.modules.elster_mock import test_elster_connection, get_elster_info


def test_elster_connection_mock():
    """Test ELSTER-Verbindungstest (Mock)."""
    result = test_elster_connection()
    
    assert result["status"] == "connected_mock"
    assert "timestamp" in result
    assert "certificate" in result
    assert result["certificate"]["issuer"] == "MOCK-CA-ELSTER"
    assert result["test_tax_number"] == "9198011310010"
    assert "note" in result
    assert "Mock" in result["note"]


def test_elster_info_endpoint():
    """Test ELSTER Info-Endpoint."""
    result = get_elster_info()
    
    assert result["integration_status"] == "mock"
    assert "available_endpoints" in result
    assert len(result["available_endpoints"]) == 2
    
    # Prüfe test-connection endpoint
    test_conn_endpoint = next(
        e for e in result["available_endpoints"] 
        if e["path"] == "/api/v1/elster/test-connection"
    )
    assert test_conn_endpoint["method"] == "POST"
    assert test_conn_endpoint["status"] == "mock"
    
    # Prüfe info endpoint
    info_endpoint = next(
        e for e in result["available_endpoints"] 
        if e["path"] == "/api/v1/elster/info"
    )
    assert info_endpoint["method"] == "GET"
    assert info_endpoint["status"] == "active"
    
    # Prüfe Requirements
    assert "required_for_production" in result
    assert "ELSTER ERiC-Library Integration" in result["required_for_production"]
    assert result["documentation"] == "https://www.elster.de/elsterweb/entwickler"
