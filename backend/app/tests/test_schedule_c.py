"""
Comprehensive tests for Schedule C Business Income and Deductions.
IRC §162, IRC §280A (Home Office), IRC §274 (Vehicle & Meals).
"""
import pytest
from backend.app.modules.schedule_c import (
    ScheduleCIncomeExpensesInput,
    HomeOfficeSimplifiedInput,
    HomeOfficeActualInput,
    VehicleStandardMileageInput,
    VehicleActualExpensesInput,
    calculate_schedule_c,
    calculate_home_office_simplified,
    calculate_home_office_actual,
    calculate_vehicle_standard_mileage,
    calculate_vehicle_actual_expenses,
    get_schedule_c_overview,
    STANDARD_MILEAGE_RATE_2024,
    SIMPLIFIED_HOME_OFFICE_RATE,
    SIMPLIFIED_HOME_OFFICE_MAX_DEDUCTION,
)


# ===============================================================================
# Home Office Deduction Tests
# ===============================================================================

def test_home_office_simplified_basic():
    """Test simplified home office at 200 sqft = $1,000"""
    input_data = HomeOfficeSimplifiedInput(square_footage=200)
    result = calculate_home_office_simplified(input_data)
    
    assert result.method == "simplified"
    assert result.deduction_amount == 200 * SIMPLIFIED_HOME_OFFICE_RATE  # $1,000
    assert result.square_footage_used == 200
    assert result.business_use_percentage is None


def test_home_office_simplified_at_max():
    """Test simplified home office at max 300 sqft = $1,500"""
    input_data = HomeOfficeSimplifiedInput(square_footage=300)
    result = calculate_home_office_simplified(input_data)
    
    assert result.deduction_amount == SIMPLIFIED_HOME_OFFICE_MAX_DEDUCTION  # $1,500
    assert result.square_footage_used == 300


def test_home_office_simplified_exceeds_max():
    """Test simplified home office caps at 300 sqft even if more entered"""
    input_data = HomeOfficeSimplifiedInput(square_footage=400)
    result = calculate_home_office_simplified(input_data)
    
    assert result.deduction_amount == SIMPLIFIED_HOME_OFFICE_MAX_DEDUCTION  # $1,500
    assert result.square_footage_used == 300
    assert result.details["requested_sqft"] == 400


def test_home_office_actual_basic():
    """Test actual expense method with 20% business use"""
    input_data = HomeOfficeActualInput(
        business_square_footage=200,
        total_home_square_footage=1000,
        mortgage_interest=12000,
        utilities=2400,
        insurance=1200,
    )
    result = calculate_home_office_actual(input_data)
    
    assert result.method == "actual"
    assert result.business_use_percentage == 20.0  # 200/1000
    # Indirect: (12000 + 2400 + 1200) * 0.20 = 3120
    assert result.deduction_amount == 3120.0


def test_home_office_actual_with_direct_expenses():
    """Test actual method with direct expenses (100% deductible)"""
    input_data = HomeOfficeActualInput(
        business_square_footage=150,
        total_home_square_footage=1000,
        direct_expenses=500,  # Office-only repairs
        mortgage_interest=10000,
        utilities=2000,
    )
    result = calculate_home_office_actual(input_data)
    
    # Business % = 15% (150/1000)
    # Indirect: (10000 + 2000) * 0.15 = 1800
    # Direct: 500
    # Total: 2300
    assert result.business_use_percentage == 15.0
    assert result.deduction_amount == 2300.0


def test_home_office_actual_income_limitation():
    """Test home office deduction limited to business income"""
    input_data = HomeOfficeActualInput(
        business_square_footage=300,
        total_home_square_footage=1000,
        mortgage_interest=20000,
        utilities=5000,
    )
    business_income = 5000  # Low income
    result = calculate_home_office_actual(input_data, business_income)
    
    # Business % = 30%
    # Indirect: (20000 + 5000) * 0.30 = 7500
    # But limited to business income of 5000
    assert result.deduction_amount == 5000.0


def test_home_office_actual_validation_error():
    """Test validation: business sqft cannot exceed total sqft"""
    with pytest.raises(ValueError, match="cannot exceed total home sqft"):
        HomeOfficeActualInput(
            business_square_footage=1200,
            total_home_square_footage=1000,
        )


# ===============================================================================
# Vehicle Deduction Tests
# ===============================================================================

