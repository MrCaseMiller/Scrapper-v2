"""SQLite storage layer for simulation data."""

import json
from datetime import datetime
from typing import Optional
import aiosqlite
from pathlib import Path

from ..engine.models import (
    Order, Fill, Position, Market, Resolution,
    OrderSide, OrderStatus, MarketSide
)


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: str = "data/sim.db"):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Establish database connection."""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self._init_schema()

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    async def _init_schema(self):
        """Initialize database schema."""
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS markets (
                market_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                end_date TEXT NOT NULL,
                yes_token_id TEXT NOT NULL,
                no_token_id TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                resolved INTEGER DEFAULT 0,
                resolution TEXT,
                category TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                market_id TEXT NOT NULL,
                token_id TEXT NOT NULL,
                side TEXT NOT NULL,
                market_side TEXT NOT NULL,
                size REAL NOT NULL,
                price REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                filled_size REAL DEFAULT 0,
                avg_fill_price REAL DEFAULT 0,
                expires_at TEXT,
                FOREIGN KEY (market_id) REFERENCES markets(market_id)
            );

            CREATE TABLE IF NOT EXISTS fills (
                fill_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                market_id TEXT NOT NULL,
                token_id TEXT NOT NULL,
                side TEXT NOT NULL,
                market_side TEXT NOT NULL,
                shares REAL NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL,
                fee REAL NOT NULL,
                slippage REAL DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (market_id) REFERENCES markets(market_id)
            );

            CREATE TABLE IF NOT EXISTS positions (
                token_id TEXT PRIMARY KEY,
                market_id TEXT NOT NULL,
                market_side TEXT NOT NULL,
                shares REAL NOT NULL,
                avg_entry_price REAL NOT NULL,
                current_price REAL DEFAULT 0,
                entered_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (market_id) REFERENCES markets(market_id)
            );

            CREATE TABLE IF NOT EXISTS resolutions (
                resolution_id TEXT PRIMARY KEY,
                market_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                settled_positions TEXT NOT NULL,
                payout REAL NOT NULL,
                FOREIGN KEY (market_id) REFERENCES markets(market_id)
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                balance REAL NOT NULL,
                positions_value REAL NOT NULL,
                total_value REAL NOT NULL,
                realized_pnl REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                total_fees_paid REAL NOT NULL,
                num_positions INTEGER NOT NULL,
                data TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_orders_market ON orders(market_id);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_fills_order ON fills(order_id);
            CREATE INDEX IF NOT EXISTS idx_fills_market ON fills(market_id);
            CREATE INDEX IF NOT EXISTS idx_fills_timestamp ON fills(timestamp);
            CREATE INDEX IF NOT EXISTS idx_positions_market ON positions(market_id);
            CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp);
        """)
        await self.conn.commit()

    # Market operations
    async def save_market(self, market: Market):
        """Save or update market."""
        await self.conn.execute("""
            INSERT OR REPLACE INTO markets
            (market_id, question, end_date, yes_token_id, no_token_id,
             active, resolved, resolution, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            market.market_id, market.question, market.end_date.isoformat(),
            market.yes_token_id, market.no_token_id, int(market.active),
            int(market.resolved), market.resolution, market.category,
            market.created_at.isoformat(), market.updated_at.isoformat()
        ))
        await self.conn.commit()

    async def get_market(self, market_id: str) -> Optional[Market]:
        """Get market by ID."""
        async with self.conn.execute(
            "SELECT * FROM markets WHERE market_id = ?", (market_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Market(
                    market_id=row["market_id"],
                    question=row["question"],
                    end_date=datetime.fromisoformat(row["end_date"]),
                    yes_token_id=row["yes_token_id"],
                    no_token_id=row["no_token_id"],
                    active=bool(row["active"]),
                    resolved=bool(row["resolved"]),
                    resolution=row["resolution"],
                    category=row["category"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
        return None

    async def get_active_markets(self) -> list[Market]:
        """Get all active markets."""
        markets = []
        async with self.conn.execute(
            "SELECT * FROM markets WHERE active = 1 AND resolved = 0"
        ) as cursor:
            async for row in cursor:
                markets.append(Market(
                    market_id=row["market_id"],
                    question=row["question"],
                    end_date=datetime.fromisoformat(row["end_date"]),
                    yes_token_id=row["yes_token_id"],
                    no_token_id=row["no_token_id"],
                    active=bool(row["active"]),
                    resolved=bool(row["resolved"]),
                    resolution=row["resolution"],
                    category=row["category"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                ))
        return markets

    # Order operations
    async def save_order(self, order: Order):
        """Save or update order."""
        await self.conn.execute("""
            INSERT OR REPLACE INTO orders
            (order_id, market_id, token_id, side, market_side, size, price,
             status, created_at, filled_size, avg_fill_price, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order.order_id, order.market_id, order.token_id,
            order.side.value, order.market_side.value,
            order.size, order.price, order.status.value,
            order.created_at.isoformat(), order.filled_size,
            order.avg_fill_price,
            order.expires_at.isoformat() if order.expires_at else None
        ))
        await self.conn.commit()

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        async with self.conn.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Order(
                    order_id=row["order_id"],
                    market_id=row["market_id"],
                    token_id=row["token_id"],
                    side=OrderSide(row["side"]),
                    market_side=MarketSide(row["market_side"]),
                    size=row["size"],
                    price=row["price"],
                    status=OrderStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    filled_size=row["filled_size"],
                    avg_fill_price=row["avg_fill_price"],
                    expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
                )
        return None

    async def get_resting_orders(self) -> list[Order]:
        """Get all resting orders."""
        orders = []
        async with self.conn.execute(
            "SELECT * FROM orders WHERE status = ?", (OrderStatus.RESTING.value,)
        ) as cursor:
            async for row in cursor:
                orders.append(Order(
                    order_id=row["order_id"],
                    market_id=row["market_id"],
                    token_id=row["token_id"],
                    side=OrderSide(row["side"]),
                    market_side=MarketSide(row["market_side"]),
                    size=row["size"],
                    price=row["price"],
                    status=OrderStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    filled_size=row["filled_size"],
                    avg_fill_price=row["avg_fill_price"],
                    expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
                ))
        return orders

    # Fill operations
    async def save_fill(self, fill: Fill):
        """Save fill."""
        await self.conn.execute("""
            INSERT INTO fills
            (fill_id, order_id, market_id, token_id, side, market_side,
             shares, price, size, fee, slippage, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fill.fill_id, fill.order_id, fill.market_id, fill.token_id,
            fill.side.value, fill.market_side.value, fill.shares,
            fill.price, fill.size, fill.fee, fill.slippage,
            fill.timestamp.isoformat()
        ))
        await self.conn.commit()

    async def get_recent_fills(self, limit: int = 10) -> list[Fill]:
        """Get recent fills."""
        fills = []
        async with self.conn.execute(
            "SELECT * FROM fills ORDER BY timestamp DESC LIMIT ?", (limit,)
        ) as cursor:
            async for row in cursor:
                fills.append(Fill(
                    fill_id=row["fill_id"],
                    order_id=row["order_id"],
                    market_id=row["market_id"],
                    token_id=row["token_id"],
                    side=OrderSide(row["side"]),
                    market_side=MarketSide(row["market_side"]),
                    shares=row["shares"],
                    price=row["price"],
                    size=row["size"],
                    fee=row["fee"],
                    slippage=row["slippage"],
                    timestamp=datetime.fromisoformat(row["timestamp"])
                ))
        return fills

    # Position operations
    async def save_position(self, position: Position):
        """Save or update position."""
        await self.conn.execute("""
            INSERT OR REPLACE INTO positions
            (token_id, market_id, market_side, shares, avg_entry_price,
             current_price, entered_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            position.token_id, position.market_id, position.market_side.value,
            position.shares, position.avg_entry_price, position.current_price,
            position.entered_at.isoformat(), position.updated_at.isoformat()
        ))
        await self.conn.commit()

    async def get_position(self, token_id: str) -> Optional[Position]:
        """Get position by token ID."""
        async with self.conn.execute(
            "SELECT * FROM positions WHERE token_id = ?", (token_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Position(
                    token_id=row["token_id"],
                    market_id=row["market_id"],
                    market_side=MarketSide(row["market_side"]),
                    shares=row["shares"],
                    avg_entry_price=row["avg_entry_price"],
                    current_price=row["current_price"],
                    entered_at=datetime.fromisoformat(row["entered_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
        return None

    async def get_all_positions(self) -> list[Position]:
        """Get all positions."""
        positions = []
        async with self.conn.execute("SELECT * FROM positions WHERE shares > 0") as cursor:
            async for row in cursor:
                positions.append(Position(
                    token_id=row["token_id"],
                    market_id=row["market_id"],
                    market_side=MarketSide(row["market_side"]),
                    shares=row["shares"],
                    avg_entry_price=row["avg_entry_price"],
                    current_price=row["current_price"],
                    entered_at=datetime.fromisoformat(row["entered_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                ))
        return positions

    async def delete_position(self, token_id: str):
        """Delete position (when fully closed)."""
        await self.conn.execute("DELETE FROM positions WHERE token_id = ?", (token_id,))
        await self.conn.commit()

    # Resolution operations
    async def save_resolution(self, resolution: Resolution):
        """Save resolution."""
        await self.conn.execute("""
            INSERT INTO resolutions
            (resolution_id, market_id, outcome, timestamp, settled_positions, payout)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            resolution.resolution_id, resolution.market_id, resolution.outcome,
            resolution.timestamp.isoformat(),
            json.dumps(resolution.settled_positions),
            resolution.payout
        ))
        await self.conn.commit()

    # Snapshot operations
    async def save_snapshot(self, portfolio_data: dict):
        """Save portfolio snapshot."""
        await self.conn.execute("""
            INSERT INTO snapshots
            (timestamp, balance, positions_value, total_value, realized_pnl,
             unrealized_pnl, total_fees_paid, num_positions, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            portfolio_data.get("balance", 0),
            portfolio_data.get("positions_value", 0),
            portfolio_data.get("total_value", 0),
            portfolio_data.get("realized_pnl", 0),
            portfolio_data.get("unrealized_pnl", 0),
            portfolio_data.get("total_fees_paid", 0),
            portfolio_data.get("num_positions", 0),
            json.dumps(portfolio_data)
        ))
        await self.conn.commit()

    # Config operations
    async def get_config(self, key: str) -> Optional[str]:
        """Get config value."""
        async with self.conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["value"] if row else None

    async def set_config(self, key: str, value: str):
        """Set config value."""
        await self.conn.execute("""
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.utcnow().isoformat()))
        await self.conn.commit()
