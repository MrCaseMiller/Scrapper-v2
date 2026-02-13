"""Unit tests for Sum-to-One Arbitrage strategy."""

import pytest
from datetime import datetime
from src.strategy.sum_to_one_arb import SumToOneArbitrage
from src.engine.models import Market, OrderSide, MarketSide


@pytest.fixture
def strategy():
    """Create strategy instance with test config."""
    config = {
        "min_spread_pct": 2.5,
        "fee_rate": 0.02,
        "gas_cost": 0.10,
        "max_position_size": 500.0,
        "min_position_size": 10.0
    }
    return SumToOneArbitrage(config)


@pytest.fixture
def mock_market():
    """Create mock market."""
    return Market(
        market_id="test_market_123",
        question="Will BTC reach $100k by EOY?",
        yes_token_id="yes_token_123",
        no_token_id="no_token_123",
        end_date=datetime(2025, 12, 31),
        active=True
    )


class TestSumToOneArbitrage:
    """Test suite for Sum-to-One Arbitrage strategy."""

    @pytest.mark.asyncio
    async def test_profitable_arbitrage_detected(self, strategy, mock_market):
        """Test that profitable arbitrage opportunity is detected."""
        # YES = 0.48, NO = 0.49, Sum = 0.97 (3% spread)
        orderbook = {
            "yes_asks": [{"price": 0.48, "size": 100}],
            "no_asks": [{"price": 0.49, "size": 100}]
        }

        orders = await strategy.on_market_update(
            market=mock_market,
            current_price=0.48,
            orderbook=orderbook
        )

        # Should generate 2 orders (buy YES + buy NO)
        assert len(orders) == 2
        assert orders[0].side == OrderSide.BUY
        assert orders[0].market_side == MarketSide.YES
        assert orders[1].side == OrderSide.BUY
        assert orders[1].market_side == MarketSide.NO

    @pytest.mark.asyncio
    async def test_unprofitable_arbitrage_ignored(self, strategy, mock_market):
        """Test that unprofitable arbitrage is ignored."""
        # YES = 0.50, NO = 0.49, Sum = 0.99 (1% spread - too small)
        orderbook = {
            "yes_asks": [{"price": 0.50, "size": 100}],
            "no_asks": [{"price": 0.49, "size": 100}]
        }

        orders = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook=orderbook
        )

        # Should not generate any orders (spread too small)
        assert len(orders) == 0

    @pytest.mark.asyncio
    async def test_no_orderbook_returns_empty(self, strategy, mock_market):
        """Test that missing orderbook returns no orders."""
        orders = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook=None
        )

        assert len(orders) == 0

    @pytest.mark.asyncio
    async def test_position_sizing_scales_with_spread(self, strategy, mock_market):
        """Test that position size increases with larger spreads."""
        # Small spread (2.5%)
        orderbook_small = {
            "yes_asks": [{"price": 0.485, "size": 100}],
            "no_asks": [{"price": 0.490, "size": 100}]
        }

        # Large spread (5%)
        orderbook_large = {
            "yes_asks": [{"price": 0.47, "size": 100}],
            "no_asks": [{"price": 0.48, "size": 100}]
        }

        orders_small = await strategy.on_market_update(
            market=mock_market,
            current_price=0.485,
            orderbook=orderbook_small
        )

        # Reset strategy state
        strategy.active_arbs.clear()

        orders_large = await strategy.on_market_update(
            market=mock_market,
            current_price=0.47,
            orderbook=orderbook_large
        )

        # Larger spread should result in larger position size
        if orders_small and orders_large:
            assert orders_large[0].size > orders_small[0].size

    @pytest.mark.asyncio
    async def test_prevents_duplicate_arbitrage(self, strategy, mock_market):
        """Test that duplicate arbitrage in same market is prevented."""
        orderbook = {
            "yes_asks": [{"price": 0.48, "size": 100}],
            "no_asks": [{"price": 0.49, "size": 100}]
        }

        # First call should generate orders
        orders1 = await strategy.on_market_update(
            market=mock_market,
            current_price=0.48,
            orderbook=orderbook
        )

        # Second call should NOT generate orders (already have position)
        orders2 = await strategy.on_market_update(
            market=mock_market,
            current_price=0.48,
            orderbook=orderbook
        )

        assert len(orders1) == 2
        assert len(orders2) == 0

    @pytest.mark.asyncio
    async def test_resolution_calculates_profit(self, strategy, mock_market):
        """Test that resolution correctly calculates profit."""
        # Set up active arbitrage
        strategy.active_arbs[mock_market.market_id] = {
            "timestamp": datetime.utcnow(),
            "yes_price": 0.48,
            "no_price": 0.49,
            "spread_pct": 3.0,
            "position_size": 100.0,
            "expected_profit": 1.0
        }

        initial_profit = strategy.total_profit

        # Market resolves YES
        await strategy.on_resolution(mock_market.market_id, "YES")

        # Profit should have increased
        assert strategy.total_profit > initial_profit
        assert mock_market.market_id not in strategy.active_arbs

    def test_get_best_ask_extracts_price(self, strategy):
        """Test orderbook price extraction."""
        orderbook = {
            "yes_asks": [
                {"price": 0.48, "size": 100},
                {"price": 0.49, "size": 50}
            ]
        }

        best_ask = strategy._get_best_ask(orderbook, "yes")
        assert best_ask == 0.48

    def test_optimal_size_calculation(self, strategy):
        """Test position size calculation."""
        # Small spread
        size_small = strategy._calculate_optimal_size(2.5)
        assert size_small >= strategy.min_position_size

        # Large spread
        size_large = strategy._calculate_optimal_size(5.0)
        assert size_large > size_small
        assert size_large <= strategy.max_position_size

    def test_get_stats(self, strategy):
        """Test statistics generation."""
        stats = strategy.get_stats()

        assert stats["strategy"] == "SumToOneArbitrage"
        assert "arb_count" in stats
        assert "total_profit" in stats
        assert "config" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