def test_vehicle_standard_mileage_basic():
    """Test standard mileage: 10,000 business miles @ 67¢"""
    input_data = VehicleStandardMileageInput(
        business_miles=10000,
        total_miles=15000,
    )
    result = calculate_vehicle_standard_mileage(input_data)
    
    assert result.method == "standard_mileage"
    assert result.business_use_percentage == pytest.approx(66.67, abs=0.01)
    assert result.deduction_amount == 10000 * STANDARD_MILEAGE_RATE_2024  # $6,700
    assert result.qualifies_for_listed_property is True  # >50%


def test_vehicle_standard_mileage_with_parking():
    """Test standard mileage + parking/tolls"""
    input_data = VehicleStandardMileageInput(
        business_miles=5000,
        total_miles=10000,
        parking_and_tolls=800,
    )
    result = calculate_vehicle_standard_mileage(input_data)
    
    # Mileage: 5000 * 0.67 = 3350
    # + Parking: 800
    # Total: 4150
    assert result.business_use_percentage == 50.0
    assert result.deduction_amount == 4150.0
    assert result.qualifies_for_listed_property is False  # NOT >50%, exactly 50%


def test_vehicle_standard_mileage_validation_error():
    """Test validation: business miles cannot exceed total miles"""
    with pytest.raises(ValueError, match="cannot exceed total miles"):
        VehicleStandardMileageInput(
            business_miles=20000,
            total_miles=15000,
        )


def test_vehicle_actual_expenses_basic():
    """Test actual expenses: $8,000 total, 60% business use"""
    input_data = VehicleActualExpensesInput(
        business_miles=12000,
        total_miles=20000,
        gasoline=3000,
        insurance=1200,
        repairs_and_maintenance=1500,
        depreciation=2000,
        registration=300,
    )
    result = calculate_vehicle_actual_expenses(input_data)
    
    assert result.method == "actual"
    assert result.business_use_percentage == 60.0
    # Total expenses: 3000 + 1200 + 1500 + 2000 + 300 = 8000
    # Business: 8000 * 0.60 = 4800
    assert result.deduction_amount == 4800.0
    assert result.qualifies_for_listed_property is True


def test_vehicle_actual_expenses_with_parking():
    """Test actual expenses + parking/tolls (100% deductible)"""
    input_data = VehicleActualExpensesInput(
        business_miles=8000,
        total_miles=10000,
        gasoline=2000,
        insurance=1000,
        parking_and_tolls=600,
    )
    result = calculate_vehicle_actual_expenses(input_data)
    
    # Business %: 80%
    # Vehicle expenses: 2000 + 1000 = 3000
    # Business portion: 3000 * 0.80 = 2400
    # + Parking: 600 (100% deductible)
    # Total: 3000
    assert result.business_use_percentage == 80.0
    assert result.deduction_amount == 3000.0


# ===============================================================================
# Complete Schedule C Tests
# ===============================================================================

def test_schedule_c_simple_profit():
    """Test basic Schedule C with profit"""
    income_expenses = ScheduleCIncomeExpensesInput(
        gross_receipts=100000,
        advertising=5000,
        supplies=3000,
        utilities=2000,
    )
    result = calculate_schedule_c(income_expenses)
    
    assert result.gross_income == 100000
    assert result.gross_profit == 100000  # No COGS
    assert result.total_income == 100000
    assert result.total_expenses == 10000  # 5000 + 3000 + 2000
    assert result.net_profit_or_loss == 90000
    assert result.flows_to_schedule_se is True


def test_schedule_c_with_cogs():
    """Test Schedule C with cost of goods sold"""
    income_expenses = ScheduleCIncomeExpensesInput(
        gross_receipts=200000,
        returns_and_allowances=5000,
        cost_of_goods_sold=80000,
        advertising=10000,
        rent_lease_property=24000,
    )
    result = calculate_schedule_c(income_expenses)
    
    assert result.gross_income == 200000
    assert result.returns_and_allowances == 5000
    assert result.net_gross_income == 195000
    assert result.cost_of_goods_sold == 80000
    assert result.gross_profit == 115000  # 195000 - 80000
    assert result.total_expenses == 34000  # 10000 + 24000
    assert result.net_profit_or_loss == 81000


def test_schedule_c_with_home_office():
    """Test Schedule C with simplified home office deduction"""
    income_expenses = ScheduleCIncomeExpensesInput(
        gross_receipts=75000,
        supplies=5000,
    )
    home_office = HomeOfficeSimplifiedInput(square_footage=250)
    result = calculate_schedule_c(income_expenses, home_office=home_office)
    
    # Home office: 250 * $5 = $1,250
    assert result.home_office_deduction == 1250.0
    assert result.total_expenses == 6250.0  # 5000 + 1250
    assert result.net_profit_or_loss == 68750.0


