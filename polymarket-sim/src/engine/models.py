"""Data models for orders, fills, and positions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class OrderSide(str, Enum):
    """Order side enum."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Order status enum."""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    RESTING = "RESTING"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class MarketSide(str, Enum):
    """Market position side enum."""
    YES = "YES"
    NO = "NO"


@dataclass
class Order:
    """Represents a trade order."""
    market_id: str
    token_id: str
    side: OrderSide
    size: float  # Size in USDC
    price: float  # Price per share (0-1)
    market_side: MarketSide  # YES or NO
    order_id: str = field(default_factory=lambda: str(uuid4()))
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_size: float = 0.0
    avg_fill_price: float = 0.0
    expires_at: Optional[datetime] = None

    @property
    def shares(self) -> float:
        """Calculate number of shares from size and price."""
        if self.price > 0:
            return self.size / self.price
        return 0.0

    @property
    def remaining_size(self) -> float:
        """Calculate remaining unfilled size."""
        return self.size - self.filled_size


@dataclass
class Fill:
    """Represents an executed fill."""
    fill_id: str = field(default_factory=lambda: str(uuid4()))
    order_id: str = ""
    market_id: str = ""
    token_id: str = ""
    side: OrderSide = OrderSide.BUY
    market_side: MarketSide = MarketSide.YES
    shares: float = 0.0
    price: float = 0.0  # Actual fill price
    size: float = 0.0  # Size in USDC
    fee: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    slippage: float = 0.0

    @property
    def total_cost(self) -> float:
        """Total cost including fees."""
        return self.size + self.fee


@dataclass
class Position:
    """Represents a market position."""
    token_id: str
    market_id: str
    market_side: MarketSide
    shares: float
    avg_entry_price: float
    current_price: float = 0.0
    entered_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def cost_basis(self) -> float:
        """Total cost basis of position."""
        return self.shares * self.avg_entry_price

    @property
    def market_value(self) -> float:
        """Current market value of position."""
        return self.shares * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L as percentage."""
        if self.cost_basis > 0:
            return (self.unrealized_pnl / self.cost_basis) * 100
        return 0.0


@dataclass
class Portfolio:
    """Represents portfolio state."""
    balance: float  # Available USDC
    positions: dict[str, Position] = field(default_factory=dict)
    total_deposited: float = 0.0
    realized_pnl: float = 0.0
    total_fees_paid: float = 0.0
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def positions_value(self) -> float:
        """Total market value of all positions."""
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_value(self) -> float:
        """Total portfolio value (balance + positions)."""
        return self.balance + self.positions_value

    @property
    def unrealized_pnl(self) -> float:
        """Total unrealized P&L across all positions."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    @property
    def total_pnl(self) -> float:
        """Total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    @property
    def total_return_pct(self) -> float:
        """Total return as percentage of deposited amount."""
        if self.total_deposited > 0:
            return ((self.total_value - self.total_deposited) / self.total_deposited) * 100
        return 0.0


@dataclass
class Market:
    """Represents a Polymarket market."""
    market_id: str
    question: str
    end_date: datetime
    yes_token_id: str
    no_token_id: str
    active: bool = True
    resolved: bool = False
    resolution: Optional[str] = None  # "YES", "NO", or None
    category: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OrderbookLevel:
    """Represents a single orderbook level."""
    price: float
    size: float  # Size available at this level


@dataclass
class Orderbook:
    """Represents market orderbook."""
    token_id: str
    market_id: str
    bids: list[OrderbookLevel] = field(default_factory=list)  # Buy orders
    asks: list[OrderbookLevel] = field(default_factory=list)  # Sell orders
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def best_bid(self) -> Optional[float]:
        """Highest buy price."""
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        """Lowest sell price."""
        return self.asks[0].price if self.asks else None

    @property
    def mid_price(self) -> Optional[float]:
        """Mid price between best bid and ask."""
        if self.best_bid is not None and self.best_ask is not None:
            return (self.best_bid + self.best_ask) / 2
        return None

    @property
    def spread(self) -> Optional[float]:
        """Spread between best bid and ask."""
        if self.best_bid is not None and self.best_ask is not None:
            return self.best_ask - self.best_bid
        return None


@dataclass
class Resolution:
    """Represents a market resolution event."""
    resolution_id: str = field(default_factory=lambda: str(uuid4()))
    market_id: str = ""
    outcome: str = ""  # "YES" or "NO"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    settled_positions: list[str] = field(default_factory=list)  # token_ids
    payout: float = 0.0  # Total payout from resolution
