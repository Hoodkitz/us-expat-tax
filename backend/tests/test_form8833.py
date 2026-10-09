
"""Tests for Form 8833 (Treaty-Based Return Position) module."""
import pytest
from app.modules.form8833 import (
    FilingRequirementInput, DisclosureInput,
    check_filing_requirement, create_disclosure, get_overview,
)


class TestFilingRequirement:
    """Test Form 8833 filing requirement."""

    def test_treaty_position_required(self):
        inp = FilingRequirementInput(
            treaty_country="DE",
            treaty_article="Article 15",
            position_type="RESIDENCE",
        )
        result = check_filing_requirement(inp)
        assert result.required is True
        assert isinstance(result.reason, str)

    def test_treaty_country_name(self):
        inp = FilingRequirementInput(
            treaty_country="FR",
            treaty_article="Article 4",
            position_type="RESIDENCE",
        )
        result = check_filing_requirement(inp)
        assert result.treaty_country_name == "France"

    def test_exempt_position(self):
        inp = FilingRequirementInput(
            treaty_country="DE",
            treaty_article="Article 4",
            position_type="TOTALIZATION",
        )
        result = check_filing_requirement(inp)
        assert result.required is False


class TestDisclosure:
    """Test Form 8833 disclosure creation."""

    def test_create_disclosure(self):
        inp = DisclosureInput(
            treaty_country="DE",
            treaty_article="Article 15",
            treaty_provision="Income from employment",
            taxpayer_position="German resident exempt under treaty",
            law_overruled="IRC § 861(a)(3)",
        )
        result = create_disclosure(inp)
        assert "Germany" in result.disclosure_summary
        assert "Article 15" in result.treaty_reference
        assert len(result.reporting_requirements) > 0
        assert "penalty" in result.penalty_warning.lower()


class TestOverview:
    """Test Form 8833 overview."""

    def test_overview(self):
        result = get_overview()
        assert hasattr(result, "description")
        assert hasattr(result, "common_countries")
        assert hasattr(result, "penalty_amount")
