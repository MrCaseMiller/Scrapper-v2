"""PostgreSQL database module for Supabase."""

import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text,
    Index, ForeignKey, select, delete
)

from .config import get_settings

settings = get_settings()

# Prepare database URL for async engine
db_url = settings.database_url
# Handle empty/None values
if not db_url or db_url.strip() == "":
    db_url = "sqlite+aiosqlite:///./temp.db"
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


# Database Models
class User(Base):
    """User account."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Supabase user ID or generated UUID
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=True)  # For local auth (optional)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Portfolio(Base):
    """User portfolio."""
    __tablename__ = "portfolios"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    balance = Column(Float, nullable=False)
    total_deposited = Column(Float, nullable=False)
    realized_pnl = Column(Float, default=0.0)
    total_fees_paid = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Market(Base):
    """Polymarket market."""
    __tablename__ = "markets"

    market_id = Column(String, primary_key=True)
    question = Column(Text, nullable=False)
    end_date = Column(DateTime, nullable=False)
    yes_token_id = Column(String, nullable=False)
    no_token_id = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    resolved = Column(Boolean, default=False)
    resolution = Column(String, nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_markets_active", "active", "resolved"),
    )


class Order(Base):
    """Trading order."""
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    market_id = Column(String, ForeignKey("markets.market_id"), nullable=False)
    token_id = Column(String, nullable=False)
    side = Column(String, nullable=False)  # BUY/SELL
    market_side = Column(String, nullable=False)  # YES/NO
    size = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # PENDING/FILLED/REJECTED/RESTING/EXPIRED
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_size = Column(Float, default=0.0)
    avg_fill_price = Column(Float, default=0.0)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_orders_user", "user_id"),
        Index("idx_orders_market", "market_id"),
        Index("idx_orders_status", "status"),
    )


class Fill(Base):
    """Order fill."""
    __tablename__ = "fills"

    fill_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    market_id = Column(String, ForeignKey("markets.market_id"), nullable=False)
    token_id = Column(String, nullable=False)
    side = Column(String, nullable=False)
    market_side = Column(String, nullable=False)
    shares = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    slippage = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_fills_user", "user_id"),
        Index("idx_fills_order", "order_id"),
        Index("idx_fills_market", "market_id"),
        Index("idx_fills_timestamp", "timestamp"),
    )


class Position(Base):
    """User position."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token_id = Column(String, nullable=False)
    market_id = Column(String, ForeignKey("markets.market_id"), nullable=False)
    market_side = Column(String, nullable=False)
    shares = Column(Float, nullable=False)
    avg_entry_price = Column(Float, nullable=False)
    current_price = Column(Float, default=0.0)
    entered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_positions_user", "user_id"),
        Index("idx_positions_token", "user_id", "token_id", unique=True),
        Index("idx_positions_market", "market_id"),
    )


class Resolution(Base):
    """Market resolution."""
    __tablename__ = "resolutions"

    resolution_id = Column(String, primary_key=True)
    market_id = Column(String, ForeignKey("markets.market_id"), nullable=False)
    outcome = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    settled_positions = Column(Text, nullable=False)  # JSON array
    payout = Column(Float, nullable=False)

    __table_args__ = (
        Index("idx_resolutions_market", "market_id"),
    )


class Snapshot(Base):
    """Portfolio snapshot."""
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    balance = Column(Float, nullable=False)
    positions_value = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    realized_pnl = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False)
    total_fees_paid = Column(Float, nullable=False)
    num_positions = Column(Integer, nullable=False)
    data = Column(Text, nullable=False)  # JSON

    __table_args__ = (
        Index("idx_snapshots_user", "user_id"),
        Index("idx_snapshots_timestamp", "timestamp"),
    )


# Database operations
async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session_factory() as session:
        yield session


async def create_user(user_id: str, email: str, password_hash: Optional[str] = None) -> User:
    """Create new user."""
    async with async_session_factory() as session:
        user = User(id=user_id, email=email, password_hash=password_hash)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


async def create_portfolio(user_id: str, starting_balance: float) -> Portfolio:
    """Create portfolio for user."""
    async with async_session_factory() as session:
        portfolio = Portfolio(
            user_id=user_id,
            balance=starting_balance,
            total_deposited=starting_balance
        )
        session.add(portfolio)
        await session.commit()
        await session.refresh(portfolio)
        return portfolio


async def get_user_portfolio(user_id: str) -> Optional[Portfolio]:
    """Get user's portfolio."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def get_user_positions(user_id: str) -> List[Position]:
    """Get user's positions."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Position).where(
                Position.user_id == user_id,
                Position.shares > 0
            )
        )
        return list(result.scalars().all())


async def get_recent_fills(user_id: str, limit: int = 10) -> List[Fill]:
    """Get user's recent fills."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Fill)
            .where(Fill.user_id == user_id)
            .order_by(Fill.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_resting_orders(user_id: str) -> List[Order]:
    """Get user's resting orders."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Order).where(
                Order.user_id == user_id,
                Order.status == "RESTING"
            )
        )
        return list(result.scalars().all())
