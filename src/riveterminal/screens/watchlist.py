"""Watchlist screen for managing stock lists."""

import asyncio
from textual.widgets import Static, DataTable, Input
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from typing import Dict, List, Any

from ..data.yahoo import yahoo
from ..utils.formatting import format_time_only, get_change_color
from ..db import db


class WatchlistTable(DataTable):
    """Custom DataTable for watchlist display."""
    
    def __init__(self):
        super().__init__()
        self.watchlist_data = {}
        self.current_watchlist_id = None
        
        # Configure table
        self.cursor_type = "row"
        self.zebra_stripes = True
        
        # Add columns
        self.add_column("Symbol", width=10)
        self.add_column("Name", width=25)
        self.add_column("Price", width=12)
        self.add_column("Change", width=15)
        self.add_column("Change %", width=12)
        self.add_column("Volume", width=12)
    
    async def load_watchlist(self, watchlist_id: int):
        """Load and display watchlist."""
        self.current_watchlist_id = watchlist_id
        
        # Get watchlist items
        items = db.get_watchlist_items(watchlist_id)
        if not items:
            self.clear()
            self.add_row("No stocks in watchlist")
            return
        
        # Get quotes for all symbols
        symbols = [item['ticker'] for item in items]
        quotes = await yahoo.get_multiple_quotes(symbols)
        
        # Clear and populate table
        self.clear()
        
        for item in items:
            symbol = item['ticker']
            quote = quotes.get(symbol, {})
            
            if quote:
                name = quote.get('company_name', symbol)[:25]
                price = f"${quote.get('price', 0):.2f}"
                change = quote.get('change', 0)
                change_pct = quote.get('change_percent', 0)
                volume = self._format_volume(quote.get('volume', 0))
                
                # Style the row based on change
                if change > 0:
                    style = "green"
                elif change < 0:
                    style = "red"
                else:
                    style = None
                
                self.add_row(
                    symbol,
                    name,
                    price,
                    f"{change:+.2f}",
                    f"{change_pct:+.2f}%",
                    volume,
                    key=symbol
                )
                
                # Apply style to the row if needed
                if style:
                    row_index = len(self.rows) - 1
                    for col_index in range(len(self.columns)):
                        self.update_cell_at((row_index, col_index), 
                                          self.get_cell_at((row_index, col_index)), 
                                          style=style)
            else:
                # No quote data available
                self.add_row(
                    symbol,
                    "No data",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    key=symbol
                )
    
    def _format_volume(self, volume: int) -> str:
        """Format volume with suffixes."""
        if volume >= 1_000_000:
            return f"{volume/1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"{volume/1_000:.1f}K"
        else:
            return str(volume)
    
    async def remove_selected(self):
        """Remove selected symbol from watchlist."""
        if self.cursor_row < len(self.rows) and self.current_watchlist_id:
            row_key = self.get_row_at(self.cursor_row).key
            if row_key:
                db.remove_from_watchlist(self.current_watchlist_id, row_key)
                await self.load_watchlist(self.current_watchlist_id)
                return True
        return False
    
    def get_selected_symbol(self) -> str:
        """Get currently selected symbol."""
        if self.cursor_row < len(self.rows):
            row_key = self.get_row_at(self.cursor_row).key
            return row_key if row_key else ""
        return ""


