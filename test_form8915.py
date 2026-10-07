#!/usr/bin/env python3
"""
Standalone test runner for Form 8915.
Runs tests without pytest dependency.
"""
import sys
import os
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.modules.form8915 import *

def run_tests():
    """Run all tests and report results."""
    passed = 0
    failed = 0
    errors = []
    
    print("=" * 70)
    print("Testing Form 8915 — Qualified Disaster Retirement Plan Distributions")
    print("=" * 70)
    
    # Test 1: Hurricane with home destroyed - eligible
    print("\n[TEST 1] Hurricane with home destroyed - eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="Hurricane Ian, Florida",
            distribution_date="2024-09-28",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Hurricane"
        assert result.distribution_within_window is True
        assert result.economic_loss_threshold_met is True
        print("✓ PASS: Hurricane with home destroyed is eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 1", str(e)))
    
    # Test 2: Wildfire with economic loss - eligible
    print("\n[TEST 2] Wildfire with economic loss - eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="California Wildfire",
            distribution_date="2024-08-15",
            home_destroyed=False,
            economic_loss_amt=Decimal("50000"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Wildfire"
        assert result.economic_loss_threshold_met is True
        print("✓ PASS: Wildfire with economic loss is eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 2", str(e)))
    
    # Test 3: Flood - eligible
    print("\n[TEST 3] Flood - eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="Louisiana Flood",
            distribution_date="2024-07-01",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Flood"
        print("✓ PASS: Flood disaster is eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 3", str(e)))
    
    # Test 4: Tornado - eligible
    print("\n[TEST 4] Tornado - eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="Oklahoma Tornado",
            distribution_date="2024-05-20",
            home_destroyed=False,
            economic_loss_amt=Decimal("25000"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Tornado"
        print("✓ PASS: Tornado disaster is eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 4", str(e)))
    
    # Test 5: Earthquake - eligible
    print("\n[TEST 5] Earthquake - eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="California Earthquake",
            distribution_date="2024-06-10",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Earthquake"
        print("✓ PASS: Earthquake disaster is eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 5", str(e)))
    
    # Test 6: Pandemic COVID-19 - eligible
    print("\n[TEST 6] Pandemic (COVID-19) - eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="COVID-19 Pandemic",
            distribution_date="2024-03-15",
            home_destroyed=False,
            economic_loss_amt=Decimal("10000"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Pandemic (COVID-19)"
        print("✓ PASS: Pandemic disaster is eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 6", str(e)))
    
    # Test 7: Non-disaster - NOT eligible
    print("\n[TEST 7] Non-qualified disaster - NOT eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="Random Storm",
            distribution_date="2024-01-01",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is False
        print("✓ PASS: Non-qualified disaster is NOT eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 7", str(e)))
    
    # Test 8: Insufficient economic loss - NOT eligible
    print("\n[TEST 8] Insufficient economic loss - NOT eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="Hurricane",
            distribution_date="2024-09-01",
            home_destroyed=False,
            economic_loss_amt=Decimal("500"),  # Below threshold
        )
        result = check_filing_requirement(inp)
        assert result.eligible is False
        assert result.economic_loss_threshold_met is False
        print("✓ PASS: Insufficient economic loss is NOT eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 8", str(e)))
    
    # Test 9: Verify $100k limit
    print("\n[TEST 9] Verify max distribution limit $100k...")
    try:
        inp = FilingRequirementInput(
            disaster_area="Hurricane",
            distribution_date="2024-09-01",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.max_distribution_limit == MAX_DISTRIBUTION_LIMIT
        assert result.max_distribution_limit == Decimal("100000")
        print("✓ PASS: Max distribution limit is $100,000")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 9", str(e)))
    
    # Test 10: Invalid distribution date - NOT eligible
    print("\n[TEST 10] Invalid distribution date - NOT eligible...")
    try:
        inp = FilingRequirementInput(
            disaster_area="Hurricane",
            distribution_date="invalid-date",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is False
        assert "Invalid distribution date" in result.explanation
        print("✓ PASS: Invalid date format is NOT eligible")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 10", str(e)))
    
    # Test 11: Standard 3-year repayment schedule
    print("\n[TEST 11] Standard 3-year repayment schedule...")
    try:
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("75000"),
            repayment_years=3,
        )
        result = calculate_repayment_schedule(inp)
        assert result.total_distribution == Decimal("75000")
        assert result.annual_repayment == Decimal("25000")
        assert result.tax_spread_per_year == Decimal("25000")
        assert len(result.repayment_schedule) == 3
        print("✓ PASS: 3-year repayment schedule correct")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 11", str(e)))
    
    # Test 12: 2-year repayment schedule
    print("\n[TEST 12] 2-year repayment schedule...")
    try:
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("60000"),
            repayment_years=2,
        )
        result = calculate_repayment_schedule(inp)
        assert result.annual_repayment == Decimal("30000")
        assert len(result.repayment_schedule) == 2
        print("✓ PASS: 2-year repayment schedule correct")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 12", str(e)))
    
    # Test 13: 1-year repayment schedule
    print("\n[TEST 13] 1-year repayment schedule...")
    try:
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("50000"),
            repayment_years=1,
        )
        result = calculate_repayment_schedule(inp)
        assert result.annual_repayment == Decimal("50000")
        assert len(result.repayment_schedule) == 1
        print("✓ PASS: 1-year repayment schedule correct")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 13", str(e)))
    
    # Test 14: Tax spread always 3 years
    print("\n[TEST 14] Tax spread always over 3 years...")
    try:
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("90000"),
            repayment_years=1,
        )
        result = calculate_repayment_schedule(inp)
        # Tax spread is always 1/3 per year over 3 years
        assert result.tax_spread_per_year == Decimal("30000")
        print("✓ PASS: Tax spread is always 1/3 per year over 3 years")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 14", str(e)))
    
    # Test 15: Repayment schedule contains year data
    print("\n[TEST 15] Repayment schedule contains year data...")
    try:
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("60000"),
            repayment_years=3,
        )
        result = calculate_repayment_schedule(inp)
        for item in result.repayment_schedule:
            assert "year" in item
            assert "repayment_due" in item
            assert "tax_if_not_repaid" in item
        print("✓ PASS: Repayment schedule has correct structure")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 15", str(e)))
    
    # Test 16: Penalty waiver under age 59½
    print("\n[TEST 16] Penalty waiver under age 59½...")
    try:
        inp = PenaltyWaiverInput(
            age=45,
            distribution_amt=Decimal("50000"),
        )
        result = check_penalty_waiver(inp)
        assert result.waiver_eligible is True
        assert result.standard_penalty_rate == Decimal("0.10")
        assert result.waived_penalty_amount == Decimal("5000")
        print("✓ PASS: Penalty waiver applies for age 45")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 16", str(e)))
    
    # Test 17: Penalty waiver over age 59½
    print("\n[TEST 17] Penalty waiver over age 59½...")
    try:
        inp = PenaltyWaiverInput(
            age=65,
            distribution_amt=Decimal("80000"),
        )
        result = check_penalty_waiver(inp)
        assert result.waiver_eligible is True
        assert result.waived_penalty_amount == Decimal("8000")
        print("✓ PASS: Penalty waiver applies regardless of age")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 17", str(e)))
    
    # Test 18: Penalty calculation 10% of distribution
    print("\n[TEST 18] Penalty calculation 10% of distribution...")
    try:
        inp = PenaltyWaiverInput(
            age=40,
            distribution_amt=Decimal("100000"),
        )
        result = check_penalty_waiver(inp)
        assert result.waived_penalty_amount == Decimal("10000")
        print("✓ PASS: Penalty is 10% of distribution amount")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        failed += 1
        errors.append(("Test 18", str(e)))
    
    # Summary
    print("\n" + "=" * 70)
    print(f"TOTAL TESTS: {passed + failed}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    
    if failed > 0:
        print("\nFAILURE DETAILS:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")
    
    print("=" * 70)
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
