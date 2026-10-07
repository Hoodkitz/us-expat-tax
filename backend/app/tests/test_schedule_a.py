"""
Tests for Schedule A (Itemized Deductions) calculations.
Covers edge cases, threshold boundaries, and different filing statuses.
"""
from app.modules.schedule_a import (
    ScheduleAInput,
    calculate_schedule_a,
    get_schedule_a_overview,
)


class TestScheduleACalculations:
    """Test Schedule A itemized deduction calculations."""

    def test_zero_agi_zero_deductions(self):
        """Zero AGI with no deductions should result in zero itemized deductions."""
        input_data = ScheduleAInput(
            adjusted_gross_income=0.0,
            medical_expenses=0.0,
            state_local_taxes=0.0,
            mortgage_interest=0.0,
            mortgage_debt=0.0,
            charitable_contributions=0.0,
            casualty_theft_losses=0.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.adjusted_gross_income == 0.0
        assert result.medical_expenses_deductible == 0.0
        assert result.salt_deductible == 0.0
        assert result.mortgage_interest_deductible == 0.0
        assert result.charitable_contributions_deductible == 0.0
        assert result.casualty_theft_losses_deductible == 0.0
        assert result.total_itemized_deductions == 0.0
        assert result.standard_deduction == 15_000.0
        assert result.recommended_deduction == 15_000.0
        assert result.use_itemized is False

    def test_medical_expenses_below_floor(self):
        """Medical expenses below 7.5% AGI floor should not be deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            medical_expenses=5_000.0,  # Below 7.5% of 100k = 7,500
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.medical_expenses_deductible == 0.0

    def test_medical_expenses_above_floor(self):
        """Medical expenses above 7.5% AGI floor should be partially deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            medical_expenses=10_000.0,  # 7.5% of 100k = 7,500; deductible = 2,500
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.medical_expenses_deductible == 2_500.0

    def test_medical_expenses_exactly_at_floor(self):
        """Medical expenses exactly at 7.5% AGI floor should not be deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            medical_expenses=7_500.0,  # Exactly 7.5% of 100k
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.medical_expenses_deductible == 0.0

    def test_salt_below_cap(self):
        """SALT below $10,000 cap should be fully deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            state_local_taxes=8_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.salt_deductible == 8_000.0

    def test_salt_at_cap(self):
        """SALT exactly at $10,000 cap should be fully deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            state_local_taxes=10_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.salt_deductible == 10_000.0

    def test_salt_above_cap(self):
        """SALT above $10,000 cap should be capped at $10,000."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            state_local_taxes=15_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.salt_deductible == 10_000.0

    def test_salt_cap_married_filing_separately(self):
        """SALT cap for married filing separately should be $5,000."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            state_local_taxes=8_000.0,
            filing_status="married_filing_separately",
        )
        result = calculate_schedule_a(input_data)

        assert result.salt_deductible == 5_000.0

    def test_mortgage_interest_within_debt_limit(self):
        """Mortgage interest on debt within $750k limit should be fully deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            mortgage_interest=8_000.0,
            mortgage_debt=400_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.mortgage_interest_deductible == 8_000.0

    def test_mortgage_interest_above_debt_limit(self):
        """Mortgage interest on debt above $750k should be prorated."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            mortgage_interest=16_000.0,
            mortgage_debt=800_000.0,  # Above $750k limit
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        # Prorated: 750k/800k * 16,000 = 15,000
        assert result.mortgage_interest_deductible == 15_000.0

    def test_mortgage_interest_exactly_at_debt_limit(self):
        """Mortgage interest on debt exactly at $750k should be fully deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            mortgage_interest=15_000.0,
            mortgage_debt=750_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.mortgage_interest_deductible == 15_000.0

    def test_charitable_contributions_below_limit(self):
        """Charitable contributions below 60% AGI limit should be fully deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            charitable_contributions=30_000.0,  # Below 60% of 100k = 60,000
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.charitable_contributions_deductible == 30_000.0

    def test_charitable_contributions_above_limit(self):
        """Charitable contributions above 60% AGI limit should be capped."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            charitable_contributions=80_000.0,  # Above 60% of 100k = 60,000
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.charitable_contributions_deductible == 60_000.0

    def test_charitable_contributions_exactly_at_limit(self):
        """Charitable contributions exactly at 60% AGI limit should be fully deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            charitable_contributions=60_000.0,  # Exactly 60% of 100k
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.charitable_contributions_deductible == 60_000.0

    def test_casualty_losses_deductible(self):
        """Casualty/theft losses from federal disasters should be fully deductible."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            casualty_theft_losses=5_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        assert result.casualty_theft_losses_deductible == 5_000.0

    def test_itemized_exceeds_standard_deduction(self):
        """When itemized deductions exceed standard deduction, recommend itemizing."""
        input_data = ScheduleAInput(
            adjusted_gross_income=200_000.0,
            medical_expenses=20_000.0,  # 7.5% of 200k = 15,000; deductible = 5,000
            state_local_taxes=10_000.0,  # Capped at 10,000
            mortgage_interest=15_000.0,
            mortgage_debt=500_000.0,
            charitable_contributions=50_000.0,  # 60% of 200k = 120,000; fully deductible
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        # Total itemized: 5,000 + 10,000 + 15,000 + 50,000 = 80,000
        # Standard deduction: 15,000
        assert result.total_itemized_deductions == 80_000.0
        assert result.standard_deduction == 15_000.0
        assert result.recommended_deduction == 80_000.0
        assert result.use_itemized is True

    def test_standard_deduction_exceeds_itemized(self):
        """When standard deduction exceeds itemized, recommend standard."""
        input_data = ScheduleAInput(
            adjusted_gross_income=50_000.0,
            medical_expenses=2_000.0,  # Below 7.5% floor
            state_local_taxes=5_000.0,
            mortgage_interest=3_000.0,
            mortgage_debt=200_000.0,
            charitable_contributions=1_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        # Total itemized: 0 + 5,000 + 3,000 + 1,000 = 9,000
        # Standard deduction: 15,000
        assert result.total_itemized_deductions == 9_000.0
        assert result.standard_deduction == 15_000.0
        assert result.recommended_deduction == 15_000.0
        assert result.use_itemized is False

    def test_married_filing_jointly_standard_deduction(self):
        """Married filing jointly should have $30,000 standard deduction."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            filing_status="married_filing_jointly",
        )
        result = calculate_schedule_a(input_data)

        assert result.standard_deduction == 30_000.0

    def test_married_filing_separately_standard_deduction(self):
        """Married filing separately should have $15,000 standard deduction."""
        input_data = ScheduleAInput(
            adjusted_gross_income=100_000.0,
            filing_status="married_filing_separately",
        )
        result = calculate_schedule_a(input_data)

        assert result.standard_deduction == 15_000.0

    def test_comprehensive_itemized_deductions(self):
        """Test comprehensive calculation with all deduction types."""
        input_data = ScheduleAInput(
            adjusted_gross_income=150_000.0,
            medical_expenses=15_000.0,  # 7.5% of 150k = 11,250; deductible = 3,750
            state_local_taxes=12_000.0,  # Capped at 10,000
            mortgage_interest=10_000.0,
            mortgage_debt=600_000.0,  # Within limit
            charitable_contributions=40_000.0,  # 60% of 150k = 90,000; fully deductible
            casualty_theft_losses=2_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        # Medical: 15,000 - 11,250 = 3,750
        assert result.medical_expenses_deductible == 3_750.0
        # SALT: capped at 10,000
        assert result.salt_deductible == 10_000.0
        # Mortgage: fully deductible (within limit)
        assert result.mortgage_interest_deductible == 10_000.0
        # Charitable: fully deductible (below 60% limit)
        assert result.charitable_contributions_deductible == 40_000.0
        # Casualty: fully deductible
        assert result.casualty_theft_losses_deductible == 2_000.0
        # Total: 3,750 + 10,000 + 10,000 + 40,000 + 2,000 = 65,750
        assert result.total_itemized_deductions == 65_750.0
        assert result.use_itemized is True

    def test_rounding_precision(self):
        """Test that results are properly rounded to 2 decimal places."""
        input_data = ScheduleAInput(
            adjusted_gross_income=75_333.33,
            medical_expenses=8_000.0,
            state_local_taxes=10_000.0,
            mortgage_interest=5_000.0,
            mortgage_debt=300_000.0,
            charitable_contributions=2_000.0,
            filing_status="single",
        )
        result = calculate_schedule_a(input_data)

        # All monetary values should have at most 2 decimal places
        assert result.medical_expenses_deductible == round(result.medical_expenses_deductible, 2)
        assert result.salt_deductible == round(result.salt_deductible, 2)
        assert result.mortgage_interest_deductible == round(result.mortgage_interest_deductible, 2)
        assert result.charitable_contributions_deductible == round(result.charitable_contributions_deductible, 2)
        assert result.casualty_theft_losses_deductible == round(result.casualty_theft_losses_deductible, 2)
        assert result.total_itemized_deductions == round(result.total_itemized_deductions, 2)


class TestScheduleAOverview:
    """Test Schedule A overview function."""

    def test_overview_structure(self):
        """Overview should contain all required sections."""
        overview = get_schedule_a_overview()

        assert "title" in overview
        assert "statutory_authority" in overview
        assert "tax_year" in overview
        assert "deduction_rules" in overview
        assert "standard_deduction_2025" in overview
        assert "calculation_steps" in overview
        assert "notes" in overview

    def test_overview_statutory_authority(self):
        """Overview should reference correct IRC sections."""
        overview = get_schedule_a_overview()
        authorities = overview["statutory_authority"]

        assert any("IRC §63" in auth for auth in authorities)
        assert any("IRC §213" in auth for auth in authorities)
        assert any("IRC §164" in auth for auth in authorities)
        assert any("IRC §163" in auth for auth in authorities)
        assert any("IRC §170" in auth for auth in authorities)
        assert any("IRC §165" in auth for auth in authorities)

    def test_overview_tax_year(self):
        """Overview should specify 2025 tax year."""
        overview = get_schedule_a_overview()
        assert overview["tax_year"] == 2025

    def test_overview_deduction_rules(self):
        """Overview should contain correct deduction rules."""
        overview = get_schedule_a_overview()
        rules = overview["deduction_rules"]

        assert "medical_expenses" in rules
        assert "salt" in rules
        assert "mortgage_interest" in rules
        assert "charitable_contributions" in rules
        assert "casualty_theft_losses" in rules

        assert rules["medical_expenses"]["floor"] == "7.5% of AGI"
        assert rules["salt"]["cap"] == "$10,000"
        assert rules["mortgage_interest"]["debt_cap"] == "$750,000"
        assert rules["charitable_contributions"]["agi_limit"] == "60%"

    def test_overview_standard_deduction(self):
        """Overview should contain correct 2025 standard deduction amounts."""
        overview = get_schedule_a_overview()
        std = overview["standard_deduction_2025"]

        assert std["single"] == "$15,000"
        assert std["married_filing_jointly"] == "$30,000"
        assert std["married_filing_separately"] == "$15,000"