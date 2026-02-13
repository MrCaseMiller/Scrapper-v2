"""Tests for trading strategies."""

import pytest
from datetime import datetime

from src.strategy.threshold import NaiveThreshold
from src.strategy.mean_reversion import MeanReversion
from src.strategy.manual import Manual
from src.engine.models import Market, OrderSide, MarketSide


@pytest.mark.asyncio
async def test_threshold_strategy_buy_signal():
    """Test threshold strategy buy signal."""
    strategy = NaiveThreshold({
        "buy_below": 0.3,
        "sell_above": 0.7,
        "position_size": 100.0
    })

    market = Market(
        market_id="test_market",
        question="Test question?",
        end_date=datetime.utcnow(),
        yes_token_id="yes_token",
        no_token_id="no_token"
    )

    # Price below threshold, no position
    orders = await strategy.on_market_update(market, 0.25)

    assert len(orders) == 1
    assert orders[0].side == OrderSide.BUY
    assert orders[0].size == 100.0


@pytest.mark.asyncio
async def test_manual_strategy():
    """Test manual strategy."""
    strategy = Manual()

    market = Market(
        market_id="test_market",
        question="Test question?",
        end_date=datetime.utcnow(),
        yes_token_id="yes_token",
        no_token_id="no_token"
    )

    # Initially no orders
    orders = await strategy.on_market_update(market, 0.5)
    assert len(orders) == 0

    # Add manual order
    strategy.add_order(
        market_id="test_market",
        token_id="yes_token",
        side=OrderSide.BUY,
        market_side=MarketSide.YES,
        size=100.0,
        price=0.5
    )

    # Should return the pending order
    orders = await strategy.on_market_update(market, 0.5)
    assert len(orders) == 1
    assert orders[0].side == OrderSide.BUY
