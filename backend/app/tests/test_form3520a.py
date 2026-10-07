"""
Tests for Form 3520-A Foreign Trust Annual Information Return.

Coverage:
- Filing requirement determination (Owner/Beneficiary, Grantor/Non-Grantor)
- Income distribution calculations
- Foreign Grantor Trust Statement generation
- Penalty calculations (§6677)
- Edge cases and boundary conditions
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.modules.form3520a import (
    determine_filing_requirement,
    IncomeDistributionItem,
    calculate_income_distribution,
    generate_foreign_grantor_statement,
    calculate_form3520a_penalties,
    get_form3520a_overview,
)


# ---------------------------------------------------------------------------
# Filing Requirement Tests
# ---------------------------------------------------------------------------


class TestFilingRequirement:
    """Test filing requirement determination for Form 3520-A."""

    def test_foreign_grantor_trust_with_us_owner_requires_filing(self):
        """Foreign grantor trust with U.S. owner must file Form 3520-A."""
        result = determine_filing_requirement(
            is_us_owner=True,
            is_us_beneficiary=False,
            trust_type="FOREIGN_GRANTOR",
            received_distribution=False,
            distribution_amount_usd=0.0,
        )

        assert result["filing_required"] is True
        assert result["filer_role"] == "OWNER"
        assert result["trust_type"] == "FOREIGN_GRANTOR"
        assert "Foreign grantor trust with U.S. owner must file" in result["reasons"][0]

    def test_non_grantor_trust_with_distribution_requires_filing(self):
        """Non-grantor trust with distribution to U.S. beneficiary requires filing."""
        result = determine_filing_requirement(
            is_us_owner=False,
            is_us_beneficiary=True,
            trust_type="NON_GRANTOR",
            received_distribution=True,
            distribution_amount_usd=50000.0,
        )

        assert result["filing_required"] is True
        assert result["filer_role"] == "BENEFICIARY"
        assert result["trust_type"] == "NON_GRANTOR"
        assert "50,000.00" in result["reasons"][0]

    def test_non_grantor_trust_without_distribution_no_filing(self):
        """Non-grantor trust without distribution does not require filing."""
        result = determine_filing_requirement(
            is_us_owner=False,
            is_us_beneficiary=True,
            trust_type="NON_GRANTOR",
            received_distribution=False,
            distribution_amount_usd=0.0,
        )

        assert result["filing_required"] is False
        assert result["filer_role"] is None

    def test_non_grantor_trust_with_zero_distribution_no_filing(self):
        """Non-grantor trust with $0 distribution does not require filing."""
        result = determine_filing_requirement(
            is_us_owner=False,
            is_us_beneficiary=True,
            trust_type="NON_GRANTOR",
            received_distribution=True,
            distribution_amount_usd=0.0,
        )

        assert result["filing_required"] is False

    def test_foreign_trust_no_us_connection_no_filing(self):
        """Foreign trust with no U.S. owners or beneficiaries does not require filing."""
        result = determine_filing_requirement(
            is_us_owner=False,
            is_us_beneficiary=False,
            trust_type="NON_GRANTOR",
            received_distribution=False,
            distribution_amount_usd=0.0,
        )

        assert result["filing_required"] is False


# ---------------------------------------------------------------------------
# Income Distribution Tests
# ---------------------------------------------------------------------------


class TestIncomeDistribution:
    """Test income distribution calculations."""

    def test_single_dividend_distribution(self):
        """Calculate single dividend distribution."""
        distributions = [
            IncomeDistributionItem(
                income_type="DIVIDENDS",
                gross_amount_usd=10000.0,
                withholding_tax_usd=1500.0,
                distribution_date="2024-06-15",
                source_country="CH",
            )
        ]

        result = calculate_income_distribution(distributions, "NON_GRANTOR")

        assert result["total_distributions"] == 1
        assert result["total_gross_usd"] == 10000.0
        assert result["total_withholding_usd"] == 1500.0
        assert result["total_net_usd"] == 8500.0
        assert "DIVIDENDS" in result["by_income_type"]
        assert result["by_income_type"]["DIVIDENDS"]["gross_usd"] == 10000.0

    def test_multiple_distributions_same_type(self):
        """Calculate multiple distributions of same income type."""
        distributions = [
            IncomeDistributionItem(
                income_type="INTEREST",
                gross_amount_usd=5000.0,
                withholding_tax_usd=0.0,
                distribution_date="2024-03-15",
                source_country="CH",
            ),
            IncomeDistributionItem(
                income_type="INTEREST",
                gross_amount_usd=7500.0,
                withholding_tax_usd=0.0,
                distribution_date="2024-09-15",
                source_country="CH",
            ),
        ]

        result = calculate_income_distribution(distributions, "NON_GRANTOR")

        assert result["total_distributions"] == 2
        assert result["total_gross_usd"] == 12500.0
        assert result["by_income_type"]["INTEREST"]["count"] == 2
        assert result["by_income_type"]["INTEREST"]["gross_usd"] == 12500.0

    def test_mixed_income_types(self):
        """Calculate distributions with multiple income types."""
        distributions = [
            IncomeDistributionItem(
                income_type="DIVIDENDS",
                gross_amount_usd=15000.0,
                withholding_tax_usd=2250.0,
                distribution_date="2024-06-15",
                source_country="CH",
            ),
            IncomeDistributionItem(
                income_type="INTEREST",
                gross_amount_usd=5000.0,
                withholding_tax_usd=0.0,
                distribution_date="2024-06-15",
                source_country="CH",
            ),
            IncomeDistributionItem(
                income_type="CAPITAL_GAINS",
                gross_amount_usd=25000.0,
                withholding_tax_usd=0.0,
                distribution_date="2024-12-15",
                source_country="CH",
            ),
        ]

        result = calculate_income_distribution(distributions, "NON_GRANTOR")

        assert result["total_distributions"] == 3
        assert result["total_gross_usd"] == 45000.0
        assert result["total_withholding_usd"] == 2250.0
        assert result["total_net_usd"] == 42750.0
        assert len(result["by_income_type"]) == 3
        assert "DIVIDENDS" in result["by_income_type"]
        assert "INTEREST" in result["by_income_type"]
        assert "CAPITAL_GAINS" in result["by_income_type"]

    def test_grantor_trust_tax_treatment(self):
        """Grantor trust income is taxed to owner, not beneficiary."""
        distributions = [
            IncomeDistributionItem(
                income_type="DIVIDENDS",
                gross_amount_usd=10000.0,
                withholding_tax_usd=0.0,
                distribution_date="2024-06-15",
                source_country="CH",
            )
        ]

        result = calculate_income_distribution(distributions, "FOREIGN_GRANTOR")

        assert "taxable to U.S. grantor/owner" in result["tax_treatment"]

    def test_non_grantor_trust_tax_treatment(self):
        """Non-grantor trust distributions are taxed to beneficiary."""
        distributions = [
            IncomeDistributionItem(
                income_type="DIVIDENDS",
                gross_amount_usd=10000.0,
                withholding_tax_usd=0.0,
                distribution_date="2024-06-15",
                source_country="CH",
            )
        ]

        result = calculate_income_distribution(distributions, "NON_GRANTOR")

        assert "taxable to U.S. beneficiary" in result["tax_treatment"]

    def test_zero_distributions(self):
        """Handle empty distribution list."""
        result = calculate_income_distribution([], "NON_GRANTOR")

        assert result["total_distributions"] == 0
        assert result["total_gross_usd"] == 0.0
        assert result["total_net_usd"] == 0.0


# ---------------------------------------------------------------------------
# Foreign Grantor Trust Statement Tests
# ---------------------------------------------------------------------------


class TestForeignGrantorStatement:
    """Test Foreign Grantor Trust Owner Statement generation."""

    def test_generate_complete_statement(self):
        """Generate complete grantor trust owner statement."""
        result = generate_foreign_grantor_statement(
            trust_name="Swiss Family Trust",
            trust_ein="98-7654321",
            trust_country="CH",
            us_owner_name="John Doe",
            us_owner_ssn="123-45-6789",
            tax_year=2024,
            trust_assets_usd=500000.0,
            trust_income_usd=45000.0,
            trust_distributions_usd=20000.0,
        )

        assert result["statement_type"] == "FOREIGN_GRANTOR_TRUST_OWNER_STATEMENT"
        assert result["trust_name"] == "Swiss Family Trust"
        assert result["trust_ein"] == "98-7654321"
        assert result["trust_country"] == "CH"
        assert result["us_owner_name"] == "John Doe"
        assert result["us_owner_ssn"] == "123-45-6789"
        assert result["tax_year"] == 2024
        assert result["trust_assets_usd"] == 500000.0
        assert result["trust_income_usd"] == 45000.0
        assert result["trust_distributions_usd"] == 20000.0
        assert len(result["owner_obligations"]) == 4
        assert "IRC §679" in result["grantor_trust_rules"]

    def test_statement_with_zero_distributions(self):
        """Generate statement for trust with no distributions."""
        result = generate_foreign_grantor_statement(
            trust_name="Test Trust",
            trust_ein="00-0000000",
            trust_country="LI",
            us_owner_name="Jane Smith",
            us_owner_ssn="987-65-4321",
            tax_year=2024,
            trust_assets_usd=1000000.0,
            trust_income_usd=75000.0,
            trust_distributions_usd=0.0,
        )

        assert result["trust_distributions_usd"] == 0.0
        assert result["trust_income_usd"] == 75000.0  # Income still exists


# ---------------------------------------------------------------------------
# Penalty Calculator Tests
# ---------------------------------------------------------------------------


class TestPenaltyCalculator:
    """Test IRC §6677 penalty calculations."""

    def test_no_penalty_filed_on_time(self):
        """No penalty when filed on time."""
        deadline = "2024-03-15"
        filed = "2024-03-10"  # 5 days early

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=filed,
            trust_gross_value_usd=500000.0,
        )

        assert result["days_late"] == 0
        assert result["total_penalty_usd"] == 0.0
        assert len(result["penalties"]) == 0

    def test_initial_penalty_5_percent(self):
        """Initial failure penalty is 5% of trust value."""
        deadline = "2024-03-15"
        filed = "2024-04-15"  # 31 days late

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=filed,
            trust_gross_value_usd=500000.0,
        )

        assert result["days_late"] == 31
        assert result["total_penalty_usd"] == 25000.0  # 5% of $500k
        assert len(result["penalties"]) == 1
        assert result["penalties"][0]["type"] == "INITIAL_FAILURE"
        assert result["penalties"][0]["rate"] == "5%"

    def test_continuing_penalty_after_90_days(self):
        """Continuing penalty of 5% per 30-day period after 90 days."""
        deadline = "2024-03-15"
        filed = "2024-07-15"  # 122 days late (90 + 32)

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=filed,
            trust_gross_value_usd=500000.0,
        )

        assert result["days_late"] == 122
        # Initial: 5% = $25,000
        # Continuing: 32 days beyond 90 = 2 periods × 5% = $50,000
        # Total: $75,000
        assert result["total_penalty_usd"] == 75000.0
        assert len(result["penalties"]) == 2
        assert result["penalties"][1]["type"] == "CONTINUING_FAILURE"
        assert result["penalties"][1]["periods"] == 2

    def test_penalty_capped_at_25_percent(self):
        """Penalty capped at 25% of trust value."""
        deadline = "2024-03-15"
        filed = "2024-12-15"  # 275 days late

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=filed,
            trust_gross_value_usd=500000.0,
        )

        # Maximum penalty: 25% of $500k = $125,000
        assert result["total_penalty_usd"] == 125000.0
        assert result["penalty_capped"] is True
        assert result["maximum_penalty_usd"] == 125000.0

    def test_not_yet_filed_uses_current_date(self):
        """Calculate penalty for unfiled return using current date."""
        # Set deadline 180 days ago
        deadline_date = datetime.now() - timedelta(days=180)
        deadline = deadline_date.strftime("%Y-%m-%d")

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=None,  # Not yet filed
            trust_gross_value_usd=500000.0,
        )

        assert result["actual_filing_date"] is None
        assert result["days_late"] >= 180
        assert result["total_penalty_usd"] > 0

    def test_penalty_calculation_precision(self):
        """Verify penalty calculation with non-round numbers."""
        deadline = "2024-03-15"
        filed = "2024-04-20"

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=filed,
            trust_gross_value_usd=367892.45,
        )

        expected_penalty = 367892.45 * 0.05  # 5%
        assert abs(result["total_penalty_usd"] - expected_penalty) < 0.01

    def test_small_trust_value(self):
        """Calculate penalty for small trust value."""
        deadline = "2024-03-15"
        filed = "2024-06-15"  # 92 days late (triggers continuing penalty)

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=filed,
            trust_gross_value_usd=10000.0,
        )

        # Initial: 5% = $500
        # Continuing: 2 days beyond 90 = 1 period × 5% = $500
        # Total: $1,000
        assert result["total_penalty_usd"] == 1000.0

    def test_large_trust_value(self):
        """Calculate penalty for large trust value."""
        deadline = "2024-03-15"
        filed = "2025-03-15"  # 365 days late

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=filed,
            trust_gross_value_usd=10000000.0,
        )

        # Capped at 25%
        assert result["total_penalty_usd"] == 2500000.0
        assert result["penalty_capped"] is True


# ---------------------------------------------------------------------------
# Overview Tests
# ---------------------------------------------------------------------------


class TestOverview:
    """Test Form 3520-A overview endpoint."""

    def test_overview_structure(self):
        """Verify overview contains all required sections."""
        overview = get_form3520a_overview()

        assert overview["form"] == "3520-A"
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "filing_deadline" in overview
        assert "extension_available" in overview
        assert "trust_types" in overview
        assert "penalties" in overview
        assert "related_forms" in overview
        assert "key_references" in overview

    def test_overview_trust_types(self):
        """Verify trust types are documented."""
        overview = get_form3520a_overview()

        trust_types = overview["trust_types"]
        assert "FOREIGN_GRANTOR" in trust_types
        assert "NON_GRANTOR" in trust_types
        assert "IRC §§671-679" in trust_types["FOREIGN_GRANTOR"]["description"]

    def test_overview_penalties(self):
        """Verify penalty information is documented."""
        overview = get_form3520a_overview()

        penalties = overview["penalties"]
        assert "initial_failure" in penalties
        assert "continuing_failure" in penalties
        assert penalties["initial_failure"]["rate"] == "5%"
        assert penalties["continuing_failure"]["max_rate"] == "25%"
        assert "IRC §6677" in penalties["initial_failure"]["statute"]


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_distribution_with_high_withholding(self):
        """Handle distribution where withholding exceeds gross (shouldn't happen but test)."""
        distributions = [
            IncomeDistributionItem(
                income_type="DIVIDENDS",
                gross_amount_usd=10000.0,
                withholding_tax_usd=10000.0,
                distribution_date="2024-06-15",
                source_country="CH",
            )
        ]

        result = calculate_income_distribution(distributions, "NON_GRANTOR")

        assert result["total_net_usd"] == 0.0

    def test_very_small_distribution(self):
        """Handle very small distribution amounts."""
        distributions = [
            IncomeDistributionItem(
                income_type="INTEREST",
                gross_amount_usd=0.01,
                withholding_tax_usd=0.0,
                distribution_date="2024-06-15",
                source_country="CH",
            )
        ]

        result = calculate_income_distribution(distributions, "NON_GRANTOR")

        assert result["total_gross_usd"] == 0.01
        assert result["total_net_usd"] == 0.01

    def test_penalty_filed_exactly_on_deadline(self):
        """No penalty when filed exactly on deadline."""
        deadline = "2024-03-15"

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=deadline,
            trust_gross_value_usd=500000.0,
        )

        assert result["days_late"] == 0
        assert result["total_penalty_usd"] == 0.0

    def test_penalty_91_days_late_triggers_continuing(self):
        """Verify continuing penalty triggers at exactly 91 days."""
        deadline = "2024-03-15"
        filed_date = datetime.strptime(deadline, "%Y-%m-%d") + timedelta(days=91)
        filed = filed_date.strftime("%Y-%m-%d")

        result = calculate_form3520a_penalties(
            filing_deadline=deadline,
            actual_filing_date=filed,
            trust_gross_value_usd=500000.0,
        )

        assert result["days_late"] == 91
        # Should have both initial and continuing penalty
        assert len(result["penalties"]) == 2
