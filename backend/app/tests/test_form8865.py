"""
Tests for Form 8865 module (Foreign Partnerships).

Covers:
- Filing requirement checks (Categories 1-5)
- Income summary (Subpart F, GILTI, QBI)
- Penalty calculations
- Edge cases and boundary conditions
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.form8865 import (
    FilingRequirementInput,
    PartnershipInput,
    IncomeSummaryInput,
    PenaltyCalculationInput,
    check_filing_requirement,
    summarize_income,
    calculate_penalty,
    get_overview,
    CATEGORY_1_CONTROL_THRESHOLD,
    CATEGORY_2_OWNERSHIP_THRESHOLD,
    CATEGORY_4_CONTRIBUTION_THRESHOLD,
    PENALTY_BASE,
    PENALTY_CONTINUED_PER_30_DAYS,
    PENALTY_CONTINUED_MAX,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

REGISTER_PAYLOAD = {
    "email": "form8865-test@example.com",
    "password": "securepassword123",
    "tenant_name": "Form8865 Test Corp",
}


@pytest.fixture()
def auth_token(tmp_path, monkeypatch):
    """Register a fresh tenant and return a valid JWT."""
    import app.auth.router as auth_router_module

    monkeypatch.setattr(auth_router_module, "TENANTS_FILE", tmp_path / "tenants.json")
    monkeypatch.setattr(auth_router_module, "DATA_DIR", tmp_path)

    client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test filing requirement - Category 1 (Control >50%)
# ---------------------------------------------------------------------------

def test_filing_requirement_category_1_control():
    """Test Category 1: Control (>50% ownership)."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Alpha GmbH & Co. KG",
                country="DE",
                ownership_percentage=60.0,
                us_controlled=False,
                fair_market_value_usd=500_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    assert result.filing_required is True
    assert "Category 1: Control" in result.categories
    assert result.total_partnerships == 1
    assert result.penalty_if_not_filed == PENALTY_BASE
    assert "60.0% > 50%" in result.reasons[0]


def test_filing_requirement_category_1_exactly_50_percent():
    """Test Category 1 boundary: exactly 50% does NOT trigger Category 1."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Beta Ltd",
                country="UK",
                ownership_percentage=50.0,
                us_controlled=False,
                fair_market_value_usd=200_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    # Exactly 50% does NOT trigger Category 1 (must be >50%)
    # But triggers Category 5 (≥10%)
    assert "Category 1: Control" not in result.categories
    assert "Category 5: Ownership (≥10%)" in result.categories


# ---------------------------------------------------------------------------
# Test filing requirement - Category 2 (U.S.-controlled partnership)
# ---------------------------------------------------------------------------

def test_filing_requirement_category_2_us_controlled():
    """Test Category 2: ≥10% ownership in U.S.-controlled partnership."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Gamma SARL",
                country="FR",
                ownership_percentage=15.0,
                us_controlled=True,  # U.S. persons collectively own >50%
                fair_market_value_usd=300_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    assert result.filing_required is True
    assert "Category 2: Ownership (U.S.-controlled)" in result.categories
    assert "15.0% of U.S.-controlled partnership" in result.reasons[0]


def test_filing_requirement_category_2_not_us_controlled():
    """Test that <10% or non-U.S.-controlled does not trigger Category 2."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Delta KG",
                country="AT",
                ownership_percentage=8.0,
                us_controlled=True,
                fair_market_value_usd=100_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    # <10% does not trigger Category 2
    assert "Category 2: Ownership (U.S.-controlled)" not in result.categories
    # But also does not trigger Category 5 (also requires ≥10%)
    assert result.filing_required is False


# ---------------------------------------------------------------------------
# Test filing requirement - Category 3 (Reportable event)
# ---------------------------------------------------------------------------

def test_filing_requirement_category_3_reportable_event():
    """Test Category 3: Reportable event (acquisition/disposition/change ≥10%)."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Epsilon Ltd",
                country="IE",
                ownership_percentage=12.0,
                us_controlled=False,
                reportable_event=True,  # Acquisition/disposition/change ≥10%
                fair_market_value_usd=250_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    assert result.filing_required is True
    assert "Category 3: Reportable Event" in result.categories
    assert "acquisition/disposition/change" in result.reasons[0].lower()


