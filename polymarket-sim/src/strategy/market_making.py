"""Market Making Strategy.

Provides liquidity by placing simultaneous buy and sell orders,
profiting from the bid-ask spread.

How it works:
1. Place BUY limit order at $0.50 (bid)
2. Place SELL limit order at $0.52 (ask)
3. Earn $0.02 spread when both fill
4. Repeat continuously

Risk Management:
1. Inventory Skewing: Adjust prices based on current inventory
   - If holding too many YES shares → lower bid, raise ask (encourage selling)
   - If short YES shares → raise bid, lower ask (encourage buying back)

2. Adverse Selection: Avoid getting "picked off" by informed traders
   - Monitor for sudden price movements
   - Widen spreads during high volatility
   - Pull quotes when major news events occur

3. Position Limits: Cap max inventory to limit directional exposure

Example:
  Neutral inventory:
    - BUY @ $0.495, SELL @ $0.505 (1% spread)

  Long inventory (holding +100 YES):
    - BUY @ $0.490, SELL @ $0.510 (2% spread, skewed to sell)

  Short inventory (holding -50 YES):
    - BUY @ $0.500, SELL @ $0.500 (0% spread, need to buy back urgently)
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from collections import deque

from .base import Strategy
from ..engine.models import Order, OrderSide, MarketSide, Market, Portfolio


class MarketMaking(Strategy):
    """
    Market making strategy with inventory management.

    Provides liquidity and earns bid-ask spread.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)

        # Spread configuration
        self.base_spread = config.get("base_spread", 0.02)  # 2% base spread
        self.min_spread = config.get("min_spread", 0.005)  # 0.5% minimum
        self.max_spread = config.get("max_spread", 0.05)  # 5% maximum

        # Position sizing
        self.order_size = config.get("order_size", 100.0)  # $ per order
        self.max_inventory = config.get("max_inventory", 500.0)  # Max $ inventory
        self.target_inventory = config.get("target_inventory", 0.0)  # Ideal = neutral

        # Risk management
        self.volatility_multiplier = config.get("volatility_multiplier", 2.0)
        self.skew_factor = config.get("skew_factor", 0.01)  # 1% price skew per $100 inventory
        self.quote_ttl_seconds = config.get("quote_ttl", 60)  # Refresh quotes every minute

        # State tracking
        self.inventory: Dict[str, float] = {}  # {token_id: shares}
        self.active_quotes: Dict[str, dict] = {}  # {market_id: quote_info}
        self.price_history: Dict[str, deque] = {}  # For volatility calculation

        # Performance
        self.total_spread_earned = 0.0
        self.fill_count = 0
        self.adverse_selection_count = 0  # Times we got picked off

    async def on_market_update(
        self,
        market: Market,
        current_price: float,
        orderbook: dict = None
    ) -> List[Order]:
        """
        Update market making quotes.

        Args:
            market: Market object
            current_price: Current mid price
            orderbook: Full orderbook

        Returns:
            List of limit orders (buy + sell)
        """
        orders = []

        # Update price history for volatility calculation
        self._update_price_history(market.yes_token_id, current_price)

        # Check if we need to refresh quotes
        if not self._should_update_quotes(market.market_id):
            return orders

        # Calculate current inventory
        inventory_value = self._get_inventory_value(market.yes_token_id, current_price)

        # Check inventory limits
        if abs(inventory_value) > self.max_inventory:
            # Too much inventory - only quote on the reducing side
            return self._inventory_reduction_quotes(
                market, current_price, inventory_value
            )

        # Calculate volatility adjustment
        volatility = self._calculate_volatility(market.yes_token_id)
        volatility_adjustment = min(2.0, volatility * self.volatility_multiplier)

        # Calculate inventory skew
        skew = self._calculate_inventory_skew(inventory_value)

        # Calculate bid-ask spread
        spread = self.base_spread * volatility_adjustment
        spread = max(self.min_spread, min(self.max_spread, spread))

        # Calculate bid and ask prices with skew
        mid_price = current_price
        half_spread = spread / 2

        bid_price = mid_price - half_spread - skew
        ask_price = mid_price + half_spread - skew

        # Ensure prices are valid [0.01, 0.99]
        bid_price = max(0.01, min(0.98, bid_price))
        ask_price = max(0.02, min(0.99, ask_price))

        # Ensure bid < ask
        if bid_price >= ask_price:
            mid = (bid_price + ask_price) / 2
            bid_price = mid - 0.01
            ask_price = mid + 0.01

        # Create buy order (bid)
        buy_order = Order(
            market_id=market.market_id,
            token_id=market.yes_token_id,
            side=OrderSide.BUY,
            market_side=MarketSide.YES,
            size=self.order_size,
            price=bid_price,
            order_type="LIMIT",
            ttl_seconds=self.quote_ttl_seconds
        )

        # Create sell order (ask)
        sell_order = Order(
            market_id=market.market_id,
            token_id=market.yes_token_id,
            side=OrderSide.SELL,
            market_side=MarketSide.YES,
            size=self.order_size,
            price=ask_price,
            order_type="LIMIT",
            ttl_seconds=self.quote_ttl_seconds
        )

        orders.extend([buy_order, sell_order])

        # Track active quotes
        self.active_quotes[market.market_id] = {
            "timestamp": datetime.utcnow(),
            "bid": bid_price,
            "ask": ask_price,
            "spread": spread,
            "mid": mid_price,
            "inventory": inventory_value,
            "skew": skew
        }

        print(f"📊 MM Quote: {market.question[:40]}...")
        print(f"   Bid: ${bid_price:.4f}, Ask: ${ask_price:.4f}, Spread: {spread:.2%}")
        print(f"   Inventory: ${inventory_value:+.2f}, Skew: {skew:+.4f}")

        return orders

    async def on_fill(self, fill):
        """
        Called when one of our orders fills.
        Update inventory and calculate spread earned.
        """
        token_id = fill.token_id
        side = fill.side
        price = fill.price
        size = fill.size

        # Update inventory
        shares_change = size / price  # Convert USDC to shares

        if side == OrderSide.BUY:
            self.inventory[token_id] = self.inventory.get(token_id, 0) + shares_change
        else:  # SELL
            self.inventory[token_id] = self.inventory.get(token_id, 0) - shares_change

        self.fill_count += 1

        # Check if we earned spread (bought and sold around mid)
        market_id = fill.market_id
        if market_id in self.active_quotes:
            quote = self.active_quotes[market_id]
            mid = quote["mid"]

            if side == OrderSide.BUY and price < mid:
                spread_earned = (mid - price) * shares_change
                self.total_spread_earned += spread_earned
                print(f"💰 Spread earned: ${spread_earned:.2f} (buy below mid)")

            elif side == OrderSide.SELL and price > mid:
                spread_earned = (price - mid) * shares_change
                self.total_spread_earned += spread_earned
                print(f"💰 Spread earned: ${spread_earned:.2f} (sell above mid)")

        print(f"✅ Fill: {side.value} {shares_change:.2f} shares @ ${price:.4f}")
        print(f"   New inventory: {self.inventory.get(token_id, 0):.2f} shares")

    async def on_portfolio_update(self, portfolio: Portfolio):
        """Update inventory from portfolio."""
        self.inventory.clear()

        for token_id, position in portfolio.positions.items():
            self.inventory[token_id] = position.shares

    def _should_update_quotes(self, market_id: str) -> bool:
        """Check if quotes need refreshing."""
        if market_id not in self.active_quotes:
            return True

        quote = self.active_quotes[market_id]
        age = (datetime.utcnow() - quote["timestamp"]).seconds

        return age >= self.quote_ttl_seconds

    def _update_price_history(self, token_id: str, price: float):
        """Track price history for volatility calculation."""
        if token_id not in self.price_history:
            self.price_history[token_id] = deque(maxlen=60)  # 1 min history

        self.price_history[token_id].append((datetime.utcnow(), price))

    def _calculate_volatility(self, token_id: str) -> float:
        """
        Calculate recent price volatility.

        Returns:
            Volatility multiplier (1.0 = normal, 2.0 = high)
        """
        if token_id not in self.price_history:
            return 1.0

        prices = [p for _, p in self.price_history[token_id]]

        if len(prices) < 10:
            return 1.0

        # Calculate price range as % of mid
        min_price = min(prices)
        max_price = max(prices)
        mid_price = (min_price + max_price) / 2

        if mid_price == 0:
            return 1.0

        volatility = (max_price - min_price) / mid_price

        # Normalize to 1.0-3.0 range
        return 1.0 + min(2.0, volatility * 10)

    def _get_inventory_value(self, token_id: str, current_price: float) -> float:
        """Calculate inventory value in USDC."""
        shares = self.inventory.get(token_id, 0)
        return shares * current_price

    def _calculate_inventory_skew(self, inventory_value: float) -> float:
        """
        Calculate price skew based on inventory.

        Positive inventory (long) → negative skew (lower prices to encourage selling)
        Negative inventory (short) → positive skew (raise prices to encourage buying)

        Args:
            inventory_value: Current inventory in USDC

        Returns:
            Price skew (added to both bid and ask)
        """
        # Skew proportional to inventory
        # $100 inventory → -1% price adjustment
        skew = -(inventory_value / 100) * self.skew_factor

        # Cap skew at ±5%
        return max(-0.05, min(0.05, skew))

    def _inventory_reduction_quotes(
        self,
        market: Market,
        current_price: float,
        inventory_value: float
    ) -> List[Order]:
        """
        Generate aggressive quotes to reduce inventory.

        If long (positive inventory): Only quote sell side at tight spread
        If short (negative inventory): Only quote buy side at tight spread
        """
        orders = []

        if inventory_value > 0:
            # Long - need to sell
            ask_price = current_price - 0.01  # Aggressive ask

            sell_order = Order(
                market_id=market.market_id,
                token_id=market.yes_token_id,
                side=OrderSide.SELL,
                market_side=MarketSide.YES,
                size=min(abs(inventory_value), self.order_size),
                price=max(0.01, ask_price),
                order_type="LIMIT"
            )
            orders.append(sell_order)

            print(f"⚠️  Reducing long inventory: selling @ ${ask_price:.4f}")

        else:
            # Short - need to buy
            bid_price = current_price + 0.01  # Aggressive bid

            buy_order = Order(
                market_id=market.market_id,
                token_id=market.yes_token_id,
                side=OrderSide.BUY,
                market_side=MarketSide.YES,
                size=min(abs(inventory_value), self.order_size),
                price=min(0.99, bid_price),
                order_type="LIMIT"
            )
            orders.append(buy_order)

            print(f"⚠️  Reducing short inventory: buying @ ${bid_price:.4f}")

        return orders

    def get_stats(self) -> dict:
        """Get strategy statistics."""
        total_inventory_value = sum(self.inventory.values())

        return {
            "strategy": "MarketMaking",
            "fill_count": self.fill_count,
            "total_spread_earned": round(self.total_spread_earned, 2),
            "avg_spread_per_fill": round(
                self.total_spread_earned / max(1, self.fill_count), 4
            ),
            "active_quotes": len(self.active_quotes),
            "inventory_count": len(self.inventory),
            "total_inventory_value": round(total_inventory_value, 2),
            "adverse_selection_count": self.adverse_selection_count
        }
