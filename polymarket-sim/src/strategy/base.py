"""Base strategy interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..engine.models import Order, Portfolio, Market


class Strategy(ABC):
    """Base class for trading strategies."""

    def __init__(self, config: dict = None):
        """
        Initialize strategy.

        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    async def on_market_update(
        self,
        market: Market,
        current_price: float,
        orderbook: dict = None
    ) -> list[Order]:
        """
        Called when market data updates.

        Args:
            market: Market object
            current_price: Current mid price
            orderbook: Optional orderbook data

        Returns:
            List of orders to execute (or empty list)
        """
        pass

    async def on_resolution(self, market_id: str, outcome: str):
        """
        Called when a market resolves.

        Args:
            market_id: Resolved market ID
            outcome: Resolution outcome ("YES" or "NO")
        """
        pass

    async def on_portfolio_update(self, portfolio: Portfolio):
        """
        Called after portfolio changes.

        Args:
            portfolio: Updated portfolio state
        """
        pass

    async def on_fill(self, fill):
        """
        Called when an order fills.

        Args:
            fill: Fill object
        """
        pass

    def get_name(self) -> str:
        """Get strategy name."""
        return self.name

    def get_config(self) -> dict:
        """Get strategy configuration."""
        return self.config
