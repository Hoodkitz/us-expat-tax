"""
Form 8854 Expatriation Tax Module
Handles covered expatriate tests, exit tax calculations, and penalties.
"""
from datetime import datetime
from typing import Optional


# 2025 IRS thresholds
NET_WORTH_THRESHOLD = 2_000_000
TAX_LIABILITY_THRESHOLD_2025 = 206_000
MARK_TO_MARKET_EXEMPTION_2025 = 866_000
FAILURE_TO_FILE_PENALTY = 10_000
LONG_TERM_RESIDENT_YEARS = 8
LONG_TERM_RESIDENT_LOOKBACK = 15


class FilingRequirementTest:
    """Test if individual is a covered expatriate."""
    
    @staticmethod
    def net_worth_test(net_worth: float) -> bool:
        """Test if net worth exceeds $2M threshold."""
        return net_worth > NET_WORTH_THRESHOLD
    
    @staticmethod
    def tax_liability_test(five_year_avg_tax: float, year: int = 2025) -> bool:
        """Test if 5-year average tax liability exceeds threshold."""
        threshold = TAX_LIABILITY_THRESHOLD_2025
        return five_year_avg_tax > threshold
    
    @staticmethod
    def long_term_resident_test(
        years_of_residence: int,
        lookback_period: int = LONG_TERM_RESIDENT_LOOKBACK
    ) -> bool:
        """Test if individual was long-term resident (>=8 of last 15 years)."""
        return years_of_residence >= LONG_TERM_RESIDENT_YEARS
    
    @staticmethod
    def is_covered_expatriate(
        net_worth: float,
        five_year_avg_tax: float,
        years_of_residence: int,
        year: int = 2025
    ) -> dict:
        """
        Determine if individual is a covered expatriate.
        
        Returns:
            dict with test results and covered_expatriate status
        """
        net_worth_exceeds = FilingRequirementTest.net_worth_test(net_worth)
        tax_liability_exceeds = FilingRequirementTest.tax_liability_test(
            five_year_avg_tax, year
        )
        is_long_term = FilingRequirementTest.long_term_resident_test(years_of_residence)
        
        # Covered expatriate if ANY test is true
        is_covered = net_worth_exceeds or tax_liability_exceeds
        
        return {
            "covered_expatriate": is_covered,
            "net_worth_test": {
                "exceeds_threshold": net_worth_exceeds,
                "net_worth": net_worth,
                "threshold": NET_WORTH_THRESHOLD,
            },
            "tax_liability_test": {
                "exceeds_threshold": tax_liability_exceeds,
                "five_year_avg_tax": five_year_avg_tax,
                "threshold": TAX_LIABILITY_THRESHOLD_2025,
            },
            "long_term_resident_test": {
                "is_long_term_resident": is_long_term,
                "years_of_residence": years_of_residence,
                "required_years": LONG_TERM_RESIDENT_YEARS,
            },
        }


class ExitTaxCalculator:
    """Calculate exit tax under mark-to-market regime."""
    
    @staticmethod
    def calculate_mark_to_market_gain(
        fair_market_value: float,
        adjusted_basis: float
    ) -> float:
        """Calculate unrealized gain for mark-to-market assets."""
        return max(0, fair_market_value - adjusted_basis)
    
    @staticmethod
    def apply_exemption(gain: float, year: int = 2025) -> dict:
        """
        Apply mark-to-market exemption.
        
        Returns:
            dict with taxable_gain and exemption_used
        """
        exemption = MARK_TO_MARKET_EXEMPTION_2025
        exemption_used = min(gain, exemption)
        taxable_gain = max(0, gain - exemption)
        
        return {
            "total_gain": gain,
            "exemption_amount": exemption,
            "exemption_used": exemption_used,
            "taxable_gain": taxable_gain,
        }
    
    @staticmethod
    def calculate_exit_tax(
        fair_market_value: float,
        adjusted_basis: float,
        capital_gains_rate: float = 0.20,
        year: int = 2025
    ) -> dict:
        """
        Calculate total exit tax liability.
        
        Args:
            fair_market_value: FMV of assets on expatriation date
            adjusted_basis: Tax basis of assets
            capital_gains_rate: Long-term capital gains rate (default 20%)
            year: Tax year (default 2025)
        
        Returns:
            dict with detailed exit tax calculation
        """
        gain = ExitTaxCalculator.calculate_mark_to_market_gain(
            fair_market_value, adjusted_basis
        )
        
        exemption_result = ExitTaxCalculator.apply_exemption(gain, year)
        
        exit_tax = exemption_result["taxable_gain"] * capital_gains_rate
        
        return {
            "fair_market_value": fair_market_value,
            "adjusted_basis": adjusted_basis,
            "unrealized_gain": gain,
            "exemption": exemption_result["exemption_amount"],
            "exemption_used": exemption_result["exemption_used"],
            "taxable_gain": exemption_result["taxable_gain"],
            "capital_gains_rate": capital_gains_rate,
            "exit_tax": exit_tax,
        }


class PenaltyCalculator:
    """Calculate penalties for Form 8854 non-compliance."""
    
    @staticmethod
    def failure_to_file_penalty(
        months_late: int,
        penalty_per_occurrence: int = FAILURE_TO_FILE_PENALTY
    ) -> dict:
        """
        Calculate failure-to-file penalty.
        
        Base penalty is $10,000 per occurrence.
        
        Args:
            months_late: Number of months the filing is late
            penalty_per_occurrence: Base penalty amount
        
        Returns:
            dict with penalty calculation
        """
        # One penalty per occurrence
        penalty = penalty_per_occurrence
        
        return {
            "months_late": months_late,
            "penalty_per_occurrence": penalty_per_occurrence,
            "total_penalty": penalty,
            "description": f"Failure to file Form 8854: ${penalty:,}",
        }
    
    @staticmethod
    def estimate_total_penalties(
        failed_to_file: bool,
        months_late: int = 0,
    ) -> dict:
        """
        Estimate total penalties for Form 8854 non-compliance.
        
        Returns:
            dict with total penalty estimate
        """
        penalties = []
        total = 0
        
        if failed_to_file and months_late > 0:
            failure_penalty = PenaltyCalculator.failure_to_file_penalty(months_late)
            penalties.append(failure_penalty)
            total += failure_penalty["total_penalty"]
        
        return {
            "total_penalties": total,
            "penalties": penalties,
        }


def get_form8854_overview() -> dict:
    """Get overview of Form 8854 requirements and thresholds."""
    return {
        "form_name": "Form 8854",
        "description": "Initial and Annual Expatriation Statement",
        "purpose": "Report expatriation from U.S. citizenship or long-term residency",
        "covered_expatriate_tests": {
            "net_worth_threshold": NET_WORTH_THRESHOLD,
            "tax_liability_threshold_2025": TAX_LIABILITY_THRESHOLD_2025,
            "long_term_resident_requirement": f"{LONG_TERM_RESIDENT_YEARS} of last {LONG_TERM_RESIDENT_LOOKBACK} years",
        },
        "exit_tax": {
            "mark_to_market_exemption_2025": MARK_TO_MARKET_EXEMPTION_2025,
            "typical_capital_gains_rate": 0.20,
        },
        "penalties": {
            "failure_to_file": FAILURE_TO_FILE_PENALTY,
        },
        "filing_requirement": "Must file if you expatriated during the tax year",
        "due_date": "Due with income tax return for year of expatriation",
    }
