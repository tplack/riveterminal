"""Dashboard screen showing market overview."""

import asyncio
from datetime import datetime
from textual.widgets import Static, DataTable
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.align import Align

from ..data.yahoo import yahoo
from ..utils.formatting import format_price_change, format_volume, format_time_only
from ..config import MARKET_INDICES, COLORS


class MarketOverviewWidget(Static):
    """Widget showing major market indices."""
    
    def __init__(self):
        super().__init__()
        self.market_data = {}
    
    async def refresh_data(self):
        """Refresh market data."""
        try:
            self.market_data = await yahoo.get_market_overview()
            self.update_display()
        except Exception as e:
            self.update(f"Error loading market data: {e}")
    
    def update_display(self):
        """Update the display with current market data."""
        if not self.market_data:
            self.update("Loading market data...")
            return
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Index", style="bright_white", width=12)
        table.add_column("Price", justify="right", width=12)
        table.add_column("Change", justify="right", width=15)
        table.add_column("Volume", justify="right", width=12)
        
        # Map symbols to display names
        index_names = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ",
            "^VIX": "VIX",
            "^RUT": "Russell 2K"
        }
        
        for symbol, data in self.market_data.items():
            name = index_names.get(symbol, symbol)
            price = f"${data.get('price', 0):.2f}"
            
            # Format change with color
            change = data.get('change', 0)
            change_pct = data.get('change_percent', 0)
            
            if change > 0:
                change_str = f"+{change:.2f} (+{change_pct:.2f}%)"
                change_style = "green"
            elif change < 0:
                change_str = f"{change:.2f} ({change_pct:.2f}%)"
                change_style = "red" 
            else:
                change_str = "0.00 (0.00%)"
                change_style = "white"
            
            volume = format_volume(data.get('volume', 0))
            
            table.add_row(name, price, change_str, volume)
            
            # Apply color to the change column
            if len(table.rows) > 0:
                table.columns[2].style = change_style
        
        panel = Panel(
            Align.center(table),
            title="📊 Market Overview",
            title_align="left",
            border_style="cyan"
        )
        
        self.update(panel)


class TopMoversWidget(Static):
    """Widget showing top gainers and losers."""
    
    def __init__(self):
        super().__init__()
        self.movers_data = {"gainers": [], "losers": []}
    
    async def refresh_data(self):
        """Refresh top movers data."""
        try:
            self.movers_data = await yahoo.get_top_movers(5)
            self.update_display()
        except Exception as e:
            self.update(f"Error loading movers: {e}")
    
    def update_display(self):
        """Update the display with top movers."""
        if not self.movers_data["gainers"] and not self.movers_data["losers"]:
            self.update("Loading top movers...")
            return
        
        # Create side-by-side tables
        gainers_table = Table(show_header=True, header_style="bold green")
        gainers_table.add_column("Gainers", style="bright_white", width=8)
        gainers_table.add_column("Price", justify="right", width=10)
        gainers_table.add_column("Change", justify="right", style="green", width=12)
        
        for stock in self.movers_data["gainers"][:5]:
            symbol = stock.get('symbol', 'N/A')
            price = f"${stock.get('price', 0):.2f}"
            change_pct = stock.get('change_percent', 0)
            gainers_table.add_row(symbol, price, f"+{change_pct:.1f}%")
        
        losers_table = Table(show_header=True, header_style="bold red")
        losers_table.add_column("Losers", style="bright_white", width=8)
        losers_table.add_column("Price", justify="right", width=10)
        losers_table.add_column("Change", justify="right", style="red", width=12)
        
        for stock in self.movers_data["losers"][:5]:
            symbol = stock.get('symbol', 'N/A')
            price = f"${stock.get('price', 0):.2f}"
            change_pct = stock.get('change_percent', 0)
            losers_table.add_row(symbol, price, f"{change_pct:.1f}%")
        
        # Combine tables side by side
        from rich.columns import Columns
        combined = Columns([gainers_table, losers_table])
        
        panel = Panel(
            combined,
            title="🔥 Top Movers",
            title_align="left", 
            border_style="yellow"
        )
        
        self.update(panel)


