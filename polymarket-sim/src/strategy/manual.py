"""Manual strategy - accepts orders from terminal input."""

import asyncio
from typing import Optional

from .base import Strategy
from ..engine.models import Order, OrderSide, MarketSide, Market


class Manual(Strategy):
    """
    Manual strategy for human-in-the-loop trading.

    Waits for user input from terminal to generate orders.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.pending_orders: list[Order] = []

    async def on_market_update(
        self,
        market: Market,
        current_price: float,
        orderbook: dict = None
    ) -> list[Order]:
        """Return any pending orders."""
        orders = self.pending_orders.copy()
        self.pending_orders.clear()
        return orders

    def add_order(
        self,
        market_id: str,
        token_id: str,
        side: OrderSide,
        market_side: MarketSide,
        size: float,
        price: float
    ):
        """
        Add an order to be executed on next market update.

        Args:
            market_id: Market ID
            token_id: Token ID
            side: BUY or SELL
            market_side: YES or NO
            size: Order size in USDC
            price: Limit price
        """
        order = Order(
            market_id=market_id,
            token_id=token_id,
            side=side,
            market_side=market_side,
            size=size,
            price=price
        )
        self.pending_orders.append(order)

    def has_pending_orders(self) -> bool:
        """Check if there are pending orders."""
        return len(self.pending_orders) > 0
