"""Sum-to-One Arbitrage Strategy.

In binary markets, YES + NO prices should sum to $1.00.
If the sum is < $0.975 (accounting for 2% fee), we can arbitrage by buying both sides.

Example:
  YES = $0.48, NO = $0.49 → Sum = $0.97
  Cost: $0.97, Payout: $1.00, Gross Profit: $0.03 (3%)
  After 2% fee: Net Profit ~1% ($0.01)

Risk Management:
  - Only trade when spread > min_spread_pct (default 2.5%)
  - Respect max_position_size to limit exposure
  - Monitor gas costs (Polygon)
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from .base import Strategy
from ..engine.models import Order, OrderSide, MarketSide, Market


class SumToOneArbitrage(Strategy):
    """
    Sum-to-One Arbitrage strategy.

    Exploits mispricing where YES + NO != $1.00
    """

    def __init__(self, config: dict = None):
        super().__init__(config)

        # Configuration
        self.min_spread_pct = config.get("min_spread_pct", 2.5)  # Minimum profitable spread
        self.fee_rate = config.get("fee_rate", 0.02)  # 2% winner fee
        self.gas_cost_estimate = config.get("gas_cost", 0.10)  # Polygon gas in USDC
        self.max_position_size = config.get("max_position_size", 500.0)  # Max $ per arb
        self.min_position_size = config.get("min_position_size", 10.0)  # Min $ to bother

        # Calculate breakeven spread (fee + gas as % of position)
        # For $100 position: 2% fee = $2, gas = $0.10 → need ~2.2% spread

        # State tracking
        self.arb_count = 0
        self.total_profit = 0.0
        self.active_arbs = {}  # {market_id: arb_details}

    async def on_market_update(
        self,
        market: Market,
        current_price: float,
        orderbook: dict = None
    ) -> List[Order]:
        """
        Check for sum-to-one arbitrage opportunities.

        Args:
            market: Market object
            current_price: YES token mid price
            orderbook: Full orderbook with bids/asks

        Returns:
            List of orders (YES buy + NO buy if arb exists)
        """
        orders = []

        # Need orderbook to get best bid/ask
        if not orderbook:
            return orders

        # Skip if already have active arb in this market
        if market.market_id in self.active_arbs:
            return orders

        try:
            # Get best prices for YES and NO
            yes_ask = self._get_best_ask(orderbook, "yes")  # Price to BUY YES
            no_ask = self._get_best_ask(orderbook, "no")    # Price to BUY NO

            if yes_ask is None or no_ask is None:
                return orders

            # Calculate sum and spread opportunity
            price_sum = yes_ask + no_ask
            spread_pct = (1.0 - price_sum) * 100  # How much under $1.00

            # Calculate breakeven with dynamic gas cost
            position_size = min(self.max_position_size,
                              self._calculate_optimal_size(spread_pct))

            gas_cost_pct = (self.gas_cost_estimate / position_size) * 100
            breakeven_spread = self.fee_rate * 100 + gas_cost_pct

            # Check if profitable
            if spread_pct < breakeven_spread or spread_pct < self.min_spread_pct:
                return orders

            # Check minimum size
            if position_size < self.min_position_size:
                return orders

            # Calculate expected profit
            gross_profit = position_size * (spread_pct / 100)
            fee_cost = position_size * self.fee_rate
            net_profit = gross_profit - fee_cost - self.gas_cost_estimate

            # Only execute if net profit > $1
            if net_profit < 1.0:
                return orders

            # Create paired orders (buy both YES and NO)
            yes_order = Order(
                market_id=market.market_id,
                token_id=market.yes_token_id,
                side=OrderSide.BUY,
                market_side=MarketSide.YES,
                size=position_size,  # USDC amount
                price=yes_ask,  # Take the ask
                order_type="MARKET"  # Immediate execution
            )

            no_order = Order(
                market_id=market.market_id,
                token_id=market.no_token_id,
                side=OrderSide.BUY,
                market_side=MarketSide.NO,
                size=position_size,  # USDC amount
                price=no_ask,  # Take the ask
                order_type="MARKET"
            )

            orders.extend([yes_order, no_order])

            # Track this arbitrage
            self.active_arbs[market.market_id] = {
                "timestamp": datetime.utcnow(),
                "yes_price": yes_ask,
                "no_price": no_ask,
                "spread_pct": spread_pct,
                "position_size": position_size,
                "expected_profit": net_profit
            }

            self.arb_count += 1

            print(f"🎯 Arb found! {market.question[:50]}...")
            print(f"   YES: ${yes_ask:.3f}, NO: ${no_ask:.3f}, Sum: ${price_sum:.3f}")
            print(f"   Spread: {spread_pct:.2f}%, Size: ${position_size:.2f}")
            print(f"   Expected profit: ${net_profit:.2f}")

        except Exception as e:
            print(f"Error checking arb for {market.market_id}: {e}")

        return orders

    async def on_resolution(self, market_id: str, outcome: str):
        """
        Called when market resolves.
        Calculate actual profit from arbitrage.
        """
        if market_id in self.active_arbs:
            arb = self.active_arbs[market_id]

            # One side wins, one side loses
            # Win: Get $1.00 - 2% fee = $0.98 per dollar
            # Loss: Lose the cost

            yes_cost = arb["position_size"] * arb["yes_price"]
            no_cost = arb["position_size"] * arb["no_price"]
            total_cost = yes_cost + no_cost

            # Winner side gets full payout minus fee
            payout = arb["position_size"] * (1 - self.fee_rate)

            # Profit = Payout - Total Cost
            actual_profit = payout - total_cost

            self.total_profit += actual_profit

            print(f"✅ Arb resolved! Market: {market_id}")
            print(f"   Expected: ${arb['expected_profit']:.2f}")
            print(f"   Actual: ${actual_profit:.2f}")
            print(f"   Total profit: ${self.total_profit:.2f}")

            del self.active_arbs[market_id]

    def _get_best_ask(self, orderbook: dict, side: str) -> Optional[float]:
        """
        Get best ask price (lowest price to buy).

        Args:
            orderbook: Orderbook data structure
            side: "yes" or "no"

        Returns:
            Best ask price or None
        """
        try:
            # Orderbook structure varies by API
            # Typically: {"bids": [...], "asks": [...]}
            asks = orderbook.get(f"{side}_asks", orderbook.get("asks", []))

            if not asks:
                return None

            # Asks are sorted lowest to highest
            # Format: [{"price": 0.48, "size": 100}, ...]
            best_ask = asks[0]
            return float(best_ask.get("price", best_ask.get("p", 0)))

        except (KeyError, IndexError, ValueError):
            return None

    def _calculate_optimal_size(self, spread_pct: float) -> float:
        """
        Calculate optimal position size based on spread.
        Larger spreads = larger positions (more confidence).

        Args:
            spread_pct: Spread percentage

        Returns:
            Optimal position size in USDC
        """
        # Scale position size with spread
        # 2.5% spread → min size
        # 5%+ spread → max size

        if spread_pct <= self.min_spread_pct:
            return self.min_position_size

        # Linear scaling
        scale_factor = min(1.0, (spread_pct - self.min_spread_pct) / 2.5)

        size_range = self.max_position_size - self.min_position_size
        optimal_size = self.min_position_size + (size_range * scale_factor)

        return round(optimal_size, 2)

    def get_stats(self) -> dict:
        """Get strategy statistics."""
        return {
            "strategy": "SumToOneArbitrage",
            "arb_count": self.arb_count,
            "active_arbs": len(self.active_arbs),
            "total_profit": round(self.total_profit, 2),
            "avg_profit_per_arb": round(self.total_profit / max(1, self.arb_count), 2),
            "config": {
                "min_spread_pct": self.min_spread_pct,
                "fee_rate": self.fee_rate,
                "max_position_size": self.max_position_size
            }
        }