class DashboardScreen(Screen):
    """Main dashboard screen."""
    
    BINDINGS = [
        ("1", "show_dashboard", "Dashboard"),
        ("2", "show_quote", "Quote"),
        ("3", "show_watchlist", "Watchlist"),
        ("4", "show_chart", "Chart"),
        ("5", "show_economic", "Economic"),
        ("6", "show_news", "News"),
        ("7", "show_screener", "Screener"),
        ("9", "show_crypto", "Crypto"),
        ("r", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        self.refresh_timer = None
    
    def compose(self):
        """Compose the dashboard layout."""
        with Vertical():
            # Header with time
            yield Static(self._get_header(), id="header")
            
            with Horizontal():
                # Left column - Market overview
                with Vertical():
                    yield MarketOverviewWidget()
                    yield TopMoversWidget()
                
                # Right column - Additional info (placeholder for now)
                yield Static(self._get_info_panel(), id="info_panel")
    
    def _get_header(self) -> Panel:
        """Get header panel with current time."""
        current_time = format_time_only()
        header_text = Text()
        header_text.append("RiverTerminal", style="bold cyan")
        header_text.append(" | ", style="white")
        header_text.append(f"Market Dashboard", style="bold white")
        header_text.append(" | ", style="white") 
        header_text.append(f"🕒 {current_time}", style="yellow")
        
        return Panel(
            Align.center(header_text),
            height=3,
            style="bold",
            border_style="blue"
        )
    
    def _get_info_panel(self) -> Panel:
        """Get info panel with instructions."""
        info_text = Text()
        info_text.append("📈 Welcome to RiverTerminal\n\n", style="bold cyan")
        info_text.append("Navigation:\n", style="bold white")
        info_text.append("• 1: Dashboard (current)\n", style="white")
        info_text.append("• 2: Quote screen\n", style="white")
        info_text.append("• 3: Watchlist\n", style="white")
        info_text.append("• 4: Charts\n", style="white")
        info_text.append("• 5: Economic (FRED data)\n", style="white")
        info_text.append("• 6: News\n", style="white")
        info_text.append("• 7: Screener (stock filters)\n", style="white")
        info_text.append("• 9: Crypto dashboard\n", style="white")
        info_text.append("• R: Refresh data\n\n", style="white")
        info_text.append("Command Bar:\n", style="bold white")
        info_text.append("• /: Focus command bar\n", style="white")
        info_text.append("Type ticker symbols (AAPL, MSFT)\n", style="white")
        info_text.append("or commands (ECON, CRYPTO)\n", style="white")
        
        return Panel(
            info_text,
            title="ℹ️ Quick Guide",
            title_align="left",
            border_style="green"
        )
    
    async def on_mount(self):
        """Initialize the screen."""
        await self.refresh_all_data()
        # Set up auto-refresh every 30 seconds
        self.set_interval(30.0, self.refresh_all_data)
        # Update header clock every second
        self.set_interval(1.0, self.update_header)
    
    async def refresh_all_data(self):
        """Refresh all dashboard data."""
        market_widget = self.query_one(MarketOverviewWidget)
        movers_widget = self.query_one(TopMoversWidget)
        
        # Refresh market data and movers in parallel
        await asyncio.gather(
            market_widget.refresh_data(),
            movers_widget.refresh_data(),
            return_exceptions=True
        )
    
    def update_header(self):
        """Update the header with current time."""
        header_widget = self.query_one("#header", Static)
        header_widget.update(self._get_header())
    
    def action_refresh(self):
        """Manual refresh action."""
        asyncio.create_task(self.refresh_all_data())
    
    def action_show_dashboard(self):
        """Show dashboard (current screen)."""
        pass  # Already on dashboard
    
    def action_show_quote(self):
        """Switch to quote screen."""
        self.app.push_screen("quote")
    
    def action_show_watchlist(self):
        """Switch to watchlist screen."""
        self.app.push_screen("watchlist")
    
    def action_show_chart(self):
        """Switch to chart screen."""
        self.app.push_screen("chart")
    
    def action_show_news(self):
        """Switch to news screen."""
        self.app.push_screen("news")
    
    def action_show_economic(self):
        """Switch to economic screen."""
        self.app.push_screen("economic")
    
    def action_show_screener(self):
        """Switch to screener screen."""
        self.app.push_screen("screener")
    
    def action_show_crypto(self):
        """Switch to crypto screen."""
        self.app.push_screen("crypto")