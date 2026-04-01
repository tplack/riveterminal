"""Options chain viewer for RiverTerminal."""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    DataTable, Static, Button, Input, Label, Select, Tabs, TabPane
)
from textual.coordinate import Coordinate
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..data.yahoo import YahooDataProvider
from ..utils.formatting import format_currency, format_percentage, get_color_for_change


class OptionsScreen(Screen):
    """Options chain viewer with put/call data and Greeks."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("c", "show_calls", "Calls Only"),
        ("p", "show_puts", "Puts Only"),
        ("b", "show_both", "Both"),
        ("n", "next_expiry", "Next Expiry"),
        ("prev", "prev_expiry", "Prev Expiry"),
        ("enter", "view_option_details", "Option Details"),
    ]
    
    def __init__(self, ticker: str = "AAPL"):
        super().__init__()
        self.yahoo = YahooDataProvider()
        self.current_ticker = ticker.upper()
        self.expiry_dates = []
        self.current_expiry_index = 0
        self.current_view = "both"  # "calls", "puts", "both"
        self.options_data = {}
        self.underlying_price = 0.0
        
    def compose(self) -> ComposeResult:
        """Compose the options chain layout."""
        with Vertical():
            # Header
            yield Static(f"📊 OPTIONS CHAIN - {self.current_ticker}", classes="header", id="header")
            
            # Input controls
            with Horizontal(classes="controls"):
                yield Label("Ticker:")
                yield Input(value=self.current_ticker, placeholder="AAPL", id="ticker_input")
                yield Button("Load", id="load_btn", variant="primary")
                yield Label("Expiry:")
                yield Static("Loading...", id="expiry_info")
                yield Button("◀ Prev", id="prev_btn")
                yield Button("Next ▶", id="next_btn")
            
            # Underlying info
            with Horizontal(classes="underlying-info"):
                yield Static("Underlying: Loading...", id="underlying_info")
                yield Static("Last Update: --", id="last_update")
                
            # View selector tabs
            with Tabs("calls", "puts", "both", id="view_tabs"):
                with TabPane("Calls", id="calls_tab"):
                    yield DataTable(id="calls_table", cursor_type="row")
                    
                with TabPane("Puts", id="puts_tab"):
                    yield DataTable(id="puts_table", cursor_type="row")
                    
                with TabPane("Both", id="both_tab"):
                    with Horizontal():
                        with Vertical(classes="calls-column"):
                            yield Static("🟢 CALLS", classes="table-header")
                            yield DataTable(id="calls_table_both", cursor_type="row")
                        with Vertical(classes="puts-column"):
                            yield Static("🔴 PUTS", classes="table-header")
                            yield DataTable(id="puts_table_both", cursor_type="row")
            
            # Option details panel
            yield Static("Select an option to view details", id="option_details")
    
    async def on_mount(self) -> None:
        """Initialize the options screen."""
        await self.load_options_chain()
    
    async def load_options_chain(self) -> None:
        """Load options chain data for current ticker."""
        try:
            self.notify(f"Loading options for {self.current_ticker}...")
            
            # Get options data from Yahoo Finance
            options_info = await self.yahoo.get_options_chain(self.current_ticker)
            
            if not options_info:
                self.notify(f"No options data found for {self.current_ticker}")
                return
            
            # Extract expiry dates
            self.expiry_dates = options_info.get('expiry_dates', [])
            if not self.expiry_dates:
                self.notify(f"No expiry dates found for {self.current_ticker}")
                return
            
            # Reset to first expiry
            self.current_expiry_index = 0
            
            # Get underlying price
            self.underlying_price = options_info.get('underlying_price', 0.0)
            
            # Store options data
            self.options_data = options_info.get('options', {})
            
            await self.update_display()
            await self.setup_tables()
            await self.populate_tables()
            
        except Exception as e:
            self.notify(f"Error loading options: {e}")
    
    async def update_display(self) -> None:
        """Update header and info displays."""
        try:
            # Update header
            self.query_one("#header").update(f"📊 OPTIONS CHAIN - {self.current_ticker}")
            
            # Update underlying info
            underlying_text = f"Underlying: {self.current_ticker} = ${self.underlying_price:.2f}"
            self.query_one("#underlying_info").update(underlying_text)
            
            # Update expiry info
            if self.expiry_dates:
                current_expiry = self.expiry_dates[self.current_expiry_index]
                expiry_text = f"{current_expiry} ({self.current_expiry_index + 1}/{len(self.expiry_dates)})"
                self.query_one("#expiry_info").update(expiry_text)
            
            # Update timestamp
            now = datetime.now().strftime("%H:%M:%S")
            self.query_one("#last_update").update(f"Last Update: {now}")
            
        except Exception as e:
            pass  # Ignore display update errors
    
    async def setup_tables(self) -> None:
        """Set up all options tables."""
        tables = [
            self.query_one("#calls_table"),
            self.query_one("#puts_table"),
            self.query_one("#calls_table_both"),
            self.query_one("#puts_table_both"),
        ]
        
        for table in tables:
            table.clear()
            table.add_columns(
                "Strike", "Last", "Bid", "Ask", "Volume", "OI", "IV", "Delta", "Gamma", "Theta"
            )
            table.cursor_type = "row"
    
    async def populate_tables(self) -> None:
        """Populate options tables with current expiry data."""
        if not self.expiry_dates or self.current_expiry_index >= len(self.expiry_dates):
            return
        
        current_expiry = self.expiry_dates[self.current_expiry_index]
        options_for_expiry = self.options_data.get(current_expiry, {})
        
        calls = options_for_expiry.get('calls', [])
        puts = options_for_expiry.get('puts', [])
        
        # Populate calls tables
        calls_tables = [self.query_one("#calls_table"), self.query_one("#calls_table_both")]
        for table in calls_tables:
            table.clear()
            table.add_columns(
                "Strike", "Last", "Bid", "Ask", "Volume", "OI", "IV", "Delta", "Gamma", "Theta"
            )
            await self.populate_table_with_options(table, calls, "call")
        
        # Populate puts tables  
        puts_tables = [self.query_one("#puts_table"), self.query_one("#puts_table_both")]
        for table in puts_tables:
            table.clear()
            table.add_columns(
                "Strike", "Last", "Bid", "Ask", "Volume", "OI", "IV", "Delta", "Gamma", "Theta"
            )
            await self.populate_table_with_options(table, puts, "put")
    
    async def populate_table_with_options(self, table: DataTable, options: List[Dict], option_type: str) -> None:
        """Populate a table with options data."""
        try:
            for option in options:
                strike = option.get('strike', 0)
                last = option.get('lastPrice', 0)
                bid = option.get('bid', 0)
                ask = option.get('ask', 0)
                volume = option.get('volume', 0)
                open_interest = option.get('openInterest', 0)
                implied_vol = option.get('impliedVolatility', 0)
                
                # Greeks (may not be available)
                delta = option.get('delta', 0)
                gamma = option.get('gamma', 0) 
                theta = option.get('theta', 0)
                
                # Color coding for ITM/OTM
                if option_type == "call":
                    itm = strike < self.underlying_price
                else:
                    itm = strike > self.underlying_price
                
                strike_color = "green" if itm else "white"
                
                # Format values
                strike_str = f"[{strike_color}]{strike:.2f}[/]"
                last_str = f"{last:.2f}" if last > 0 else "-"
                bid_str = f"{bid:.2f}" if bid > 0 else "-"
                ask_str = f"{ask:.2f}" if ask > 0 else "-"
                vol_str = f"{volume:,}" if volume > 0 else "-"
                oi_str = f"{open_interest:,}" if open_interest > 0 else "-"
                iv_str = f"{implied_vol:.1%}" if implied_vol > 0 else "-"
                delta_str = f"{delta:.3f}" if delta != 0 else "-"
                gamma_str = f"{gamma:.3f}" if gamma != 0 else "-" 
                theta_str = f"{theta:.3f}" if theta != 0 else "-"
                
                table.add_row(
                    strike_str, last_str, bid_str, ask_str, vol_str, 
                    oi_str, iv_str, delta_str, gamma_str, theta_str
                )
                
        except Exception as e:
            self.notify(f"Error populating table: {e}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "load_btn":
            ticker = self.query_one("#ticker_input").value.strip().upper()
            if ticker:
                self.current_ticker = ticker
                await self.load_options_chain()
        elif button_id == "prev_btn":
            await self.prev_expiry()
        elif button_id == "next_btn":
            await self.next_expiry()
    
    async def prev_expiry(self) -> None:
        """Switch to previous expiry date."""
        if self.expiry_dates and self.current_expiry_index > 0:
            self.current_expiry_index -= 1
            await self.update_display()
            await self.populate_tables()
    
    async def next_expiry(self) -> None:
        """Switch to next expiry date."""
        if self.expiry_dates and self.current_expiry_index < len(self.expiry_dates) - 1:
            self.current_expiry_index += 1
            await self.update_display()
            await self.populate_tables()
    
    def action_next_expiry(self) -> None:
        """Action to go to next expiry."""
        asyncio.create_task(self.next_expiry())
    
    def action_prev_expiry(self) -> None:
        """Action to go to previous expiry."""
        asyncio.create_task(self.prev_expiry())
    
    def action_refresh(self) -> None:
        """Refresh options chain."""
        asyncio.create_task(self.load_options_chain())
    
    def action_show_calls(self) -> None:
        """Show calls tab."""
        tabs = self.query_one("#view_tabs")
        tabs.active = "calls"
    
    def action_show_puts(self) -> None:
        """Show puts tab."""
        tabs = self.query_one("#view_tabs")
        tabs.active = "puts"
    
    def action_show_both(self) -> None:
        """Show both calls and puts."""
        tabs = self.query_one("#view_tabs")
        tabs.active = "both"
    
    async def action_view_option_details(self) -> None:
        """View details for selected option."""
        try:
            # Get active tab
            tabs = self.query_one("#view_tabs")
            active_tab = tabs.active
            
            if active_tab == "calls":
                table = self.query_one("#calls_table")
            elif active_tab == "puts":
                table = self.query_one("#puts_table")
            else:
                # For "both" tab, we need to determine which table has focus
                table = self.query_one("#calls_table_both")  # Default to calls
            
            cursor = table.cursor_coordinate
            if cursor.row >= 0:
                # Get option data for selected row
                if not self.expiry_dates:
                    return
                    
                current_expiry = self.expiry_dates[self.current_expiry_index]
                options_for_expiry = self.options_data.get(current_expiry, {})
                
                if active_tab in ["calls", "both"]:
                    options_list = options_for_expiry.get('calls', [])
                    option_type = "CALL"
                else:
                    options_list = options_for_expiry.get('puts', [])
                    option_type = "PUT"
                
                if cursor.row < len(options_list):
                    option = options_list[cursor.row]
                    await self.show_option_details(option, option_type)
                    
        except Exception as e:
            self.notify(f"Error viewing details: {e}")
    
    async def show_option_details(self, option: Dict, option_type: str) -> None:
        """Show detailed information for a specific option."""
        try:
            strike = option.get('strike', 0)
            expiry = self.expiry_dates[self.current_expiry_index]
            
            details = f"""
