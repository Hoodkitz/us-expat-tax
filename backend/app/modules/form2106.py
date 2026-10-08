"""
Form 2106 — Employee Business Expenses.

Business logic for Form 2106 calculations under IRC §62.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form2106Input:
    """Input for Form 2106 calculation."""
    employee_expenses: Decimal
    travel_expenses: Decimal
    meal_expenses: Decimal
    vehicle_expenses: Decimal
    agi: Decimal
    tax_year: int = 2025


@dataclass
class Form2106Result:
    """Result of Form 2106 calculation."""
    total_expenses: Decimal
    deductible_meals: Decimal
    deductible_expenses: Decimal
    agi_floor: Decimal
    net_deduction: Decimal
    explanation: str


def calculate_form2106(inp: Form2106Input) -> Form2106Result:
    """Calculate Form 2106 employee business expenses."""
    # 2% AGI floor suspended 2018-2025 under TCJA
    agi_floor = Decimal("0")
    
    # Meals deductible at 50%
    deductible_meals = (inp.meal_expenses * Decimal("0.5")).quantize(Decimal("0.01"))
    
    # Total deductible expenses
    deductible_expenses = (
        inp.employee_expenses + inp.travel_expenses + 
        deductible_meals + inp.vehicle_expenses
    )
    
    net_deduction = max(deductible_expenses - agi_floor, Decimal("0"))
    
    explanation = (
        f"Employee business expenses: ${deductible_expenses:,.2f} "
        f"(Meals at 50%: ${deductible_meals:,.2f})"
    )
    
    return Form2106Result(
        total_expenses=inp.employee_expenses + inp.travel_expenses + inp.meal_expenses + inp.vehicle_expenses,
        deductible_meals=deductible_meals,
        deductible_expenses=deductible_expenses,
        agi_floor=agi_floor,
        net_deduction=net_deduction,
        explanation=explanation,
    )


def get_form2106_overview() -> dict:
    """Returns a structured explanation of Form 2106."""
    return {
        "form": "Form 2106",
        "title": "Employee Business Expenses",
        "purpose": "Form 2106 is used by employees to deduct unreimbursed business expenses incurred in the performance of their job.",
        "who_must_file": [
            "Employees with unreimbursed business expenses",
            "Armed forces reservists",
            "Qualified performing artists",
            "Fee-basis state or local government officials",
        ],
        "key_rules": [
            "Subject to 2% of AGI floor (suspended 2018-2025 under TCJA)",
            "Meals deductible at 50%",
            "Travel expenses must be away from home overnight",
            "Vehicle expenses can use standard mileage rate (70¢/mile for 2025)",
        ],
        "statutory_references": ["IRC §62", "IRC §162", "IRC §274"],
        "related_forms": ["Schedule A", "Form 1040"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-2106",
    }
