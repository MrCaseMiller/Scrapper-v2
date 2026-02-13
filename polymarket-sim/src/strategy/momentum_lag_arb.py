"""Momentum & Lag Arbitrage Strategy for 15-Minute Markets.

Exploits latency between spot crypto exchanges (Binance, Coinbase) and
Polymarket's 15-minute Up/Down prediction markets.

How it works:
1. Monitor BTC/ETH/SOL prices on high-liquidity spot exchanges
2. Detect rapid price movements (momentum)
3. Front-run Polymarket market adjustments by buying before the lag catches up

Example:
  - BTC jumps +0.5% on Binance in 5 seconds
  - Polymarket "BTC-15m-Up" market still shows 50% probability
  - Bot buys "Up" shares before market adjusts to ~70%
  - Profit when market catches up to reality

Risk Management:
  - Only trade on strong momentum signals (> threshold)
  - Use position sizing based on confidence
  - Exit quickly if momentum reverses
  - Track exchange latency to ensure edge exists
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from collections import deque
import asyncio

from .base import Strategy
from ..engine.models import Order, OrderSide, MarketSide, Market


class MomentumLagArbitrage(Strategy):
    """
    Momentum/Lag Arbitrage for 15-minute crypto prediction markets.

    Monitors spot exchanges and front-runs Polymarket price adjustments.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)

        # Strategy configuration
        self.momentum_threshold = config.get("momentum_threshold", 0.4)  # 0.4% move
        self.confidence_threshold = config.get("confidence_threshold", 0.65)  # 65%+
        self.max_position_size = config.get("max_position_size", 200.0)
        self.min_position_size = config.get("min_position_size", 20.0)
        self.exit_threshold = config.get("exit_threshold", 0.15)  # Exit if momentum < 0.15%
        self.lookback_seconds = config.get("lookback_seconds", 60)  # 1 min window

        # Asset tracking
        self.supported_assets = config.get("assets", ["BTC", "ETH", "SOL"])

        # Price history from spot exchanges
        # {asset: deque([(timestamp, price), ...])}
        self.spot_prices: Dict[str, deque] = {
            asset: deque(maxlen=120)  # 2 minutes at 1s resolution
            for asset in self.supported_assets
        }

        # Current positions {market_id: position_info}
        self.positions: Dict[str, dict] = {}

        # Performance tracking
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0.0

        # Latency tracking (how fast is our edge?)
        self.avg_latency_ms = config.get("expected_latency_ms", 500)  # 500ms edge

    async def update_spot_price(self, asset: str, price: float):
        """
        Update spot price from external exchange.
        Call this from exchange WebSocket feed.

        Args:
            asset: Asset symbol (BTC, ETH, SOL)
            price: Current spot price
        """
        if asset not in self.spot_prices:
            return

        self.spot_prices[asset].append((datetime.utcnow(), price))

    async def on_market_update(
        self,
        market: Market,
        current_price: float,
        orderbook: dict = None
    ) -> List[Order]:
        """
        Check for momentum lag arbitrage opportunities.

        Args:
            market: Polymarket 15-minute market
            current_price: Current YES (Up) probability
            orderbook: Order book data

        Returns:
            List of orders to execute
        """
        orders = []

        # Parse market to identify asset (BTC, ETH, SOL)
        asset = self._parse_asset_from_market(market)
        if not asset or asset not in self.supported_assets:
            return orders

        # Calculate current momentum from spot prices
        momentum_pct, direction = self._calculate_momentum(asset)

        if momentum_pct is None:
            return orders  # Not enough data

        # Check if we already have a position
        has_position = market.market_id in self.positions

        # Entry logic
        if not has_position:
            orders.extend(
                await self._check_entry(
                    market, current_price, momentum_pct, direction, asset
                )
            )

        # Exit logic
        else:
            orders.extend(
                await self._check_exit(
                    market, current_price, momentum_pct, direction
                )
            )

        return orders

    async def _check_entry(
        self,
        market: Market,
        current_price: float,
        momentum_pct: float,
        direction: str,
        asset: str
    ) -> List[Order]:
        """Check if we should enter a position."""
        orders = []

        # Need strong momentum
        if abs(momentum_pct) < self.momentum_threshold:
            return orders

        # Calculate expected probability based on momentum
        # Simple heuristic: 0.5% momentum → ~70% probability of continuing
        expected_prob = self._momentum_to_probability(momentum_pct, direction)

        # Calculate edge (mispricing)
        if direction == "UP":
            edge = expected_prob - current_price
            market_side = MarketSide.YES
        else:
            edge = expected_prob - (1 - current_price)
            market_side = MarketSide.NO

        # Only trade if edge is significant
        if edge < 0.1:  # Need at least 10% edge
            return orders

        # Calculate confidence (higher momentum = higher confidence)
        confidence = min(0.95, 0.5 + (abs(momentum_pct) / 2.0))

        if confidence < self.confidence_threshold:
            return orders

        # Position sizing based on confidence and edge
        position_size = self._calculate_position_size(confidence, edge)

        # Create order
        order = Order(
            market_id=market.market_id,
            token_id=market.yes_token_id if direction == "UP" else market.no_token_id,
            side=OrderSide.BUY,
            market_side=market_side,
            size=position_size,
            price=current_price if direction == "UP" else (1 - current_price),
            order_type="MARKET"
        )

        orders.append(order)

        # Track position
        self.positions[market.market_id] = {
            "entry_time": datetime.utcnow(),
            "entry_price": current_price,
            "direction": direction,
            "size": position_size,
            "asset": asset,
            "entry_momentum": momentum_pct,
            "expected_prob": expected_prob
        }

        print(f"🚀 Momentum trade: {asset} {direction}")
        print(f"   Momentum: {momentum_pct:+.2f}%, Edge: {edge:.2%}")
        print(f"   Entry: ${current_price:.3f}, Size: ${position_size:.2f}")

        return orders

    async def _check_exit(
        self,
        market: Market,
        current_price: float,
        momentum_pct: float,
        direction: str
    ) -> List[Order]:
        """Check if we should exit current position."""
        orders = []

        position = self.positions.get(market.market_id)
        if not position:
            return orders

        should_exit = False
        exit_reason = ""

        # Exit reason 1: Momentum reversed
        if direction != position["direction"]:
            should_exit = True
            exit_reason = "Momentum reversed"

        # Exit reason 2: Momentum weakened significantly
        elif abs(momentum_pct) < self.exit_threshold:
            should_exit = True
            exit_reason = "Momentum weakened"

        # Exit reason 3: Profit target hit (20% move in our favor)
        profit_pct = (current_price - position["entry_price"]) / position["entry_price"]
        if position["direction"] == "UP" and profit_pct > 0.20:
            should_exit = True
            exit_reason = "Profit target hit"
        elif position["direction"] == "DOWN" and profit_pct < -0.20:
            should_exit = True
            exit_reason = "Profit target hit"

        # Exit reason 4: Stop loss (-10% move against us)
        if position["direction"] == "UP" and profit_pct < -0.10:
            should_exit = True
            exit_reason = "Stop loss"
        elif position["direction"] == "DOWN" and profit_pct > 0.10:
            should_exit = True
            exit_reason = "Stop loss"

        # Exit reason 5: Market about to expire (< 2 min left)
        time_in_trade = (datetime.utcnow() - position["entry_time"]).seconds
        if time_in_trade > 13 * 60:  # 13 minutes (market is 15 min)
            should_exit = True
            exit_reason = "Time expiration"

        if should_exit:
            # Create exit order (sell our position)
            market_side = MarketSide.YES if position["direction"] == "UP" else MarketSide.NO

            order = Order(
                market_id=market.market_id,
                token_id=market.yes_token_id if position["direction"] == "UP" else market.no_token_id,
                side=OrderSide.SELL,
                market_side=market_side,
                size=position["size"],
                price=current_price,
                order_type="MARKET"
            )

            orders.append(order)

            # Calculate P&L
            entry = position["entry_price"]
            pnl = position["size"] * (current_price - entry) / entry

            self.total_pnl += pnl
            self.trade_count += 1
            if pnl > 0:
                self.win_count += 1

            print(f"📤 Exit {position['asset']} position: {exit_reason}")
            print(f"   Entry: ${entry:.3f}, Exit: ${current_price:.3f}")
            print(f"   P&L: ${pnl:+.2f}, Win rate: {self.win_count}/{self.trade_count}")

            del self.positions[market.market_id]

        return orders

    def _calculate_momentum(self, asset: str) -> tuple[Optional[float], Optional[str]]:
        """
        Calculate price momentum from spot exchange data.

        Returns:
            (momentum_pct, direction) or (None, None)
        """
        prices = self.spot_prices.get(asset, [])

        if len(prices) < 10:
            return None, None

        # Get recent prices within lookback window
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.lookback_seconds)

        recent = [(ts, p) for ts, p in prices if ts > cutoff]

        if len(recent) < 2:
            return None, None

        # Calculate momentum as % change from start to end of window
        start_price = recent[0][1]
        end_price = recent[-1][1]

        momentum_pct = ((end_price - start_price) / start_price) * 100
        direction = "UP" if momentum_pct > 0 else "DOWN"

        return momentum_pct, direction

    def _momentum_to_probability(self, momentum_pct: float, direction: str) -> float:
        """
        Convert momentum % to expected probability.

        Simple model:
          0.5% momentum → 70% prob
          1.0% momentum → 80% prob
          2.0% momentum → 90% prob
        """
        abs_momentum = abs(momentum_pct)

        # Logistic-like curve
        base_prob = 0.5
        boost = min(0.45, abs_momentum / 2.0 * 0.4)

        return base_prob + boost

    def _calculate_position_size(self, confidence: float, edge: float) -> float:
        """Calculate position size using Kelly-like criterion."""
        # Kelly fraction: f = (confidence * edge) / edge = confidence
        # Use fractional Kelly for safety (1/4 Kelly)

        kelly_fraction = confidence * 0.25

        size_range = self.max_position_size - self.min_position_size
        position_size = self.min_position_size + (size_range * kelly_fraction)

        return round(position_size, 2)

    def _parse_asset_from_market(self, market: Market) -> Optional[str]:
        """
        Extract asset from market question.

        Examples:
          "BTC 15-Min Up or Down?" → BTC
          "Will ETH go up in next 15 min?" → ETH
        """
        question = market.question.upper()

        for asset in self.supported_assets:
            if asset in question:
                return asset

        return None

    async def on_resolution(self, market_id: str, outcome: str):
        """Market resolved - calculate final P&L."""
        if market_id in self.positions:
            position = self.positions[market_id]

            # Did we win?
            won = (position["direction"] == "UP" and outcome == "YES") or \
                  (position["direction"] == "DOWN" and outcome == "NO")

            pnl = position["size"] if won else -position["size"]
            self.total_pnl += pnl
            self.trade_count += 1

            if won:
                self.win_count += 1

            print(f"{'✅ WIN' if won else '❌ LOSS'}: {position['asset']} {position['direction']}")
            print(f"   P&L: ${pnl:+.2f}")

            del self.positions[market_id]

    def get_stats(self) -> dict:
        """Get strategy statistics."""
        return {
            "strategy": "MomentumLagArbitrage",
            "trade_count": self.trade_count,
            "win_count": self.win_count,
            "win_rate": self.win_count / max(1, self.trade_count),
            "total_pnl": round(self.total_pnl, 2),
            "active_positions": len(self.positions),
            "avg_pnl_per_trade": round(self.total_pnl / max(1, self.trade_count), 2)
        }