🎯 OPTION DETAILS

Contract: {self.current_ticker} {expiry} {strike:.2f} {option_type}
Underlying: {self.current_ticker} @ ${self.underlying_price:.2f}

PRICING:
Last Price: ${option.get('lastPrice', 0):.2f}
Bid: ${option.get('bid', 0):.2f}
Ask: ${option.get('ask', 0):.2f}
Mark: ${(option.get('bid', 0) + option.get('ask', 0)) / 2:.2f}

VOLUME & INTEREST:
Volume: {option.get('volume', 0):,}
Open Interest: {option.get('openInterest', 0):,}
Bid Size: {option.get('bidSize', 0):,}
Ask Size: {option.get('askSize', 0):,}

GREEKS:
Delta: {option.get('delta', 0):.4f}
Gamma: {option.get('gamma', 0):.4f}
Theta: {option.get('theta', 0):.4f}
Vega: {option.get('vega', 0):.4f}
Rho: {option.get('rho', 0):.4f}

IMPLIED VOLATILITY: {option.get('impliedVolatility', 0):.2%}

MONEYNESS:
"""
            
            if option_type == "CALL":
                moneyness = self.underlying_price - strike
                if moneyness > 0:
                    details += f"In-the-Money by ${moneyness:.2f}"
                else:
                    details += f"Out-of-the-Money by ${abs(moneyness):.2f}"
            else:
                moneyness = strike - self.underlying_price
                if moneyness > 0:
                    details += f"In-the-Money by ${moneyness:.2f}"
                else:
                    details += f"Out-of-the-Money by ${abs(moneyness):.2f}"
            
            self.query_one("#option_details").update(details.strip())
            
        except Exception as e:
            self.query_one("#option_details").update(f"Error loading details: {e}")
    
    def set_ticker(self, ticker: str) -> None:
        """Set ticker and reload options."""
        self.current_ticker = ticker.upper()
        self.query_one("#ticker_input").value = self.current_ticker
        asyncio.create_task(self.load_options_chain())