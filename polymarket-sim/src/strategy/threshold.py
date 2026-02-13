"""Naive threshold strategy implementation."""

from datetime import datetime
from typing import Optional

from .base import Strategy
from ..engine.models import Order, OrderSide, MarketSide, Market


class NaiveThreshold(Strategy):
    """
    Simple threshold-based strategy.

    Buys YES when price drops below threshold.
    Sells YES when price rises above threshold.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.buy_below = config.get("buy_below", 0.3)
        self.sell_above = config.get("sell_above", 0.7)
        self.position_size = config.get("position_size", 100.0)

        # Track positions by token_id
        self.positions: dict[str, float] = {}

    async def on_market_update(
        self,
        market: Market,
        current_price: float,
        orderbook: dict = None
    ) -> list[Order]:
        """Generate orders based on price thresholds."""
        orders = []

        # Only trade on YES tokens for simplicity
        token_id = market.yes_token_id
        market_id = market.market_id

        # Check if we have a position
        has_position = token_id in self.positions and self.positions[token_id] > 0

        # Buy signal: price below buy threshold and no position
        if current_price < self.buy_below and not has_position:
            order = Order(
                market_id=market_id,
                token_id=token_id,
                side=OrderSide.BUY,
                market_side=MarketSide.YES,
                size=self.position_size,
                price=self.buy_below  # Limit price
            )
            orders.append(order)

        # Sell signal: price above sell threshold and have position
        elif current_price > self.sell_above and has_position:
            shares = self.positions[token_id]
            order = Order(
                market_id=market_id,
                token_id=token_id,
                side=OrderSide.SELL,
                market_side=MarketSide.YES,
                size=shares * current_price,  # Approximate size in USDC
                price=self.sell_above  # Limit price
            )
            orders.append(order)

        return orders

    async def on_portfolio_update(self, portfolio):
        """Update internal position tracking."""
        self.positions.clear()
        for token_id, position in portfolio.positions.items():
            self.positions[token_id] = position.shares
