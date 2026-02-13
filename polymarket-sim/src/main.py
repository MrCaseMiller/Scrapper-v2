"""Main entry point for Polymarket Simulation Trader."""

import asyncio
import signal
import sys
from pathlib import Path
import yaml

from .data.gamma import GammaClient
from .data.clob import CLOBClient
from .data.ws import WebSocketClient
from .engine.executor import ExecutionEngine
from .engine.portfolio import PortfolioTracker
from .storage.db import Database
from .strategy.threshold import NaiveThreshold
from .strategy.mean_reversion import MeanReversion
from .strategy.manual import Manual
from .ui.dashboard import Dashboard


class SimulationTrader:
    """Main simulation trader orchestrator."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.running = False

        # Components
        self.db: Database = None
        self.gamma: GammaClient = None
        self.clob: CLOBClient = None
        self.ws: WebSocketClient = None
        self.executor: ExecutionEngine = None
        self.portfolio: PortfolioTracker = None
        self.strategy = None
        self.dashboard: Dashboard = None

        # Market tracking
        self.active_markets = []
        self.signal_count = 0

    async def initialize(self):
        """Initialize all components."""
        # Load config
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            print(f"Config file not found: {self.config_path}")
            sys.exit(1)

        # Initialize database
        db_path = Path(__file__).parent.parent / "data" / "sim.db"
        self.db = Database(str(db_path))
        await self.db.connect()

        # Initialize API clients
        api_config = self.config.get("api", {})
        self.gamma = GammaClient(
            base_url=api_config.get("gamma_base_url"),
            timeout=api_config.get("request_timeout", 10),
            max_retries=api_config.get("max_retries", 3),
            retry_backoff=api_config.get("retry_backoff_factor", 2.0),
            cache_ttl=self.config.get("data", {}).get("cache_ttl_seconds", 60),
            db=self.db
        )

        self.clob = CLOBClient(
            base_url=api_config.get("clob_base_url"),
            timeout=api_config.get("request_timeout", 10),
            max_retries=api_config.get("max_retries", 3),
            retry_backoff=api_config.get("retry_backoff_factor", 2.0)
        )

        self.ws = WebSocketClient(
            ws_url=api_config.get("ws_url"),
            reconnect_delay=5.0,
            ping_interval=30.0
        )

        # Initialize execution engine
        exec_config = self.config.get("execution", {})
        self.executor = ExecutionEngine(
            clob_client=self.clob,
            db=self.db,
            slippage_factor=exec_config.get("slippage_factor", 0.001),
            fee_rate=exec_config.get("fee_rate", 0.02),
            order_ttl_hours=exec_config.get("order_ttl_hours", 24)
        )

        # Initialize portfolio
        portfolio_config = self.config.get("portfolio", {})
        self.portfolio = PortfolioTracker(
            db=self.db,
            clob_client=self.clob,
            starting_balance=portfolio_config.get("starting_balance", 1000.0)
        )
        await self.portfolio.initialize()

        # Initialize strategy
        strategy_config = self.config.get("strategy", {})
        active_strategy = strategy_config.get("active", "manual")

        if active_strategy == "threshold":
            self.strategy = NaiveThreshold(strategy_config.get("threshold", {}))
        elif active_strategy == "mean_reversion":
            self.strategy = MeanReversion(strategy_config.get("mean_reversion", {}))
        else:
            self.strategy = Manual(strategy_config.get("manual", {}))

        # Set up callbacks
        self.executor.set_fill_callback(self._on_fill)
        self.portfolio.set_position_update_callback(self._on_portfolio_update)

        # Initialize dashboard
        self.dashboard = Dashboard()
        self.dashboard.update_data(
            portfolio=self.portfolio.get_portfolio(),
            strategy_name=self.strategy.get_name(),
            strategy_signals=0
        )

        print(f"Initialized with strategy: {self.strategy.get_name()}")
        print(f"Starting balance: ${self.portfolio.portfolio.balance:,.2f}")

    async def start(self):
        """Start the simulation trader."""
        self.running = True

        # Start dashboard
        self.dashboard.start()

        # Discover markets
        await self._discover_markets()

        # Start background tasks
        tasks = [
            asyncio.create_task(self._price_update_loop()),
            asyncio.create_task(self._portfolio_update_loop()),
            asyncio.create_task(self._check_resolutions_loop()),
            asyncio.create_task(self._dashboard_update_loop())
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """Stop the simulation trader."""
        self.running = False

        # Stop dashboard
        if self.dashboard:
            self.dashboard.stop()

        # Close connections
        if self.ws:
            await self.ws.disconnect()
        if self.gamma:
            await self.gamma.close()
        if self.clob:
            await self.clob.close()
        if self.db:
            await self.db.close()

        print("\nShutdown complete.")

    async def _discover_markets(self):
        """Discover and cache active markets."""
        try:
            markets = await self.gamma.get_markets(limit=20, active=True, closed=False)
            self.active_markets = markets[:5]  # Track top 5 for simplicity
            print(f"Discovered {len(self.active_markets)} active markets")
        except Exception as e:
            print(f"Error discovering markets: {e}")

    async def _price_update_loop(self):
        """Main loop for price updates and signal generation."""
        update_interval = self.config.get("data", {}).get("price_update_interval", 1)

        while self.running:
            try:
                for market in self.active_markets:
                    # Get current price
                    price = await self.clob.get_mid_price(
                        market.yes_token_id,
                        market.market_id
                    )

                    if price is None:
                        continue

                    # Get orderbook for strategy
                    orderbook = await self.clob.get_orderbook(
                        market.yes_token_id,
                        market.market_id
                    )

                    # Generate signals
                    orders = await self.strategy.on_market_update(
                        market,
                        price,
                        orderbook
                    )

                    # Execute orders
                    for order in orders:
                        self.signal_count += 1
                        await self._execute_order(order)

                # Check resting orders
                await self.executor.check_resting_orders(
                    self.portfolio.portfolio.balance
                )

            except Exception as e:
                print(f"Error in price update loop: {e}")

            await asyncio.sleep(update_interval)

    async def _portfolio_update_loop(self):
        """Update portfolio prices periodically."""
        update_interval = self.config.get("ui", {}).get("portfolio_recalc_seconds", 5)

        while self.running:
            try:
                await self.portfolio.update_prices()
            except Exception as e:
                print(f"Error updating portfolio: {e}")

            await asyncio.sleep(update_interval)

    async def _check_resolutions_loop(self):
        """Check for market resolutions periodically."""
        check_interval = 300  # 5 minutes

        while self.running:
            try:
                for market in self.active_markets:
                    outcome = await self.gamma.check_resolution(market.market_id)
                    if outcome:
                        await self._handle_resolution(market.market_id, outcome)
                        # Remove from active markets
                        self.active_markets = [
                            m for m in self.active_markets
                            if m.market_id != market.market_id
                        ]
            except Exception as e:
                print(f"Error checking resolutions: {e}")

            await asyncio.sleep(check_interval)

    async def _dashboard_update_loop(self):
        """Update dashboard display."""
        refresh_interval = self.config.get("ui", {}).get("refresh_rate_seconds", 1)

        while self.running:
            try:
                # Get recent fills
                recent_fills = await self.db.get_recent_fills(limit=10)

                # Get resting orders
                resting_orders = await self.db.get_resting_orders()

                # Update dashboard
                self.dashboard.update_data(
                    portfolio=self.portfolio.get_portfolio(),
                    recent_fills=recent_fills,
                    resting_orders=resting_orders,
                    strategy_name=self.strategy.get_name(),
                    strategy_signals=self.signal_count
                )

                self.dashboard.refresh()

            except Exception as e:
                pass  # Silently handle dashboard errors

            await asyncio.sleep(refresh_interval)

    async def _execute_order(self, order):
        """Execute an order."""
        try:
            filled_order = await self.executor.submit_order(
                order,
                self.portfolio.portfolio.balance
            )
        except Exception as e:
            print(f"Error executing order: {e}")

    async def _on_fill(self, fill):
        """Handle fill event."""
        try:
            await self.portfolio.process_fill(fill)
            await self.strategy.on_fill(fill)
        except Exception as e:
            print(f"Error processing fill: {e}")

    async def _on_portfolio_update(self, portfolio):
        """Handle portfolio update event."""
        try:
            await self.strategy.on_portfolio_update(portfolio)
        except Exception as e:
            print(f"Error in portfolio update callback: {e}")

    async def _handle_resolution(self, market_id: str, outcome: str):
        """Handle market resolution."""
        try:
            resolution = await self.portfolio.settle_market(market_id, outcome)
            await self.strategy.on_resolution(market_id, outcome)
            print(f"\nMarket resolved: {market_id} → {outcome}")
            print(f"Payout: ${resolution.payout:,.2f}")
        except Exception as e:
            print(f"Error handling resolution: {e}")


async def main():
    """Main entry point."""
    # Determine config path
    config_path = Path(__file__).parent.parent / "config.yaml"

    trader = SimulationTrader(str(config_path))

    # Setup signal handlers
    def signal_handler(sig, frame):
        asyncio.create_task(trader.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await trader.initialize()
        await trader.start()
    except KeyboardInterrupt:
        await trader.stop()
    except Exception as e:
        print(f"Fatal error: {e}")
        await trader.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
