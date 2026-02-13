#!/usr/bin/env python3
"""
Paper Trading CLI Tool

Run any strategy with fake money and real market data.

Usage:
    python scripts/paper_trade.py --strategy sum_to_one_arb --capital 10000
    python scripts/paper_trade.py --strategy momentum_lag_arb --capital 5000 --interval 3
    python scripts/paper_trade.py --strategy market_making --capital 20000
    python scripts/paper_trade.py --strategy llm_directional --capital 15000

Examples:
    # Sum-to-One Arbitrage with $10k
    python scripts/paper_trade.py --strategy sum_to_one_arb

    # Momentum arbitrage with $5k, 3-second updates
    python scripts/paper_trade.py --strategy momentum_lag_arb --capital 5000 --interval 3

    # Market making with custom spread
    python scripts/paper_trade.py --strategy market_making --capital 20000 --config '{"base_spread": 0.03}'

    # LLM directional with custom edge threshold
    python scripts/paper_trade.py --strategy llm_directional --config '{"min_edge_pct": 20.0}'
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.paper_trading import PaperTradingEngine
from src.strategy import (
    NaiveThreshold,
    MeanReversion,
    SumToOneArbitrage,
    MomentumLagArbitrage,
    MarketMaking,
    LLMDirectional
)


STRATEGIES = {
    "threshold": NaiveThreshold,
    "mean_reversion": MeanReversion,
    "sum_to_one_arb": SumToOneArbitrage,
    "momentum_lag_arb": MomentumLagArbitrage,
    "market_making": MarketMaking,
    "llm_directional": LLMDirectional,
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Paper Trading CLI - Test strategies with fake money",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        choices=STRATEGIES.keys(),
        help="Trading strategy to use"
    )

    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Starting capital in USDC (default: 10000)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Update interval in seconds (default: 5)"
    )

    parser.add_argument(
        "--markets",
        type=int,
        default=10,
        help="Maximum number of markets to track (default: 10)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="{}",
        help="Strategy config as JSON string (default: {})"
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Parse strategy config
    try:
        strategy_config = json.loads(args.config)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid config JSON: {e}")
        sys.exit(1)

    # Create strategy instance
    strategy_class = STRATEGIES[args.strategy]
    strategy = strategy_class(strategy_config)

    print(f"\n🎮 Starting Paper Trading")
    print(f"   Strategy: {args.strategy}")
    print(f"   Capital: ${args.capital:,.2f}")
    print(f"   Interval: {args.interval}s")
    print(f"   Max Markets: {args.markets}")

    if strategy_config:
        print(f"   Config: {json.dumps(strategy_config, indent=6)}")

    print()

    # Create paper trading engine
    engine = PaperTradingEngine(
        strategy=strategy,
        starting_capital=args.capital,
        update_interval=args.interval,
        max_markets=args.markets
    )

    # Start trading
    try:
        await engine.start()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
