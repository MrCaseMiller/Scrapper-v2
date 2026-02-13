"""Unit tests for Market Making strategy."""

import pytest
from datetime import datetime
from src.strategy.market_making import MarketMaking
from src.engine.models import Market, OrderSide, MarketSide, Portfolio, Position


@pytest.fixture
def strategy():
    """Create strategy instance with test config."""
    config = {
        "base_spread": 0.02,  # 2%
        "min_spread": 0.005,  # 0.5%
        "max_spread": 0.05,   # 5%
        "order_size": 100.0,
        "max_inventory": 500.0,
        "target_inventory": 0.0,
        "skew_factor": 0.01
    }
    return MarketMaking(config)


@pytest.fixture
def mock_market():
    """Create mock market."""
    return Market(
        market_id="test_market_mm",
        question="Will ETH reach $5k?",
        yes_token_id="yes_eth",
        no_token_id="no_eth",
        end_date=datetime(2025, 12, 31),
        active=True
    )


class TestMarketMaking:
    """Test suite for Market Making strategy."""

    @pytest.mark.asyncio
    async def test_generates_bid_and_ask(self, strategy, mock_market):
        """Test that MM generates both bid and ask orders."""
        orders = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook={}
        )

        # Should generate 2 orders (BUY + SELL)
        assert len(orders) == 2

        buy_orders = [o for o in orders if o.side == OrderSide.BUY]
        sell_orders = [o for o in orders if o.side == OrderSide.SELL]

        assert len(buy_orders) == 1
        assert len(sell_orders) == 1

        # Bid should be below mid, ask should be above mid
        bid = buy_orders[0].price
        ask = sell_orders[0].price
        mid = 0.50

        assert bid < mid
        assert ask > mid

    @pytest.mark.asyncio
    async def test_spread_maintains_minimum(self, strategy, mock_market):
        """Test that spread respects minimum."""
        orders = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook={}
        )

        buy_orders = [o for o in orders if o.side == OrderSide.BUY]
        sell_orders = [o for o in orders if o.side == OrderSide.SELL]

        if buy_orders and sell_orders:
            spread = sell_orders[0].price - buy_orders[0].price
            assert spread >= strategy.min_spread

    @pytest.mark.asyncio
    async def test_inventory_skewing_long_position(self, strategy, mock_market):
        """Test that long inventory skews quotes downward (encourage selling)."""
        # Set positive inventory (long)
        strategy.inventory["yes_eth"] = 200.0  # Long 200 shares

        orders = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook={}
        )

        if len(orders) == 2:
            buy_orders = [o for o in orders if o.side == OrderSide.BUY]
            sell_orders = [o for o in orders if o.side == OrderSide.SELL]

            # With positive inventory, both bid and ask should be lower than neutral
            # (skewed to encourage selling)
            neutral_mid = 0.50
            bid = buy_orders[0].price
            ask = sell_orders[0].price

            # Average of bid/ask should be below neutral mid
            avg = (bid + ask) / 2
            assert avg < neutral_mid

    @pytest.mark.asyncio
    async def test_inventory_limit_triggers_reduction(self, strategy, mock_market):
        """Test that excessive inventory triggers reduction quotes."""
        # Set inventory beyond max limit
        strategy.inventory["yes_eth"] = 600.0  # Exceeds max_inventory of 500

        orders = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook={}
        )

        # Should only quote on reducing side (SELL only)
        sell_orders = [o for o in orders if o.side == OrderSide.SELL]
        buy_orders = [o for o in orders if o.side == OrderSide.BUY]

        assert len(sell_orders) > 0
        assert len(buy_orders) == 0

    @pytest.mark.asyncio
    async def test_quote_refresh_timing(self, strategy, mock_market):
        """Test that quotes are not refreshed too frequently."""
        # First update
        orders1 = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook={}
        )

        # Immediate second update (should not refresh)
        orders2 = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook={}
        )

        # First should generate quotes
        assert len(orders1) > 0

        # Second should not (within TTL)
        assert len(orders2) == 0

    @pytest.mark.asyncio
    async def test_volatility_widens_spread(self, strategy, mock_market):
        """Test that high volatility widens the spread."""
        # Add stable price history (low volatility)
        for i in range(20):
            strategy._update_price_history("yes_eth", 0.50)

        orders_low_vol = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook={}
        )

        # Clear quotes
        strategy.active_quotes.clear()

        # Add volatile price history
        for i in range(20):
            price = 0.50 + (i % 2) * 0.05  # Oscillate between 0.50 and 0.55
            strategy._update_price_history("yes_eth", price)

        orders_high_vol = await strategy.on_market_update(
            market=mock_market,
            current_price=0.50,
            orderbook={}
        )

        # Calculate spreads
        if orders_low_vol and orders_high_vol:
            buy_low = [o for o in orders_low_vol if o.side == OrderSide.BUY][0]
            sell_low = [o for o in orders_low_vol if o.side == OrderSide.SELL][0]
            spread_low = sell_low.price - buy_low.price

            buy_high = [o for o in orders_high_vol if o.side == OrderSide.BUY][0]
            sell_high = [o for o in orders_high_vol if o.side == OrderSide.SELL][0]
            spread_high = sell_high.price - buy_high.price

            # High volatility should have wider spread
            assert spread_high > spread_low

    @pytest.mark.asyncio
    async def test_on_fill_updates_inventory(self, strategy):
        """Test that fills update inventory correctly."""
        class MockFill:
            def __init__(self):
                self.token_id = "yes_test"
                self.side = OrderSide.BUY
                self.price = 0.50
                self.size = 100.0  # $100 USDC
                self.market_id = "test_market"

        fill = MockFill()

        # Initial inventory
        initial_inventory = strategy.inventory.get("yes_test", 0)

        # Process fill
        await strategy.on_fill(fill)

        # Inventory should increase
        new_inventory = strategy.inventory.get("yes_test", 0)
        assert new_inventory > initial_inventory

    def test_calculate_volatility(self, strategy):
        """Test volatility calculation."""
        token_id = "test_token"

        # Add stable prices
        for _ in range(30):
            strategy._update_price_history(token_id, 0.50)

        vol_stable = strategy._calculate_volatility(token_id)

        # Add volatile prices
        for i in range(30):
            price = 0.50 + (i % 2) * 0.10  # High oscillation
            strategy._update_price_history(token_id, price)

        vol_high = strategy._calculate_volatility(token_id)

        # High volatility should be greater
        assert vol_high > vol_stable

    def test_inventory_skew_calculation(self, strategy):
        """Test inventory skew calculation."""
        # Neutral inventory
        skew_neutral = strategy._calculate_inventory_skew(0.0)
        assert skew_neutral == 0.0

        # Positive inventory (long) → negative skew (lower prices)
        skew_long = strategy._calculate_inventory_skew(100.0)
        assert skew_long < 0

        # Negative inventory (short) → positive skew (higher prices)
        skew_short = strategy._calculate_inventory_skew(-100.0)
        assert skew_short > 0

    def test_get_stats(self, strategy):
        """Test statistics generation."""
        stats = strategy.get_stats()

        assert stats["strategy"] == "MarketMaking"
        assert "fill_count" in stats
        assert "total_spread_earned" in stats
        assert "active_quotes" in stats
        assert "inventory_count" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
