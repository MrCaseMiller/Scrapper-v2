"""Mean reversion strategy implementation."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from .base import Strategy
from ..engine.models import Order, OrderSide, MarketSide, Market


class MeanReversion(Strategy):
    """
    Mean reversion strategy.

    Tracks historical prices and trades when current price
    deviates significantly from the mean.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.lookback_periods = config.get("lookback_periods", 24)  # hours
        self.deviation_threshold = config.get("deviation_threshold", 0.15)
        self.position_size = config.get("position_size", 100.0)

        # Price history: {token_id: [(timestamp, price), ...]}
        self.price_history: dict[str, list[tuple[datetime, float]]] = defaultdict(list)

        # Track positions
        self.positions: dict[str, float] = {}

    async def on_market_update(
        self,
        market: Market,
        current_price: float,
        orderbook: dict = None
    ) -> list[Order]:
        """Generate orders based on mean reversion."""
        orders = []

        token_id = market.yes_token_id
        market_id = market.market_id

        # Update price history
        now = datetime.utcnow()
        self.price_history[token_id].append((now, current_price))

        # Clean old data
        cutoff = now - timedelta(hours=self.lookback_periods)
        self.price_history[token_id] = [
            (ts, price) for ts, price in self.price_history[token_id]
            if ts > cutoff
        ]

        # Need at least 10 data points
        if len(self.price_history[token_id]) < 10:
            return orders

        # Calculate mean
        prices = [p for _, p in self.price_history[token_id]]
        mean_price = sum(prices) / len(prices)

        # Calculate deviation
        deviation = (current_price - mean_price) / mean_price if mean_price > 0 else 0

        # Check if we have a position
        has_position = token_id in self.positions and self.positions[token_id] > 0

        # Buy signal: price significantly below mean and no position
        if deviation < -self.deviation_threshold and not has_position:
            order = Order(
                market_id=market_id,
                token_id=token_id,
                side=OrderSide.BUY,
                market_side=MarketSide.YES,
                size=self.position_size,
                price=current_price * 1.02  # Limit slightly above current
            )
            orders.append(order)

        # Sell signal: price significantly above mean and have position
        elif deviation > self.deviation_threshold and has_position:
            shares = self.positions[token_id]
            order = Order(
                market_id=market_id,
                token_id=token_id,
                side=OrderSide.SELL,
                market_side=MarketSide.YES,
                size=shares * current_price,
                price=current_price * 0.98  # Limit slightly below current
            )
            orders.append(order)

        return orders

    async def on_portfolio_update(self, portfolio):
        """Update internal position tracking."""
        self.positions.clear()
        for token_id, position in portfolio.positions.items():
            self.positions[token_id] = position.shares