class WatchlistScreen(Screen):
    """Watchlist screen for managing stock lists."""
    
    BINDINGS = [
        ("f1", "show_dashboard", "Dashboard"),
        ("f2", "show_quote", "Quote"),
        ("f3", "show_watchlist", "Watchlist"),
        ("f4", "show_chart", "Chart"),
        ("f6", "show_news", "News"),
        ("a", "add_symbol", "Add Symbol"),
        ("d", "delete_symbol", "Delete"),
        ("enter", "view_quote", "View Quote"),
        ("r", "refresh", "Refresh"),
        ("escape", "back", "Back"),
    ]
    
    def __init__(self):
        super().__init__()
        self.current_watchlist_id = None
        self.add_symbol_mode = False
    
    def compose(self):
        """Compose the watchlist screen layout."""
        with Vertical():
            # Header
            yield Static(self._get_header(), id="header")
            
            # Add symbol input (initially hidden)
            with Horizontal(id="add_symbol_container"):
                yield Static("Add Symbol: ", shrink=True)
                yield Input(
                    placeholder="Enter ticker symbol to add",
                    id="add_symbol_input"
                )
            
            # Watchlist table
            yield WatchlistTable()
            
            # Instructions
            yield Static(self._get_instructions(), id="instructions")
    
    def _get_header(self) -> Panel:
        """Get header panel."""
        current_time = format_time_only()
        header_text = Text()
        header_text.append("RiverTerminal", style="bold cyan")
        header_text.append(" | ", style="white")
        header_text.append("Watchlist", style="bold white")
        header_text.append(" | ", style="white")
        header_text.append(f"🕒 {current_time}", style="yellow")
        
        return Panel(
            Align.center(header_text),
            height=3,
            style="bold",
            border_style="blue"
        )
    
    def _get_instructions(self) -> Panel:
        """Get instructions panel."""
        instructions = Text()
        instructions.append("📋 Watchlist Controls:\n\n", style="bold cyan")
        instructions.append("• A: Add new symbol\n", style="white")
        instructions.append("• D: Delete selected symbol\n", style="white")
        instructions.append("• Enter: View quote for selected symbol\n", style="white")
        instructions.append("• R: Refresh prices\n", style="white")
        instructions.append("• ↑↓: Navigate list\n", style="white")
        
        return Panel(
            instructions,
            title="ℹ️ Instructions",
            title_align="left",
            border_style="green",
            height=10
        )
    
    async def on_mount(self):
        """Initialize the screen."""
        # Get default watchlist
        self.current_watchlist_id = db.get_default_watchlist_id()
        
        # Hide add symbol input initially
        add_container = self.query_one("#add_symbol_container")
        add_container.display = False
        
        # Load watchlist data
        await self.load_watchlist()
        
        # Set up auto-refresh every 30 seconds
        self.set_interval(30.0, self.load_watchlist)
        # Update header clock every second
        self.set_interval(1.0, self.update_header)
    
    async def load_watchlist(self):
        """Load watchlist data."""
        if self.current_watchlist_id:
            table = self.query_one(WatchlistTable)
            await table.load_watchlist(self.current_watchlist_id)
    
    def update_header(self):
        """Update the header with current time."""
        header_widget = self.query_one("#header", Static)
        header_widget.update(self._get_header())
    
    async def on_input_submitted(self, event):
        """Handle input submission."""
        if event.input.id == "add_symbol_input":
            symbol = event.input.value.strip().upper()
            if symbol:
                try:
                    success = db.add_to_watchlist(self.current_watchlist_id, symbol)
                    if success:
                        self.notify(f"Added {symbol} to watchlist")
                        await self.load_watchlist()
                    else:
                        self.notify(f"{symbol} already in watchlist")
                except Exception as e:
                    self.notify(f"Error adding symbol: {e}")
                
                # Hide input and clear
                event.input.value = ""
                self._hide_add_input()
    
    def _show_add_input(self):
        """Show add symbol input."""
        add_container = self.query_one("#add_symbol_container")
        add_container.display = True
        add_input = self.query_one("#add_symbol_input", Input)
        add_input.focus()
        self.add_symbol_mode = True
    
    def _hide_add_input(self):
        """Hide add symbol input."""
        add_container = self.query_one("#add_symbol_container")
        add_container.display = False
        table = self.query_one(WatchlistTable)
        table.focus()
        self.add_symbol_mode = False
    
    def action_add_symbol(self):
        """Show add symbol input."""
        self._show_add_input()
    
    async def action_delete_symbol(self):
        """Delete selected symbol from watchlist."""
        table = self.query_one(WatchlistTable)
        success = await table.remove_selected()
        if success:
            symbol = table.get_selected_symbol()
            self.notify(f"Removed {symbol} from watchlist")
        else:
            self.notify("No symbol selected")
    
    def action_view_quote(self):
        """View quote for selected symbol."""
        table = self.query_one(WatchlistTable)
        symbol = table.get_selected_symbol()
        if symbol:
            from .quote import QuoteScreen
            self.app.push_screen(QuoteScreen(symbol))
    
    def action_refresh(self):
        """Manual refresh action."""
        asyncio.create_task(self.load_watchlist())
    
    def action_back(self):
        """Go back to previous screen."""
        if self.add_symbol_mode:
            self._hide_add_input()
        else:
            self.app.pop_screen()
    
    def action_show_dashboard(self):
        """Switch to dashboard screen."""
        self.app.pop_screen()
    
    def action_show_quote(self):
        """Switch to quote screen."""
        self.app.push_screen("quote")
    
    def action_show_watchlist(self):
        """Stay on watchlist screen."""
        pass
    
    def action_show_chart(self):
        """Switch to chart screen."""
        table = self.query_one(WatchlistTable)
        symbol = table.get_selected_symbol()
        if symbol:
            from .chart import ChartScreen
            self.app.push_screen(ChartScreen(symbol))
        else:
            self.app.push_screen("chart")
    
    def action_show_news(self):
        """Switch to news screen."""
        self.app.push_screen("news")
    
    async def on_key(self, event: events.Key):
        """Handle key events."""
        if event.key == "escape" and self.add_symbol_mode:
            self._hide_add_input()
            event.prevent_default()
        else:
            await super().on_key(event)