def test_filing_requirement_category_3_no_event():
    """Test that reportable_event=False does not trigger Category 3."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Zeta OHG",
                country="DE",
                ownership_percentage=12.0,
                us_controlled=False,
                reportable_event=False,
                fair_market_value_usd=150_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    # No reportable event → no Category 3
    assert "Category 3: Reportable Event" not in result.categories
    # But triggers Category 5 (≥10%)
    assert "Category 5: Ownership (≥10%)" in result.categories


# ---------------------------------------------------------------------------
# Test filing requirement - Category 4 (Contribution >$100k)
# ---------------------------------------------------------------------------

def test_filing_requirement_category_4_contribution():
    """Test Category 4: Contribution >$100,000."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Theta SARL",
                country="LU",
                ownership_percentage=5.0,
                us_controlled=False,
                capital_contributed_usd=150_000.0,
                fair_market_value_usd=200_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    assert result.filing_required is True
    assert "Category 4: Contribution" in result.categories
    assert "$150,000" in result.reasons[0]


def test_filing_requirement_category_4_exactly_100k():
    """Test Category 4 boundary: exactly $100k does NOT trigger (must be >$100k)."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Iota Ltd",
                country="CH",
                ownership_percentage=3.0,
                us_controlled=False,
                capital_contributed_usd=100_000.0,  # Exactly $100k
                fair_market_value_usd=120_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    # Exactly $100k does NOT trigger Category 4 (must be >$100k)
    assert "Category 4: Contribution" not in result.categories
    # <10% ownership → no Category 5
    assert result.filing_required is False


# ---------------------------------------------------------------------------
# Test filing requirement - Category 5 (≥10% ownership)
# ---------------------------------------------------------------------------

def test_filing_requirement_category_5_ownership():
    """Test Category 5: ≥10% ownership (post-2020)."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Kappa KG",
                country="DE",
                ownership_percentage=10.0,
                us_controlled=False,
                fair_market_value_usd=80_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    assert result.filing_required is True
    assert "Category 5: Ownership (≥10%)" in result.categories
    assert "10.0% of 'Kappa KG' (≥10%)" in result.reasons[0]


def test_filing_requirement_category_5_boundary_9_percent():
    """Test Category 5 boundary: <10% does not trigger."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Lambda Ltd",
                country="NL",
                ownership_percentage=9.0,
                us_controlled=False,
                fair_market_value_usd=50_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    assert result.filing_required is False
    assert "Category 5: Ownership (≥10%)" not in result.categories


# ---------------------------------------------------------------------------
# Test filing requirement - No categories triggered
# ---------------------------------------------------------------------------

def test_filing_requirement_no_categories():
    """Test case where no categories apply."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Mu AG",
                country="CH",
                ownership_percentage=2.0,
                us_controlled=False,
                capital_contributed_usd=10_000.0,
                fair_market_value_usd=30_000.0,
            )
        ],
    )
    result = check_filing_requirement(inp)

    assert result.filing_required is False
    assert len(result.categories) == 0
    assert result.penalty_if_not_filed == 0.0
    assert "not required" in result.recommendation.lower()


# ---------------------------------------------------------------------------
# Test income summary
# ---------------------------------------------------------------------------

def test_income_summary_subpart_f_gilti():
    """Test income summary with Subpart F and GILTI."""
    inp = IncomeSummaryInput(
        tax_year=2024,
        partnership_name="Alpha Foreign LP",
        subpart_f_income_usd=30_000.0,
        gilti_usd=15_000.0,
        qbi_199a_usd=0.0,
        ordinary_income_usd=50_000.0,
        capital_gain_usd=5_000.0,
        foreign_tax_paid_usd=12_000.0,
    )
    result = summarize_income(inp)

    assert result.total_income_usd == 100_000.0
    assert result.foreign_tax_credit_eligible is True
    assert "Subpart F income: $30,000.00" in result.notes[0]
    assert "GILTI: $15,000.00" in result.notes[1]


def test_income_summary_qbi_199a():
    """Test income summary with QBI (§199A)."""
    inp = IncomeSummaryInput(
        tax_year=2024,
        partnership_name="Beta Domestic Partnership",
        subpart_f_income_usd=0.0,
        gilti_usd=0.0,
        qbi_199a_usd=80_000.0,
        ordinary_income_usd=0.0,
        capital_gain_usd=0.0,
        foreign_tax_paid_usd=0.0,
    )
    result = summarize_income(inp)

    assert result.total_income_usd == 80_000.0
    assert result.foreign_tax_credit_eligible is False
    assert "QBI: $80,000.00" in result.notes[0]
    assert "20% deduction under §199A" in result.notes[0]


