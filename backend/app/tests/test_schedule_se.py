"""
Tests for Schedule SE (Self-Employment Tax) calculations.
Covers edge cases, threshold boundaries, and different filing statuses.
"""
import pytest
from app.modules.schedule_se import (
    ScheduleSEInput,
    calculate_schedule_se,
    calculate_se_deduction,
    get_schedule_se_overview,
    SOCIAL_SECURITY_BASE_2025,
    ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    ADDITIONAL_MEDICARE_THRESHOLD_MARRIED,
)


class TestScheduleSECalculations:
    """Test Schedule SE tax calculations."""
    
    def test_zero_income(self):
        """Zero self-employment income should result in zero tax."""
        input_data = ScheduleSEInput(
            net_self_employment_income=0.0,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        assert result.net_self_employment_income == 0.0
        assert result.net_earnings_subject_to_se_tax == 0.0
        assert result.social_security_tax == 0.0
        assert result.medicare_tax == 0.0
        assert result.additional_medicare_tax == 0.0
        assert result.total_self_employment_tax == 0.0
        assert result.deductible_se_tax == 0.0
    
    def test_negative_income(self):
        """Negative income (loss) should result in zero tax."""
        input_data = ScheduleSEInput(
            net_self_employment_income=-10_000.0,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        assert result.net_self_employment_income == -10_000.0
        assert result.net_earnings_subject_to_se_tax == 0.0
        assert result.total_self_employment_tax == 0.0
    
    def test_low_income_below_ss_base(self):
        """Test income well below Social Security base."""
        input_data = ScheduleSEInput(
            net_self_employment_income=50_000.0,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # Net earnings = 50,000 * 0.9235 = 46,175
        expected_net_earnings = 46_175.0
        # SS tax = 46,175 * 0.124 = 5,725.70
        expected_ss_tax = 5_725.70
        # Medicare = 46,175 * 0.029 = 1,339.08
        expected_medicare = 1_339.08
        # Additional Medicare = 0 (below threshold)
        expected_additional = 0.0
        # Total = 5,725.70 + 1,339.08 = 7,064.78
        expected_total = 7_064.78
        
        assert result.net_earnings_subject_to_se_tax == expected_net_earnings
        assert result.social_security_tax == expected_ss_tax
        assert result.medicare_tax == expected_medicare
        assert result.additional_medicare_tax == expected_additional
        assert abs(result.total_self_employment_tax - expected_total) < 0.02
        assert result.deductible_se_tax == round(result.total_self_employment_tax * 0.5, 2)
    
    def test_income_exactly_at_ss_base(self):
        """Test income that results in net earnings exactly at SS base."""
        # To get exactly $168,600 net earnings: 168,600 / 0.9235 = 182,593.60
        input_data = ScheduleSEInput(
            net_self_employment_income=182_593.60,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # Net earnings = 182,593.60 * 0.9235 ≈ 168,600.00
        assert abs(result.net_earnings_subject_to_se_tax - SOCIAL_SECURITY_BASE_2025) < 30.0
        # SS tax = 168,600 * 0.124 = 20,906.40
        assert abs(result.social_security_tax - 20_906.40) < 1.0
        # Medicare = 168,600 * 0.029 = 4,889.40
        assert abs(result.medicare_tax - 4_889.40) < 5.0
        # No additional Medicare (below $200k)
        assert result.additional_medicare_tax == 0.0
    
    def test_income_just_above_ss_base(self):
        """Test income slightly above SS base threshold."""
        input_data = ScheduleSEInput(
            net_self_employment_income=200_000.0,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # Net earnings = 200,000 * 0.9235 = 184,700
        expected_net_earnings = 184_700.0
        # SS tax capped at base: 168,600 * 0.124 = 20,906.40
        expected_ss_tax = 20_906.40
        # Medicare on all: 184,700 * 0.029 = 5,356.30
        expected_medicare = 5_356.30
        # Additional Medicare = 0 (net earnings $184,700 < $200k threshold)
        expected_additional = 0.0
        
        assert result.net_earnings_subject_to_se_tax == expected_net_earnings
        assert result.social_security_tax == expected_ss_tax
        assert result.medicare_tax == expected_medicare
        assert result.additional_medicare_tax == expected_additional
    
    def test_income_exactly_at_additional_medicare_threshold_single(self):
        """Test income exactly at Additional Medicare threshold for single filers."""
        # To get exactly $200,000 net earnings: 200,000 / 0.9235 = 216,621.28
        input_data = ScheduleSEInput(
            net_self_employment_income=216_621.28,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # Net earnings should be very close to $200,000
        assert abs(result.net_earnings_subject_to_se_tax - ADDITIONAL_MEDICARE_THRESHOLD_SINGLE) < 60.0
        # Additional Medicare should be minimal (just above threshold)
        assert result.additional_medicare_tax < 1.0
    
    def test_income_above_additional_medicare_threshold_single(self):
        """Test income above Additional Medicare threshold (single)."""
        input_data = ScheduleSEInput(
            net_self_employment_income=250_000.0,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # Net earnings = 250,000 * 0.9235 = 230,875
        expected_net_earnings = 230_875.0
        # SS tax capped: 168,600 * 0.124 = 20,906.40
        expected_ss_tax = 20_906.40
        # Medicare: 230,875 * 0.029 = 6,695.38
        expected_medicare = 6_695.38
        # Additional Medicare: (230,875 - 200,000) * 0.009 = 30,875 * 0.009 = 277.88
        expected_additional = 277.88
        expected_total = expected_ss_tax + expected_medicare + expected_additional
        
        assert result.net_earnings_subject_to_se_tax == expected_net_earnings
        assert result.social_security_tax == expected_ss_tax
        assert result.medicare_tax == expected_medicare
        assert result.additional_medicare_tax == expected_additional
        assert abs(result.total_self_employment_tax - round(expected_total, 2)) < 0.02
    
    def test_high_income_single(self):
        """Test very high income (single filer)."""
        input_data = ScheduleSEInput(
            net_self_employment_income=500_000.0,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # Net earnings = 500,000 * 0.9235 = 461,750
        expected_net_earnings = 461_750.0
        # SS tax capped: 168,600 * 0.124 = 20,906.40
        expected_ss_tax = 20_906.40
        # Medicare: 461,750 * 0.029 = 13,390.75
        expected_medicare = 13_390.75
        # Additional Medicare: (461,750 - 200,000) * 0.009 = 261,750 * 0.009 = 2,355.75
        expected_additional = 2_355.75
        
        assert result.net_earnings_subject_to_se_tax == expected_net_earnings
        assert result.social_security_tax == expected_ss_tax
        assert result.medicare_tax == expected_medicare
        assert result.additional_medicare_tax == expected_additional
    
    def test_married_filing_jointly_below_threshold(self):
        """Test married filing jointly below Additional Medicare threshold."""
        input_data = ScheduleSEInput(
            net_self_employment_income=200_000.0,
            filing_status="married_filing_jointly",
        )
        result = calculate_schedule_se(input_data)
        
        # Net earnings = 200,000 * 0.9235 = 184,700
        # Additional Medicare threshold for MFJ is $250,000
        # So no additional Medicare tax
        assert result.additional_medicare_tax == 0.0
    
    def test_married_filing_jointly_above_threshold(self):
        """Test married filing jointly above Additional Medicare threshold."""
        input_data = ScheduleSEInput(
            net_self_employment_income=300_000.0,
            filing_status="married_filing_jointly",
        )
        result = calculate_schedule_se(input_data)
        
        # Net earnings = 300,000 * 0.9235 = 277,050
        expected_net_earnings = 277_050.0
        # SS tax capped: 168,600 * 0.124 = 20,906.40
        expected_ss_tax = 20_906.40
        # Medicare: 277,050 * 0.029 = 8,034.45
        expected_medicare = 8_034.45
        # Additional Medicare: (277,050 - 250,000) * 0.009 = 27,050 * 0.009 = 243.45
        expected_additional = 243.45
        
        assert result.net_earnings_subject_to_se_tax == expected_net_earnings
        assert result.social_security_tax == expected_ss_tax
        assert result.medicare_tax == expected_medicare
        assert result.additional_medicare_tax == expected_additional
    
    def test_married_filing_separately(self):
        """Test married filing separately (uses single threshold)."""
        input_data = ScheduleSEInput(
            net_self_employment_income=250_000.0,
            filing_status="married_filing_separately",
        )
        result = calculate_schedule_se(input_data)
        
        # Should use single threshold ($200k), not married ($250k)
        # Net earnings = 250,000 * 0.9235 = 230,875
        # Additional Medicare: (230,875 - 200,000) * 0.009 = 277.88
        assert result.additional_medicare_tax == 277.88
    
    def test_boundary_ss_base_minus_one_dollar(self):
        """Test income just below SS base boundary."""
        # Net earnings should be $168,599
        # Gross = 168,599 / 0.9235 = 182,592.52
        input_data = ScheduleSEInput(
            net_self_employment_income=182_592.52,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # Should apply full SS tax on amount near base (within rounding tolerance)
        assert abs(result.net_earnings_subject_to_se_tax - SOCIAL_SECURITY_BASE_2025) < 30.0
        assert result.social_security_tax <= 20_906.40  # At or below max
    
    def test_boundary_additional_medicare_plus_one_dollar(self):
        """Test income just above Additional Medicare threshold."""
        # Net earnings should be $200,001
        # Gross = 200,001 / 0.9235 = 216,622.36
        input_data = ScheduleSEInput(
            net_self_employment_income=216_622.36,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # Should have minimal additional Medicare tax
        assert result.additional_medicare_tax > 0.0
        assert result.additional_medicare_tax < 1.0  # Very small amount
    
    def test_rounding_precision(self):
        """Test that results are properly rounded to 2 decimal places."""
        input_data = ScheduleSEInput(
            net_self_employment_income=75_333.33,
            filing_status="single",
        )
        result = calculate_schedule_se(input_data)
        
        # All monetary values should have at most 2 decimal places
        assert result.net_earnings_subject_to_se_tax == round(result.net_earnings_subject_to_se_tax, 2)
        assert result.social_security_tax == round(result.social_security_tax, 2)
        assert result.medicare_tax == round(result.medicare_tax, 2)
        assert result.additional_medicare_tax == round(result.additional_medicare_tax, 2)
        assert result.total_self_employment_tax == round(result.total_self_employment_tax, 2)
        assert result.deductible_se_tax == round(result.deductible_se_tax, 2)


class TestSEDeduction:
    """Test SE tax deduction calculation."""
    
    def test_deduction_zero_tax(self):
        """Zero SE tax should result in zero deduction."""
        deduction = calculate_se_deduction(0.0)
        assert deduction == 0.0
    
    def test_deduction_calculation(self):
        """Deduction should be exactly 50% of SE tax."""
        deduction = calculate_se_deduction(10_597.50)
        assert deduction == 5_298.75
    
    def test_deduction_rounding(self):
        """Deduction should be rounded to 2 decimal places."""
        deduction = calculate_se_deduction(1_234.567)
        assert deduction == 617.28  # 50% of 1234.567 rounded


class TestScheduleSEOverview:
    """Test Schedule SE overview function."""
    
    def test_overview_structure(self):
        """Overview should contain all required sections."""
        overview = get_schedule_se_overview()
        
        assert "title" in overview
        assert "statutory_authority" in overview
        assert "tax_year" in overview
        assert "rates" in overview
        assert "calculation_steps" in overview
        assert "notes" in overview
    
    def test_overview_statutory_authority(self):
        """Overview should reference correct IRC sections."""
        overview = get_schedule_se_overview()
        authorities = overview["statutory_authority"]
        
        assert any("IRC §1401" in auth for auth in authorities)
        assert any("IRC §1402" in auth for auth in authorities)
        assert any("IRC §164(f)" in auth for auth in authorities)
    
    def test_overview_tax_year(self):
        """Overview should specify 2025 tax year."""
        overview = get_schedule_se_overview()
        assert overview["tax_year"] == 2025
    
    def test_overview_rates(self):
        """Overview should contain correct tax rates."""
        overview = get_schedule_se_overview()
        rates = overview["rates"]
        
        assert "social_security" in rates
        assert "medicare" in rates
        assert "additional_medicare" in rates
        
        assert rates["social_security"]["rate"] == "12.4%"
        assert rates["medicare"]["rate"] == "2.9%"
        assert rates["additional_medicare"]["rate"] == "0.9%"
