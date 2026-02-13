"""Trading bot manager for web app."""

import asyncio
from typing import Dict, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import simulation modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.gamma import GammaClient
from src.data.clob import CLOBClient
from src.engine.executor import ExecutionEngine
from src.engine.portfolio import PortfolioTracker
from src.strategy.threshold import NaiveThreshold
from src.strategy.mean_reversion import MeanReversion
from src.strategy.manual import Manual
from src.strategy.sum_to_one_arb import SumToOneArbitrage
from src.strategy.momentum_lag_arb import MomentumLagArbitrage
from src.strategy.market_making import MarketMaking
from src.strategy.llm_directional import LLMDirectional
from .database import async_session_factory


class BotInstance:
    """Single bot instance for a user."""

    def __init__(self, user_id: str, config: dict):
        self.user_id = user_id
        self.config = config
        self.running = False
        self.task: Optional[asyncio.Task] = None

        # Components
        self.gamma: Optional[GammaClient] = None
        self.clob: Optional[CLOBClient] = None
        self.executor: Optional[ExecutionEngine] = None
        self.portfolio: Optional[PortfolioTracker] = None
        self.strategy = None

        # State
        self.active_markets = []
        self.signal_count = 0
        self.error_count = 0
        self.last_update = None

    async def initialize(self):
        """Initialize bot components."""
        # Initialize API clients
        api_config = {
            "gamma_base_url": "https://gamma-api.polymarket.com",
            "clob_base_url": "https://clob.polymarket.com",
            "request_timeout": 10,
            "max_retries": 3,
            "retry_backoff_factor": 2.0
        }

        self.gamma = GammaClient(
            base_url=api_config["gamma_base_url"],
            timeout=api_config["request_timeout"],
            max_retries=api_config["max_retries"],
            retry_backoff=api_config["retry_backoff_factor"],
            cache_ttl=60,
            db=None  # Web version doesn't use local DB for caching
        )

        self.clob = CLOBClient(
            base_url=api_config["clob_base_url"],
            timeout=api_config["request_timeout"],
            max_retries=api_config["max_retries"],
            retry_backoff=api_config["retry_backoff_factor"]
        )

        # Initialize execution engine
        self.executor = ExecutionEngine(
            clob_client=self.clob,
            db=None,  # Web version uses PostgreSQL directly
            slippage_factor=self.config.get("slippage_factor", 0.001),
            fee_rate=self.config.get("fee_rate", 0.02),
            order_ttl_hours=self.config.get("order_ttl_hours", 24)
        )

        # Initialize strategy
        strategy_type = self.config.get("strategy", "threshold")
        strategy_params = self.config.get("strategy_params", {})

        strategy_map = {
            "threshold": NaiveThreshold,
            "mean_reversion": MeanReversion,
            "manual": Manual,
            "sum_to_one_arb": SumToOneArbitrage,
            "momentum_lag_arb": MomentumLagArbitrage,
            "market_making": MarketMaking,
            "llm_directional": LLMDirectional,
        }

        strategy_class = strategy_map.get(strategy_type, NaiveThreshold)
        self.strategy = strategy_class(strategy_params)

    async def start(self):
        """Start the bot."""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._run())

    async def stop(self):
        """Stop the bot."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        # Cleanup
        if self.gamma:
            await self.gamma.close()
        if self.clob:
            await self.clob.close()

    async def _run(self):
        """Main bot loop."""
        await self.initialize()

        # Discover markets
        try:
            markets = await self.gamma.get_markets(
                limit=self.config.get("max_markets", 10),
                active=True,
                closed=False
            )
            self.active_markets = markets[:self.config.get("max_markets", 5)]
        except Exception as e:
            print(f"Error discovering markets: {e}")

        # Main loop
        while self.running:
            try:
                await self._trading_loop()
                self.last_update = datetime.utcnow()
                await asyncio.sleep(self.config.get("update_interval", 5))
            except Exception as e:
                print(f"Bot error for user {self.user_id}: {e}")
                self.error_count += 1
                await asyncio.sleep(5)

    async def _trading_loop(self):
        """Single iteration of trading logic."""
        for market in self.active_markets:
            try:
                # Get current price
                price = await self.clob.get_mid_price(
                    market.yes_token_id,
                    market.market_id
                )

                if price is None:
                    continue

                # Get orderbook
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

                # Execute orders (would need to integrate with database)
                for order in orders:
                    self.signal_count += 1
                    # TODO: Execute order and save to database

            except Exception as e:
                print(f"Error trading market {market.market_id}: {e}")

    def get_status(self) -> dict:
        """Get bot status."""
        return {
            "user_id": self.user_id,
            "running": self.running,
            "strategy": self.strategy.get_name() if self.strategy else None,
            "active_markets": len(self.active_markets),
            "signal_count": self.signal_count,
            "error_count": self.error_count,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "config": self.config
        }


class BotManager:
    """Manages multiple bot instances."""

    def __init__(self):
        self.bots: Dict[str, BotInstance] = {}

    async def start_bot(self, user_id: str, config: dict) -> dict:
        """Start a bot for a user."""
        # Stop existing bot if running
        if user_id in self.bots:
            await self.stop_bot(user_id)

        # Create and start new bot
        bot = BotInstance(user_id, config)
        self.bots[user_id] = bot
        await bot.start()

        return bot.get_status()

    async def stop_bot(self, user_id: str) -> dict:
        """Stop a user's bot."""
        if user_id not in self.bots:
            return {"error": "Bot not running"}

        bot = self.bots[user_id]
        await bot.stop()
        del self.bots[user_id]

        return {"user_id": user_id, "running": False}

    def get_bot_status(self, user_id: str) -> Optional[dict]:
        """Get status of a user's bot."""
        if user_id not in self.bots:
            return None

        return self.bots[user_id].get_status()

    async def stop_all(self):
        """Stop all bots."""
        for bot in self.bots.values():
            await bot.stop()
        self.bots.clear()


# Global bot manager instance
bot_manager = BotManager()