def test_income_summary_zero_income():
    """Test income summary with zero income."""
    inp = IncomeSummaryInput(
        tax_year=2024,
        partnership_name="Gamma Dormant Partnership",
        subpart_f_income_usd=0.0,
        gilti_usd=0.0,
        qbi_199a_usd=0.0,
        ordinary_income_usd=0.0,
        capital_gain_usd=0.0,
        foreign_tax_paid_usd=0.0,
    )
    result = summarize_income(inp)

    assert result.total_income_usd == 0.0
    assert result.foreign_tax_credit_eligible is False
    assert "No income reported" in result.notes[0]


# ---------------------------------------------------------------------------
# Test penalty calculation
# ---------------------------------------------------------------------------

def test_penalty_base_only():
    """Test base penalty only (no continued failure, not willful)."""
    inp = PenaltyCalculationInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Alpha GmbH",
                country="DE",
                ownership_percentage=55.0,
                us_controlled=False,
                fair_market_value_usd=400_000.0,
            )
        ],
        days_unreported=0,
        is_willful=False,
    )
    result = calculate_penalty(inp)

    assert result.base_penalty == PENALTY_BASE
    assert result.continued_failure_penalty == 0.0
    assert result.willful_penalty == 0.0
    assert result.total_penalty == PENALTY_BASE


def test_penalty_continued_failure():
    """Test continued failure penalty (90 days = 3 periods)."""
    inp = PenaltyCalculationInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Beta Ltd",
                country="UK",
                ownership_percentage=25.0,
                us_controlled=True,
                fair_market_value_usd=300_000.0,
            )
        ],
        days_unreported=90,
        is_willful=False,
    )
    result = calculate_penalty(inp)

    assert result.base_penalty == PENALTY_BASE
    assert result.continued_failure_penalty == 3 * PENALTY_CONTINUED_PER_30_DAYS
    assert result.willful_penalty == 0.0
    assert result.total_penalty == PENALTY_BASE + 3 * PENALTY_CONTINUED_PER_30_DAYS


def test_penalty_continued_failure_max():
    """Test continued failure penalty cap ($50k max)."""
    inp = PenaltyCalculationInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Gamma SARL",
                country="FR",
                ownership_percentage=80.0,
                us_controlled=False,
                fair_market_value_usd=1_000_000.0,
            )
        ],
        days_unreported=365,  # 12 periods, but capped at $50k
        is_willful=False,
    )
    result = calculate_penalty(inp)

    assert result.continued_failure_penalty == PENALTY_CONTINUED_MAX
    assert result.total_penalty == PENALTY_BASE + PENALTY_CONTINUED_MAX


def test_penalty_willful_failure():
    """Test willful failure penalty (50% of partnership value)."""
    inp = PenaltyCalculationInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Delta KG",
                country="AT",
                ownership_percentage=100.0,
                us_controlled=False,
                fair_market_value_usd=500_000.0,
            )
        ],
        days_unreported=0,
        is_willful=True,
    )
    result = calculate_penalty(inp)

    assert result.base_penalty == PENALTY_BASE
    assert result.willful_penalty == 500_000.0 * 0.50
    assert result.total_penalty == PENALTY_BASE + 250_000.0
    assert "Criminal penalties may also apply" in result.explanation


def test_penalty_willful_no_value():
    """Test willful failure penalty when partnership value is unknown."""
    inp = PenaltyCalculationInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Epsilon Ltd",
                country="IE",
                ownership_percentage=60.0,
                us_controlled=False,
                fair_market_value_usd=0.0,  # Value unknown
            )
        ],
        days_unreported=0,
        is_willful=True,
    )
    result = calculate_penalty(inp)

    # Minimum willful penalty when value is unknown
    assert result.willful_penalty == 100_000.0


def test_penalty_no_filing_requirement():
    """Test that no penalty applies if filing is not required."""
    inp = PenaltyCalculationInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Zeta AG",
                country="CH",
                ownership_percentage=3.0,
                us_controlled=False,
                fair_market_value_usd=20_000.0,
            )
        ],
        days_unreported=60,
        is_willful=True,
    )
    result = calculate_penalty(inp)

    assert result.total_penalty == 0.0
    assert "No filing requirement" in result.explanation


# ---------------------------------------------------------------------------
# Test overview
# ---------------------------------------------------------------------------

def test_get_overview():
    """Test that overview returns all required fields."""
    overview = get_overview()

    assert overview.title == "Form 8865: Return of U.S. Persons With Respect to Certain Foreign Partnerships"
    assert "Category 1: Control" in overview.category_1
    assert "Category 2: Ownership" in overview.category_2
    assert "Category 3: Reportable Event" in overview.category_3
    assert "Category 4: Contribution" in overview.category_4
    assert "Category 5: Ownership" in overview.category_5
    assert "$10,000 base penalty" in overview.penalties
    assert "April 15" in overview.filing_deadline


