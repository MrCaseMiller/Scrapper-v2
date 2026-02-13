"""Portfolio tracker for position and P&L management."""

from datetime import datetime
from typing import Optional

from .models import Portfolio, Position, Fill, OrderSide, MarketSide, Resolution
from ..data.clob import CLOBClient
from ..storage.db import Database


class PortfolioTracker:
    """Manages portfolio state and P&L."""

    def __init__(
        self,
        db: Database,
        clob_client: CLOBClient,
        starting_balance: float = 1000.0
    ):
        self.db = db
        self.clob = clob_client
        self.portfolio = Portfolio(
            balance=starting_balance,
            total_deposited=starting_balance
        )

        # Callbacks
        self.on_position_update: Optional[callable] = None

    async def initialize(self):
        """Initialize portfolio from database."""
        # Load balance from config
        balance_str = await self.db.get_config("portfolio_balance")
        if balance_str:
            self.portfolio.balance = float(balance_str)
        else:
            # Save initial balance
            await self.db.set_config("portfolio_balance", str(self.portfolio.balance))

        # Load starting deposit
        deposit_str = await self.db.get_config("total_deposited")
        if deposit_str:
            self.portfolio.total_deposited = float(deposit_str)
        else:
            await self.db.set_config("total_deposited", str(self.portfolio.total_deposited))

        # Load realized P&L
        pnl_str = await self.db.get_config("realized_pnl")
        if pnl_str:
            self.portfolio.realized_pnl = float(pnl_str)

        # Load total fees
        fees_str = await self.db.get_config("total_fees_paid")
        if fees_str:
            self.portfolio.total_fees_paid = float(fees_str)

        # Load positions
        positions = await self.db.get_all_positions()
        for pos in positions:
            self.portfolio.positions[pos.token_id] = pos

        # Update current prices
        await self.update_prices()

    async def process_fill(self, fill: Fill):
        """
        Process a fill and update portfolio.

        Args:
            fill: Fill to process
        """
        if fill.side == OrderSide.BUY:
            await self._process_buy_fill(fill)
        else:
            await self._process_sell_fill(fill)

        # Update fees
        self.portfolio.total_fees_paid += fill.fee
        await self.db.set_config("total_fees_paid", str(self.portfolio.total_fees_paid))

        # Save portfolio state
        await self._save_state()

        # Callback
        if self.on_position_update:
            await self.on_position_update(self.portfolio)

    async def _process_buy_fill(self, fill: Fill):
        """Process a buy fill."""
        # Deduct cost from balance
        total_cost = fill.size + fill.fee
        self.portfolio.balance -= total_cost
        await self.db.set_config("portfolio_balance", str(self.portfolio.balance))

        # Update position
        token_id = fill.token_id
        if token_id in self.portfolio.positions:
            # Add to existing position
            position = self.portfolio.positions[token_id]
            old_cost = position.shares * position.avg_entry_price
            new_cost = fill.shares * fill.price
            total_shares = position.shares + fill.shares
            position.avg_entry_price = (old_cost + new_cost) / total_shares if total_shares > 0 else 0
            position.shares = total_shares
            position.updated_at = datetime.utcnow()
        else:
            # Create new position
            position = Position(
                token_id=token_id,
                market_id=fill.market_id,
                market_side=fill.market_side,
                shares=fill.shares,
                avg_entry_price=fill.price,
                current_price=fill.price
            )
            self.portfolio.positions[token_id] = position

        # Save position
        await self.db.save_position(position)

    async def _process_sell_fill(self, fill: Fill):
        """Process a sell fill."""
        # Add proceeds to balance (minus fees)
        proceeds = fill.size - fill.fee
        self.portfolio.balance += proceeds
        await self.db.set_config("portfolio_balance", str(self.portfolio.balance))

        # Update position
        token_id = fill.token_id
        if token_id in self.portfolio.positions:
            position = self.portfolio.positions[token_id]

            # Calculate realized P&L
            cost_basis = fill.shares * position.avg_entry_price
            realized_pnl = proceeds - cost_basis
            self.portfolio.realized_pnl += realized_pnl
            await self.db.set_config("realized_pnl", str(self.portfolio.realized_pnl))

            # Reduce position
            position.shares -= fill.shares
            position.updated_at = datetime.utcnow()

            if position.shares <= 0:
                # Position closed
                del self.portfolio.positions[token_id]
                await self.db.delete_position(token_id)
            else:
                await self.db.save_position(position)

    async def update_prices(self):
        """Update current prices for all positions."""
        for token_id, position in self.portfolio.positions.items():
            price = await self.clob.get_mid_price(token_id, position.market_id)
            if price is not None:
                position.current_price = price
                position.updated_at = datetime.utcnow()
                await self.db.save_position(position)

        self.portfolio.updated_at = datetime.utcnow()

    async def settle_position(self, token_id: str, outcome: str, payout_per_share: float = 1.0):
        """
        Settle a position when market resolves.

        Args:
            token_id: Token ID to settle
            outcome: "YES" or "NO"
            payout_per_share: Payout per share (default $1 for winners, $0 for losers)
        """
        if token_id not in self.portfolio.positions:
            return

        position = self.portfolio.positions[token_id]

        # Determine if this position wins
        wins = (position.market_side.value == outcome)

        if wins:
            # Credit payout
            payout = position.shares * payout_per_share
            self.portfolio.balance += payout

            # Calculate realized P&L
            cost_basis = position.shares * position.avg_entry_price
            pnl = payout - cost_basis
            self.portfolio.realized_pnl += pnl
        else:
            # Position expires worthless
            cost_basis = position.shares * position.avg_entry_price
            self.portfolio.realized_pnl -= cost_basis

        # Remove position
        del self.portfolio.positions[token_id]
        await self.db.delete_position(token_id)

        # Save state
        await self._save_state()

        return wins

    async def settle_market(self, market_id: str, outcome: str) -> Resolution:
        """
        Settle all positions for a market.

        Args:
            market_id: Market ID
            outcome: "YES" or "NO"

        Returns:
            Resolution object with settlement details
        """
        settled_tokens = []
        total_payout = 0.0

        # Find all positions for this market
        positions_to_settle = [
            (token_id, pos)
            for token_id, pos in list(self.portfolio.positions.items())
            if pos.market_id == market_id
        ]

        for token_id, position in positions_to_settle:
            wins = (position.market_side.value == outcome)

            if wins:
                payout = position.shares
                total_payout += payout
                await self.settle_position(token_id, outcome, payout_per_share=1.0)
            else:
                await self.settle_position(token_id, outcome, payout_per_share=0.0)

            settled_tokens.append(token_id)

        # Create resolution record
        resolution = Resolution(
            market_id=market_id,
            outcome=outcome,
            settled_positions=settled_tokens,
            payout=total_payout
        )

        await self.db.save_resolution(resolution)

        return resolution

    async def take_snapshot(self):
        """Save portfolio snapshot for time-series analysis."""
        snapshot_data = {
            "balance": self.portfolio.balance,
            "positions_value": self.portfolio.positions_value,
            "total_value": self.portfolio.total_value,
            "realized_pnl": self.portfolio.realized_pnl,
            "unrealized_pnl": self.portfolio.unrealized_pnl,
            "total_fees_paid": self.portfolio.total_fees_paid,
            "num_positions": len(self.portfolio.positions),
            "positions": {
                token_id: {
                    "market_id": pos.market_id,
                    "market_side": pos.market_side.value,
                    "shares": pos.shares,
                    "avg_entry": pos.avg_entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl
                }
                for token_id, pos in self.portfolio.positions.items()
            }
        }

        await self.db.save_snapshot(snapshot_data)

    async def _save_state(self):
        """Save portfolio state to database."""
        await self.db.set_config("portfolio_balance", str(self.portfolio.balance))
        await self.db.set_config("realized_pnl", str(self.portfolio.realized_pnl))
        await self.db.set_config("total_fees_paid", str(self.portfolio.total_fees_paid))

    def get_portfolio(self) -> Portfolio:
        """Get current portfolio state."""
        return self.portfolio

    def set_position_update_callback(self, callback: callable):
        """Set callback for position updates."""
        self.on_position_update = callback
