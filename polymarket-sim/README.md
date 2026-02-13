# Polymarket Simulation Trader

A paper trading bot that consumes real Polymarket prediction market data and executes simulated trades against a local portfolio. No real money. No API keys for write operations. Real prices, fake execution.

## What This Is

The system monitors live markets, executes strategy logic, tracks positions, and scores performance against actual market resolutions. This provides a sandbox environment for validating prediction market strategies before capital deployment.

## Features

- **Real Data, Simulated Execution**: Consumes live Polymarket orderbook data via read-only APIs
- **Multiple Strategies**: Pluggable strategy system with threshold, mean reversion, and manual modes
- **Portfolio Tracking**: Complete position management with P&L calculations and market-to-market updates
- **Terminal Dashboard**: High-density Rich terminal UI showing positions, fills, and strategy state
- **Complete Audit Trail**: All trades, fills, and resolutions logged to SQLite
- **Market Resolution**: Automatic detection and settlement of resolved markets

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   DATA LAYER (read-only)             │
│  Gamma API ──→ Market Discovery                     │
│  CLOB API  ──→ Orderbook Snapshots / Price Feeds    │
│  WebSocket ──→ Real-time Price Updates              │
├─────────────────────────────────────────────────────┤
│                   STRATEGY LAYER                     │
│  Strategy Interface ──→ Signal Generation           │
│  Pluggable strategies (swap without rewiring)       │
├─────────────────────────────────────────────────────┤
│                   EXECUTION LAYER (simulated)        │
│  Order Matching ──→ Fill Simulation                 │
│  Slippage Model ──→ Realistic Execution             │
│  Position Tracker ──→ Portfolio State               │
├─────────────────────────────────────────────────────┤
│                   STORAGE LAYER                      │
│  SQLite ──→ Trades, Positions, Market Snapshots     │
└─────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip

### Setup

1. Clone the repository
2. Navigate to the project directory:
   ```bash
   cd polymarket-sim
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure settings in `config.yaml`:
   - Set starting balance
   - Choose strategy (manual, threshold, mean_reversion)
   - Adjust execution parameters (slippage, fees)

## Usage

### Running the Simulation

Start the simulation trader:

```bash
python -m src.main
```

Or use the convenience script:

```bash
python run.py
```

### Configuration

Edit `config.yaml` to customize:

**Portfolio Settings:**
- `starting_balance`: Initial USDC balance (default: 1000)

**Strategy Settings:**
- `active`: Choose strategy: "manual", "threshold", or "mean_reversion"
- Strategy-specific parameters for each strategy type

**Execution Settings:**
- `slippage_factor`: Simulated slippage (default: 0.001 = 0.1%)
- `fee_rate`: Trading fees (default: 0.02 = 2%)
- `order_ttl_hours`: Resting order expiry (default: 24h)

### Strategies

#### Manual Strategy
Human-in-the-loop trading. Orders are submitted manually via terminal input.

#### Threshold Strategy
Simple threshold-based strategy:
- Buys YES when price drops below `buy_below` threshold
- Sells YES when price rises above `sell_above` threshold

#### Mean Reversion Strategy
Trades based on deviation from historical mean:
- Tracks price history over `lookback_periods` hours
- Buys when price deviates below mean by `deviation_threshold`
- Sells when price deviates above mean by `deviation_threshold`

## Dashboard

The terminal dashboard displays:
- Portfolio value and P&L
- Active positions with unrealized P&L
- Recent fills with timestamps and prices
- Resting orders with expiry times
- Strategy name and signal count

Press `Ctrl+C` to exit gracefully.

## Database

All activity is logged to `data/sim.db` (SQLite):

**Tables:**
- `markets` - Market metadata and resolutions
- `orders` - All submitted orders
- `fills` - All executed fills
- `positions` - Current position state
- `resolutions` - Market settlement records
- `snapshots` - Portfolio snapshots over time
- `config` - Runtime configuration

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Development

### Project Structure

```
polymarket-sim/
├── src/
│   ├── data/          # API clients (Gamma, CLOB, WebSocket)
│   ├── engine/        # Execution engine and portfolio tracker
│   ├── strategy/      # Strategy implementations
│   ├── storage/       # SQLite database layer
│   ├── ui/            # Terminal dashboard
│   └── main.py        # Main orchestrator
├── tests/             # Unit tests
├── data/              # SQLite database (gitignored)
├── config.yaml        # Configuration
└── requirements.txt   # Dependencies
```

### Adding a New Strategy

1. Create a new file in `src/strategy/`
2. Inherit from `Strategy` base class
3. Implement `on_market_update()` method
4. Return list of `Order` objects
5. Update `config.yaml` to use your strategy

Example:

```python
from .base import Strategy
from ..engine.models import Order, OrderSide, MarketSide

class MyStrategy(Strategy):
    async def on_market_update(self, market, current_price, orderbook):
        orders = []
        # Your strategy logic here
        return orders
```

## Milestones

- ✅ **M1: Data Pipeline** - Market data client operational
- ✅ **M2: Execution Engine** - Simulated fills against real orderbooks
- ✅ **M3: Strategy Framework** - Pluggable strategy system
- ✅ **M4: Terminal Dashboard** - Rich UI with live updates
- ✅ **M5: Resolution Scoring** - Market settlement and P&L calculation
- ⏳ **M6: Backtest Mode** - Replay historical data (future)

## Technical Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.11+ | Rich ecosystem for data/trading |
| HTTP | httpx | Async-native, connection pooling |
| WebSocket | websockets | Standard async WebSocket client |
| Storage | SQLite | Zero config, portable, sufficient for sim scale |
| Terminal UI | rich | High-density terminal rendering |
| Scheduling | asyncio | Native event loop |

## Notes

- **Read-Only APIs**: All Polymarket API calls are read-only. No authentication required.
- **No Real Money**: This is a simulation. No real trades are executed.
- **Rate Limits**: Respects API rate limits with exponential backoff
- **Data Caching**: Market data cached locally with configurable TTL

## License

© Special Projects Studio

## Support

For issues or questions, please open an issue on the repository.