# ---------------------------------------------------------------------------
# Test edge cases
# ---------------------------------------------------------------------------

def test_multiple_partnerships_multiple_categories():
    """Test multiple partnerships triggering different categories."""
    inp = FilingRequirementInput(
        tax_year=2024,
        partnerships=[
            PartnershipInput(
                name="Alpha GmbH",
                country="DE",
                ownership_percentage=55.0,
                us_controlled=False,
                fair_market_value_usd=600_000.0,
            ),
            PartnershipInput(
                name="Beta Ltd",
                country="UK",
                ownership_percentage=15.0,
                us_controlled=True,
                fair_market_value_usd=200_000.0,
            ),
            PartnershipInput(
                name="Gamma SARL",
                country="FR",
                ownership_percentage=8.0,
                us_controlled=False,
                capital_contributed_usd=120_000.0,
                fair_market_value_usd=150_000.0,
            ),
        ],
    )
    result = check_filing_requirement(inp)

    assert result.filing_required is True
    assert "Category 1: Control" in result.categories
    assert "Category 2: Ownership (U.S.-controlled)" in result.categories
    assert "Category 4: Contribution" in result.categories
    assert result.total_partnerships == 3


# ---------------------------------------------------------------------------
# HTTP router tests
# ---------------------------------------------------------------------------

def test_router_filing_requirement_requires_jwt():
    """POST /api/v1/form8865/filing-requirement without token → 401."""
    resp = client.post(
        "/api/v1/form8865/filing-requirement",
        json={
            "tax_year": 2024,
            "partnerships": [
                {
                    "name": "Test Partnership",
                    "country": "DE",
                    "ownership_percentage": 55.0,
                    "us_controlled": False,
                    "fair_market_value_usd": 500_000.0,
                }
            ],
        },
    )
    assert resp.status_code == 401


def test_router_filing_requirement_with_jwt(auth_token):
    """POST /api/v1/form8865/filing-requirement with valid JWT → 200."""
    resp = client.post(
        "/api/v1/form8865/filing-requirement",
        json={
            "tax_year": 2024,
            "partnerships": [
                {
                    "name": "Alpha GmbH",
                    "country": "DE",
                    "ownership_percentage": 60.0,
                    "us_controlled": False,
                    "fair_market_value_usd": 500_000.0,
                }
            ],
        },
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filing_required"] is True
    assert "Category 1: Control" in data["categories"]


def test_router_income_summary_with_jwt(auth_token):
    """POST /api/v1/form8865/income-summary with valid JWT → 200."""
    resp = client.post(
        "/api/v1/form8865/income-summary",
        json={
            "tax_year": 2024,
            "partnership_name": "Alpha Foreign LP",
            "subpart_f_income_usd": 30_000.0,
            "gilti_usd": 15_000.0,
            "qbi_199a_usd": 0.0,
            "ordinary_income_usd": 50_000.0,
            "capital_gain_usd": 5_000.0,
            "foreign_tax_paid_usd": 12_000.0,
        },
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_income_usd"] == 100_000.0
    assert data["foreign_tax_credit_eligible"] is True


def test_router_penalty_calculation_with_jwt(auth_token):
    """POST /api/v1/form8865/penalty-calculation with valid JWT → 200."""
    resp = client.post(
        "/api/v1/form8865/penalty-calculation",
        json={
            "tax_year": 2024,
            "partnerships": [
                {
                    "name": "Alpha GmbH",
                    "country": "DE",
                    "ownership_percentage": 55.0,
                    "us_controlled": False,
                    "fair_market_value_usd": 400_000.0,
                }
            ],
            "days_unreported": 90,
            "is_willful": False,
        },
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["base_penalty"] == PENALTY_BASE
    assert data["continued_failure_penalty"] == 3 * PENALTY_CONTINUED_PER_30_DAYS
    assert data["total_penalty"] == PENALTY_BASE + 3 * PENALTY_CONTINUED_PER_30_DAYS


def test_router_overview_with_jwt(auth_token):
    """GET /api/v1/form8865/overview with valid JWT → 200."""
    resp = client.get(
        "/api/v1/form8865/overview",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Form 8865" in data["title"]
    assert data["category_1"]
    assert data["category_5"]
    assert data["penalties"]
