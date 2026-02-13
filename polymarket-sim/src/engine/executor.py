"""Simulation execution engine for order matching and fills."""

from datetime import datetime, timedelta
from typing import Optional
import asyncio

from .models import (
    Order, Fill, OrderSide, OrderStatus, MarketSide,
    Orderbook
)
from ..data.clob import CLOBClient
from ..storage.db import Database


class ExecutionEngine:
    """Simulated execution engine."""

    def __init__(
        self,
        clob_client: CLOBClient,
        db: Database,
        slippage_factor: float = 0.001,
        fee_rate: float = 0.02,
        order_ttl_hours: int = 24
    ):
        self.clob = clob_client
        self.db = db
        self.slippage_factor = slippage_factor
        self.fee_rate = fee_rate
        self.order_ttl_hours = order_ttl_hours

        # Callbacks for execution events
        self.on_fill: Optional[callable] = None
        self.on_reject: Optional[callable] = None

    async def submit_order(self, order: Order, portfolio_balance: float) -> Order:
        """
        Submit order for execution.

        Args:
            order: Order to execute
            portfolio_balance: Current portfolio balance

        Returns:
            Updated order with status
        """
        # Check balance
        if order.side == OrderSide.BUY:
            required_balance = order.size
            if required_balance > portfolio_balance:
                order.status = OrderStatus.REJECTED
                await self.db.save_order(order)
                if self.on_reject:
                    await self.on_reject(order, "Insufficient balance")
                return order

        # Get orderbook
        orderbook = await self.clob.get_orderbook(order.token_id, order.market_id)
        if not orderbook:
            order.status = OrderStatus.REJECTED
            await self.db.save_order(order)
            if self.on_reject:
                await self.on_reject(order, "No orderbook data")
            return order

        # Attempt to match order
        fill_result = await self._match_order(order, orderbook)

        if fill_result:
            # Order filled (fully or partially)
            fill, filled_size, avg_price = fill_result

            order.filled_size += filled_size
            order.avg_fill_price = avg_price

            if order.filled_size >= order.size:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIAL

            # Save fill and order
            await self.db.save_fill(fill)
            await self.db.save_order(order)

            # Call callback
            if self.on_fill:
                await self.on_fill(fill)

        else:
            # Order cannot be filled immediately - mark as resting
            order.status = OrderStatus.RESTING
            order.expires_at = datetime.utcnow() + timedelta(hours=self.order_ttl_hours)
            await self.db.save_order(order)

        return order

    async def _match_order(
        self,
        order: Order,
        orderbook: Orderbook
    ) -> Optional[tuple[Fill, float, float]]:
        """
        Match order against orderbook.

        Returns:
            Tuple of (Fill, filled_size, avg_fill_price) or None
        """
        if order.side == OrderSide.BUY:
            return await self._match_buy_order(order, orderbook)
        else:
            return await self._match_sell_order(order, orderbook)

    async def _match_buy_order(
        self,
        order: Order,
        orderbook: Orderbook
    ) -> Optional[tuple[Fill, float, float]]:
        """Match a buy order against asks."""
        if not orderbook.asks:
            return None

        best_ask = orderbook.best_ask
        if best_ask is None or order.price < best_ask:
            # Price not competitive, order rests
            return None

        # Calculate how much can be filled
        remaining_size = order.remaining_size
        filled_size = 0.0
        total_cost = 0.0

        for ask_level in orderbook.asks:
            if ask_level.price > order.price:
                break  # No more levels within our price

            available_at_level = ask_level.size * ask_level.price  # Size in USDC
            fill_at_level = min(remaining_size, available_at_level)

            filled_size += fill_at_level
            total_cost += fill_at_level
            remaining_size -= fill_at_level

            if remaining_size <= 0:
                break

        if filled_size <= 0:
            return None

        # Calculate average fill price and shares
        avg_fill_price = total_cost / filled_size if filled_size > 0 else 0
        shares = filled_size / avg_fill_price if avg_fill_price > 0 else 0

        # Apply slippage
        slippage = filled_size * self.slippage_factor
        avg_fill_price *= (1 + self.slippage_factor)

        # Calculate fees
        fee = filled_size * self.fee_rate

        # Create fill
        fill = Fill(
            order_id=order.order_id,
            market_id=order.market_id,
            token_id=order.token_id,
            side=order.side,
            market_side=order.market_side,
            shares=shares,
            price=avg_fill_price,
            size=filled_size,
            fee=fee,
            slippage=slippage,
            timestamp=datetime.utcnow()
        )

        return (fill, filled_size, avg_fill_price)

    async def _match_sell_order(
        self,
        order: Order,
        orderbook: Orderbook
    ) -> Optional[tuple[Fill, float, float]]:
        """Match a sell order against bids."""
        if not orderbook.bids:
            return None

        best_bid = orderbook.best_bid
        if best_bid is None or order.price > best_bid:
            # Price not competitive, order rests
            return None

        # For sell orders, size is in shares not USDC
        # We need to convert
        shares_to_sell = order.shares
        filled_shares = 0.0
        total_proceeds = 0.0

        for bid_level in orderbook.bids:
            if bid_level.price < order.price:
                break  # No more levels within our price

            # Convert bid size (USDC) to shares at this price
            available_shares_at_level = bid_level.size / bid_level.price if bid_level.price > 0 else 0
            remaining_shares = shares_to_sell - filled_shares
            fill_shares = min(remaining_shares, available_shares_at_level)

            filled_shares += fill_shares
            total_proceeds += fill_shares * bid_level.price

            if filled_shares >= shares_to_sell:
                break

        if filled_shares <= 0:
            return None

        # Calculate average fill price
        avg_fill_price = total_proceeds / filled_shares if filled_shares > 0 else 0
        filled_size = total_proceeds

        # Apply slippage (reduces proceeds for sells)
        slippage = filled_size * self.slippage_factor
        avg_fill_price *= (1 - self.slippage_factor)
        filled_size -= slippage

        # Calculate fees
        fee = filled_size * self.fee_rate

        # Create fill
        fill = Fill(
            order_id=order.order_id,
            market_id=order.market_id,
            token_id=order.token_id,
            side=order.side,
            market_side=order.market_side,
            shares=filled_shares,
            price=avg_fill_price,
            size=filled_size,
            fee=fee,
            slippage=slippage,
            timestamp=datetime.utcnow()
        )

        return (fill, filled_size, avg_fill_price)

    async def check_resting_orders(self, portfolio_balance: float):
        """
        Check resting orders and attempt to fill them.
        Expire old orders.
        """
        resting_orders = await self.db.get_resting_orders()
        now = datetime.utcnow()

        for order in resting_orders:
            # Check if expired
            if order.expires_at and order.expires_at < now:
                order.status = OrderStatus.EXPIRED
                await self.db.save_order(order)
                continue

            # Try to fill
            orderbook = await self.clob.get_orderbook(order.token_id, order.market_id)
            if orderbook:
                fill_result = await self._match_order(order, orderbook)

                if fill_result:
                    fill, filled_size, avg_price = fill_result

                    order.filled_size += filled_size
                    order.avg_fill_price = avg_price

                    if order.filled_size >= order.size:
                        order.status = OrderStatus.FILLED
                    else:
                        order.status = OrderStatus.PARTIAL

                    await self.db.save_fill(fill)
                    await self.db.save_order(order)

                    if self.on_fill:
                        await self.on_fill(fill)

    def set_fill_callback(self, callback: callable):
        """Set callback for fill events."""
        self.on_fill = callback

    def set_reject_callback(self, callback: callable):
        """Set callback for rejection events."""
        self.on_reject = callback
