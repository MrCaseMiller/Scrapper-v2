"""Tests for execution engine."""

import pytest
from datetime import datetime

from src.engine.models import Order, OrderSide, MarketSide, Orderbook, OrderbookLevel
from src.engine.executor import ExecutionEngine


@pytest.mark.asyncio
async def test_order_creation():
    """Test order creation."""
    order = Order(
        market_id="test_market",
        token_id="test_token",
        side=OrderSide.BUY,
        market_side=MarketSide.YES,
        size=100.0,
        price=0.5
    )

    assert order.market_id == "test_market"
    assert order.side == OrderSide.BUY
    assert order.size == 100.0
    assert order.shares == 200.0  # 100 / 0.5


def test_orderbook_properties():
    """Test orderbook properties."""
    orderbook = Orderbook(
        token_id="test",
        market_id="test",
        bids=[
            OrderbookLevel(price=0.6, size=100),
            OrderbookLevel(price=0.55, size=200)
        ],
        asks=[
            OrderbookLevel(price=0.65, size=150),
            OrderbookLevel(price=0.7, size=250)
        ]
    )

    assert orderbook.best_bid == 0.6
    assert orderbook.best_ask == 0.65
    assert orderbook.mid_price == 0.625
    assert orderbook.spread == 0.05
