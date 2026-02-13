"""Tests for portfolio tracker."""

import pytest
from datetime import datetime

from src.engine.models import Portfolio, Position, MarketSide


def test_portfolio_creation():
    """Test portfolio creation."""
    portfolio = Portfolio(
        balance=1000.0,
        total_deposited=1000.0
    )

    assert portfolio.balance == 1000.0
    assert portfolio.total_value == 1000.0
    assert portfolio.total_return_pct == 0.0


def test_position_pnl_calculation():
    """Test position P&L calculation."""
    position = Position(
        token_id="test",
        market_id="test_market",
        market_side=MarketSide.YES,
        shares=100.0,
        avg_entry_price=0.5,
        current_price=0.7
    )

    assert position.cost_basis == 50.0  # 100 * 0.5
    assert position.market_value == 70.0  # 100 * 0.7
    assert position.unrealized_pnl == 20.0  # 70 - 50
    assert position.unrealized_pnl_pct == 40.0  # (20 / 50) * 100


def test_portfolio_with_positions():
    """Test portfolio calculations with positions."""
    portfolio = Portfolio(
        balance=500.0,
        total_deposited=1000.0
    )

    # Add position
    position = Position(
        token_id="test1",
        market_id="market1",
        market_side=MarketSide.YES,
        shares=100.0,
        avg_entry_price=0.5,
        current_price=0.7
    )
    portfolio.positions["test1"] = position

    assert portfolio.positions_value == 70.0
    assert portfolio.total_value == 570.0  # 500 + 70
    assert portfolio.unrealized_pnl == 20.0
