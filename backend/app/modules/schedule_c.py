"""
Schedule C (Form 1040) - Profit or Loss From Business (Sole Proprietorship)
IRC §162 Trade or Business Expenses, IRC §280A Home Office, IRC §274 Vehicle & Listed Property
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator


# 2024 Tax Constants (IRS Notice 2024-08)
STANDARD_MILEAGE_RATE_2024 = 0.67  # 67 cents per mile
SIMPLIFIED_HOME_OFFICE_RATE = 5.0  # $5 per square foot
SIMPLIFIED_HOME_OFFICE_MAX_SQFT = 300  # Maximum 300 square feet
SIMPLIFIED_HOME_OFFICE_MAX_DEDUCTION = 1500.0  # $1,500 maximum
BUSINESS_USE_PERCENTAGE_THRESHOLD = 0.50  # >50% required for listed property
MEALS_DEDUCTION_PERCENTAGE = 0.50  # Only 50% of meals deductible (IRC §274(n))


# ===============================================================================
# Income & Expenses Models
# ===============================================================================

class ScheduleCIncomeExpensesInput(BaseModel):
    """Schedule C Part I (Income) and Part II (Expenses)"""
    # Part I: Income
    gross_receipts: float = Field(default=0.0, ge=0, description="Gross receipts or sales")
    returns_and_allowances: float = Field(default=0.0, ge=0, description="Returns and allowances")
    cost_of_goods_sold: float = Field(default=0.0, ge=0, description="Cost of goods sold (COGS)")
    other_income: float = Field(default=0.0, description="Other income (including credits)")
    
    # Part II: Expenses (IRC §162 ordinary and necessary business expenses)
    advertising: float = Field(default=0.0, ge=0, description="Advertising")
    car_and_truck: float = Field(default=0.0, ge=0, description="Car and truck expenses (if not using std mileage)")
    commissions_and_fees: float = Field(default=0.0, ge=0, description="Commissions and fees")
    contract_labor: float = Field(default=0.0, ge=0, description="Contract labor")
    depletion: float = Field(default=0.0, ge=0, description="Depletion")
    depreciation: float = Field(default=0.0, ge=0, description="Depreciation and section 179 expense")
    employee_benefit_programs: float = Field(default=0.0, ge=0, description="Employee benefit programs")
    insurance: float = Field(default=0.0, ge=0, description="Insurance (other than health)")
    interest_mortgage: float = Field(default=0.0, ge=0, description="Mortgage interest (paid to banks)")
    interest_other: float = Field(default=0.0, ge=0, description="Other interest")
    legal_and_professional: float = Field(default=0.0, ge=0, description="Legal and professional services")
    office_expense: float = Field(default=0.0, ge=0, description="Office expense")
    pension_and_profit_sharing: float = Field(default=0.0, ge=0, description="Pension and profit-sharing plans")
    rent_lease_vehicles: float = Field(default=0.0, ge=0, description="Rent or lease - vehicles, machinery, equipment")
    rent_lease_property: float = Field(default=0.0, ge=0, description="Rent or lease - other business property")
    repairs_and_maintenance: float = Field(default=0.0, ge=0, description="Repairs and maintenance")
    supplies: float = Field(default=0.0, ge=0, description="Supplies (not included in COGS)")
    taxes_and_licenses: float = Field(default=0.0, ge=0, description="Taxes and licenses")
    travel: float = Field(default=0.0, ge=0, description="Travel (excluding meals)")
    meals: float = Field(default=0.0, ge=0, description="Meals (subject to 50% limitation)")
    utilities: float = Field(default=0.0, ge=0, description="Utilities")
    wages: float = Field(default=0.0, ge=0, description="Wages (less employment credits)")
    other_expenses: float = Field(default=0.0, ge=0, description="Other expenses")


# ===============================================================================
# Home Office Deduction (IRC §280A)
# ===============================================================================

class HomeOfficeSimplifiedInput(BaseModel):
    """Simplified home office deduction: $5/sqft, max 300 sqft ($1,500)"""
    method: Literal["simplified"] = "simplified"
    square_footage: float = Field(..., gt=0, le=SIMPLIFIED_HOME_OFFICE_MAX_SQFT * 2, 
                                   description="Business use square footage")


class HomeOfficeActualInput(BaseModel):
    """Actual expense method for home office deduction"""
    method: Literal["actual"] = "actual"
    business_square_footage: float = Field(..., gt=0, description="Square footage used for business")
    total_home_square_footage: float = Field(..., gt=0, description="Total home square footage")
    
    # Direct expenses (100% deductible if exclusively business)
    direct_expenses: float = Field(default=0.0, ge=0, description="Direct expenses (repairs to office only)")
    
    # Indirect expenses (prorated by business percentage)
    mortgage_interest: float = Field(default=0.0, ge=0, description="Mortgage interest")
    real_estate_taxes: float = Field(default=0.0, ge=0, description="Real estate taxes")
    utilities: float = Field(default=0.0, ge=0, description="Utilities")
    insurance: float = Field(default=0.0, ge=0, description="Homeowner's/renter's insurance")
    repairs_and_maintenance: float = Field(default=0.0, ge=0, description="General home repairs")
    depreciation: float = Field(default=0.0, ge=0, description="Depreciation of home")
    other_expenses: float = Field(default=0.0, ge=0, description="Other home expenses")
    
    @model_validator(mode='after')
    def validate_business_sqft(self) -> 'HomeOfficeActualInput':
        if self.business_square_footage > self.total_home_square_footage:
            raise ValueError(
                f"Business sqft ({self.business_square_footage}) cannot exceed "
                f"total home sqft ({self.total_home_square_footage})"
            )
        return self


class HomeOfficeResult(BaseModel):
    """Home office deduction result"""
    method: Literal["simplified", "actual"]
    deduction_amount: float
    business_use_percentage: float | None = None  # Only for actual method
    square_footage_used: float
    details: dict


# ===============================================================================
# Vehicle Deduction (IRC §274)
# ===============================================================================

class VehicleStandardMileageInput(BaseModel):
    """Standard mileage rate method (67¢/mile for 2024)"""
    method: Literal["standard_mileage"] = "standard_mileage"
    business_miles: float = Field(..., ge=0, description="Business miles driven")
    total_miles: float = Field(..., gt=0, description="Total miles driven")
    parking_and_tolls: float = Field(default=0.0, ge=0, description="Business parking and tolls")
    
    @model_validator(mode='after')
    def validate_business_miles(self) -> 'VehicleStandardMileageInput':
        if self.business_miles > self.total_miles:
            raise ValueError(
                f"Business miles ({self.business_miles}) cannot exceed total miles ({self.total_miles})"
            )
        return self


class VehicleActualExpensesInput(BaseModel):
    """Actual expenses method for vehicle deduction"""
    method: Literal["actual"] = "actual"
    business_miles: float = Field(..., ge=0, description="Business miles driven")
    total_miles: float = Field(..., gt=0, description="Total miles driven")
    
    # Actual vehicle expenses
    gasoline: float = Field(default=0.0, ge=0, description="Gasoline and oil")
    repairs_and_maintenance: float = Field(default=0.0, ge=0, description="Repairs and maintenance")
    tires: float = Field(default=0.0, ge=0, description="Tires")
    insurance: float = Field(default=0.0, ge=0, description="Insurance")
    registration: float = Field(default=0.0, ge=0, description="License and registration fees")
    lease_payments: float = Field(default=0.0, ge=0, description="Lease payments")
    depreciation: float = Field(default=0.0, ge=0, description="Depreciation")
    interest_on_car_loan: float = Field(default=0.0, ge=0, description="Interest on car loan")
    parking_and_tolls: float = Field(default=0.0, ge=0, description="Business parking and tolls")
    other_expenses: float = Field(default=0.0, ge=0, description="Other vehicle expenses")
    
    @model_validator(mode='after')
    def validate_business_miles(self) -> 'VehicleActualExpensesInput':
        if self.business_miles > self.total_miles:
            raise ValueError(
                f"Business miles ({self.business_miles}) cannot exceed total miles ({self.total_miles})"
            )
        return self


class VehicleResult(BaseModel):
    """Vehicle deduction result"""
    method: Literal["standard_mileage", "actual"]
    deduction_amount: float
    business_use_percentage: float
    business_miles: float
    total_miles: float
    qualifies_for_listed_property: bool  # Requires >50% business use
    details: dict


# ===============================================================================
# Schedule C Calculation Result
# ===============================================================================

class ScheduleCResult(BaseModel):
    """Complete Schedule C calculation result"""
    # Part I: Income
    gross_income: float
    returns_and_allowances: float
    net_gross_income: float  # Gross income - returns
    cost_of_goods_sold: float
    gross_profit: float  # Net gross income - COGS
    other_income: float
    total_income: float  # Gross profit + other income
    
    # Part II: Expenses
    total_expenses: float
    home_office_deduction: float
    vehicle_deduction: float
    meals_deduction_adjustment: float  # 50% limitation on meals
    
    # Net Profit/Loss
    net_profit_or_loss: float
    flows_to_schedule_se: bool  # True if positive net profit
    
    # Breakdown
    expense_breakdown: dict


# ===============================================================================
# Calculation Functions
# ===============================================================================

def calculate_home_office_simplified(input_data: HomeOfficeSimplifiedInput) -> HomeOfficeResult:
    """
    Simplified home office deduction: $5 per square foot, max 300 sqft ($1,500).
    IRC §280A(c)(1) regular and exclusive use requirement.
    """
    sqft_used = min(input_data.square_footage, SIMPLIFIED_HOME_OFFICE_MAX_SQFT)
    deduction = min(sqft_used * SIMPLIFIED_HOME_OFFICE_RATE, SIMPLIFIED_HOME_OFFICE_MAX_DEDUCTION)
    
    return HomeOfficeResult(
        method="simplified",
        deduction_amount=round(deduction, 2),
        business_use_percentage=None,
        square_footage_used=round(sqft_used, 2),
        details={
            "rate_per_sqft": SIMPLIFIED_HOME_OFFICE_RATE,
            "max_sqft": SIMPLIFIED_HOME_OFFICE_MAX_SQFT,
            "max_deduction": SIMPLIFIED_HOME_OFFICE_MAX_DEDUCTION,
            "requested_sqft": input_data.square_footage,
            "sqft_used": sqft_used,
        },
    )


def calculate_home_office_actual(input_data: HomeOfficeActualInput, business_income: float | None = None) -> HomeOfficeResult:
    """
    Actual expense method: Allocate home expenses by business-use percentage.
    IRC §280A(c)(5) - Deduction limited to gross income from business use.
    """
    business_pct = (input_data.business_square_footage / input_data.total_home_square_footage) * 100
    
    # Indirect expenses (prorated)
    indirect_total = (
        input_data.mortgage_interest +
        input_data.real_estate_taxes +
        input_data.utilities +
        input_data.insurance +
        input_data.repairs_and_maintenance +
        input_data.depreciation +
        input_data.other_expenses
    )
    indirect_deduction = indirect_total * (business_pct / 100)
    
    # Direct expenses (100% deductible)
    direct_deduction = input_data.direct_expenses
    
    total_deduction = indirect_deduction + direct_deduction
    
    # Apply business income limit if provided (cannot create loss)
    if business_income is not None and business_income >= 0:
        total_deduction = min(total_deduction, business_income)
    
    return HomeOfficeResult(
        method="actual",
        deduction_amount=round(total_deduction, 2),
        business_use_percentage=round(business_pct, 2),
        square_footage_used=input_data.business_square_footage,
        details={
            "business_sqft": input_data.business_square_footage,
            "total_sqft": input_data.total_home_square_footage,
            "business_percentage": round(business_pct, 2),
            "indirect_expenses": round(indirect_total, 2),
            "indirect_deduction": round(indirect_deduction, 2),
            "direct_deduction": round(direct_deduction, 2),
            "total_before_limit": round(total_deduction, 2),
            "business_income_limit": business_income,
        },
    )


def calculate_vehicle_standard_mileage(input_data: VehicleStandardMileageInput) -> VehicleResult:
    """
    Standard mileage rate: 67 cents per mile (2024) + parking/tolls.
    IRC §274(d) substantiation requirements.
    """
    business_pct = (input_data.business_miles / input_data.total_miles) * 100 if input_data.total_miles > 0 else 0
    mileage_deduction = input_data.business_miles * STANDARD_MILEAGE_RATE_2024
    total_deduction = mileage_deduction + input_data.parking_and_tolls
    qualifies = business_pct > (BUSINESS_USE_PERCENTAGE_THRESHOLD * 100)
    
    return VehicleResult(
        method="standard_mileage",
        deduction_amount=round(total_deduction, 2),
        business_use_percentage=round(business_pct, 2),
        business_miles=input_data.business_miles,
        total_miles=input_data.total_miles,
        qualifies_for_listed_property=qualifies,
        details={
            "standard_mileage_rate": STANDARD_MILEAGE_RATE_2024,
            "mileage_deduction": round(mileage_deduction, 2),
            "parking_and_tolls": input_data.parking_and_tolls,
            "business_use_threshold": f">{BUSINESS_USE_PERCENTAGE_THRESHOLD * 100}%",
        },
    )


def calculate_vehicle_actual_expenses(input_data: VehicleActualExpensesInput) -> VehicleResult:
    """
    Actual expenses method: Total vehicle costs × business-use percentage.
    IRC §274(d) substantiation and adequate records required.
    """
    business_pct = (input_data.business_miles / input_data.total_miles) * 100 if input_data.total_miles > 0 else 0
    
    total_expenses = (
        input_data.gasoline +
        input_data.repairs_and_maintenance +
        input_data.tires +
        input_data.insurance +
        input_data.registration +
        input_data.lease_payments +
        input_data.depreciation +
        input_data.interest_on_car_loan +
        input_data.other_expenses
    )
    
    # Business portion + parking/tolls (100% deductible)
    business_expense = total_expenses * (business_pct / 100)
    total_deduction = business_expense + input_data.parking_and_tolls
    qualifies = business_pct > (BUSINESS_USE_PERCENTAGE_THRESHOLD * 100)
    
    return VehicleResult(
        method="actual",
        deduction_amount=round(total_deduction, 2),
        business_use_percentage=round(business_pct, 2),
        business_miles=input_data.business_miles,
        total_miles=input_data.total_miles,
        qualifies_for_listed_property=qualifies,
        details={
            "total_vehicle_expenses": round(total_expenses, 2),
            "business_portion": round(business_expense, 2),
            "parking_and_tolls": input_data.parking_and_tolls,
            "business_use_threshold": f">{BUSINESS_USE_PERCENTAGE_THRESHOLD * 100}%",
        },
    )


def calculate_schedule_c(
    income_expenses: ScheduleCIncomeExpensesInput,
    home_office: HomeOfficeSimplifiedInput | HomeOfficeActualInput | None = None,
    vehicle: VehicleStandardMileageInput | VehicleActualExpensesInput | None = None,
) -> ScheduleCResult:
    """
    Calculate complete Schedule C (Form 1040) - Profit or Loss From Business.
    
    IRC §162: Trade or business expenses
    IRC §280A: Home office deduction
    IRC §274(n): Meals limitation (50%)
    IRC §274(d): Vehicle substantiation
    """
    # Part I: Income
    gross_income = income_expenses.gross_receipts
    returns = income_expenses.returns_and_allowances
    net_gross = gross_income - returns
    cogs = income_expenses.cost_of_goods_sold
    gross_profit = net_gross - cogs
    other_income = income_expenses.other_income
    total_income = gross_profit + other_income
    
    # Part II: Expenses (ordinary expenses before special deductions)
    ordinary_expenses = (
        income_expenses.advertising +
        income_expenses.car_and_truck +
        income_expenses.commissions_and_fees +
        income_expenses.contract_labor +
        income_expenses.depletion +
        income_expenses.depreciation +
        income_expenses.employee_benefit_programs +
        income_expenses.insurance +
        income_expenses.interest_mortgage +
        income_expenses.interest_other +
        income_expenses.legal_and_professional +
        income_expenses.office_expense +
        income_expenses.pension_and_profit_sharing +
        income_expenses.rent_lease_vehicles +
        income_expenses.rent_lease_property +
        income_expenses.repairs_and_maintenance +
        income_expenses.supplies +
        income_expenses.taxes_and_licenses +
        income_expenses.travel +
        income_expenses.utilities +
        income_expenses.wages +
        income_expenses.other_expenses
    )
    
    # Meals limitation (IRC §274(n)): Only 50% deductible
    meals_entered = income_expenses.meals
    meals_deduction = meals_entered * MEALS_DEDUCTION_PERCENTAGE
    meals_adjustment = meals_entered - meals_deduction
    
    # Calculate business income before home office (for income limit)
    business_income_before_home_office = total_income - ordinary_expenses - meals_deduction
    
    # Home office deduction
    home_office_deduction = 0.0
    if home_office:
        if home_office.method == "simplified":
            ho_result = calculate_home_office_simplified(home_office)
        else:
            ho_result = calculate_home_office_actual(home_office, business_income_before_home_office)
        home_office_deduction = ho_result.deduction_amount
    
    # Vehicle deduction
    vehicle_deduction = 0.0
    if vehicle:
        if vehicle.method == "standard_mileage":
            veh_result = calculate_vehicle_standard_mileage(vehicle)
        else:
            veh_result = calculate_vehicle_actual_expenses(vehicle)
        vehicle_deduction = veh_result.deduction_amount
    
    # Total expenses
    total_expenses = (
        ordinary_expenses +
        meals_deduction +
        home_office_deduction +
        vehicle_deduction
    )
    
    # Net profit or loss
    net_profit_or_loss = total_income - total_expenses
    
    return ScheduleCResult(
        gross_income=round(gross_income, 2),
        returns_and_allowances=round(returns, 2),
        net_gross_income=round(net_gross, 2),
        cost_of_goods_sold=round(cogs, 2),
        gross_profit=round(gross_profit, 2),
        other_income=round(other_income, 2),
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        home_office_deduction=round(home_office_deduction, 2),
        vehicle_deduction=round(vehicle_deduction, 2),
        meals_deduction_adjustment=round(meals_adjustment, 2),
        net_profit_or_loss=round(net_profit_or_loss, 2),
        flows_to_schedule_se=(net_profit_or_loss > 0),
        expense_breakdown={
            "ordinary_expenses": round(ordinary_expenses, 2),
            "meals_50_percent_limit": round(meals_deduction, 2),
            "home_office": round(home_office_deduction, 2),
            "vehicle": round(vehicle_deduction, 2),
        },
    )


def get_schedule_c_overview() -> dict:
    """Return Schedule C statutory authority and calculation rules"""
    return {
        "title": "Schedule C (Form 1040) - Profit or Loss From Business",
        "statutory_authority": [
            "IRC §162 - Trade or business expenses",
            "IRC §280A(c) - Home office deduction",
            "IRC §274(n) - Meals and entertainment limitation (50%)",
            "IRC §274(d) - Vehicle substantiation requirements",
            "IRC §179 - Section 179 expense deduction",
        ],
        "home_office_methods": {
            "simplified": {
                "rate": f"${SIMPLIFIED_HOME_OFFICE_RATE}/sqft",
                "max_sqft": SIMPLIFIED_HOME_OFFICE_MAX_SQFT,
                "max_deduction": f"${SIMPLIFIED_HOME_OFFICE_MAX_DEDUCTION}",
                "requirements": ["Regular and exclusive business use"],
            },
            "actual": {
                "method": "Allocate home expenses by business-use percentage",
                "limitation": "Cannot exceed gross income from business use of home",
                "requirements": ["Regular and exclusive business use", "Principal place of business"],
            },
        },
        "vehicle_deduction_methods": {
            "standard_mileage": {
                "rate_2024": f"${STANDARD_MILEAGE_RATE_2024}/mile",
                "plus": "Parking and tolls 100% deductible",
                "requirements": ["Adequate mileage log (IRC §274(d))"],
            },
            "actual_expenses": {
                "method": "Total vehicle expenses × business-use percentage",
                "plus": "Parking and tolls 100% deductible",
                "listed_property": f">50% business use required for depreciation",
                "requirements": ["Adequate mileage log and expense records"],
            },
        },
        "meals_limitation": {
            "deductible_percentage": f"{MEALS_DEDUCTION_PERCENTAGE * 100}%",
            "authority": "IRC §274(n)",
            "note": "Entertainment expenses are generally NOT deductible (TCJA 2017)",
        },
        "flows_to": {
            "schedule_se": "Net profit flows to Schedule SE for self-employment tax",
            "form_1040_line_3": "Net profit or loss appears on Form 1040 Schedule 1 Line 3",
        },
    }
