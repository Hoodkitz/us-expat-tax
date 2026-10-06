"""
Tests for Form 8833 Treaty-Based Return Position Disclosure.

Covers:
- Filing requirement checks for different position types
- Totalization exemption from Form 8833
- Disclosure generation with treaty positions
- Overview endpoint with common countries and articles
- Penalty amounts ($1,000 per failure)
- Filing deadlines
- All endpoints return 200
- Edge cases: unknown countries, various position types
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.form8833 import (
    FilingRequirementInput,
    DisclosureInput,
    check_filing_requirement,
    create_disclosure,
    get_overview,
    PENALTY_FAILURE_TO_DISCLOSE,
    TREATY_COUNTRIES,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# 1. Filing Requirement Tests
# ---------------------------------------------------------------------------

def test_filing_required_residence_position():
    """Filing required for treaty residence position."""
    inp = FilingRequirementInput(
        treaty_country="DE",
        treaty_article="Article 4",
        position_type="RESIDENCE",
    )
    result = check_filing_requirement(inp)
    assert result.required is True
    assert "RESIDENCE" in result.reason
    assert result.penalty_if_not_filed == PENALTY_FAILURE_TO_DISCLOSE
    assert result.treaty_country_name == "Germany"
    assert result.position_type == "RESIDENCE"

def test_filing_required_business_profits():
    """Filing required for business profits exemption."""
    inp = FilingRequirementInput(
        treaty_country="GB",
        treaty_article="Article 7",
        position_type="BUSINESS_PROFITS",
    )
    result = check_filing_requirement(inp)
    assert result.required is True
    assert "United Kingdom" in result.reason
    assert result.penalty_if_not_filed == PENALTY_FAILURE_TO_DISCLOSE

def test_filing_required_dividends():
    """Filing required for dividend withholding reduction."""
    inp = FilingRequirementInput(
        treaty_country="CA",
        treaty_article="Article 10",
        position_type="DIVIDENDS",
    )
    result = check_filing_requirement(inp)
    assert result.required is True
    assert "Canada" in result.reason

def test_filing_required_pensions():
    """Filing required for pension distribution treatment."""
    inp = FilingRequirementInput(
        treaty_country="DE",
        treaty_article="Article 18",
        position_type="PENSIONS",
    )
    result = check_filing_requirement(inp)
    assert result.required is True
    assert "Germany" in result.reason

def test_filing_not_required_totalization():
    """Totalization positions are exempt from Form 8833."""
    inp = FilingRequirementInput(
        treaty_country="DE",
        treaty_article="Article 1 (Totalization Agreement)",
        position_type="TOTALIZATION",
    )
    result = check_filing_requirement(inp)
    assert result.required is False
    assert "exempt" in result.reason.lower()
    assert "totalization" in result.reason.lower()
    assert result.penalty_if_not_filed == 0.0

def test_filing_deadline_format():
    """Filing deadline should be in YYYY-MM-DD format."""
    inp = FilingRequirementInput(
        treaty_country="FR",
        treaty_article="Article 4",
        position_type="RESIDENCE",
    )
    result = check_filing_requirement(inp)
    assert "-" in result.filing_deadline
    assert len(result.filing_deadline) == 10  # YYYY-MM-DD

def test_unknown_country_code():
    """Unknown country codes should still work with code as name."""
    inp = FilingRequirementInput(
        treaty_country="XX",
        treaty_article="Article 1",
        position_type="RESIDENCE",
    )
    result = check_filing_requirement(inp)
    assert result.required is True
    # Should use country code if not in known list
    assert "XX" in result.treaty_country_name or result.treaty_country_name == "XX"

# ---------------------------------------------------------------------------
# 2. Disclosure Tests
# ---------------------------------------------------------------------------

def test_disclosure_residence_position():
    """Create disclosure for treaty residence position."""
    inp = DisclosureInput(
        treaty_country="DE",
        treaty_article="Article 4",
        treaty_provision="A person is resident where they have a permanent home available",
        taxpayer_position="I am a resident of Germany under Article 4 due to permanent home and center of vital interests in Germany",
        law_overruled="IRC §7701(b) - Substantial Presence Test",
    )
    result = create_disclosure(inp)
    assert "Germany" in result.disclosure_summary
    assert "Article 4" in result.disclosure_summary
    assert len(result.reporting_requirements) >= 4
    assert "Form 8833" in result.reporting_requirements[0]
    assert "U.S.-Germany" in result.treaty_reference
    assert "1,000" in result.penalty_warning or "1000" in result.penalty_warning

def test_disclosure_business_profits():
    """Create disclosure for business profits exemption."""
    inp = DisclosureInput(
        treaty_country="GB",
        treaty_article="Article 7",
        treaty_provision="Business profits shall be taxable only in the residence state unless attributable to a permanent establishment",
        taxpayer_position="No permanent establishment in the U.S., all profits taxable only in the UK",
        law_overruled="IRC §882 - Tax on foreign corporations",
    )
    result = create_disclosure(inp)
    assert "United Kingdom" in result.disclosure_summary or "United Kingdom" in result.treaty_reference
    assert "Article 7" in result.treaty_reference
    assert len(result.reporting_requirements) > 0

def test_disclosure_pension_treatment():
    """Create disclosure for pension distribution."""
    inp = DisclosureInput(
        treaty_country="CA",
        treaty_article="Article 18",
        treaty_provision="Pensions arising in a contracting state shall be taxable only in that state",
        taxpayer_position="Canadian pension should be taxable only in Canada under Article 18",
        law_overruled="IRC §61 - Gross income",
    )
    result = create_disclosure(inp)
    assert "Canada" in result.disclosure_summary or "Canada" in result.treaty_reference
    assert len(result.reporting_requirements) >= 4
    assert "$1,000" in result.penalty_warning or "1,000" in result.penalty_warning

def test_disclosure_requires_all_fields():
    """Disclosure summary should include all provided information."""
    inp = DisclosureInput(
        treaty_country="FR",
        treaty_article="Article 11",
        treaty_provision="Interest arising in contracting state taxable only in residence state",
        taxpayer_position="French-source interest exempt from U.S. tax under treaty",
        law_overruled="IRC §871 - Tax on nonresident alien individuals",
    )
    result = create_disclosure(inp)
    assert result.disclosure_summary
    assert result.treaty_reference
    assert result.penalty_warning
    assert len(result.reporting_requirements) > 0

# ---------------------------------------------------------------------------
# 3. Overview Tests
# ---------------------------------------------------------------------------

def test_overview_structure():
    """Overview should include all required information."""
    result = get_overview()
    assert result.description
    assert len(result.common_countries) > 0
    assert len(result.common_articles) > 0
    assert result.filing_threshold
    assert result.penalty_amount == PENALTY_FAILURE_TO_DISCLOSE

def test_overview_includes_major_countries():
    """Overview should include major treaty countries."""
    result = get_overview()
    # Check for key countries
    assert "DE" in result.common_countries
    assert "GB" in result.common_countries or "United Kingdom" in result.common_countries.values()
    assert "CA" in result.common_countries

def test_overview_includes_common_articles():
    """Overview should include common treaty articles."""
    result = get_overview()
    articles_text = " ".join(result.common_articles.values())
    assert "Residence" in articles_text or "residence" in articles_text
    assert "Business" in articles_text or "business" in articles_text
    assert "Pension" in articles_text or "pension" in articles_text

def test_overview_penalty_correct():
    """Overview should show correct penalty amount."""
    result = get_overview()
    assert result.penalty_amount == 1_000.0

# ---------------------------------------------------------------------------
# 4. API Endpoint Tests
# ---------------------------------------------------------------------------

def test_api_filing_requirement_endpoint():
    """Test /filing-requirement endpoint."""
    response = client.post(
        "/api/v1/form8833/filing-requirement",
        json={
            "treaty_country": "DE",
            "treaty_article": "Article 4",
            "position_type": "RESIDENCE",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["required"] is True
    assert data["penalty_if_not_filed"] == PENALTY_FAILURE_TO_DISCLOSE

def test_api_disclosure_endpoint():
    """Test /disclosure endpoint."""
    response = client.post(
        "/api/v1/form8833/disclosure",
        json={
            "treaty_country": "GB",
            "treaty_article": "Article 7",
            "treaty_provision": "Business profits provision",
            "taxpayer_position": "No PE in US",
            "law_overruled": "IRC §882",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "disclosure_summary" in data
    assert "reporting_requirements" in data
    assert isinstance(data["reporting_requirements"], list)

def test_api_overview_endpoint():
    """Test /overview endpoint."""
    response = client.get("/api/v1/form8833/overview")
    assert response.status_code == 200
    data = response.json()
    assert "description" in data
    assert "common_countries" in data
    assert "common_articles" in data
    assert "penalty_amount" in data

# ---------------------------------------------------------------------------
# 5. Edge Cases and Validation
# ---------------------------------------------------------------------------

def test_multiple_position_types():
    """Test various position types."""
    position_types = ["INTEREST", "ROYALTIES", "GOVERNMENT_SERVICE", "STUDENTS_TEACHERS", "OTHER_INCOME"]
    for pos_type in position_types:
        inp = FilingRequirementInput(
            treaty_country="DE",
            treaty_article="Article 1",
            position_type=pos_type,
        )
        result = check_filing_requirement(inp)
        assert result.required is True
        assert result.penalty_if_not_filed == PENALTY_FAILURE_TO_DISCLOSE

def test_penalty_consistency():
    """Penalty should be consistent across all required filings."""
    positions = [
        ("RESIDENCE", "Article 4"),
        ("BUSINESS_PROFITS", "Article 7"),
        ("DIVIDENDS", "Article 10"),
    ]
    for pos_type, article in positions:
        inp = FilingRequirementInput(
            treaty_country="CA",
            treaty_article=article,
            position_type=pos_type,
        )
        result = check_filing_requirement(inp)
        if result.required:
            assert result.penalty_if_not_filed == PENALTY_FAILURE_TO_DISCLOSE

def test_disclosure_long_position():
    """Test disclosure with long taxpayer position text."""
    long_position = "X" * 500  # Very long position statement
    inp = DisclosureInput(
        treaty_country="DE",
        treaty_article="Article 4",
        treaty_provision="Test provision",
        taxpayer_position=long_position,
        law_overruled="IRC §7701(b)",
    )
    result = create_disclosure(inp)
    # Should handle long text gracefully
    assert result.disclosure_summary
    assert len(result.disclosure_summary) > 0
