"""
Tests for Form 8949 — Sales and Other Dispositions of Capital Assets.

Tests cover:
- Short-term gains (held <= 1 year)
- Long-term gains (held > 1 year)
- Short-term losses
- Long-term losses
- Mixed short-term and long-term transactions
- Break-even transactions
- Multiple transactions with netting
- Edge cases (exactly 1 year, leap year)
- API endpoint tests
"""
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.modules.form8949 import (
    Transaction,
    Form8949Input,
    calculate_form8949,
    get_form8949_overview,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: Get auth token
# ---------------------------------------------------------------------------

def _auth_headers() -> dict:
    """Create a valid JWT token for testing."""
    from app.auth.utils import create_access_token
    token = create_access_token(data={"sub": "test-user", "tenant_id": "test-tenant"})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Module-level tests (direct function calls)
# ---------------------------------------------------------------------------

class TestShortTermGains:
    """Tests for short-term capital gains (held <= 1 year)."""

    def test_short_term_gain_basic(self):
        """Stock held 6 months with a gain should be short-term."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2024-01-15",
                purchase_price=Decimal("10000"),
                sale_date="2024-07-15",
                sale_price=Decimal("12500"),
                description="AAPL",
            )
        ])
        result = calculate_form8949(inp)
        assert result.short_term_count == 1
        assert result.long_term_count == 0
        assert result.short_term_total == Decimal("2500.00")
        assert result.long_term_total == Decimal("0.00")
        assert result.net_gain_loss == Decimal("2500.00")
        assert result.short_term_transactions[0].holding_period == "short-term"
        assert result.short_term_transactions[0].gain_loss == Decimal("2500.00")

    def test_short_term_gain_one_day(self):
        """Stock held 1 day should be short-term."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2024-06-01",
                purchase_price=Decimal("5000"),
                sale_date="2024-06-02",
                sale_price=Decimal("5100"),
                description="TSLA",
            )
        ])
        result = calculate_form8949(inp)
        assert result.short_term_count == 1
        assert result.short_term_total == Decimal("100.00")
        assert result.short_term_transactions[0].holding_days == 1

    def test_short_term_gain_exactly_one_year(self):
        """Stock held exactly 1 year should be short-term (not > 1 year)."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2023-06-15",
                purchase_price=Decimal("8000"),
                sale_date="2024-06-15",
                sale_price=Decimal("9000"),
                description="MSFT",
            )
        ])
        result = calculate_form8949(inp)
        assert result.short_term_count == 1
        assert result.long_term_count == 0
        assert result.short_term_transactions[0].holding_period == "short-term"


class TestLongTermGains:
    """Tests for long-term capital gains (held > 1 year)."""

    def test_long_term_gain_basic(self):
        """Stock held 2 years with a gain should be long-term."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2022-03-10",
                purchase_price=Decimal("15000"),
                sale_date="2024-03-10",
                sale_price=Decimal("22000"),
                description="GOOGL",
            )
        ])
        result = calculate_form8949(inp)
        assert result.long_term_count == 1
        assert result.short_term_count == 0
        assert result.long_term_total == Decimal("7000.00")
        assert result.net_gain_loss == Decimal("7000.00")
        assert result.long_term_transactions[0].holding_period == "long-term"

    def test_long_term_gain_one_year_plus_one_day(self):
        """Stock held 1 year + 1 day should be long-term."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2023-06-15",
                purchase_price=Decimal("10000"),
                sale_date="2024-06-16",
                sale_price=Decimal("11000"),
                description="AMZN",
            )
        ])
        result = calculate_form8949(inp)
        assert result.long_term_count == 1
        assert result.short_term_count == 0
        assert result.long_term_transactions[0].holding_period == "long-term"

    def test_long_term_gain_leap_year(self):
        """Stock held across a leap year boundary."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2020-02-28",
                purchase_price=Decimal("5000"),
                sale_date="2021-03-01",
                sale_price=Decimal("6500"),
                description="BTC",
            )
        ])
        result = calculate_form8949(inp)
        assert result.long_term_count == 1
        assert result.long_term_total == Decimal("1500.00")


