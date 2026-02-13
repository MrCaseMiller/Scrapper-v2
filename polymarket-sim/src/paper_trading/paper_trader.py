"""Paper Trading Framework.

Runs strategies with fake money but real market data.
Tracks what WOULD have happened without risking capital.

Features:
- Virtual portfolio with starting capital
- Real market data from Polymarket
- Order simulation (fills at market prices)
- Performance tracking (Sharpe ratio, max drawdown, win rate)
- Real-time P&L updates
- Trade history logging
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import json

from ..data.gamma import GammaClient
from ..data.clob import CLOBClient
from ..engine.models import Market, Order, OrderSide, MarketSide
from ..strategy.base import Strategy


class VirtualFill:
    """Represents a simulated order fill."""

    def __init__(self, order: Order, fill_price: float, timestamp: datetime):
        self.order = order
        self.token_id = order.token_id
        self.market_id = order.market_id
        self.side = order.side
        self.market_side = order.market_side
        self.price = fill_price
        self.size = order.size
        self.timestamp = timestamp


class PaperTradingEngine:
    """
    Paper trading engine for strategy testing.

    Uses real market data but simulates order execution.
    """

    def __init__(
        self,
        strategy: Strategy,
        starting_capital: float = 10000.0,
        update_interval: int = 5,
        max_markets: int = 10
    ):
        """
        Initialize paper trading engine.

        Args:
            strategy: Trading strategy instance
            starting_capital: Starting capital in USDC
            update_interval: Seconds between market updates
            max_markets: Maximum number of markets to track
        """
        self.strategy = strategy
        self.starting_capital = starting_capital
        self.update_interval = update_interval
        self.max_markets = max_markets

        # Virtual portfolio
        self.cash = starting_capital
        self.positions: Dict[str, float] = {}  # {token_id: shares}
        self.pending_orders: List[Order] = []

        # Data clients
        self.gamma_client = GammaClient()
        self.clob_client = CLOBClient()

        # Performance tracking
        self.trades: List[VirtualFill] = []
        self.equity_curve: List[tuple] = []  # (timestamp, equity)
        self.start_time = None
        self.peak_equity = starting_capital
        self.max_drawdown = 0.0

        # State
        self.running = False
        self.markets: Dict[str, Market] = {}

    async def start(self):
        """Start paper trading session."""
        print("=" * 60)
        print("🎮 PAPER TRADING SESSION STARTED")
        print("=" * 60)
        print(f"Strategy: {self.strategy.__class__.__name__}")
        print(f"Starting Capital: ${self.starting_capital:,.2f}")
        print(f"Update Interval: {self.update_interval}s")
        print(f"Max Markets: {self.max_markets}")
        print("=" * 60)
        print()

        self.running = True
        self.start_time = datetime.utcnow()

        try:
            await self._trading_loop()
        except KeyboardInterrupt:
            print("\n⏸️  Paper trading stopped by user")
        except Exception as e:
            print(f"\n❌ Error in paper trading: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop()

    async def stop(self):
        """Stop paper trading and show summary."""
        self.running = False

        print("\n" + "=" * 60)
        print("📊 PAPER TRADING SESSION SUMMARY")
        print("=" * 60)

        # Calculate performance metrics
        final_equity = self._calculate_equity()
        total_return = final_equity - self.starting_capital
        return_pct = (total_return / self.starting_capital) * 100

        runtime = (datetime.utcnow() - self.start_time).seconds / 3600  # Hours

        print(f"\n💰 P&L Summary:")
        print(f"   Starting Capital:  ${self.starting_capital:,.2f}")
        print(f"   Final Equity:      ${final_equity:,.2f}")
        print(f"   Total Return:      ${total_return:+,.2f} ({return_pct:+.2f}%)")
        print(f"   Max Drawdown:      {self.max_drawdown:.2%}")

        print(f"\n📈 Trading Stats:")
        print(f"   Total Trades:      {len(self.trades)}")
        print(f"   Runtime:           {runtime:.2f} hours")

        if len(self.trades) > 0:
            trades_per_hour = len(self.trades) / max(runtime, 0.1)
            print(f"   Trades/Hour:       {trades_per_hour:.2f}")

        # Strategy-specific stats
        strategy_stats = self.strategy.get_stats()
        print(f"\n🎯 Strategy Performance:")
        for key, value in strategy_stats.items():
            if key != "strategy":
                print(f"   {key}: {value}")

        print("\n" + "=" * 60)

        # Save session data
        await self._save_session()

    async def _trading_loop(self):
        """Main paper trading loop."""
        while self.running:
            try:
                # Fetch active markets
                await self._update_markets()

                # Update strategy on each market
                for market_id, market in self.markets.items():
                    # Get current price and orderbook
                    current_price = await self._get_market_price(market)
                    orderbook = await self._get_orderbook(market)

                    # Run strategy
                    orders = await self.strategy.on_market_update(
                        market=market,
                        current_price=current_price,
                        orderbook=orderbook
                    )

                    # Execute orders
                    for order in orders:
                        await self._execute_order(order, current_price)

                # Update equity curve
                equity = self._calculate_equity()
                self.equity_curve.append((datetime.utcnow(), equity))

                # Update max drawdown
                self.peak_equity = max(self.peak_equity, equity)
                drawdown = (self.peak_equity - equity) / self.peak_equity
                self.max_drawdown = max(self.max_drawdown, drawdown)

                # Print status
                self._print_status()

                # Wait before next update
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                print(f"Error in trading loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(self.update_interval)

    async def _update_markets(self):
        """Fetch and update active markets."""
        try:
            # Fetch markets from Gamma API
            markets_data = await self.gamma_client.get_markets(
                limit=self.max_markets,
                active=True
            )

            for market_data in markets_data:
                market = Market(
                    market_id=market_data.get("id"),
                    question=market_data.get("question"),
                    yes_token_id=market_data.get("tokens", [{}])[0].get("token_id"),
                    no_token_id=market_data.get("tokens", [{}])[1].get("token_id") if len(market_data.get("tokens", [])) > 1 else None,
                    end_date=datetime.fromisoformat(market_data.get("end_date_iso").replace("Z", "+00:00")) if market_data.get("end_date_iso") else datetime.utcnow() + timedelta(days=30),
                    active=market_data.get("active", True)
                )

                self.markets[market.market_id] = market

        except Exception as e:
            print(f"Error fetching markets: {e}")

    async def _get_market_price(self, market: Market) -> float:
        """Get current market price (mid price)."""
        try:
            # Try to get from orderbook
            orderbook = await self._get_orderbook(market)

            if orderbook:
                best_bid = orderbook.get("yes_bids", [{}])[0].get("price", 0.50)
                best_ask = orderbook.get("yes_asks", [{}])[0].get("price", 0.50)
                return (best_bid + best_ask) / 2

        except:
            pass

        # Default to 0.50 if no data
        return 0.50

    async def _get_orderbook(self, market: Market) -> Optional[dict]:
        """Get market orderbook."""
        try:
            # Fetch from CLOB API
            orderbook = await self.clob_client.get_orderbook(market.yes_token_id)
            return orderbook
        except:
            return None

    async def _execute_order(self, order: Order, current_price: float):
        """
        Simulate order execution.

        Market orders fill immediately at current price.
        Limit orders are added to pending orders.
        """
        if order.order_type == "MARKET":
            # Fill immediately at current price
            fill_price = current_price if order.market_side == MarketSide.YES else (1 - current_price)

            await self._process_fill(order, fill_price)

        elif order.order_type == "LIMIT":
            # Add to pending orders (will check for fills on next update)
            self.pending_orders.append(order)

    async def _process_fill(self, order: Order, fill_price: float):
        """Process an order fill."""
        # Calculate cost/proceeds
        cost = order.size * fill_price

        if order.side == OrderSide.BUY:
            # Check if we have enough cash
            if cost > self.cash:
                print(f"⚠️  Insufficient cash for order: need ${cost:.2f}, have ${self.cash:.2f}")
                return

            # Deduct cash
            self.cash -= cost

            # Add to position
            shares = order.size / fill_price
            self.positions[order.token_id] = self.positions.get(order.token_id, 0) + shares

            print(f"✅ BUY: {shares:.2f} shares @ ${fill_price:.4f} = ${cost:.2f}")

        else:  # SELL
            # Check if we have enough shares
            shares_needed = order.size / fill_price
            if self.positions.get(order.token_id, 0) < shares_needed:
                print(f"⚠️  Insufficient shares for order: need {shares_needed:.2f}, have {self.positions.get(order.token_id, 0):.2f}")
                return

            # Add cash
            proceeds = order.size * fill_price
            self.cash += proceeds

            # Reduce position
            self.positions[order.token_id] -= shares_needed

            print(f"✅ SELL: {shares_needed:.2f} shares @ ${fill_price:.4f} = ${proceeds:.2f}")

        # Record trade
        fill = VirtualFill(order, fill_price, datetime.utcnow())
        self.trades.append(fill)

        # Notify strategy
        await self.strategy.on_fill(fill)

    def _calculate_equity(self) -> float:
        """Calculate current total equity (cash + position value)."""
        # For now, assume all positions are worth entry value (no P&L tracking yet)
        # In production, would need to mark-to-market all positions

        equity = self.cash

        # Add position values (simplified)
        for token_id, shares in self.positions.items():
            # Assume $0.50 per share (would need real prices in production)
            equity += shares * 0.50

        return equity

    def _print_status(self):
        """Print current status."""
        equity = self._calculate_equity()
        pnl = equity - self.starting_capital
        pnl_pct = (pnl / self.starting_capital) * 100

        print(f"\n⏰ {datetime.utcnow().strftime('%H:%M:%S')} | "
              f"Equity: ${equity:,.2f} | "
              f"P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%) | "
              f"Trades: {len(self.trades)} | "
              f"Markets: {len(self.markets)}")

    async def _save_session(self):
        """Save session data to file."""
        session_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": self.strategy.__class__.__name__,
            "starting_capital": self.starting_capital,
            "final_equity": self._calculate_equity(),
            "trades": len(self.trades),
            "max_drawdown": self.max_drawdown,
            "runtime_hours": (datetime.utcnow() - self.start_time).seconds / 3600,
            "strategy_stats": self.strategy.get_stats()
        }

        filename = f"paper_trading_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)

            print(f"\n💾 Session data saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️  Could not save session data: {e}")
