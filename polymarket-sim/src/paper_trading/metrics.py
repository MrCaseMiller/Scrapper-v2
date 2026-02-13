"""Performance Metrics Calculator.

Calculates advanced trading performance metrics:
- Sharpe Ratio: Risk-adjusted return
- Sortino Ratio: Downside risk-adjusted return
- Max Drawdown: Largest peak-to-trough decline
- Win Rate: % of profitable trades
- Profit Factor: Gross profits / gross losses
- Calmar Ratio: Return / max drawdown
- Average Trade: Mean P&L per trade
"""

import numpy as np
from typing import List, Tuple
from datetime import datetime


class PerformanceMetrics:
    """Calculate trading performance metrics."""

    def __init__(
        self,
        equity_curve: List[Tuple[datetime, float]],
        trades: List = None,
        risk_free_rate: float = 0.05  # 5% annual
    ):
        """
        Initialize metrics calculator.

        Args:
            equity_curve: List of (timestamp, equity) tuples
            trades: List of trade objects with profit/loss
            risk_free_rate: Annual risk-free rate (for Sharpe)
        """
        self.equity_curve = equity_curve
        self.trades = trades or []
        self.risk_free_rate = risk_free_rate

    def calculate_all(self) -> dict:
        """Calculate all performance metrics."""
        return {
            "total_return": self.total_return(),
            "return_pct": self.return_pct(),
            "sharpe_ratio": self.sharpe_ratio(),
            "sortino_ratio": self.sortino_ratio(),
            "max_drawdown": self.max_drawdown(),
            "max_drawdown_pct": self.max_drawdown_pct(),
            "calmar_ratio": self.calmar_ratio(),
            "win_rate": self.win_rate(),
            "profit_factor": self.profit_factor(),
            "avg_win": self.avg_win(),
            "avg_loss": self.avg_loss(),
            "largest_win": self.largest_win(),
            "largest_loss": self.largest_loss(),
            "avg_trade": self.avg_trade(),
            "total_trades": len(self.trades),
            "winning_trades": self.winning_trades(),
            "losing_trades": self.losing_trades()
        }

    def total_return(self) -> float:
        """Calculate total return in dollars."""
        if len(self.equity_curve) < 2:
            return 0.0

        start_equity = self.equity_curve[0][1]
        end_equity = self.equity_curve[-1][1]

        return end_equity - start_equity

    def return_pct(self) -> float:
        """Calculate total return as percentage."""
        if len(self.equity_curve) < 2:
            return 0.0

        start_equity = self.equity_curve[0][1]
        end_equity = self.equity_curve[-1][1]

        return ((end_equity - start_equity) / start_equity) * 100

    def sharpe_ratio(self) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted return).

        Sharpe = (mean_return - risk_free_rate) / std_return

        Higher is better (> 1.0 is good, > 2.0 is excellent)
        """
        if len(self.equity_curve) < 2:
            return 0.0

        # Calculate returns
        returns = self._calculate_returns()

        if len(returns) == 0:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Annualize (assuming daily returns)
        annual_mean = mean_return * 252  # 252 trading days
        annual_std = std_return * np.sqrt(252)

        sharpe = (annual_mean - self.risk_free_rate) / annual_std

        return round(sharpe, 3)

    def sortino_ratio(self) -> float:
        """
        Calculate Sortino Ratio (downside risk-adjusted return).

        Only considers downside volatility (negative returns).
        Better than Sharpe for asymmetric return distributions.
        """
        if len(self.equity_curve) < 2:
            return 0.0

        returns = self._calculate_returns()

        if len(returns) == 0:
            return 0.0

        mean_return = np.mean(returns)

        # Calculate downside deviation (only negative returns)
        negative_returns = [r for r in returns if r < 0]

        if len(negative_returns) == 0:
            return float('inf')  # No downside!

        downside_std = np.std(negative_returns)

        if downside_std == 0:
            return 0.0

        # Annualize
        annual_mean = mean_return * 252
        annual_downside_std = downside_std * np.sqrt(252)

        sortino = (annual_mean - self.risk_free_rate) / annual_downside_std

        return round(sortino, 3)

    def max_drawdown(self) -> float:
        """Calculate maximum drawdown in dollars."""
        if len(self.equity_curve) < 2:
            return 0.0

        peak = self.equity_curve[0][1]
        max_dd = 0.0

        for timestamp, equity in self.equity_curve:
            if equity > peak:
                peak = equity

            dd = peak - equity
            max_dd = max(max_dd, dd)

        return round(max_dd, 2)

    def max_drawdown_pct(self) -> float:
        """Calculate maximum drawdown as percentage."""
        if len(self.equity_curve) < 2:
            return 0.0

        peak = self.equity_curve[0][1]
        max_dd_pct = 0.0

        for timestamp, equity in self.equity_curve:
            if equity > peak:
                peak = equity

            if peak > 0:
                dd_pct = ((peak - equity) / peak) * 100
                max_dd_pct = max(max_dd_pct, dd_pct)

        return round(max_dd_pct, 2)

    def calmar_ratio(self) -> float:
        """
        Calculate Calmar Ratio (return / max drawdown).

        Measures return relative to downside risk.
        Higher is better (> 1.0 is good)
        """
        max_dd = self.max_drawdown_pct()

        if max_dd == 0:
            return 0.0

        annual_return = self.return_pct()  # Simplified (would need to annualize)

        return round(annual_return / max_dd, 3)

    def win_rate(self) -> float:
        """Calculate win rate (% of profitable trades)."""
        if len(self.trades) == 0:
            return 0.0

        winning = self.winning_trades()
        return round((winning / len(self.trades)) * 100, 2)

    def winning_trades(self) -> int:
        """Count winning trades."""
        return sum(1 for trade in self.trades if self._trade_pnl(trade) > 0)

    def losing_trades(self) -> int:
        """Count losing trades."""
        return sum(1 for trade in self.trades if self._trade_pnl(trade) < 0)

    def profit_factor(self) -> float:
        """
        Calculate profit factor (gross profits / gross losses).

        > 1.0 means profitable
        > 2.0 is excellent
        """
        gross_profit = sum(self._trade_pnl(t) for t in self.trades if self._trade_pnl(t) > 0)
        gross_loss = abs(sum(self._trade_pnl(t) for t in self.trades if self._trade_pnl(t) < 0))

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        return round(gross_profit / gross_loss, 3)

    def avg_win(self) -> float:
        """Calculate average winning trade."""
        wins = [self._trade_pnl(t) for t in self.trades if self._trade_pnl(t) > 0]

        if len(wins) == 0:
            return 0.0

        return round(np.mean(wins), 2)

    def avg_loss(self) -> float:
        """Calculate average losing trade."""
        losses = [self._trade_pnl(t) for t in self.trades if self._trade_pnl(t) < 0]

        if len(losses) == 0:
            return 0.0

        return round(np.mean(losses), 2)

    def largest_win(self) -> float:
        """Find largest winning trade."""
        wins = [self._trade_pnl(t) for t in self.trades if self._trade_pnl(t) > 0]

        if len(wins) == 0:
            return 0.0

        return round(max(wins), 2)

    def largest_loss(self) -> float:
        """Find largest losing trade."""
        losses = [self._trade_pnl(t) for t in self.trades if self._trade_pnl(t) < 0]

        if len(losses) == 0:
            return 0.0

        return round(min(losses), 2)

    def avg_trade(self) -> float:
        """Calculate average P&L per trade."""
        if len(self.trades) == 0:
            return 0.0

        pnls = [self._trade_pnl(t) for t in self.trades]
        return round(np.mean(pnls), 2)

    def _calculate_returns(self) -> List[float]:
        """Calculate period-over-period returns."""
        if len(self.equity_curve) < 2:
            return []

        returns = []

        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i-1][1]
            curr_equity = self.equity_curve[i][1]

            if prev_equity > 0:
                ret = (curr_equity - prev_equity) / prev_equity
                returns.append(ret)

        return returns

    def _trade_pnl(self, trade) -> float:
        """Extract P&L from trade object."""
        # Handle different trade formats
        if hasattr(trade, 'pnl'):
            return trade.pnl
        elif isinstance(trade, dict):
            return trade.get('pnl', 0.0)
        else:
            return 0.0


def print_metrics(metrics: dict):
    """Pretty print performance metrics."""
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE METRICS")
    print("=" * 60)

    print("\n💰 Returns:")
    print(f"   Total Return:      ${metrics['total_return']:+,.2f}")
    print(f"   Return %:          {metrics['return_pct']:+.2f}%")

    print("\n📈 Risk-Adjusted:")
    print(f"   Sharpe Ratio:      {metrics['sharpe_ratio']:.3f}")
    print(f"   Sortino Ratio:     {metrics['sortino_ratio']:.3f}")
    print(f"   Calmar Ratio:      {metrics['calmar_ratio']:.3f}")

    print("\n📉 Drawdown:")
    print(f"   Max Drawdown:      ${metrics['max_drawdown']:,.2f}")
    print(f"   Max Drawdown %:    {metrics['max_drawdown_pct']:.2f}%")

    print("\n🎯 Trade Statistics:")
    print(f"   Total Trades:      {metrics['total_trades']}")
    print(f"   Win Rate:          {metrics['win_rate']:.2f}%")
    print(f"   Profit Factor:     {metrics['profit_factor']:.3f}")

    print(f"\n   Winning Trades:    {metrics['winning_trades']}")
    print(f"   Losing Trades:     {metrics['losing_trades']}")
    print(f"   Avg Win:           ${metrics['avg_win']:+.2f}")
    print(f"   Avg Loss:          ${metrics['avg_loss']:+.2f}")
    print(f"   Largest Win:       ${metrics['largest_win']:+.2f}")
    print(f"   Largest Loss:      ${metrics['largest_loss']:+.2f}")
    print(f"   Avg Trade:         ${metrics['avg_trade']:+.2f}")

    print("\n" + "=" * 60)