class TestShortTermLosses:
    """Tests for short-term capital losses."""

    def test_short_term_loss_basic(self):
        """Stock held 3 months with a loss should be short-term."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2024-01-01",
                purchase_price=Decimal("20000"),
                sale_date="2024-04-01",
                sale_price=Decimal("17500"),
                description="META",
            )
        ])
        result = calculate_form8949(inp)
        assert result.short_term_count == 1
        assert result.short_term_total == Decimal("-2500.00")
        assert result.net_gain_loss == Decimal("-2500.00")
        assert result.short_term_transactions[0].gain_loss == Decimal("-2500.00")


class TestLongTermLosses:
    """Tests for long-term capital losses."""

    def test_long_term_loss_basic(self):
        """Stock held 3 years with a loss should be long-term."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2021-01-15",
                purchase_price=Decimal("30000"),
                sale_date="2024-01-15",
                sale_price=Decimal("25000"),
                description="NFLX",
            )
        ])
        result = calculate_form8949(inp)
        assert result.long_term_count == 1
        assert result.long_term_total == Decimal("-5000.00")
        assert result.net_gain_loss == Decimal("-5000.00")


class TestMixedTransactions:
    """Tests for mixed short-term and long-term transactions."""

    def test_mixed_gain_and_loss(self):
        """Mix of short-term gain and long-term loss."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2024-01-01",
                purchase_price=Decimal("10000"),
                sale_date="2024-06-01",
                sale_price=Decimal("12000"),
                description="STOCK-A",
            ),
            Transaction(
                purchase_date="2022-01-01",
                purchase_price=Decimal("20000"),
                sale_date="2024-06-01",
                sale_price=Decimal("18000"),
                description="STOCK-B",
            ),
        ])
        result = calculate_form8949(inp)
        assert result.short_term_count == 1
        assert result.long_term_count == 1
        assert result.short_term_total == Decimal("2000.00")
        assert result.long_term_total == Decimal("-2000.00")
        assert result.net_gain_loss == Decimal("0.00")

    def test_multiple_short_term_transactions(self):
        """Multiple short-term transactions should be netted."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2024-01-01",
                purchase_price=Decimal("10000"),
                sale_date="2024-03-01",
                sale_price=Decimal("11000"),
                description="TRADE-1",
            ),
            Transaction(
                purchase_date="2024-02-01",
                purchase_price=Decimal("5000"),
                sale_date="2024-05-01",
                sale_price=Decimal("4500"),
                description="TRADE-2",
            ),
            Transaction(
                purchase_date="2024-03-01",
                purchase_price=Decimal("8000"),
                sale_date="2024-08-01",
                sale_price=Decimal("9500"),
                description="TRADE-3",
            ),
        ])
        result = calculate_form8949(inp)
        assert result.short_term_count == 3
        assert result.long_term_count == 0
        # 1000 - 500 + 1500 = 2000
        assert result.short_term_total == Decimal("2000.00")
        assert result.net_gain_loss == Decimal("2000.00")

    def test_multiple_long_term_transactions(self):
        """Multiple long-term transactions should be netted."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2020-01-01",
                purchase_price=Decimal("10000"),
                sale_date="2024-01-02",
                sale_price=Decimal("15000"),
                description="LONG-1",
            ),
            Transaction(
                purchase_date="2019-06-01",
                purchase_price=Decimal("20000"),
                sale_date="2024-06-02",
                sale_price=Decimal("18000"),
                description="LONG-2",
            ),
        ])
        result = calculate_form8949(inp)
        assert result.long_term_count == 2
        assert result.short_term_count == 0
        # 5000 - 2000 = 3000
        assert result.long_term_total == Decimal("3000.00")

    def test_net_loss_scenario(self):
        """Net loss across both short-term and long-term."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2024-01-01",
                purchase_price=Decimal("10000"),
                sale_date="2024-06-01",
                sale_price=Decimal("8000"),
                description="LOSS-1",
            ),
            Transaction(
                purchase_date="2022-01-01",
                purchase_price=Decimal("20000"),
                sale_date="2024-06-01",
                sale_price=Decimal("15000"),
                description="LOSS-2",
            ),
        ])
        result = calculate_form8949(inp)
        assert result.short_term_total == Decimal("-2000.00")
        assert result.long_term_total == Decimal("-5000.00")
        assert result.net_gain_loss == Decimal("-7000.00")


