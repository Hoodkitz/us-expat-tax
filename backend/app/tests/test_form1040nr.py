"""
Tests für Form 1040-NR: U.S. Nonresident Alien Income Tax Return
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ===========================================================================
# Helper
# ===========================================================================

def _get_auth_headers() -> dict:
    """Registriert einen Test-Mandanten und gibt Auth-Header zurück."""
    # Registrieren
    reg_response = client.post(
        "/auth/register",
        json={
            "email": "test1040nr@example.com",
            "password": "testpass123",
            "tenant_name": "Test 1040NR",
        },
    )
    if reg_response.status_code == 409:
        # Bereits registriert
        pass
    else:
        assert reg_response.status_code == 201

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test1040nr@example.com",
            "password": "testpass123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# Filing Requirement Tests
# ===========================================================================

class TestFilingRequirement:
    """Tests für POST /api/v1/form1040nr/filing-requirement"""

    def test_filing_required_with_eci(self):
        """ECI-Einkommen erfordert immer Form 1040-NR."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            json={
                "tax_year": 2024,
                "us_source_income": 0,
                "effectively_connected_income": 50000,
                "fdap_income": 0,
                "tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_required"] is True
        assert any("ECI" in r for r in data["reasons"])

    def test_filing_required_with_fdap_no_withholding(self):
        """FDAP ohne Quellensteuer erfordert Form 1040-NR."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            json={
                "tax_year": 2024,
                "us_source_income": 0,
                "effectively_connected_income": 0,
                "fdap_income": 10000,
                "tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_required"] is True
        assert any("FDAP" in r for r in data["reasons"])

    def test_filing_not_required_with_sufficient_withholding(self):
        """FDAP mit ausreichender Quellensteuer erfordert kein Form 1040-NR."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            json={
                "tax_year": 2024,
                "us_source_income": 0,
                "effectively_connected_income": 0,
                "fdap_income": 10000,
                "tax_withheld": 3000,  # 30% Quellensteuer
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_required"] is False

    def test_filing_required_with_us_source_income_no_treaty(self):
        """US-Quelleinkommen ohne Abkommen erfordert Form 1040-NR."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            json={
                "tax_year": 2024,
                "us_source_income": 5000,
                "effectively_connected_income": 0,
                "fdap_income": 0,
                "tax_withheld": 0,
                "is_treaty_country_resident": False,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_required"] is True

    def test_filing_not_required_with_treaty(self):
        """US-Quelleinkommen mit Abkommen kann befreit sein."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            json={
                "tax_year": 2024,
                "us_source_income": 5000,
                "effectively_connected_income": 0,
                "fdap_income": 0,
                "tax_withheld": 0,
                "is_treaty_country_resident": True,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_required"] is False
        assert any("Abkommen" in r for r in data["reasons"])

    def test_no_filing_required_no_income(self):
        """Kein Einkommen = keine Pflicht."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            json={
                "tax_year": 2024,
                "us_source_income": 0,
                "effectively_connected_income": 0,
                "fdap_income": 0,
                "tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_required"] is False

    def test_filing_requirement_unauthorized(self):
        """Ohne Token wird der Endpunkt nicht aufgerufen."""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            json={
                "tax_year": 2024,
                "us_source_income": 50000,
                "effectively_connected_income": 0,
                "fdap_income": 0,
                "tax_withheld": 0,
            },
        )
        assert response.status_code == 401


# ===========================================================================
# Tax Calculation Tests
# ===========================================================================

class TestTaxCalculation:
    """Tests für POST /api/v1/form1040nr/calculate"""

    def test_basic_tax_calculation(self):
        """Grundlegende Steuerberechnung."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 50000,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 50000
        assert data["taxable_income"] == 50000
        assert data["tax_before_credits"] > 0
        assert data["tax_after_credits"] > 0
        assert data["tax_due"] > 0

    def test_tax_calculation_with_deductions(self):
        """Steuerberechnung mit Abzügen."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 50000,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 10000,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_deductions"] == 10000
        assert data["taxable_income"] == 40000

    def test_tax_calculation_with_credits(self):
        """Steuerberechnung mit Gutschriften."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 50000,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 5000,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_credits"] == 5000
        assert data["tax_after_credits"] < data["tax_before_credits"]

    def test_tax_calculation_with_withholding(self):
        """Steuerberechnung mit einbehaltenen Steuern."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 50000,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 10000,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["federal_tax_withheld"] == 10000
        assert data["tax_due"] == max(0, data["tax_after_credits"] - 10000)

    def test_tax_calculation_refund(self):
        """Rückerstattung wenn zu viel einbehalten wurde."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 50000,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 20000,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["refund"] > 0
        assert data["tax_due"] == 0

    def test_tax_calculation_treaty_rate(self):
        """Steuerberechnung mit Steuerabkommen."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 50000,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 0,
                "is_treaty_country_resident": True,
                "treaty_reduced_rate": 0.15,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["treaty_applied"] is True
        assert data["treaty_rate"] == 0.15
        assert data["tax_before_credits"] == 50000 * 0.15

    def test_tax_calculation_multiple_income_types(self):
        """Steuerberechnung mit mehreren Einkunftsarten."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 40000,
                "interest_income": 5000,
                "dividend_income": 3000,
                "capital_gains": 2000,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 50000
        assert data["income_breakdown"]["wages_salaries"] == 40000
        assert data["income_breakdown"]["interest_income"] == 5000
        assert data["income_breakdown"]["dividend_income"] == 3000
        assert data["income_breakdown"]["capital_gains"] == 2000

    def test_tax_calculation_zero_income(self):
        """Steuerberechnung ohne Einkommen."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 0,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 0
        assert data["tax_before_credits"] == 0
        assert data["tax_due"] == 0

    def test_tax_calculation_unauthorized(self):
        """Ohne Token wird der Endpunkt nicht aufgerufen."""
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 50000,
            },
        )
        assert response.status_code == 401

    def test_tax_calculation_married_filing_status(self):
        """Steuerberechnung mit verheiratetem Status."""
        headers = _get_auth_headers()
        response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Married Filing Jointly",
                "wages_salaries": 100000,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 0,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 0,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_status"] == "Married Filing Jointly"
        assert data["total_income"] == 100000


# ===========================================================================
# Overview Tests
# ===========================================================================

class TestOverview:
    """Tests für GET /api/v1/form1040nr/overview"""

    def test_overview_returns_data(self):
        """Übersicht liefert alle erwarteten Felder."""
        headers = _get_auth_headers()
        response = client.get(
            "/api/v1/form1040nr/overview",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form_name"] == "Form 1040-NR"
        assert "form_title" in data
        assert "description" in data
        assert "filing_deadline" in data
        assert "who_must_file" in data
        assert "income_types" in data
        assert "tax_rates" in data
        assert "deductions_available" in data
        assert "credits_available" in data
        assert "special_rules" in data

    def test_overview_unauthorized(self):
        """Ohne Token wird der Endpunkt nicht aufgerufen."""
        response = client.get("/api/v1/form1040nr/overview")
        assert response.status_code == 401


# ===========================================================================
# Integration Tests
# ===========================================================================

class TestIntegration:
    """Integrationstests für Form 1040-NR"""

    def test_full_workflow(self):
        """Kompletter Workflow: Filing Check -> Calculate -> Overview."""
        headers = _get_auth_headers()

        # 1. Filing Check
        filing_response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            json={
                "tax_year": 2024,
                "us_source_income": 0,
                "effectively_connected_income": 60000,
                "fdap_income": 5000,
                "tax_withheld": 1500,
            },
            headers=headers,
        )
        assert filing_response.status_code == 200
        filing_data = filing_response.json()
        assert filing_data["filing_required"] is True

        # 2. Calculate
        calc_response = client.post(
            "/api/v1/form1040nr/calculate",
            json={
                "tax_year": 2024,
                "filing_status": "Single",
                "wages_salaries": 60000,
                "interest_income": 0,
                "dividend_income": 0,
                "capital_gains": 0,
                "business_income": 0,
                "rental_income": 0,
                "other_income": 5000,
                "itemized_deductions": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "foreign_tax_credit": 0,
                "child_tax_credit": 0,
                "other_credits": 0,
                "federal_tax_withheld": 1500,
            },
            headers=headers,
        )
        assert calc_response.status_code == 200
        calc_data = calc_response.json()
        assert calc_data["total_income"] == 65000

        # 3. Overview
        overview_response = client.get(
            "/api/v1/form1040nr/overview",
            headers=headers,
        )
        assert overview_response.status_code == 200
        overview_data = overview_response.json()
        assert overview_data["form_name"] == "Form 1040-NR"
