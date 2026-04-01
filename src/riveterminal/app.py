"""Main RiverTerminal application."""

import asyncio
from typing import Dict, Any, Optional
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual import events
from textual.driver import Driver

from .widgets.command_bar import CommandBar
from .widgets.ticker_tape import TickerTape
from .screens.dashboard import DashboardScreen
from .screens.quote import QuoteScreen
from .screens.watchlist import WatchlistScreen
from .screens.chart import ChartScreen
from .screens.news import NewsScreen
from .screens.economic import EconomicScreen
from .screens.screener import ScreenerScreen
from .screens.crypto import CryptoScreen
from .screens.portfolio import PortfolioScreen
from .screens.options import OptionsScreen
from .config import get_config


class RiverTerminalApp(App):
    """Main RiverTerminal application."""
    
    TITLE = "RiverTerminal"
    SUB_TITLE = "Open-Source Bloomberg Terminal"
    
    CSS = """
/* Global styles */
Screen {
    background: #000011;
    color: #FFFFFF;
}

/* Command Bar */
CommandBar {
    dock: top;
    height: 3;
    border: solid yellow;
    background: #000011;
    color: yellow;
    text-style: bold;
}

CommandBar:focus {
    border: solid #FFFF00;
    background: #111122;
}

/* Ticker Tape */
TickerTape {
    dock: bottom;
    height: 1;
    background: #000011;
    color: #00FF00;
    text-style: bold;
}

/* Tables */
DataTable {
    background: #000011;
    color: #FFFFFF;
}

DataTable > .datatable--header {
    background: #001122;
    color: #00FFFF;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #003366;
}

/* Panels */
Panel {
    border: solid #0088FF;
    background: #000011;
}

/* Buttons */
Button {
    background: #001122;
    color: #FFFFFF;
    border: solid #0088FF;
}

Button.-primary {
    background: #0088FF;
    color: #FFFFFF;
}

Button:hover {
    background: #003366;
}

/* Inputs */
Input {
    background: #000011;
    color: #FFFFFF;
    border: solid #0088FF;
}

Input:focus {
    border: solid #00FFFF;
}

/* Static text containers */
Static {
    background: #000011;
    color: #FFFFFF;
}

/* Containers */
Vertical {
    background: #000011;
}

Horizontal {
    background: #000011;
}
"""
    
    BINDINGS = [
        ("0", "show_options", "Options"),
        ("1", "show_dashboard", "Dashboard"),
        ("2", "show_quote", "Quote"),
        ("3", "show_watchlist", "Watchlist"),
        ("4", "show_chart", "Chart"),
        ("5", "show_economic", "Economic"),
        ("6", "show_news", "News"),
        ("7", "show_screener", "Screener"),
        ("8", "show_portfolio", "Portfolio"),
        ("9", "show_crypto", "Crypto"),
        ("e", "export_data", "Export"),
        ("ctrl+c", "quit", "Quit"),
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("?", "show_help", "Help"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = get_config()
        self.current_screen_name = "dashboard"
        
        # Install screens
        self.install_screen(DashboardScreen(), name="dashboard")
        self.install_screen(QuoteScreen(), name="quote")
        self.install_screen(WatchlistScreen(), name="watchlist")
        self.install_screen(ChartScreen(), name="chart")
        self.install_screen(EconomicScreen(), name="economic")
        self.install_screen(NewsScreen(), name="news")
        self.install_screen(ScreenerScreen(), name="screener")
        self.install_screen(PortfolioScreen(), name="portfolio")
        self.install_screen(CryptoScreen(), name="crypto")
        self.install_screen(OptionsScreen(), name="options")
    
    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        with Vertical():
            yield CommandBar()
            # Main content area is handled by screens
            yield TickerTape()
    
    async def on_mount(self) -> None:
        """Initialize the application."""
        # Switch to dashboard screen
        self.switch_screen("dashboard")
        
        # Set up ticker tape updates
        ticker_tape = self.query_one(TickerTape)
        ticker_tape.add_news_item("Welcome to RiverTerminal!", "SYSTEM")
        
        # Focus command bar
        command_bar = self.query_one(CommandBar)
        command_bar.focus()
    
    async def on_command_bar_command_entered(self, message: CommandBar.CommandEntered) -> None:
        """Handle command bar input."""
        command = message.command.upper().strip()
        
        if not command:
            return
        
        # Handle navigation commands
        if command in ["DASHBOARD", "HOME", "MAIN"]:
            self.switch_screen("dashboard")
            
        elif command in ["QUOTE", "Q"]:
            self.switch_screen("quote")
            
        elif command in ["WATCHLIST", "WATCH", "WL"]:
            self.switch_screen("watchlist")
            
        elif command in ["CHART", "CHARTS", "C"]:
            self.switch_screen("chart")
            
        elif command in ["NEWS", "N"]:
            self.switch_screen("news")
            
        elif command in ["ECONOMIC", "ECON", "E"]:
            self.switch_screen("economic")
            
        elif command in ["SCREENER", "SCREEN", "S"]:
            self.switch_screen("screener")
            
        elif command in ["PORTFOLIO", "PORT", "P"]:
            self.switch_screen("portfolio")
            
        elif command in ["OPTIONS", "OPT", "O"]:
            self.switch_screen("options")
            
        elif command in ["CRYPTO", "CRYPT", "CR"]:
            self.switch_screen("crypto")
            
        elif command in ["HELP", "?", "H"]:
            self.action_show_help()
            
        elif command in ["QUIT", "EXIT", "Q"]:
            self.exit()
            
        else:
            # Treat as ticker symbol lookup
            await self._handle_ticker_command(command)
    
    async def _handle_ticker_command(self, ticker: str) -> None:
        """Handle ticker symbol commands."""
        # Validate ticker format (basic check)
        if len(ticker) > 0 and ticker.replace(".", "").replace("-", "").isalnum():
            # Switch to quote screen with this ticker
            if self.current_screen_name != "quote":
                self.switch_screen("quote")
            
            # Wait a moment for screen to load, then set symbol
            await asyncio.sleep(0.1)
            
            current_screen = self.screen
            if hasattr(current_screen, 'set_symbol'):
                current_screen.set_symbol(ticker)
            else:
                # If quote screen not ready, install new one with symbol
                self.install_screen(QuoteScreen(ticker), name="quote")
                self.switch_screen("quote")
                
            # Update ticker tape
            ticker_tape = self.query_one(TickerTape)
            ticker_tape.add_news_item(f"Viewing {ticker}", "LOOKUP")
        else:
            # Invalid ticker format
            self.notify(f"Invalid ticker symbol: {ticker}")
    
    def switch_screen(self, screen_name: str) -> None:
        """Switch to named screen."""
        try:
            self.push_screen(screen_name)
            self.current_screen_name = screen_name
        except Exception as e:
            self.notify(f"Error switching to {screen_name}: {e}")
    
    def action_show_dashboard(self) -> None:
        """Show dashboard screen."""
        self.switch_screen("dashboard")
    
    def action_show_quote(self) -> None:
        """Show quote screen."""
        self.switch_screen("quote")
    
    def action_show_watchlist(self) -> None:
        """Show watchlist screen."""
        self.switch_screen("watchlist")
    
    def action_show_chart(self) -> None:
        """Show chart screen."""
        self.switch_screen("chart")
    
    def action_show_news(self) -> None:
        """Show news screen."""
        self.switch_screen("news")
    
    def action_show_economic(self) -> None:
        """Show economic dashboard."""
        self.switch_screen("economic")
    
    def action_show_screener(self) -> None:
        """Show stock screener."""
        self.switch_screen("screener")
    
    def action_show_portfolio(self) -> None:
        """Show portfolio tracker."""
        self.switch_screen("portfolio")
    
    def action_show_options(self) -> None:
        """Show options chain."""
        self.switch_screen("options")
    
    def action_show_crypto(self) -> None:
        """Show crypto dashboard."""
        self.switch_screen("crypto")
    
    def action_refresh(self) -> None:
        """Refresh current screen."""
        current_screen = self.screen
        if hasattr(current_screen, 'refresh'):
            current_screen.refresh()
        else:
            self.notify("Refreshed")
    
    def action_export_data(self) -> None:
        """Export current screen data."""
        try:
            current_screen = self.screen
            if hasattr(current_screen, 'action_export_data'):
                current_screen.action_export_data()
            else:
                self.notify("Export not available for this screen")
        except Exception as e:
            self.notify(f"Export error: {e}")
    
    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
RiverTerminal Help - Phase 3 Enhanced

Navigation:
  0 - Options Chain (view options for any stock)
  1 - Dashboard (market overview)
  2 - Quote screen (individual stocks)
  3 - Watchlist (your saved stocks)
  4 - Charts (enhanced with SMA & volume)
  5 - Economic (FRED data, yields)
  6 - News (financial news)
  7 - Screener (stock filters)
  8 - Portfolio Tracker (manage positions)
  9 - Crypto (cryptocurrency data)

Command Bar:
  / - Focus command bar
  Type ticker symbols (AAPL, MSFT, TSLA) to view quotes
  Type commands: DASHBOARD, QUOTE, CHART, PORTFOLIO, OPTIONS
  
General:
  Q or Ctrl+C - Quit application
  R - Refresh current screen
  E - Export current screen data
  ? - Show this help
  
New Features:
  Portfolio: Track positions, P&L, allocations
  Options: View chains, Greeks, expirations  
  Charts: SMA overlays, volume, multi-ticker
  Export: Save data to CSV files
"""
        self.notify(help_text)
    
    async def on_key(self, event: events.Key) -> None:
        """Handle global key events."""
        # Always allow command bar to receive focus with slash
        if event.key == "/":
            command_bar = self.query_one(CommandBar)
            command_bar.focus()
            event.prevent_default()
        else:
            try:
                # Try to handle the key with parent, but don't crash on undefined keys
                await super().on_key(event)
            except Exception:
                # Silently ignore undefined key presses to prevent crashes
                pass


def main() -> None:
    """Run the RiverTerminal application."""
    app = RiverTerminalApp()
    
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error running RiverTerminal: {e}")
        raise


if __name__ == "__main__":
    main()