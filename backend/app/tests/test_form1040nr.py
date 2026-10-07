"""
Tests for Form 1040-NR Non-Resident Alien Tax Return
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.models.form1040nr import (
    ResidentStatus,
    IncomeType,
    WithholdingType,
    IncomeItem,
)

client = TestClient(app)


# Mock authentication
@pytest.fixture
def mock_auth_headers():
    return {"Authorization": "Bearer mock_token"}


class TestSubstantialPresenceTest:
    """Test Substantial Presence Test calculations"""
    
    def test_spt_passes_current_year_only(self, mock_auth_headers):
        """Test SPT passes with 183+ days in current year"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 200,
                "days_in_us_prior_year_1": 0,
                "days_in_us_prior_year_2": 0,
                "has_us_sourced_income": False,
                "gross_income": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["substantial_presence_days"] == "200.00"
        assert data["passes_substantial_presence_test"] is True
        assert data["resident_status"] == "resident"
    
    def test_spt_passes_with_prior_years(self, mock_auth_headers):
        """Test SPT passes with weighted prior year days"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 120,
                "days_in_us_prior_year_1": 120,  # 120/3 = 40
                "days_in_us_prior_year_2": 150,  # 150/6 = 25
                "has_us_sourced_income": False,
                "gross_income": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # 120 + 40 + 25 = 185
        assert float(data["substantial_presence_days"]) >= 183
        assert data["passes_substantial_presence_test"] is True
    
    def test_spt_fails_insufficient_days(self, mock_auth_headers):
        """Test SPT fails with insufficient days"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 100,
                "days_in_us_prior_year_1": 100,
                "days_in_us_prior_year_2": 100,
                "has_us_sourced_income": False,
                "gross_income": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # 100 + 33.33 + 16.67 = 150
        assert float(data["substantial_presence_days"]) < 183
        assert data["passes_substantial_presence_test"] is False
        assert data["resident_status"] == "non_resident"
    
    def test_dual_status_year(self, mock_auth_headers):
        """Test dual-status year determination"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 150,
                "days_in_us_prior_year_1": 0,
                "days_in_us_prior_year_2": 0,
                "has_us_sourced_income": True,
                "gross_income": 50000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_status"] == "dual_status"
        assert data["passes_substantial_presence_test"] is False


class TestTreatyTiebreaker:
    """Test treaty tiebreaker rules"""
    
    def test_treaty_resident_tiebreaker(self, mock_auth_headers):
        """Test treaty tiebreaker for closer connection"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 200,
                "treaty_country": "Germany",
                "has_us_sourced_income": True,
                "gross_income": 75000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_status"] == "treaty_resident"
        assert data["treaty_exemption_applies"] is True
        assert data["passes_substantial_presence_test"] is True
    
    def test_student_treaty_exemption(self, mock_auth_headers):
        """Test student exemption under treaty"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 200,
                "treaty_country": "India",
                "is_student": True,
                "has_us_sourced_income": True,
                "gross_income": 25000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "Student from treaty country" in data["reasoning"]
    
    def test_teacher_treaty_exemption(self, mock_auth_headers):
        """Test teacher exemption under treaty"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 180,
                "treaty_country": "China",
                "is_teacher": True,
                "has_us_sourced_income": True,
                "gross_income": 50000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "Teacher from treaty country" in data["reasoning"]