class TestEdgeCases:
    """Edge case tests."""

    def test_break_even_transaction(self):
        """Transaction with zero gain/loss."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2024-01-01",
                purchase_price=Decimal("10000"),
                sale_date="2024-06-01",
                sale_price=Decimal("10000"),
                description="BREAK-EVEN",
            )
        ])
        result = calculate_form8949(inp)
        assert result.short_term_count == 1
        assert result.short_term_total == Decimal("0.00")
        assert result.net_gain_loss == Decimal("0.00")

    def test_empty_transactions(self):
        """Empty transaction list should return zero totals."""
        inp = Form8949Input(transactions=[])
        result = calculate_form8949(inp)
        assert result.short_term_count == 0
        assert result.long_term_count == 0
        assert result.short_term_total == Decimal("0.00")
        assert result.long_term_total == Decimal("0.00")
        assert result.net_gain_loss == Decimal("0.00")

    def test_large_gain(self):
        """Large gain transaction."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2023-01-01",
                purchase_price=Decimal("100000"),
                sale_date="2024-06-01",
                sale_price=Decimal("250000"),
                description="BIG-GAIN",
            )
        ])
        result = calculate_form8949(inp)
        assert result.long_term_total == Decimal("150000.00")
        assert result.net_gain_loss == Decimal("150000.00")

    def test_small_fractional_amounts(self):
        """Transactions with fractional cents."""
        inp = Form8949Input(transactions=[
            Transaction(
                purchase_date="2024-01-01",
                purchase_price=Decimal("100.50"),
                sale_date="2024-06-01",
                sale_price=Decimal("150.75"),
                description="SMALL",
            )
        ])
        result = calculate_form8949(inp)
        assert result.short_term_total == Decimal("50.25")


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestCalculateEndpoint:
    """Tests for /api/v1/form8949/calculate endpoint."""

    def test_calculate_endpoint_short_term(self):
        """Test calculate endpoint with short-term transaction."""
        resp = client.post(
            "/api/v1/form8949/calculate",
            json={
                "transactions": [
                    {
                        "purchase_date": "2024-01-15",
                        "purchase_price": "10000.00",
                        "sale_date": "2024-07-15",
                        "sale_price": "12500.00",
                        "description": "AAPL",
                    }
                ]
            },
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["short_term_count"] == 1
        assert data["long_term_count"] == 0
        assert data["short_term_total"] == "2500.00"
        assert data["net_gain_loss"] == "2500.00"
        assert len(data["short_term_transactions"]) == 1
        assert data["short_term_transactions"][0]["description"] == "AAPL"

    def test_calculate_endpoint_long_term(self):
        """Test calculate endpoint with long-term transaction."""
        resp = client.post(
            "/api/v1/form8949/calculate",
            json={
                "transactions": [
                    {
                        "purchase_date": "2022-03-10",
                        "purchase_price": "15000.00",
                        "sale_date": "2024-03-10",
                        "sale_price": "22000.00",
                        "description": "GOOGL",
                    }
                ]
            },
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["long_term_count"] == 1
        assert data["short_term_count"] == 0
        assert data["long_term_total"] == "7000.00"

    def test_calculate_endpoint_mixed(self):
        """Test calculate endpoint with mixed transactions."""
        resp = client.post(
            "/api/v1/form8949/calculate",
            json={
                "transactions": [
                    {
                        "purchase_date": "2024-01-01",
                        "purchase_price": "10000.00",
                        "sale_date": "2024-06-01",
                        "sale_price": "12000.00",
                        "description": "STOCK-A",
                    },
                    {
                        "purchase_date": "2022-01-01",
                        "purchase_price": "20000.00",
                        "sale_date": "2024-06-01",
                        "sale_price": "18000.00",
                        "description": "STOCK-B",
                    },
                ]
            },
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["short_term_count"] == 1
        assert data["long_term_count"] == 1
        assert data["short_term_total"] == "2000.00"
        assert data["long_term_total"] == "-2000.00"
        assert data["net_gain_loss"] == "0.00"

    def test_calculate_endpoint_requires_auth(self):
        """Test that calculate endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form8949/calculate",
            json={
                "transactions": [
                    {
                        "purchase_date": "2024-01-01",
                        "purchase_price": "10000.00",
                        "sale_date": "2024-06-01",
                        "sale_price": "12000.00",
                        "description": "TEST",
                    }
                ]
            },
        )
        assert resp.status_code == 401

    def test_calculate_endpoint_empty_transactions(self):
        """Test calculate endpoint with empty transaction list."""
        resp = client.post(
            "/api/v1/form8949/calculate",
            json={"transactions": []},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["short_term_count"] == 0
        assert data["long_term_count"] == 0
        assert data["net_gain_loss"] == "0.00"


class TestOverviewEndpoint:
    """Tests for /api/v1/form8949/overview endpoint."""

    def test_overview_endpoint(self):
        """Test overview endpoint returns Form 8949 info."""
        resp = client.get(
            "/api/v1/form8949/overview",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["form"] == "Form 8949"
        assert "title" in data
        assert "purpose" in data
        assert "key_rules" in data
        assert "statutory_references" in data

    def test_overview_endpoint_requires_auth(self):
        """Test that overview endpoint requires authentication."""
        resp = client.get("/api/v1/form8949/overview")
        assert resp.status_code == 401
