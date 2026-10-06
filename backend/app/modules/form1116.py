"""
Form 1116 Foreign Tax Credit (FTC) module.

Implements the FTC limitation formula per IRC §904:
  FTC Limitation = US Tax Before Credit × (Foreign Income / Total Income)
  Allowable FTC  = min(Foreign Taxes Paid, FTC Limitation)
  Excess Credit  = max(0, Foreign Taxes Paid − FTC Limitation)

Carryover rules: 1-year carryback, 10-year carryforward.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Income category type
# ---------------------------------------------------------------------------

IncomeCategoryLiteral = Literal[
    "general",
    "passive",
    "section901j",
    "certain_income_re_sanctioned_countries",
]

INCOME_CATEGORY_EXPLANATIONS: dict[str, str] = {
    "general": (
        "General category income (basket): wages, salaries, and most active business "
        "income earned abroad. Most US expats fall into this category."
    ),
    "passive": (
        "Passive category income: dividends, interest, rents, royalties, and capital "
        "gains not attributable to an active trade or business."
    ),
    "section901j": (
        "Section 901(j) income: income from countries designated as state sponsors of "
        "terrorism (e.g., Cuba, Iran, North Korea, Syria). FTC is generally disallowed."
    ),
    "certain_income_re_sanctioned_countries": (
        "Income subject to sanctions-related restrictions. Special rules apply; "
        "consult a qualified tax professional before claiming this credit."
    ),
}

CARRYFORWARD_YEARS = 10
CARRYBACK_YEARS = 1

# ---------------------------------------------------------------------------
# FEIE limits (approximate) for comparison calculations
# ---------------------------------------------------------------------------

FEIE_LIMITS: dict[int, float] = {
    2020: 107_600.0,
    2021: 108_700.0,
    2022: 112_000.0,
    2023: 120_000.0,
    2024: 126_500.0,
    2025: 130_000.0,
}

# Approximate single-filer marginal tax rates for FEIE vs FTC comparison
# Using simplified 2024 tax brackets
_BRACKETS_2024 = [
    (11_600.0, 0.10),
    (47_150.0, 0.12),
    (100_525.0, 0.22),
    (191_950.0, 0.24),
    (243_725.0, 0.32),
    (609_350.0, 0.35),
    (float("inf"), 0.37),
]


def _estimate_us_tax(income: float, tax_year: int) -> float:
    """
    Simplified US federal income tax estimate (single filer, standard deduction).
    Used ONLY for the FEIE-vs-FTC comparison endpoint.
    """
    # Standard deduction approximation
    standard_deduction = 14_600.0 + max(0, (tax_year - 2024)) * 400
    taxable = max(0.0, income - standard_deduction)

    brackets = _BRACKETS_2024  # simplified – same brackets for all years in range
    tax = 0.0
    prev_limit = 0.0
    for limit, rate in brackets:
        if taxable <= prev_limit:
            break
        chunk = min(taxable, limit) - prev_limit
        tax += chunk * rate
        prev_limit = limit
    return round(tax, 2)


# ---------------------------------------------------------------------------
# FTC calculation models
# ---------------------------------------------------------------------------

class FTCInput(BaseModel):
    foreign_taxes_paid: float = Field(..., ge=0)
    foreign_income: float = Field(..., ge=0)
    total_income: float = Field(..., gt=0)
    us_tax_before_credit: float = Field(..., ge=0)
    income_category: IncomeCategoryLiteral = "general"
    tax_year: int = Field(..., ge=2000, le=2099)


class FTCResult(BaseModel):
    ftc_limitation: float
    allowable_ftc: float
    excess_credit: float
    us_tax_after_credit: float
    effective_rate: float
    carryforward_years: int
    carryback_years: int
    recommendation: str
    income_category_explanation: str


def calculate_ftc(inp: FTCInput) -> FTCResult:
    """
    Core FTC limitation formula (IRC §904(a)):
      ftc_limitation = us_tax_before_credit × (foreign_income / total_income)
      allowable_ftc  = min(foreign_taxes_paid, ftc_limitation)
      excess_credit  = max(0, foreign_taxes_paid - ftc_limitation)
    """
    ratio = min(inp.foreign_income / inp.total_income, 1.0)
    ftc_limitation = round(inp.us_tax_before_credit * ratio, 2)
    allowable_ftc = round(min(inp.foreign_taxes_paid, ftc_limitation), 2)
    excess_credit = round(max(0.0, inp.foreign_taxes_paid - ftc_limitation), 2)
    us_tax_after_credit = round(max(0.0, inp.us_tax_before_credit - allowable_ftc), 2)
    effective_rate = (
        round(us_tax_after_credit / inp.total_income * 100, 4)
        if inp.total_income > 0
        else 0.0
    )

    # Build recommendation
    if inp.income_category == "section901j":
        recommendation = (
            "⚠️  Section 901(j) income: FTC is generally disallowed for taxes paid to "
            "designated state-sponsors of terrorism. Consider alternative strategies."
        )
    elif allowable_ftc >= inp.us_tax_before_credit:
        recommendation = (
            "✅ Your FTC fully eliminates your US tax liability. "
            "No additional US tax owed on this income."
        )
    elif excess_credit > 0:
        recommendation = (
            f"📋 You have ${excess_credit:,.2f} in excess credits. "
            f"You may carry them back {CARRYBACK_YEARS} year or forward {CARRYFORWARD_YEARS} years "
            "to offset future US tax on foreign-source income."
        )
    else:
        recommendation = (
            f"✅ FTC reduces your US tax from ${inp.us_tax_before_credit:,.2f} to "
            f"${us_tax_after_credit:,.2f}. Consider also reviewing FEIE eligibility."
        )

    return FTCResult(
        ftc_limitation=ftc_limitation,
        allowable_ftc=allowable_ftc,
        excess_credit=excess_credit,
        us_tax_after_credit=us_tax_after_credit,
        effective_rate=effective_rate,
        carryforward_years=CARRYFORWARD_YEARS,
        carryback_years=CARRYBACK_YEARS,
        recommendation=recommendation,
        income_category_explanation=INCOME_CATEGORY_EXPLANATIONS[inp.income_category],
    )


# ---------------------------------------------------------------------------
# FEIE vs FTC comparison
# ---------------------------------------------------------------------------

class FeieVsFtcInput(BaseModel):
    foreign_income: float = Field(..., ge=0)
    foreign_taxes_paid: float = Field(..., ge=0)
    total_us_income: float = Field(..., gt=0)
    tax_year: int = Field(..., ge=2000, le=2099)


class StrategyResult(BaseModel):
    strategy: str
    excluded_or_credited: float
    us_tax_owed: float
    net_tax_saving: float
    description: str


class FeieVsFtcResult(BaseModel):
    feie: StrategyResult
    ftc: StrategyResult
    recommended_strategy: str
    recommendation_detail: str


def compare_feie_vs_ftc(inp: FeieVsFtcInput) -> FeieVsFtcResult:
    """
    Estimates US tax under FEIE vs FTC and recommends the better option.

    FEIE: excludes foreign earned income up to the annual limit, then applies
    stacking rules (income is taxed at the marginal rate as if exclusion income
    were at the bottom of the bracket — simplified here as a flat reduction).

    FTC: computes the §904 limitation and allows credit for foreign taxes paid.
    """
    feie_limit = FEIE_LIMITS.get(inp.tax_year, 126_500.0)
    feie_exclusion = min(inp.foreign_income, feie_limit)

    # FEIE path: taxable income = total - excluded foreign income
    feie_taxable = max(0.0, inp.total_us_income - feie_exclusion)
    feie_us_tax = _estimate_us_tax(feie_taxable, inp.tax_year)
    feie_baseline_tax = _estimate_us_tax(inp.total_us_income, inp.tax_year)

    # FTC path: compute full US tax, then apply FTC limitation
    ftc_us_tax_before = _estimate_us_tax(inp.total_us_income, inp.tax_year)
    ratio = min(inp.foreign_income / inp.total_us_income, 1.0)
    ftc_limitation = round(ftc_us_tax_before * ratio, 2)
    allowable_ftc = round(min(inp.foreign_taxes_paid, ftc_limitation), 2)
    ftc_us_tax_after = round(max(0.0, ftc_us_tax_before - allowable_ftc), 2)

    feie_saving = round(feie_baseline_tax - feie_us_tax, 2)
    ftc_saving = round(feie_baseline_tax - ftc_us_tax_after, 2)

    feie_strategy = StrategyResult(
        strategy="FEIE (Form 2555)",
        excluded_or_credited=feie_exclusion,
        us_tax_owed=feie_us_tax,
        net_tax_saving=feie_saving,
        description=(
            f"Excludes ${feie_exclusion:,.2f} of foreign earned income "
            f"(limit: ${feie_limit:,.2f} for {inp.tax_year}). "
            f"Results in US tax of ${feie_us_tax:,.2f}."
        ),
    )

    ftc_strategy = StrategyResult(
        strategy="FTC (Form 1116)",
        excluded_or_credited=allowable_ftc,
        us_tax_owed=ftc_us_tax_after,
        net_tax_saving=ftc_saving,
        description=(
            f"Credits ${allowable_ftc:,.2f} of ${inp.foreign_taxes_paid:,.2f} foreign "
            f"taxes paid (limitation: ${ftc_limitation:,.2f}). "
            f"Results in US tax of ${ftc_us_tax_after:,.2f}."
        ),
    )

    if feie_us_tax <= ftc_us_tax_after:
        recommended = "FEIE (Form 2555)"
        detail = (
            f"FEIE saves ${feie_saving - ftc_saving:,.2f} more than FTC for your scenario. "
            "FEIE is typically better when foreign taxes are low relative to income."
        )
    else:
        recommended = "FTC (Form 1116)"
        detail = (
            f"FTC saves ${ftc_saving - feie_saving:,.2f} more than FEIE for your scenario. "
            "FTC is typically better when you pay high foreign taxes (foreign rate > US rate)."
        )

    return FeieVsFtcResult(
        feie=feie_strategy,
        ftc=ftc_strategy,
        recommended_strategy=recommended,
        recommendation_detail=detail,
    )


# ---------------------------------------------------------------------------
# Carryover persistence (JSON file-based, tenant-isolated)
# ---------------------------------------------------------------------------

_DEFAULT_CARRYOVER_FILE = Path(__file__).parent.parent.parent / "data" / "ftc_carryovers.json"


def _get_carryover_file() -> Path:
    return _DEFAULT_CARRYOVER_FILE


def _load_carryovers(data_file: Path | None = None) -> dict[str, list]:
    path = data_file or _get_carryover_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return {"entries": []}
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if "entries" not in raw:
        raw["entries"] = []
    return raw


def _save_carryovers(data: dict[str, list], data_file: Path | None = None) -> None:
    path = data_file or _get_carryover_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def save_carryover(
    tenant_id: str,
    tax_year: int,
    excess_credit: float,
    income_category: str,
    *,
    data_file: Path | None = None,
) -> dict[str, Any]:
    """
    Persist an FTC carryover record for a tenant. Returns the saved record.
    """
    data = _load_carryovers(data_file)
    record_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    # Expiry: carryforward expires 10 years after the tax year
    expires_tax_year = tax_year + CARRYFORWARD_YEARS
    carryback_tax_year = tax_year - CARRYBACK_YEARS

    entry: dict[str, Any] = {
        "id": record_id,
        "tenant_id": tenant_id,
        "tax_year": tax_year,
        "excess_credit": excess_credit,
        "income_category": income_category,
        "created_at": created_at,
        "carryforward_expires_after_tax_year": expires_tax_year,
        "carryback_available_for_tax_year": carryback_tax_year,
    }
    data["entries"].append(entry)
    _save_carryovers(data, data_file)
    return entry


def get_carryovers(
    tenant_id: str,
    *,
    data_file: Path | None = None,
) -> list[dict[str, Any]]:
    """Returns all carryover records for a tenant, newest first."""
    data = _load_carryovers(data_file)
    entries = [e for e in data["entries"] if e["tenant_id"] == tenant_id]
    return sorted(entries, key=lambda e: e.get("created_at", ""), reverse=True)
