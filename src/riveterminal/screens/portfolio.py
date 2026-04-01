"""Portfolio tracker screen for RiverTerminal."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    DataTable, Static, Button, Input, Label, SelectionList, 
    Collapsible, ProgressBar
)
from textual.coordinate import Coordinate
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.bar import Bar

from ..data.yahoo import YahooDataProvider
from ..db import db
from ..utils.formatting import format_currency, format_percentage, get_color_for_change


class PortfolioScreen(Screen):
    """Portfolio tracker screen with position management and P&L calculation."""
    
    BINDINGS = [
        ("a", "add_position", "Add Position"),
        ("e", "edit_position", "Edit Position"),
        ("d", "delete_position", "Delete Position"), 
        ("r", "refresh", "Refresh"),
        ("div", "view_dividends", "View Dividends"),
        ("export", "export_data", "Export to CSV"),
    ]
    
    def __init__(self):
        super().__init__()
        self.yahoo = YahooDataProvider()
        self.positions_data = []
        self.current_prices = {}
        self.adding_position = False
        self.editing_position_id = None
        
    def compose(self) -> ComposeResult:
        """Compose the portfolio screen layout."""
        with Vertical():
            # Header
            yield Static("📊 PORTFOLIO TRACKER", classes="header")
            
            # Summary stats
            with Horizontal(classes="summary-row"):
                yield Static("Total Value: Loading...", id="total_value")
                yield Static("Daily P&L: Loading...", id="daily_pnl") 
                yield Static("Total P&L: Loading...", id="total_pnl")
                yield Static("Total Return: Loading...", id="total_return")
            
            # Allocation chart
            with Collapsible(title="📈 Allocation Breakdown", collapsed=False):
                yield Static("", id="allocation_chart")
            
            # Position entry form (initially hidden)
            with Collapsible(title="➕ Add New Position", collapsed=True, id="position_form"):
                with Horizontal():
                    yield Label("Ticker:")
                    yield Input(placeholder="AAPL", id="ticker_input")
                with Horizontal():
                    yield Label("Shares:")
                    yield Input(placeholder="100", id="shares_input")
                with Horizontal():
                    yield Label("Cost Basis:")
                    yield Input(placeholder="150.00", id="cost_input")
                with Horizontal():
                    yield Label("Purchase Date:")
                    yield Input(placeholder="2024-01-01", id="date_input")
                with Horizontal():
                    yield Button("Save Position", id="save_btn", variant="primary")
                    yield Button("Cancel", id="cancel_btn")
            
            # Positions table
            yield DataTable(id="positions_table", cursor_type="row")
            
            # Dividend summary
            with Collapsible(title="💰 Dividend Summary", collapsed=True):
                yield Static("", id="dividend_summary")
    
    async def on_mount(self) -> None:
        """Initialize the portfolio screen."""
        await self.setup_table()
        await self.refresh_data()
        
        # Set up periodic refresh every 30 seconds
        self.set_interval(30.0, self.refresh_prices)
    
    async def setup_table(self) -> None:
        """Set up the positions table."""
        table = self.query_one("#positions_table", DataTable)
        table.add_columns(
            "Ticker", "Shares", "Cost Basis", "Current", "Market Value", 
            "Unrealized P&L", "Unrealized %", "Purchase Date"
        )
        table.cursor_type = "row"
    
    async def refresh_data(self) -> None:
        """Refresh portfolio data and calculations."""
        try:
            # Get positions from database
            self.positions_data = db.get_portfolio_positions()
            
            if not self.positions_data:
                # No positions to display
                self.update_summary(0, 0, 0, 0)
                self.update_allocation_chart([])
                table = self.query_one("#positions_table", DataTable)
                table.clear()
                return
            
            # Get current prices for all tickers
            tickers = [pos['ticker'] for pos in self.positions_data]
            await self.fetch_current_prices(tickers)
            
            # Calculate P&L and update table
            await self.calculate_pnl()
            await self.update_table()
            await self.update_allocation_chart()
            await self.update_dividend_summary()
            
        except Exception as e:
            self.notify(f"Error refreshing portfolio: {e}")
    
    async def fetch_current_prices(self, tickers: List[str]) -> None:
        """Fetch current prices for all tickers."""
        try:
            for ticker in tickers:
                quote = await self.yahoo.get_quote(ticker)
                if quote and 'current_price' in quote:
                    self.current_prices[ticker] = float(quote['current_price'])
                else:
                    self.current_prices[ticker] = 0.0
        except Exception as e:
            self.notify(f"Error fetching prices: {e}")
    
    async def calculate_pnl(self) -> None:
        """Calculate P&L for all positions."""
        total_value = 0
        total_cost = 0
        total_pnl = 0
        
        for pos in self.positions_data:
            ticker = pos['ticker']
            shares = float(pos['shares'])
            cost_basis = float(pos['cost_basis'])
            current_price = self.current_prices.get(ticker, 0)
            
            market_value = shares * current_price
            position_cost = shares * cost_basis
            unrealized_pnl = market_value - position_cost
            
            total_value += market_value
            total_cost += position_cost
            total_pnl += unrealized_pnl
            
            # Store calculated values in position data
            pos['current_price'] = current_price
            pos['market_value'] = market_value
            pos['unrealized_pnl'] = unrealized_pnl
            pos['unrealized_pct'] = (unrealized_pnl / position_cost * 100) if position_cost > 0 else 0
        
        # Calculate total return percentage
        total_return_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        self.update_summary(total_value, 0, total_pnl, total_return_pct)  # Daily P&L not implemented yet
    
    def update_summary(self, total_value: float, daily_pnl: float, total_pnl: float, total_return_pct: float) -> None:
        """Update summary statistics display."""
        try:
            self.query_one("#total_value").update(f"Total Value: {format_currency(total_value)}")
            self.query_one("#daily_pnl").update(f"Daily P&L: {format_currency(daily_pnl)}")
            
            total_pnl_color = get_color_for_change(total_pnl)
            total_return_color = get_color_for_change(total_return_pct)
            
            total_pnl_text = Text(f"Total P&L: {format_currency(total_pnl)}")
            total_pnl_text.stylize(total_pnl_color)
            
            total_return_text = Text(f"Total Return: {format_percentage(total_return_pct)}")
            total_return_text.stylize(total_return_color)
            
            self.query_one("#total_pnl").update(total_pnl_text)
            self.query_one("#total_return").update(total_return_text)
        except Exception as e:
            pass  # Ignore update errors
    
    async def update_table(self) -> None:
        """Update the positions table with current data."""
        table = self.query_one("#positions_table", DataTable)
        table.clear()
        
        for pos in self.positions_data:
            ticker = pos['ticker']
            shares = float(pos['shares'])
            cost_basis = float(pos['cost_basis'])
            current_price = pos.get('current_price', 0)
            market_value = pos.get('market_value', 0)
            unrealized_pnl = pos.get('unrealized_pnl', 0)
            unrealized_pct = pos.get('unrealized_pct', 0)
            purchase_date = pos['purchase_date']
            
            # Format values with colors
            pnl_color = get_color_for_change(unrealized_pnl)
            pct_color = get_color_for_change(unrealized_pct)
            
            table.add_row(
                ticker,
                f"{shares:,.2f}",
                format_currency(cost_basis),
                format_currency(current_price),
                format_currency(market_value),
                f"[{pnl_color}]{format_currency(unrealized_pnl)}[/]",
                f"[{pct_color}]{format_percentage(unrealized_pct)}[/]",
                purchase_date
            )
    
    async def update_allocation_chart(self) -> None:
        """Update the allocation breakdown chart."""
        try:
            if not self.positions_data:
                self.query_one("#allocation_chart").update("No positions to display")
                return
            
            # Calculate total portfolio value
            total_value = sum(pos.get('market_value', 0) for pos in self.positions_data)
            
            if total_value <= 0:
                self.query_one("#allocation_chart").update("Portfolio value is zero")
                return
            
            # Create allocation bars
            chart_lines = []
            for pos in self.positions_data:
                ticker = pos['ticker']
                market_value = pos.get('market_value', 0)
                allocation_pct = (market_value / total_value * 100) if total_value > 0 else 0
                
                # Create ASCII bar
                bar_width = max(1, int(allocation_pct / 2))  # Scale to reasonable width
                bar = "█" * bar_width
                
                line = f"{ticker:>6}: [{allocation_pct:5.1f}%] {bar} ${market_value:,.0f}"
                chart_lines.append(line)
            
            chart_text = "\n".join(chart_lines)
            self.query_one("#allocation_chart").update(chart_text)
            
        except Exception as e:
            self.query_one("#allocation_chart").update(f"Error updating chart: {e}")
    
    async def update_dividend_summary(self) -> None:
        """Update dividend summary display."""
        try:
            dividends = db.get_all_dividends()
            
            if not dividends:
                self.query_one("#dividend_summary").update("No dividend records")
                return
            
            # Calculate total dividends for current year
            current_year = datetime.now().year
            year_dividends = [d for d in dividends if d['ex_date'].startswith(str(current_year))]
            total_year_dividends = sum(d['amount'] for d in year_dividends)
            
            summary = f"Total Dividends ({current_year}): {format_currency(total_year_dividends)}\n"
            summary += f"Total Records: {len(dividends)}\n\n"
            
            # Recent dividends
            recent = dividends[:5]  # Last 5 dividends
            if recent:
                summary += "Recent Dividends:\n"
                for div in recent:
                    summary += f"{div['ticker']:>6} {div['ex_date']:>12} {format_currency(div['amount']):>10}\n"
            
            self.query_one("#dividend_summary").update(summary)
            
        except Exception as e:
            self.query_one("#dividend_summary").update(f"Error loading dividends: {e}")
    
    async def refresh_prices(self) -> None:
        """Refresh current prices (for periodic updates)."""
        if self.positions_data:
            tickers = [pos['ticker'] for pos in self.positions_data]
            await self.fetch_current_prices(tickers)
            await self.calculate_pnl()
            await self.update_table()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "save_btn":
            await self.save_position()
        elif button_id == "cancel_btn":
            await self.cancel_position_entry()
    
    async def save_position(self) -> None:
        """Save a new or edited position."""
        try:
            ticker = self.query_one("#ticker_input").value.strip().upper()
            shares_str = self.query_one("#shares_input").value.strip()
            cost_str = self.query_one("#cost_input").value.strip()
            date_str = self.query_one("#date_input").value.strip()
            
            if not all([ticker, shares_str, cost_str, date_str]):
                self.notify("All fields are required")
                return
            
            shares = float(shares_str)
            cost_basis = float(cost_str)
            
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
            
            if self.editing_position_id:
                # Update existing position
                db.update_portfolio_position(
                    self.editing_position_id, shares, cost_basis, date_str
                )
                self.notify(f"Updated position for {ticker}")
                self.editing_position_id = None
            else:
                # Add new position
                db.add_portfolio_position(ticker, shares, cost_basis, date_str)
                self.notify(f"Added position: {ticker}")
            
            # Clear form and refresh
            await self.cancel_position_entry()
            await self.refresh_data()
            
        except ValueError as e:
            self.notify(f"Invalid input: {e}")
        except Exception as e:
            self.notify(f"Error saving position: {e}")
    
    async def cancel_position_entry(self) -> None:
        """Cancel position entry and hide form."""
        self.query_one("#ticker_input").value = ""
        self.query_one("#shares_input").value = ""
        self.query_one("#cost_input").value = ""
        self.query_one("#date_input").value = ""
        
        form = self.query_one("#position_form")
        form.collapsed = True
        self.adding_position = False
        self.editing_position_id = None
    
    def action_add_position(self) -> None:
        """Show add position form."""
        form = self.query_one("#position_form")
        form.collapsed = False
        form.title = "➕ Add New Position"
        self.adding_position = True
        self.editing_position_id = None
        
        # Focus ticker input
        self.query_one("#ticker_input").focus()
    
    def action_edit_position(self) -> None:
        """Edit selected position."""
        table = self.query_one("#positions_table", DataTable)
        
        if table.cursor_coordinate == Coordinate(0, 0):
            self.notify("Select a position to edit")
            return
        
        try:
            row_index = table.cursor_coordinate.row
            if row_index < len(self.positions_data):
                pos = self.positions_data[row_index]
                
                # Populate form with current values
                self.query_one("#ticker_input").value = pos['ticker']
                self.query_one("#shares_input").value = str(pos['shares'])
                self.query_one("#cost_input").value = str(pos['cost_basis'])
                self.query_one("#date_input").value = pos['purchase_date']
                
                # Show form
                form = self.query_one("#position_form")
                form.collapsed = False
                form.title = f"✏️ Edit Position: {pos['ticker']}"
                self.editing_position_id = pos['id']
                
                self.query_one("#ticker_input").focus()
        except Exception as e:
            self.notify(f"Error editing position: {e}")
    
    def action_delete_position(self) -> None:
        """Delete selected position."""
        table = self.query_one("#positions_table", DataTable)
        
        if table.cursor_coordinate == Coordinate(0, 0):
            self.notify("Select a position to delete")
            return
        
        try:
            row_index = table.cursor_coordinate.row
            if row_index < len(self.positions_data):
                pos = self.positions_data[row_index]
                
                # Delete from database
                db.delete_portfolio_position(pos['id'])
                self.notify(f"Deleted position: {pos['ticker']}")
                
                # Refresh data
                asyncio.create_task(self.refresh_data())
        except Exception as e:
            self.notify(f"Error deleting position: {e}")
    
    def action_refresh(self) -> None:
        """Refresh portfolio data."""
        asyncio.create_task(self.refresh_data())
        self.notify("Refreshing portfolio...")
    
    def action_export_data(self) -> None:
        """Export portfolio data to CSV."""
        try:
            import csv
            from pathlib import Path
            
            # Create export directory
            export_dir = Path.home() / "Downloads" / "riveterminal"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_dir / f"portfolio_{timestamp}.csv"
            
            # Write CSV file
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Headers
                writer.writerow([
                    'Ticker', 'Shares', 'Cost Basis', 'Current Price', 'Market Value',
                    'Unrealized P&L', 'Unrealized %', 'Purchase Date'
                ])
                
                # Data rows
                for pos in self.positions_data:
                    writer.writerow([
                        pos['ticker'],
                        pos['shares'],
                        pos['cost_basis'],
                        pos.get('current_price', 0),
                        pos.get('market_value', 0),
                        pos.get('unrealized_pnl', 0),
                        pos.get('unrealized_pct', 0),
                        pos['purchase_date']
                    ])
            
            self.notify(f"Portfolio exported to {filename}")
            
        except Exception as e:
            self.notify(f"Error exporting: {e}")