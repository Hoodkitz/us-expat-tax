"""
Schedule C API Router - Profit or Loss From Business (Sole Proprietorship)
"""
from fastapi import APIRouter, Depends

from backend.app.dependencies import get_current_tenant
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
)


router = APIRouter(prefix="/schedule-c", tags=["Schedule C"])


@router.post("/calculate")
def calculate_full_schedule_c(
    income_expenses: ScheduleCIncomeExpensesInput,
    home_office: HomeOfficeSimplifiedInput | HomeOfficeActualInput | None = None,
    vehicle: VehicleStandardMileageInput | VehicleActualExpensesInput | None = None,
    _tenant: dict = Depends(get_current_tenant),
):
    """
    Calculate complete Schedule C with optional home office and vehicle deductions.
    
    Supports both simplified and actual expense methods for home office and vehicle.
    """
    return calculate_schedule_c(income_expenses, home_office, vehicle)


@router.post("/home-office")
def calculate_home_office_deduction(
    input_data: HomeOfficeSimplifiedInput | HomeOfficeActualInput,
    business_income: float | None = None,
    _tenant: dict = Depends(get_current_tenant),
):
    """
    Calculate home office deduction only (simplified or actual method).
    
    - Simplified: $5/sqft, max 300 sqft ($1,500)
    - Actual: Allocate home expenses by business-use percentage
    """
    if input_data.method == "simplified":
        return calculate_home_office_simplified(input_data)
    else:
        return calculate_home_office_actual(input_data, business_income)


@router.post("/vehicle")
def calculate_vehicle_deduction(
    input_data: VehicleStandardMileageInput | VehicleActualExpensesInput,
    _tenant: dict = Depends(get_current_tenant),
):
    """
    Calculate vehicle deduction only (standard mileage or actual expenses).
    
    - Standard: 67¢/mile (2024) + parking/tolls
    - Actual: Total expenses × business-use percentage + parking/tolls
    """
    if input_data.method == "standard_mileage":
        return calculate_vehicle_standard_mileage(input_data)
    else:
        return calculate_vehicle_actual_expenses(input_data)


@router.get("/overview")
def get_overview(_tenant: dict = Depends(get_current_tenant)):
    """
    Get Schedule C statutory authority, rules, and calculation methods.
    
    Returns IRC references, home office methods, vehicle deduction rules, and more.
    """
    return get_schedule_c_overview()
