"""
Pytest tests for Form 3520-A Foreign Trust Annual Information Return endpoints.
Tests all endpoints: filing-requirement, trust-activity, beneficiary-reporting, penalty-calculator, overview.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.utils import create_access_token


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Generate a valid JWT token for testing."""
    return create_access_token({"tenant_id": "test-tenant-001", "sub": "test-user@example.com"})


@pytest.fixture
def auth_headers(auth_token):
    """HTTP headers with Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# Test /overview (public endpoint, no auth required)
# ---------------------------------------------------------------------------

def test_overview_success(client):
    """Test the public overview endpoint."""
    response = client.get("/api/v1/form3520a/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["form"] == "Form 3520-A"
    assert "Annual Information Return of Foreign Trust" in data["title"]
    assert "filing_deadline" in data
    assert "penalties" in data
    assert data["penalties"]["base_penalty_usd"] == 10_000.0
    assert "35" in data["penalties"]["enhanced_penalty"]  # 35% enhanced penalty


# ---------------------------------------------------------------------------
# Test POST /filing-requirement
# ---------------------------------------------------------------------------

def test_filing_requirement_us_owner_required(client, auth_headers):
    """Test filing requirement when trust has US owner."""
    payload = {
        "is_us_owner": True,
        "is_us_beneficiary": False,
        "trust_name": "Luxembourg Family Trust",
        "trust_country": "LU",
        "tax_year": 2024,
        "has_us_agent": False,
    }
    response = client.post("/api/v1/form3520a/filing-requirement", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["must_file"] is True
    assert "IRC § 6048(b)" in data["statutory_reference"]
    assert any("REQUIRED" in r for r in data["reasons"])
    assert "March 15" in data["filing_deadline"]


def test_filing_requirement_no_us_owner_not_required(client, auth_headers):
    """Test filing requirement when trust has no US owner."""
    payload = {
        "is_us_owner": False,
        "is_us_beneficiary": False,
        "trust_name": "Foreign Trust",
        "trust_country": "CH",
        "tax_year": 2024,
        "has_us_agent": True,
    }
    response = client.post("/api/v1/form3520a/filing-requirement", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["must_file"] is False
    assert any("No Form 3520-A filing obligation" in r for r in data["reasons"])


def test_filing_requirement_us_beneficiary_statement_required(client, auth_headers):
    """Test beneficiary statement requirement."""
    payload = {
        "is_us_owner": False,
        "is_us_beneficiary": True,
        "trust_name": "Swiss Trust",
        "trust_country": "CH",
        "tax_year": 2024,
        "has_us_agent": True,
    }
    response = client.post("/api/v1/form3520a/filing-requirement", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert any("Beneficiary Statement" in r for r in data["reasons"])
    assert "March 15" in data["beneficiary_statement_deadline"]


def test_filing_requirement_no_us_agent_warning(client, auth_headers):
    """Test warning when no US Agent is designated."""
    payload = {
        "is_us_owner": True,
        "is_us_beneficiary": False,
        "trust_name": "Cayman Trust",
        "trust_country": "KY",
        "tax_year": 2024,
        "has_us_agent": False,
    }
    response = client.post("/api/v1/form3520a/filing-requirement", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert any("No US agent" in r and "35%" in r for r in data["reasons"])


def test_filing_requirement_unauthorized(client):
    """Test filing-requirement without auth token (should fail)."""
    payload = {
        "is_us_owner": True,
        "is_us_beneficiary": False,
        "trust_name": "Test Trust",
        "trust_country": "LU",
        "tax_year": 2024,
        "has_us_agent": False,
    }
    response = client.post("/api/v1/form3520a/filing-requirement", json=payload)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Test POST /trust-activity
# ---------------------------------------------------------------------------

def test_trust_activity_complex_trust(client, auth_headers):
    """Test trust activity calculation for a complex trust."""
    payload = {
        "trust_type": "COMPLEX",
        "trust_corpus_usd": 500_000.0,
        "gross_income_usd": 25_000.0,
        "trust_expenses_usd": 5_000.0,
        "distributions_to_us_beneficiaries_usd": 15_000.0,
        "distributions_to_foreign_beneficiaries_usd": 0.0,
        "capital_gains_usd": 10_000.0,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/trust-activity", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["trust_type"] == "COMPLEX"
    assert data["net_income_usd"] == 30_000.0  # 25k - 5k + 10k
    assert data["distributable_net_income_usd"] == 20_000.0  # net_income - capital_gains
    assert data["distributions_to_us_beneficiaries_usd"] == 15_000.0
    assert data["undistributed_income_usd"] == 15_000.0  # 30k net - 15k distributions


def test_trust_activity_simple_trust(client, auth_headers):
    """Test trust activity for a simple trust (must distribute all income)."""
    payload = {
        "trust_type": "SIMPLE",
        "trust_corpus_usd": 200_000.0,
        "gross_income_usd": 10_000.0,
        "trust_expenses_usd": 2_000.0,
        "distributions_to_us_beneficiaries_usd": 8_000.0,
        "distributions_to_foreign_beneficiaries_usd": 0.0,
        "capital_gains_usd": 0.0,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/trust-activity", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["trust_type"] == "SIMPLE"
    assert data["net_income_usd"] == 8_000.0
    assert data["undistributed_income_usd"] == 0.0  # Simple trust: no undistributed income


def test_trust_activity_with_foreign_distributions(client, auth_headers):
    """Test trust with both US and foreign beneficiary distributions."""
    payload = {
        "trust_type": "COMPLEX",
        "trust_corpus_usd": 1_000_000.0,
        "gross_income_usd": 50_000.0,
        "trust_expenses_usd": 10_000.0,
        "distributions_to_us_beneficiaries_usd": 20_000.0,
        "distributions_to_foreign_beneficiaries_usd": 15_000.0,
        "capital_gains_usd": 5_000.0,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/trust-activity", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_distributions_usd"] == 35_000.0
    assert data["distributions_to_us_beneficiaries_usd"] == 20_000.0
    assert data["distributions_to_foreign_beneficiaries_usd"] == 15_000.0


def test_trust_activity_unauthorized(client):
    """Test trust-activity without auth token (should fail)."""
    payload = {
        "trust_type": "COMPLEX",
        "trust_corpus_usd": 500_000.0,
        "gross_income_usd": 25_000.0,
        "trust_expenses_usd": 5_000.0,
        "distributions_to_us_beneficiaries_usd": 15_000.0,
        "distributions_to_foreign_beneficiaries_usd": 0.0,
        "capital_gains_usd": 10_000.0,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/trust-activity", json=payload)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Test POST /beneficiary-reporting
# ---------------------------------------------------------------------------

def test_beneficiary_reporting_single_beneficiary(client, auth_headers):
    """Test beneficiary reporting for a single US beneficiary."""
    payload = {
        "beneficiaries": [
            {
                "name": "John Doe",
                "ssn_or_itin": "123-45-6789",
                "distribution_amount_usd": 15_000.0,
                "distribution_type": "INCOME",
                "is_income_distribution": True,
            }
        ],
        "trust_name": "Luxembourg Family Trust",
        "trust_ein": "12-3456789",
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/beneficiary-reporting", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["beneficiary_count"] == 1
    assert data["total_distributions_usd"] == 15_000.0
    assert data["beneficiaries"][0]["name"] == "John Doe"
    assert "March 15, 2025" in data["statement_deadline"]
    assert any("provide a Foreign Grantor Trust Beneficiary Statement" in r for r in data["statement_requirements"])


def test_beneficiary_reporting_multiple_beneficiaries(client, auth_headers):
    """Test beneficiary reporting for multiple US beneficiaries."""
    payload = {
        "beneficiaries": [
            {
                "name": "Alice Smith",
                "ssn_or_itin": "111-22-3333",
                "distribution_amount_usd": 10_000.0,
                "distribution_type": "INCOME",
                "is_income_distribution": True,
            },
            {
                "name": "Bob Jones",
                "ssn_or_itin": "444-55-6666",
                "distribution_amount_usd": 8_000.0,
                "distribution_type": "PRINCIPAL",
                "is_income_distribution": False,
            },
            {
                "name": "Carol White",
                "ssn_or_itin": "777-88-9999",
                "distribution_amount_usd": 12_000.0,
                "distribution_type": "MIXED",
                "is_income_distribution": True,
            },
        ],
        "trust_name": "Swiss Family Trust",
        "trust_ein": "98-7654321",
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/beneficiary-reporting", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["beneficiary_count"] == 3
    assert data["total_distributions_usd"] == 30_000.0
    assert len(data["beneficiaries"]) == 3


def test_beneficiary_reporting_unauthorized(client):
    """Test beneficiary-reporting without auth token (should fail)."""
    payload = {
        "beneficiaries": [
            {
                "name": "Test User",
                "ssn_or_itin": "123-45-6789",
                "distribution_amount_usd": 5_000.0,
                "distribution_type": "INCOME",
                "is_income_distribution": True,
            }
        ],
        "trust_name": "Test Trust",
        "trust_ein": "11-1111111",
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/beneficiary-reporting", json=payload)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Test POST /penalty-calculator
# ---------------------------------------------------------------------------

def test_penalty_calculator_base_penalty_only(client, auth_headers):
    """Test penalty calculation: on-time filing (no months late)."""
    payload = {
        "trust_corpus_usd": 500_000.0,
        "months_late": 0,
        "has_us_agent": True,
        "books_and_records_provided": True,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/penalty-calculator", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["base_penalty_usd"] == 10_000.0
    assert data["monthly_penalty_usd"] == 0.0
    assert data["enhanced_penalty_applicable"] is False
    assert data["total_penalty_usd"] == 10_000.0


def test_penalty_calculator_monthly_penalty(client, auth_headers):
    """Test penalty calculation: 6 months late."""
    payload = {
        "trust_corpus_usd": 500_000.0,
        "months_late": 6,
        "has_us_agent": True,
        "books_and_records_provided": True,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/penalty-calculator", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["base_penalty_usd"] == 10_000.0
    # 5% per month × 6 months = 30% of corpus = 150k
    assert data["monthly_penalty_usd"] == 150_000.0
    assert data["total_penalty_usd"] == 160_000.0  # 10k + 150k


def test_penalty_calculator_enhanced_penalty(client, auth_headers):
    """Test enhanced penalty: no US agent + books/records denied."""
    payload = {
        "trust_corpus_usd": 500_000.0,
        "months_late": 3,
        "has_us_agent": False,
        "books_and_records_provided": False,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/penalty-calculator", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["enhanced_penalty_applicable"] is True
    # Enhanced penalty: 35% of corpus = 175k
    assert data["enhanced_penalty_usd"] == 175_000.0
    # Standard penalty: 10k + (5% × 3 months × 500k) = 10k + 75k = 85k
    # Total = max(85k, 175k) = 175k
    assert data["total_penalty_usd"] == 175_000.0


def test_penalty_calculator_enhanced_penalty_vs_standard(client, auth_headers):
    """Test that enhanced penalty is greater of standard vs. enhanced."""
    payload = {
        "trust_corpus_usd": 100_000.0,
        "months_late": 12,
        "has_us_agent": False,
        "books_and_records_provided": False,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/penalty-calculator", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Standard: 10k + (5% × 12 × 100k) = 10k + 60k = 70k
    # Enhanced: 35% × 100k = 35k
    # Total: max(70k, 35k) = 70k
    assert data["total_penalty_usd"] == 70_000.0


def test_penalty_calculator_large_corpus(client, auth_headers):
    """Test penalty calculation for a large trust corpus."""
    payload = {
        "trust_corpus_usd": 10_000_000.0,
        "months_late": 6,
        "has_us_agent": False,
        "books_and_records_provided": False,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/penalty-calculator", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Enhanced penalty: 35% × 10M = 3.5M
    # Standard: 10k + (5% × 6 × 10M) = 10k + 3M = 3.01M
    # Total: max(3.01M, 3.5M) = 3.5M
    assert data["enhanced_penalty_applicable"] is True
    assert data["enhanced_penalty_usd"] == 3_500_000.0
    assert data["total_penalty_usd"] == 3_500_000.0


def test_penalty_calculator_mitigation_steps(client, auth_headers):
    """Test that mitigation steps are provided."""
    payload = {
        "trust_corpus_usd": 500_000.0,
        "months_late": 3,
        "has_us_agent": False,
        "books_and_records_provided": False,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/penalty-calculator", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "mitigation_steps" in data
    assert len(data["mitigation_steps"]) > 0
    assert any("File Form 3520-A immediately" in s for s in data["mitigation_steps"])
    assert any("Designate a US Agent" in s for s in data["mitigation_steps"])


def test_penalty_calculator_unauthorized(client):
    """Test penalty-calculator without auth token (should fail)."""
    payload = {
        "trust_corpus_usd": 500_000.0,
        "months_late": 6,
        "has_us_agent": True,
        "books_and_records_provided": True,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/penalty-calculator", json=payload)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Edge cases and validation tests
# ---------------------------------------------------------------------------

def test_filing_requirement_invalid_tax_year(client, auth_headers):
    """Test validation for invalid tax year."""
    payload = {
        "is_us_owner": True,
        "is_us_beneficiary": False,
        "trust_name": "Test Trust",
        "trust_country": "LU",
        "tax_year": 1999,  # Invalid: below minimum
        "has_us_agent": True,
    }
    response = client.post("/api/v1/form3520a/filing-requirement", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_trust_activity_negative_values(client, auth_headers):
    """Test validation: negative values should fail."""
    payload = {
        "trust_type": "COMPLEX",
        "trust_corpus_usd": -100_000.0,  # Invalid: negative
        "gross_income_usd": 25_000.0,
        "trust_expenses_usd": 5_000.0,
        "distributions_to_us_beneficiaries_usd": 15_000.0,
        "distributions_to_foreign_beneficiaries_usd": 0.0,
        "capital_gains_usd": 10_000.0,
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/trust-activity", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_beneficiary_reporting_empty_list(client, auth_headers):
    """Test validation: beneficiaries list cannot be empty."""
    payload = {
        "beneficiaries": [],  # Invalid: empty list
        "trust_name": "Test Trust",
        "trust_ein": "12-3456789",
        "tax_year": 2024,
    }
    response = client.post("/api/v1/form3520a/beneficiary-reporting", json=payload, headers=auth_headers)
    assert response.status_code == 422
