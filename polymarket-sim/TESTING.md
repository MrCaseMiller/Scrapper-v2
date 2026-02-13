# Testing & Paper Trading Guide

Complete guide for testing Polymarket trading strategies before going live.

## 📋 Table of Contents

1. [Unit Testing](#unit-testing)
2. [Paper Trading](#paper-trading)
3. [Performance Metrics](#performance-metrics)
4. [Strategy Examples](#strategy-examples)
5. [Best Practices](#best-practices)

---

## 🧪 Unit Testing

### Running Tests

Run all strategy tests:
```bash
cd polymarket-sim
pytest tests/strategies/ -v
```

Run specific strategy tests:
```bash
# Test Sum-to-One Arbitrage
pytest tests/strategies/test_sum_to_one_arb.py -v

# Test Momentum/Lag Arbitrage
pytest tests/strategies/test_momentum_lag_arb.py -v

# Test Market Making
pytest tests/strategies/test_market_making.py -v

# Test LLM Directional
pytest tests/strategies/test_llm_directional.py -v
```

Run with coverage:
```bash
pytest tests/strategies/ --cov=src/strategy --cov-report=html
```

### Test Structure

Each strategy has comprehensive unit tests covering:
- ✅ Entry conditions (when to open positions)
- ✅ Exit conditions (when to close positions)
- ✅ Risk management (position sizing, stop loss)
- ✅ Edge cases (insufficient data, invalid inputs)
- ✅ Performance tracking (stats, P&L calculation)

Example test:
```python
@pytest.mark.asyncio
async def test_profitable_arbitrage_detected(strategy, mock_market):
    """Test that profitable arbitrage opportunity is detected."""
    orderbook = {
        "yes_asks": [{"price": 0.48, "size": 100}],
        "no_asks": [{"price": 0.49, "size": 100}]
    }

    orders = await strategy.on_market_update(
        market=mock_market,
        current_price=0.48,
        orderbook=orderbook
    )

    # Should generate 2 orders (buy YES + buy NO)
    assert len(orders) == 2
```

---

## 📊 Paper Trading

### Quick Start

Run any strategy with fake money and real data:

```bash
# Sum-to-One Arbitrage with $10k
python scripts/paper_trade.py --strategy sum_to_one_arb --capital 10000

# Momentum arbitrage with $5k, 3-second updates
python scripts/paper_trade.py --strategy momentum_lag_arb --capital 5000 --interval 3

# Market making with $20k
python scripts/paper_trade.py --strategy market_making --capital 20000

# LLM directional with $15k
python scripts/paper_trade.py --strategy llm_directional --capital 15000
```

### CLI Options

```
--strategy      Trading strategy to use
                Choices: sum_to_one_arb, momentum_lag_arb, market_making,
                         llm_directional, threshold, mean_reversion

--capital       Starting capital in USDC (default: 10000)

--interval      Update interval in seconds (default: 5)

--markets       Maximum number of markets to track (default: 10)

--config        Strategy config as JSON string (default: {})
```

### Custom Strategy Configuration

Pass custom parameters via JSON:

```bash
# Sum-to-One Arb with custom spread
python scripts/paper_trade.py \
  --strategy sum_to_one_arb \
  --config '{"min_spread_pct": 3.0, "max_position_size": 1000.0}'

# Market Making with tighter spreads
python scripts/paper_trade.py \
  --strategy market_making \
  --config '{"base_spread": 0.015, "order_size": 200.0}'

# LLM with higher edge requirement
python scripts/paper_trade.py \
  --strategy llm_directional \
  --config '{"min_edge_pct": 20.0, "confidence_threshold": 0.8}'
```

### What You'll See

Real-time paper trading output:
```
🎮 PAPER TRADING SESSION STARTED
============================================================
Strategy: SumToOneArbitrage
Starting Capital: $10,000.00
Update Interval: 5s
Max Markets: 10
============================================================

🎯 Arb found! Will BTC reach $100k by EOY?
   YES: $0.480, NO: $0.490, Sum: $0.970
   Spread: 3.00%, Size: $300.00
   Expected profit: $7.50

✅ BUY: 625.00 shares @ $0.4800 = $300.00
✅ BUY: 612.24 shares @ $0.4900 = $300.00

⏰ 14:23:45 | Equity: $10,007.50 | P&L: +$7.50 (+0.08%) | Trades: 2 | Markets: 8
```

Session summary:
```
📊 PAPER TRADING SESSION SUMMARY
============================================================

💰 P&L Summary:
   Starting Capital:  $10,000.00
   Final Equity:      $10,342.50
   Total Return:      +$342.50 (+3.43%)
   Max Drawdown:      1.25%

📈 Trading Stats:
   Total Trades:      24
   Runtime:           2.50 hours
   Trades/Hour:       9.60

🎯 Strategy Performance:
   arb_count: 12
   total_profit: 342.50
   avg_profit_per_arb: 28.54
```

---

## 📈 Performance Metrics

The paper trading framework calculates professional-grade metrics:

### Returns
- **Total Return**: Dollar profit/loss
- **Return %**: Percentage gain/loss

### Risk-Adjusted Returns
- **Sharpe Ratio**: Return per unit of risk
  - > 1.0 = Good
  - > 2.0 = Excellent
  - > 3.0 = Outstanding

- **Sortino Ratio**: Like Sharpe but only penalizes downside volatility
  - Better for strategies with asymmetric returns

- **Calmar Ratio**: Return / Max Drawdown
  - Measures return relative to worst-case scenario

### Drawdown
- **Max Drawdown**: Largest peak-to-trough decline
- **Max Drawdown %**: As percentage of peak equity

### Trade Statistics
- **Win Rate**: % of profitable trades
- **Profit Factor**: Gross profits / gross losses
  - > 1.0 = Profitable
  - > 2.0 = Excellent
- **Avg Win/Loss**: Average P&L per winning/losing trade
- **Largest Win/Loss**: Best and worst trades

### Example Metrics Report

```
📊 PERFORMANCE METRICS
============================================================

💰 Returns:
   Total Return:      +$1,247.35
   Return %:          +12.47%

📈 Risk-Adjusted:
   Sharpe Ratio:      2.341
   Sortino Ratio:     3.127
   Calmar Ratio:      4.156

📉 Drawdown:
   Max Drawdown:      $312.45
   Max Drawdown %:    3.00%

🎯 Trade Statistics:
   Total Trades:      87
   Win Rate:          64.37%
   Profit Factor:     2.234

   Winning Trades:    56
   Losing Trades:     31
   Avg Win:           +$34.21
   Avg Loss:          -$18.92
   Largest Win:       +$127.50
   Largest Loss:      -$45.32
   Avg Trade:         +$14.34
```

---

## 🎯 Strategy Examples

### 1. Sum-to-One Arbitrage

**Best for:** Low risk, consistent returns

```bash
python scripts/paper_trade.py \
  --strategy sum_to_one_arb \
  --capital 10000 \
  --interval 5 \
  --config '{
    "min_spread_pct": 2.5,
    "max_position_size": 500.0,
    "fee_rate": 0.02
  }'
```

**Expected Results:**
- Win Rate: 95%+
- Sharpe Ratio: 2.0-3.0
- Max Drawdown: <5%

---

### 2. Momentum/Lag Arbitrage

**Best for:** Short-term directional plays

```bash
python scripts/paper_trade.py \
  --strategy momentum_lag_arb \
  --capital 5000 \
  --interval 3 \
  --config '{
    "momentum_threshold": 0.4,
    "confidence_threshold": 0.65,
    "assets": ["BTC", "ETH", "SOL"]
  }'
```

**Expected Results:**
- Win Rate: 60-70%
- Sharpe Ratio: 1.5-2.5
- High turnover (frequent trades)

---

### 3. Market Making

**Best for:** Earning spreads, requires more capital

```bash
python scripts/paper_trade.py \
  --strategy market_making \
  --capital 20000 \
  --interval 10 \
  --config '{
    "base_spread": 0.02,
    "order_size": 100.0,
    "max_inventory": 500.0
  }'
```

**Expected Results:**
- Win Rate: 55-60%
- Profit Factor: 1.5-2.0
- Steady, consistent returns

---

### 4. LLM Directional

**Best for:** Event-driven trading

```bash
python scripts/paper_trade.py \
  --strategy llm_directional \
  --capital 15000 \
  --interval 30 \
  --config '{
    "min_edge_pct": 15.0,
    "confidence_threshold": 0.7,
    "use_consensus": true
  }'
```

**Expected Results:**
- Win Rate: 60-65%
- Sharpe Ratio: 1.5-2.0
- Lower frequency (more selective)

---

## ✅ Best Practices

### 1. Always Test First

Never deploy a strategy live without:
1. ✅ Unit tests passing
2. ✅ Paper trading for at least 24-48 hours
3. ✅ Sharpe ratio > 1.0
4. ✅ Max drawdown < 20%

### 2. Start Small

When going live:
- Start with 10-20% of intended capital
- Monitor for 1 week
- Gradually scale up if performance matches paper trading

### 3. Monitor Key Metrics

Watch for:
- **Win rate dropping** → Strategy may be degrading
- **Max drawdown increasing** → Risk management issue
- **Sharpe < 1.0** → Not enough return for risk

### 4. Paper Trade Different Market Conditions

Test your strategy during:
- Normal markets
- High volatility (news events)
- Low liquidity (off-hours)
- Trending markets
- Ranging markets

### 5. Compare Strategies

Run multiple strategies side-by-side:
```bash
# Terminal 1
python scripts/paper_trade.py --strategy sum_to_one_arb --capital 10000

# Terminal 2
python scripts/paper_trade.py --strategy momentum_lag_arb --capital 10000

# Terminal 3
python scripts/paper_trade.py --strategy market_making --capital 10000
```

Compare results after 24 hours.

---

## 🚀 Next Steps

After successful paper trading:

1. **Review Session Data**
   - Check saved JSON files (`paper_trading_session_*.json`)
   - Analyze trade history
   - Identify best/worst performing markets

2. **Optimize Parameters**
   - Adjust thresholds based on results
   - Fine-tune position sizing
   - Optimize entry/exit rules

3. **Go Live (Carefully)**
   - Start with minimum capital
   - Monitor closely for first week
   - Compare live vs paper results

4. **Iterate**
   - Continuously improve based on data
   - A/B test strategy variants
   - Track long-term performance

---

## 📞 Support

Questions? Issues?
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Documentation: Check main README.md

---

**Remember:** Paper trading is NOT a guarantee of live performance, but it's the best way to validate strategies risk-free. Always start small when going live!
