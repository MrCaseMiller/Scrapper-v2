"""Rich terminal dashboard for monitoring."""

from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..engine.models import Portfolio, Fill, Order


class Dashboard:
    """Terminal dashboard using Rich."""

    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.live: Optional[Live] = None

        # Data to display
        self.portfolio: Optional[Portfolio] = None
        self.recent_fills: list[Fill] = []
        self.resting_orders: list[Order] = []
        self.strategy_name: str = ""
        self.strategy_signals: int = 0
        self.last_update: datetime = datetime.utcnow()

    def setup_layout(self):
        """Setup dashboard layout."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        self.layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )

        self.layout["left"].split_column(
            Layout(name="positions"),
            Layout(name="recent_fills")
        )

        self.layout["right"].split_column(
            Layout(name="resting_orders"),
            Layout(name="strategy_info")
        )

    def update_data(
        self,
        portfolio: Portfolio = None,
        recent_fills: list[Fill] = None,
        resting_orders: list[Order] = None,
        strategy_name: str = None,
        strategy_signals: int = None
    ):
        """Update dashboard data."""
        if portfolio:
            self.portfolio = portfolio
        if recent_fills is not None:
            self.recent_fills = recent_fills
        if resting_orders is not None:
            self.resting_orders = resting_orders
        if strategy_name:
            self.strategy_name = strategy_name
        if strategy_signals is not None:
            self.strategy_signals = strategy_signals

        self.last_update = datetime.utcnow()

    def render(self) -> Layout:
        """Render dashboard."""
        # Header
        self.layout["header"].update(self._render_header())

        # Positions
        self.layout["positions"].update(self._render_positions())

        # Recent fills
        self.layout["recent_fills"].update(self._render_recent_fills())

        # Resting orders
        self.layout["resting_orders"].update(self._render_resting_orders())

        # Strategy info
        self.layout["strategy_info"].update(self._render_strategy())

        # Footer
        self.layout["footer"].update(self._render_footer())

        return self.layout

    def _render_header(self) -> Panel:
        """Render header with portfolio summary."""
        if not self.portfolio:
            return Panel("POLYMARKET SIM · Loading...", style="bold white")

        total_value = self.portfolio.total_value
        total_pnl = self.portfolio.total_pnl
        total_pnl_pct = self.portfolio.total_return_pct

        # Color based on P&L
        pnl_color = "green" if total_pnl >= 0 else "red"
        pnl_sign = "+" if total_pnl >= 0 else ""

        header_text = (
            f"POLYMARKET SIM  ·  "
            f"${total_value:,.2f}  ·  "
            f"[{pnl_color}]{pnl_sign}${total_pnl:,.2f} ({pnl_sign}{total_pnl_pct:.1f}%)[/{pnl_color}]  ·  "
            f"{self.last_update.strftime('%H:%M:%S')}"
        )

        return Panel(header_text, style="bold white")

    def _render_positions(self) -> Panel:
        """Render positions table."""
        table = Table(show_header=True, header_style="bold", expand=True)
        table.add_column("Market", style="white", no_wrap=False)
        table.add_column("Side", style="cyan", justify="center", width=4)
        table.add_column("Shares", style="white", justify="right", width=8)
        table.add_column("Entry", style="white", justify="right", width=8)
        table.add_column("Current", style="white", justify="right", width=8)
        table.add_column("P&L", style="white", justify="right", width=10)

        if self.portfolio and self.portfolio.positions:
            for token_id, position in list(self.portfolio.positions.items())[:5]:
                # Truncate market ID for display
                market_display = position.market_id[:30] + "..." if len(position.market_id) > 30 else position.market_id

                # P&L color
                pnl = position.unrealized_pnl
                pnl_color = "green" if pnl >= 0 else "red"
                pnl_sign = "+" if pnl >= 0 else ""

                table.add_row(
                    market_display,
                    position.market_side.value,
                    f"{position.shares:.0f}",
                    f"${position.avg_entry_price:.2f}",
                    f"${position.current_price:.2f}",
                    f"[{pnl_color}]{pnl_sign}${pnl:.2f}[/{pnl_color}]"
                )
        else:
            table.add_row("No positions", "", "", "", "", "")

        return Panel(table, title="POSITIONS", border_style="blue")

    def _render_recent_fills(self) -> Panel:
        """Render recent fills table."""
        table = Table(show_header=True, header_style="bold", expand=True)
        table.add_column("Time", style="white", width=8)
        table.add_column("Side", style="cyan", justify="center", width=4)
        table.add_column("Shares", style="white", justify="right", width=8)
        table.add_column("Market", style="white", no_wrap=False)
        table.add_column("Price", style="white", justify="right", width=8)
        table.add_column("Cost", style="white", justify="right", width=10)

        for fill in self.recent_fills[:5]:
            time_str = fill.timestamp.strftime("%H:%M:%S")
            market_display = fill.market_id[:20] + "..." if len(fill.market_id) > 20 else fill.market_id

            # Color by side
            side_color = "green" if fill.side.value == "BUY" else "red"
            cost_sign = "-" if fill.side.value == "BUY" else "+"

            table.add_row(
                time_str,
                f"[{side_color}]{fill.side.value}[/{side_color}]",
                f"{fill.shares:.0f}",
                market_display,
                f"${fill.price:.2f}",
                f"{cost_sign}${fill.total_cost:.2f}"
            )

        if not self.recent_fills:
            table.add_row("", "", "", "No recent fills", "", "")

        return Panel(table, title="RECENT FILLS", border_style="blue")

    def _render_resting_orders(self) -> Panel:
        """Render resting orders table."""
        table = Table(show_header=True, header_style="bold", expand=True)
        table.add_column("Side", style="cyan", justify="center", width=4)
        table.add_column("Size", style="white", justify="right", width=8)
        table.add_column("Market", style="white", no_wrap=False)
        table.add_column("Price", style="white", justify="right", width=8)
        table.add_column("Expires", style="white", width=12)

        for order in self.resting_orders[:5]:
            market_display = order.market_id[:25] + "..." if len(order.market_id) > 25 else order.market_id

            # Format expiry
            if order.expires_at:
                now = datetime.utcnow()
                time_left = order.expires_at - now
                hours_left = int(time_left.total_seconds() / 3600)
                expires_str = f"{hours_left}h"
            else:
                expires_str = "-"

            side_color = "green" if order.side.value == "BUY" else "red"

            table.add_row(
                f"[{side_color}]{order.side.value}[/{side_color}]",
                f"${order.size:.0f}",
                market_display,
                f"${order.price:.2f}",
                expires_str
            )

        if not self.resting_orders:
            table.add_row("", "", "No resting orders", "", "")

        return Panel(table, title="RESTING ORDERS", border_style="blue")

    def _render_strategy(self) -> Panel:
        """Render strategy info."""
        if not self.portfolio:
            strategy_text = "Loading..."
        else:
            balance = self.portfolio.balance
            positions_val = self.portfolio.positions_value
            num_positions = len(self.portfolio.positions)
            fees = self.portfolio.total_fees_paid

            strategy_text = (
                f"Strategy: {self.strategy_name}\n"
                f"Signals: {self.strategy_signals}\n\n"
                f"Cash Balance: ${balance:,.2f}\n"
                f"Positions Value: ${positions_val:,.2f}\n"
                f"Num Positions: {num_positions}\n"
                f"Fees Paid: ${fees:,.2f}"
            )

        return Panel(strategy_text, title="STRATEGY", border_style="blue")

    def _render_footer(self) -> Panel:
        """Render footer."""
        footer_text = "Press Ctrl+C to exit  ·  All data logged to SQLite"
        return Panel(footer_text, style="dim white")

    def start(self):
        """Start live dashboard."""
        self.setup_layout()
        self.live = Live(self.render(), console=self.console, refresh_per_second=1)
        self.live.start()

    def stop(self):
        """Stop live dashboard."""
        if self.live:
            self.live.stop()

    def refresh(self):
        """Refresh dashboard display."""
        if self.live:
            self.live.update(self.render())