class TestWithholdingChapter3And4:
    """Test Chapter 3 and Chapter 4 withholding"""
    
    def test_chapter_3_withholding_credit(self, mock_auth_headers):
        """Test Chapter 3 (30%) withholding credit"""
        response = client.post(
            "/api/v1/form1040nr/withholding-credit",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "chapter_3_withheld": 15000,
                "chapter_4_withheld": 0,
                "backup_withheld": 0,
                "estimated_tax_paid": 5000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_chapter_3_credit"] == "15000"
        assert data["total_credits"] == "20000"
        assert data["refundable_amount"] == "20000"
    
    def test_chapter_4_fatca_withholding(self, mock_auth_headers):
        """Test Chapter 4 (FATCA) withholding credit"""
        response = client.post(
            "/api/v1/form1040nr/withholding-credit",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "chapter_3_withheld": 0,
                "chapter_4_withheld": 8000,
                "backup_withheld": 1200,
                "estimated_tax_paid": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_chapter_4_credit"] == "8000"
        assert data["total_backup_credit"] == "1200"
        assert data["total_credits"] == "9200"
    
    def test_combined_withholding_credits(self, mock_auth_headers):
        """Test combined withholding credits"""
        response = client.post(
            "/api/v1/form1040nr/withholding-credit",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "chapter_3_withheld": 10000,
                "chapter_4_withheld": 5000,
                "backup_withheld": 2000,
                "estimated_tax_paid": 8000,
                "prior_year_overpayment": 1500,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_credits"] == "26500"
        assert data["total_estimated_tax"] == "9500"


class TestFDAPvsECI:
    """Test FDAP vs ECI income classification and taxation"""
    
    def test_fdap_income_30_percent_tax(self, mock_auth_headers):
        """Test FDAP income taxed at flat 30%"""
        response = client.post(
            "/api/v1/form1040nr/income-summary",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "income_items": [
                    {
                        "description": "Dividends",
                        "income_type": "fdap",
                        "gross_amount": 50000,
                        "us_sourced": True,
                        "treaty_exempt": False,
                    }
                ],
                "standard_deduction_claimed": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_fdap"] == "50000"
        assert data["taxable_fdap"] == "50000"
        # FDAP tax = 50000 * 0.30 = 15000
        assert float(data["total_tax_before_credits"]) == 15000
    
    def test_eci_progressive_taxation(self, mock_auth_headers):
        """Test ECI income taxed at progressive rates"""
        response = client.post(
            "/api/v1/form1040nr/income-summary",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "income_items": [
                    {
                        "description": "Wages",
                        "income_type": "eci",
                        "gross_amount": 60000,
                        "us_sourced": True,
                        "treaty_exempt": False,
                    }
                ],
                "standard_deduction_claimed": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_eci"] == "60000"
        # After standard deduction: 60000 - 14600 = 45400
        assert data["taxable_eci"] == "45400.00"
        # Progressive tax on 45400
        assert float(data["total_tax_before_credits"]) > 0
        assert float(data["total_tax_before_credits"]) < 10000
    
    def test_mixed_eci_and_fdap(self, mock_auth_headers):
        """Test mixed ECI and FDAP income"""
        response = client.post(
            "/api/v1/form1040nr/income-summary",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "income_items": [
                    {
                        "description": "Wages",
                        "income_type": "eci",
                        "gross_amount": 50000,
                        "us_sourced": True,
                        "treaty_exempt": False,
                    },
                    {
                        "description": "Interest",
                        "income_type": "fdap",
                        "gross_amount": 20000,
                        "us_sourced": True,
                        "treaty_exempt": False,
                    },
                ],
                "standard_deduction_claimed": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_eci"] == "50000"
        assert data["total_fdap"] == "20000"
        assert data["total_us_sourced"] == "70000"
    
    def test_treaty_exempt_income(self, mock_auth_headers):
        """Test treaty-exempt income exclusion"""
        response = client.post(
            "/api/v1/form1040nr/income-summary",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "income_items": [
                    {
                        "description": "Scholarship",
                        "income_type": "fdap",
                        "gross_amount": 15000,
                        "us_sourced": True,
                        "treaty_exempt": True,
                        "treaty_article": "Article 20",
                    },
                    {
                        "description": "Wages",
                        "income_type": "eci",
                        "gross_amount": 40000,
                        "us_sourced": True,
                        "treaty_exempt": False,
                    },
                ],
                "standard_deduction_claimed": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_treaty_exempt"] == "15000"
        assert data["total_eci"] == "40000"
        assert data["total_fdap"] == "0"  # Treaty-exempt FDAP not counted


class TestPenaltyCalculation:
    """Test §6072 late filing penalty calculations"""
    
    def test_no_penalty_on_time_filing(self, mock_auth_headers):
        """Test no penalty when filed on time"""
        filing_deadline = date(2025, 6, 15)
        response = client.post(
            "/api/v1/form1040nr/penalty-calculator",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "filing_deadline": filing_deadline.isoformat(),
                "actual_filing_date": filing_deadline.isoformat(),
                "tax_owed": 5000,
                "was_extension_filed": False,
                "reasonable_cause": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["days_late"] == 0
        assert data["total_penalties"] == "0.00"
    
    def test_late_filing_penalty_5_percent_per_month(self, mock_auth_headers):
        """Test 5% per month late filing penalty"""
        filing_deadline = date(2025, 6, 15)
        actual_date = filing_deadline + timedelta(days=60)  # 2 months late
        response = client.post(
            "/api/v1/form1040nr/penalty-calculator",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "filing_deadline": filing_deadline.isoformat(),
                "actual_filing_date": actual_date.isoformat(),
                "tax_owed": 10000,
                "was_extension_filed": False,
                "reasonable_cause": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["days_late"] == 60
        # 2 months * 5% = 10% of 10000 = 1000
        assert float(data["late_filing_penalty"]) >= 1000
    
    def test_late_payment_penalty_half_percent_per_month(self, mock_auth_headers):
        """Test 0.5% per month late payment penalty"""
        filing_deadline = date(2025, 6, 15)
        actual_date = filing_deadline + timedelta(days=30)  # 1 month late
        response = client.post(
            "/api/v1/form1040nr/penalty-calculator",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "filing_deadline": filing_deadline.isoformat(),
                "actual_filing_date": actual_date.isoformat(),
                "tax_owed": 10000,
                "was_extension_filed": False,
                "reasonable_cause": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Late payment penalty: 1 month * 0.5% = 0.5% of 10000 = 50
        assert float(data["late_payment_penalty"]) >= 50
    
    def test_minimum_penalty_200_dollars(self, mock_auth_headers):
        """Test minimum penalty of $200"""
        filing_deadline = date(2025, 6, 15)
        actual_date = filing_deadline + timedelta(days=90)  # 3 months late
        response = client.post(
            "/api/v1/form1040nr/penalty-calculator",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "filing_deadline": filing_deadline.isoformat(),
                "actual_filing_date": actual_date.isoformat(),
                "tax_owed": 100,  # Small tax owed
                "was_extension_filed": False,
                "reasonable_cause": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_penalty_applies"] is True
        assert float(data["late_filing_penalty"]) >= 100  # Min is lesser of 200 or tax
    
    def test_interest_charges(self, mock_auth_headers):
        """Test interest charges on late payment"""
        filing_deadline = date(2025, 6, 15)
        actual_date = filing_deadline + timedelta(days=365)  # 1 year late
        response = client.post(
            "/api/v1/form1040nr/penalty-calculator",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "filing_deadline": filing_deadline.isoformat(),
                "actual_filing_date": actual_date.isoformat(),
                "tax_owed": 10000,
                "was_extension_filed": False,
                "reasonable_cause": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Interest: 8% annual on 10000 = 800
        assert float(data["interest_charges"]) >= 750
        assert float(data["interest_charges"]) <= 850
    
    def test_reasonable_cause_waiver(self, mock_auth_headers):
        """Test reasonable cause penalty waiver"""
        filing_deadline = date(2025, 6, 15)
        actual_date = filing_deadline + timedelta(days=60)
        response = client.post(
            "/api/v1/form1040nr/penalty-calculator",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "filing_deadline": filing_deadline.isoformat(),
                "actual_filing_date": actual_date.isoformat(),
                "tax_owed": 10000,
                "was_extension_filed": False,
                "reasonable_cause": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["waived_due_to_reasonable_cause"] is True
        # Only interest remains (not waived)
        assert data["late_filing_penalty"] == "0.00"
        assert data["late_payment_penalty"] == "0.00"
        assert float(data["interest_charges"]) > 0
    
    def test_extension_filing(self, mock_auth_headers):
        """Test extension adjusts deadline"""
        filing_deadline = date(2025, 6, 15)
        # File 100 days after deadline, but extension was filed
        actual_date = filing_deadline + timedelta(days=100)
        response = client.post(
            "/api/v1/form1040nr/penalty-calculator",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "filing_deadline": filing_deadline.isoformat(),
                "actual_filing_date": actual_date.isoformat(),
                "tax_owed": 5000,
                "was_extension_filed": True,
                "reasonable_cause": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Extension gives 120 days, so 100 days is within extension
        assert data["days_late"] == 0
        assert data["total_penalties"] == "0.00"


class TestFilingDeadlines:
    """Test filing deadline determination"""
    
    def test_non_resident_june_15_deadline(self, mock_auth_headers):
        """Test non-resident deadline is June 15"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 100,
                "has_us_sourced_income": True,
                "gross_income": 20000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filing_deadline"] == "2025-06-15"
        assert data["extension_deadline"] == "2025-10-15"
    
    def test_dual_status_april_15_deadline(self, mock_auth_headers):
        """Test dual-status deadline is April 15"""
        response = client.post(
            "/api/v1/form1040nr/filing-requirement",
            headers=mock_auth_headers,
            json={
                "tax_year": 2024,
                "days_in_us_current_year": 150,
                "has_us_sourced_income": True,
                "gross_income": 50000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_status"] == "dual_status"
        assert data["filing_deadline"] == "2025-04-15"


class TestOverview:
    """Test overview endpoint"""
    
    def test_overview_returns_structure(self, mock_auth_headers):
        """Test overview returns proper structure"""
        response = client.get(
            "/api/v1/form1040nr/overview?tax_year=2024",
            headers=mock_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tax_year"] == 2024
        assert "created_at" in data
        assert "updated_at" in data
