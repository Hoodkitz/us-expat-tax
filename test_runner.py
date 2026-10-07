#!/usr/bin/env python3
"""
Standalone test runner for Form 8938 Extended Features.
Runs tests without pytest dependency.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.modules.form8938_extended import *

def run_tests():
    """Run all tests and report results."""
    passed = 0
    failed = 0
    errors = []
    
    print("=" * 70)
    print("Testing Form 8938 Extended Features")
    print("=" * 70)
    
    # Test 1: Grantor Trust Reporting
    print("\n[TEST 1] Grantor trust reporting...")
    try:
        inp = ForeignTrustInput(
            trust_name="Smith Family Trust",
            trust_type="grantor",
            country="CH",
            fair_market_value_usd=500_000.0,
            distributions_received_usd=0.0,
            is_grantor=True,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.is_grantor_trust is True
        assert "Form 3520" in result.required_forms
        assert "Form 3520-A" in result.required_forms
        assert "Form 8938" in result.required_forms
        print("✓ PASS: Grantor trust requires Forms 3520, 3520-A, and 8938")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 1: Grantor trust", str(e)))
    
    # Test 2: Beneficiary Trust Reporting
    print("\n[TEST 2] Beneficiary trust reporting...")
    try:
        inp = ForeignTrustInput(
            trust_name="European Family Trust",
            trust_type="beneficiary",
            country="LU",
            fair_market_value_usd=250_000.0,
            distributions_received_usd=15_000.0,
            is_grantor=False,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.is_grantor_trust is False
        assert "Form 3520" in result.required_forms
        assert "Form 8938" in result.required_forms
        assert "Form 3520-A" not in result.required_forms
        print("✓ PASS: Beneficiary trust requires Forms 3520 and 8938 (not 3520-A)")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 2: Beneficiary trust", str(e)))
    
    # Test 3: MFJ Abroad - Below Threshold
    print("\n[TEST 3] MFJ abroad below $400k/$600k thresholds...")
    try:
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="abroad",
            year_end_value_usd=350_000.0,
            max_any_time_value_usd=450_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is False
        assert result.applicable_threshold_year_end == 400_000.0
        assert result.applicable_threshold_any_time == 600_000.0
        print("✓ PASS: MFJ abroad with $350k/$450k not required")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 3: MFJ abroad below threshold", str(e)))
    
    # Test 4: MFJ Abroad - Above Year-End Threshold
    print("\n[TEST 4] MFJ abroad above $400k year-end threshold...")
    try:
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="abroad",
            year_end_value_usd=450_000.0,
            max_any_time_value_usd=550_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert "year-end value" in result.reasons[0].lower()
        print("✓ PASS: MFJ abroad with $450k year-end required")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 4: MFJ abroad above threshold", str(e)))
    
    # Test 5: Single Domestic Thresholds
    print("\n[TEST 5] Single domestic $50k/$75k thresholds...")
    try:
        inp = JointFilingThresholdInput(
            filing_status="single",
            residency_status="domestic",
            year_end_value_usd=60_000.0,
            max_any_time_value_usd=70_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert result.applicable_threshold_year_end == 50_000.0
        assert result.applicable_threshold_any_time == 75_000.0
        print("✓ PASS: Single domestic with $60k/$70k required")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 5: Single domestic thresholds", str(e)))
    
    # Test 6: Accuracy Penalty - 40% on underpayment
    print("\n[TEST 6] 40% accuracy-related penalty...")
    try:
        inp = AccuracyPenaltyInput(
            underpayment_amount_usd=50_000.0,
            total_foreign_assets_usd=300_000.0,
            tax_year=2024,
        )
        result = calculate_accuracy_penalty(inp)
        assert result.penalty_rate == 0.40
        assert result.penalty_amount == 20_000.0
        assert "40%" in result.explanation
        print("✓ PASS: 40% penalty on $50k underpayment = $20k")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 6: Accuracy penalty", str(e)))
    
    # Test 7: Statute of Limitations - Normal (3 years)
    print("\n[TEST 7] Normal 3-year statute (assets disclosed)...")
    try:
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=True,
            foreign_asset_value_usd=500_000.0,
            gross_income_usd=200_000.0,
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        assert result.statute_years == 3
        assert result.is_extended is False
        print("✓ PASS: Assets disclosed → 3-year statute")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 7: Normal statute", str(e)))
    
    # Test 8: Statute of Limitations - Extended (6 years)
    print("\n[TEST 8] Extended 6-year statute (large undisclosed assets)...")
    try:
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=False,
            foreign_asset_value_usd=100_000.0,  # > 25% of 200k gross income
            gross_income_usd=200_000.0,
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        assert result.statute_years == 6
        assert result.is_extended is True
        print("✓ PASS: Undisclosed assets > 25% gross income → 6-year statute")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 8: Extended statute", str(e)))
    
    # Test 9: Exactly at Threshold (should NOT be required)
    print("\n[TEST 9] Exactly at threshold (should NOT trigger)...")
    try:
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="abroad",
            year_end_value_usd=400_000.0,  # Exactly at threshold
            max_any_time_value_usd=600_000.0,  # Exactly at threshold
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is False
        print("✓ PASS: Exactly at threshold does NOT trigger filing requirement")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 9: Threshold boundary", str(e)))
    
    # Test 10: Zero Values
    print("\n[TEST 10] Zero value trust (still reportable)...")
    try:
        inp = ForeignTrustInput(
            trust_name="Empty Trust",
            trust_type="beneficiary",
            country="UK",
            fair_market_value_usd=0.0,
            distributions_received_usd=0.0,
            is_grantor=False,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.fair_market_value_usd == 0.0
        print("✓ PASS: Zero-value trust still requires reporting")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 10: Zero value", str(e)))
    
    # Test 11: Large Underpayment Accuracy Penalty
    print("\n[TEST 11] Large underpayment accuracy penalty...")
    try:
        inp = AccuracyPenaltyInput(
            underpayment_amount_usd=200_000.0,
            total_foreign_assets_usd=1_000_000.0,
            tax_year=2024,
        )
        result = calculate_accuracy_penalty(inp)
        assert result.penalty_amount == 80_000.0
        print("✓ PASS: 40% of $200k underpayment = $80k penalty")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 11: Large penalty", str(e)))
    
    # Test 12: Statute with Undisclosed but Below 25% Threshold
    print("\n[TEST 12] Undisclosed assets below 25% threshold...")
    try:
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=False,
            foreign_asset_value_usd=100_000.0,  # < 25% of 1M gross income
            gross_income_usd=1_000_000.0,
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        assert result.statute_years == 3
        assert result.is_extended is False
        print("✓ PASS: Undisclosed assets < 25% → normal 3-year statute")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 12: Below 25% threshold", str(e)))
    
    # Test 13: MFJ Domestic Thresholds
    print("\n[TEST 13] MFJ domestic $100k/$150k thresholds...")
    try:
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="domestic",
            year_end_value_usd=120_000.0,
            max_any_time_value_usd=140_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert result.applicable_threshold_year_end == 100_000.0
        assert result.applicable_threshold_any_time == 150_000.0
        print("✓ PASS: MFJ domestic with $120k/$140k required")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 13: MFJ domestic", str(e)))
    
    # Test 14: Other Trust Type
    print("\n[TEST 14] Other trust type (not grantor or beneficiary)...")
    try:
        inp = ForeignTrustInput(
            trust_name="Offshore Trust",
            trust_type="other",
            country="KY",
            fair_market_value_usd=100_000.0,
            distributions_received_usd=0.0,
            is_grantor=False,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.is_grantor_trust is False
        assert "Form 8938" in result.required_forms
        # Should not require 3520/3520-A for "other" type
        assert len([f for f in result.required_forms if "3520" in f]) == 0
        print("✓ PASS: Other trust type requires only Form 8938")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 14: Other trust type", str(e)))
    
    # Test 15: Single Abroad Thresholds
    print("\n[TEST 15] Single abroad $200k/$300k thresholds...")
    try:
        inp = JointFilingThresholdInput(
            filing_status="single",
            residency_status="abroad",
            year_end_value_usd=250_000.0,
            max_any_time_value_usd=280_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert result.applicable_threshold_year_end == 200_000.0
        assert result.applicable_threshold_any_time == 300_000.0
        print("✓ PASS: Single abroad with $250k/$280k required")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 15: Single abroad", str(e)))
    
    # Summary
    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if errors:
        print("\nFailed Tests:")
        for name, error in errors:
            print(f"  - {name}: {error}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
