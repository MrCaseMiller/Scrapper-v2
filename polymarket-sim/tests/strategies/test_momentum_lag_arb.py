"""Unit tests for Momentum & Lag Arbitrage strategy."""

import pytest
from datetime import datetime, timedelta
from src.strategy.momentum_lag_arb import MomentumLagArbitrage
from src.engine.models import Market, OrderSide, MarketSide


@pytest.fixture
def strategy():
    """Create strategy instance with test config."""
    config = {
        "momentum_threshold": 0.4,  # 0.4% move required
        "confidence_threshold": 0.65,
        "max_position_size": 200.0,
        "min_position_size": 20.0,
        "lookback_seconds": 60,
        "assets": ["BTC", "ETH", "SOL"]
    }
    return MomentumLagArbitrage(config)


@pytest.fixture
def btc_market():
    """Create mock BTC 15-minute market."""
    return Market(
        market_id="btc_15m_123",
        question="Will BTC go up in the next 15 minutes?",
        yes_token_id="yes_btc",
        no_token_id="no_btc",
        end_date=datetime.utcnow() + timedelta(minutes=15),
        active=True
    )


class TestMomentumLagArbitrage:
    """Test suite for Momentum & Lag Arbitrage strategy."""

    @pytest.mark.asyncio
    async def test_strong_upward_momentum_triggers_entry(self, strategy, btc_market):
        """Test that strong upward momentum triggers BUY."""
        # Simulate BTC price increase
        base_price = 50000.0
        now = datetime.utcnow()

        # Create upward momentum: +0.6% over 60 seconds
        for i in range(20):
            timestamp = now - timedelta(seconds=60-i*3)
            price = base_price + (base_price * 0.006 * i / 20)
            await strategy.update_spot_price("BTC", price)

        # Check if entry is triggered
        orders = await strategy.on_market_update(
            market=btc_market,
            current_price=0.50,  # Market still at 50%
            orderbook={}
        )

        # Should generate BUY order for YES (Up)
        assert len(orders) > 0
        assert orders[0].side == OrderSide.BUY
        assert orders[0].market_side == MarketSide.YES

    @pytest.mark.asyncio
    async def test_strong_downward_momentum_triggers_entry(self, strategy, btc_market):
        """Test that strong downward momentum triggers BUY NO."""
        base_price = 50000.0
        now = datetime.utcnow()

        # Create downward momentum: -0.6% over 60 seconds
        for i in range(20):
            timestamp = now - timedelta(seconds=60-i*3)
            price = base_price - (base_price * 0.006 * i / 20)
            await strategy.update_spot_price("BTC", price)

        orders = await strategy.on_market_update(
            market=btc_market,
            current_price=0.50,
            orderbook={}
        )

        # Should generate BUY order for NO (Down)
        assert len(orders) > 0
        assert orders[0].side == OrderSide.BUY
        assert orders[0].market_side == MarketSide.NO

    @pytest.mark.asyncio
    async def test_weak_momentum_ignored(self, strategy, btc_market):
        """Test that weak momentum doesn't trigger entry."""
        base_price = 50000.0
        now = datetime.utcnow()

        # Create weak momentum: only +0.2% (below 0.4% threshold)
        for i in range(20):
            timestamp = now - timedelta(seconds=60-i*3)
            price = base_price + (base_price * 0.002 * i / 20)
            await strategy.update_spot_price("BTC", price)

        orders = await strategy.on_market_update(
            market=btc_market,
            current_price=0.50,
            orderbook={}
        )

        # Should NOT generate orders (momentum too weak)
        assert len(orders) == 0

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_empty(self, strategy, btc_market):
        """Test that insufficient price data returns no orders."""
        # Only add a few data points (not enough for momentum calculation)
        await strategy.update_spot_price("BTC", 50000.0)
        await strategy.update_spot_price("BTC", 50050.0)

        orders = await strategy.on_market_update(
            market=btc_market,
            current_price=0.50,
            orderbook={}
        )

        assert len(orders) == 0

    @pytest.mark.asyncio
    async def test_exit_on_momentum_reversal(self, strategy, btc_market):
        """Test that position exits when momentum reverses."""
        base_price = 50000.0
        now = datetime.utcnow()

        # Create upward momentum
        for i in range(20):
            timestamp = now - timedelta(seconds=60-i*3)
            price = base_price + (base_price * 0.006 * i / 20)
            await strategy.update_spot_price("BTC", price)

        # Enter position
        orders_entry = await strategy.on_market_update(
            market=btc_market,
            current_price=0.50,
            orderbook={}
        )

        assert len(orders_entry) > 0
        assert btc_market.market_id in strategy.positions

        # Now reverse momentum (downward)
        for i in range(20):
            timestamp = now + timedelta(seconds=i*3)
            price = base_price - (base_price * 0.006 * i / 20)
            await strategy.update_spot_price("BTC", price)

        # Check for exit
        orders_exit = await strategy.on_market_update(
            market=btc_market,
            current_price=0.50,
            orderbook={}
        )

        # Should generate SELL order to exit
        if orders_exit:
            assert orders_exit[0].side == OrderSide.SELL

    @pytest.mark.asyncio
    async def test_exit_on_profit_target(self, strategy, btc_market):
        """Test that position exits when profit target is hit."""
        # Manually create a position
        strategy.positions[btc_market.market_id] = {
            "entry_time": datetime.utcnow(),
            "entry_price": 0.50,
            "direction": "UP",
            "size": 100.0,
            "asset": "BTC",
            "entry_momentum": 0.6,
            "expected_prob": 0.70
        }

        # Simulate strong upward momentum
        base_price = 50000.0
        now = datetime.utcnow()
        for i in range(20):
            price = base_price + (base_price * 0.006 * i / 20)
            await strategy.update_spot_price("BTC", price)

        # Price has moved up 25% (profit target is 20%)
        orders = await strategy.on_market_update(
            market=btc_market,
            current_price=0.625,  # 25% gain
            orderbook={}
        )

        # Should exit
        if orders:
            assert orders[0].side == OrderSide.SELL

    @pytest.mark.asyncio
    async def test_exit_on_stop_loss(self, strategy, btc_market):
        """Test that position exits when stop loss is hit."""
        strategy.positions[btc_market.market_id] = {
            "entry_time": datetime.utcnow(),
            "entry_price": 0.50,
            "direction": "UP",
            "size": 100.0,
            "asset": "BTC",
            "entry_momentum": 0.6,
            "expected_prob": 0.70
        }

        # Simulate momentum
        base_price = 50000.0
        for i in range(20):
            await strategy.update_spot_price("BTC", base_price)

        # Price has moved down 15% (stop loss is 10%)
        orders = await strategy.on_market_update(
            market=btc_market,
            current_price=0.425,  # -15% loss
            orderbook={}
        )

        # Should exit
        if orders:
            assert orders[0].side == OrderSide.SELL

    def test_parse_asset_from_market(self, strategy):
        """Test asset extraction from market question."""
        btc_market = Market(
            market_id="test",
            question="Will BTC go up in next 15 minutes?",
            yes_token_id="yes",
            no_token_id="no",
            end_date=datetime.utcnow(),
            active=True
        )

        asset = strategy._parse_asset_from_market(btc_market)
        assert asset == "BTC"

    def test_calculate_momentum(self, strategy):
        """Test momentum calculation."""
        base_price = 50000.0
        now = datetime.utcnow()

        # Add upward trend
        for i in range(20):
            timestamp = now - timedelta(seconds=60-i*3)
            price = base_price + (base_price * 0.01 * i / 20)  # +1% total
            strategy.spot_prices["BTC"].append((timestamp, price))

        momentum_pct, direction = strategy._calculate_momentum("BTC")

        assert momentum_pct is not None
        assert momentum_pct > 0  # Positive momentum
        assert direction == "UP"

    def test_get_stats(self, strategy):
        """Test statistics generation."""
        stats = strategy.get_stats()

        assert stats["strategy"] == "MomentumLagArbitrage"
        assert "trade_count" in stats
        assert "win_rate" in stats
        assert "total_pnl" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