def test_schedule_c_home_office_income_limitation():
    """Test home office deduction limited to business income"""
    income_expenses = ScheduleCIncomeExpensesInput(
        gross_receipts=10000,
        supplies=8000,  # High expenses
    )
    home_office = HomeOfficeActualInput(
        business_square_footage=400,
        total_home_square_footage=1000,
        mortgage_interest=20000,  # Would be $8,000 deduction (40%)
    )
    result = calculate_schedule_c(income_expenses, home_office=home_office)
    
    # Business income before home office: 10000 - 8000 = 2000
    # Home office limited to 2000 (not full 8000)
    assert result.home_office_deduction == 2000.0
    assert result.net_profit_or_loss == 0.0  # Break even


def test_schedule_c_with_vehicle():
    """Test Schedule C with vehicle deduction"""
    income_expenses = ScheduleCIncomeExpensesInput(
        gross_receipts=120000,
        supplies=10000,
    )
    vehicle = VehicleStandardMileageInput(
        business_miles=15000,
        total_miles=20000,
    )
    result = calculate_schedule_c(income_expenses, vehicle=vehicle)
    
    # Vehicle: 15000 * 0.67 = 10050
    assert result.vehicle_deduction == 10050.0
    assert result.total_expenses == 20050.0  # 10000 + 10050
    assert result.net_profit_or_loss == 99950.0


def test_schedule_c_meals_limitation():
    """Test 50% meals limitation (IRC §274(n))"""
    income_expenses = ScheduleCIncomeExpensesInput(
        gross_receipts=100000,
        meals=4000,  # Only 50% deductible = $2,000
    )
    result = calculate_schedule_c(income_expenses)
    
    assert result.meals_deduction_adjustment == 2000.0  # 50% disallowed
    assert result.total_expenses == 2000.0  # Only $2,000 deductible
    assert result.net_profit_or_loss == 98000.0


def test_schedule_c_loss_scenario():
    """Test Schedule C with net loss"""
    income_expenses = ScheduleCIncomeExpensesInput(
        gross_receipts=30000,
        cost_of_goods_sold=20000,
        advertising=5000,
        rent_lease_property=12000,
        utilities=3000,
    )
    result = calculate_schedule_c(income_expenses)
    
    assert result.gross_profit == 10000
    assert result.total_expenses == 20000
    assert result.net_profit_or_loss == -10000.0
    assert result.flows_to_schedule_se is False  # No SE tax on loss


def test_schedule_c_comprehensive_integration():
    """Test full Schedule C with all features"""
    income_expenses = ScheduleCIncomeExpensesInput(
        gross_receipts=250000,
        returns_and_allowances=10000,
        cost_of_goods_sold=100000,
        advertising=8000,
        supplies=5000,
        meals=6000,  # 50% limit
        legal_and_professional=12000,
    )
    home_office = HomeOfficeSimplifiedInput(square_footage=300)
    vehicle = VehicleActualExpensesInput(
        business_miles=18000,
        total_miles=20000,
        gasoline=4000,
        insurance=1500,
        repairs_and_maintenance=2000,
    )
    result = calculate_schedule_c(income_expenses, home_office, vehicle)
    
    # Income: (250000 - 10000) - 100000 = 140000
    # Ordinary: 8000 + 5000 + 12000 = 25000
    # Meals: 3000 (50% of 6000)
    # Home office: 1500 (300 * $5)
    # Vehicle: 90% * 7500 = 6750
    # Total expenses: 25000 + 3000 + 1500 + 6750 = 36250
    # Net profit: 140000 - 36250 = 103750
    
    assert result.net_gross_income == 240000.0
    assert result.gross_profit == 140000.0
    assert result.home_office_deduction == 1500.0
    assert result.vehicle_deduction == 6750.0
    assert result.meals_deduction_adjustment == 3000.0
    assert result.net_profit_or_loss == 103750.0
    assert result.flows_to_schedule_se is True


def test_get_schedule_c_overview():
    """Test overview endpoint returns proper structure"""
    overview = get_schedule_c_overview()
    
    assert overview["title"] == "Schedule C (Form 1040) - Profit or Loss From Business"
    assert "IRC §162" in overview["statutory_authority"][0]
    assert "IRC §280A(c)" in overview["statutory_authority"][1]
    assert "IRC §274(n)" in overview["statutory_authority"][2]
    assert overview["home_office_methods"]["simplified"]["rate"] == "$5.0/sqft"
    assert overview["vehicle_deduction_methods"]["standard_mileage"]["rate_2024"] == "$0.67/mile"
    assert overview["meals_limitation"]["deductible_percentage"] == "50.0%"
