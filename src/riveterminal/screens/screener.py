"""Stock screener screen."""

import asyncio
import yfinance as yf
from typing import Dict, List, Any, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, DataTable, Input, Button, Select
from textual.screen import Screen
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from ..utils.formatting import format_number, format_percentage
from ..db import db


class ScreenerScreen(Screen):
    """Stock screener with fundamental filters."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("1", "app.show_dashboard", "Dashboard"),
        ("f", "apply_filters", "Apply Filters"),
        ("c", "clear_filters", "Clear"),
        ("a", "add_to_watchlist", "Add to Watchlist"),
        ("enter", "view_stock", "View Stock"),
        ("q", "app.quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.stocks_data = []
        self.filtered_data = []
        self.sp500_tickers = self._get_sp500_sample()  # Sample S&P 500 tickers
        self.filters = {
            "min_market_cap": None,
            "max_market_cap": None,
            "min_pe": None,
            "max_pe": None,
            "min_dividend_yield": None,
            "max_dividend_yield": None,
            "sector": None,
            "min_52w_change": None,
            "max_52w_change": None,
        }
    
    def compose(self) -> ComposeResult:
        """Compose the screener layout."""
        with Vertical():
            # Filter controls
            with Horizontal():
                with Vertical():
                    yield Static("🔍 Stock Filters", style="bold cyan")
                    with Horizontal():
                        yield Input(placeholder="Min Market Cap (B)", id="min-market-cap")
                        yield Input(placeholder="Max Market Cap (B)", id="max-market-cap")
                    with Horizontal():
                        yield Input(placeholder="Min P/E", id="min-pe")
                        yield Input(placeholder="Max P/E", id="max-pe")
                    with Horizontal():
                        yield Input(placeholder="Min Div Yield %", id="min-div-yield")
                        yield Input(placeholder="Max Div Yield %", id="max-div-yield")
                    with Horizontal():
                        yield Input(placeholder="Min 52W Change %", id="min-52w-change")
                        yield Input(placeholder="Max 52W Change %", id="max-52w-change")
                    with Horizontal():
                        yield Button("Apply Filters", id="apply-btn", variant="primary")
                        yield Button("Clear", id="clear-btn")
                        yield Button("Refresh Data", id="refresh-btn")
            
            # Results table
            yield DataTable(id="results-table")
            
            # Status bar
            yield Static("Ready", id="status-bar", classes="status")
    
    async def on_mount(self) -> None:
        """Initialize the screener."""
        self.setup_results_table()
        await self.load_stock_data()
    
    def setup_results_table(self) -> None:
        """Setup the results data table."""
        table = self.query_one("#results-table", DataTable)
        table.add_column("Symbol", width=8)
        table.add_column("Name", width=20)
        table.add_column("Price", width=10)
        table.add_column("Market Cap", width=12)
        table.add_column("P/E", width=8)
        table.add_column("Div Yield", width=10)
        table.add_column("52W Change", width=10)
        table.add_column("Sector", width=15)
        table.cursor_type = "row"
    
    async def action_refresh(self) -> None:
        """Refresh stock data."""
        await self.load_stock_data()
        self.notify("Stock data refreshed")
    
    async def action_apply_filters(self) -> None:
        """Apply current filter settings."""
        await self.apply_filters()
    
    async def action_clear_filters(self) -> None:
        """Clear all filters."""
        self.clear_filters()
    
    async def action_add_to_watchlist(self) -> None:
        """Add selected stock to watchlist."""
        table = self.query_one("#results-table", DataTable)
        if table.cursor_row >= 0 and table.cursor_row < len(self.filtered_data):
            stock = self.filtered_data[table.cursor_row]
            symbol = stock.get('symbol')
            if symbol:
                try:
                    watchlist_id = db.get_default_watchlist_id()
                    if db.add_to_watchlist(watchlist_id, symbol):
                        self.notify(f"Added {symbol} to watchlist")
                    else:
                        self.notify(f"{symbol} already in watchlist")
                except Exception as e:
                    self.notify(f"Error adding to watchlist: {e}")
    
    async def action_view_stock(self) -> None:
        """View selected stock in quote screen."""
        table = self.query_one("#results-table", DataTable)
        if table.cursor_row >= 0 and table.cursor_row < len(self.filtered_data):
            stock = self.filtered_data[table.cursor_row]
            symbol = stock.get('symbol')
            if symbol:
                # Switch to quote screen with this symbol
                self.app.push_screen("quote")
                # TODO: Set symbol on quote screen
                self.notify(f"Viewing {symbol}")
    
    async def load_stock_data(self) -> None:
        """Load fundamental data for S&P 500 stocks."""
        try:
            self.update_status("Loading stock data...")
            
            # Load data for a subset of S&P 500 stocks
            # In production, this would be cached and updated periodically
            batch_size = 20  # Process in smaller batches to avoid rate limits
            
            for i in range(0, min(len(self.sp500_tickers), 100), batch_size):
                batch = self.sp500_tickers[i:i+batch_size]
                batch_data = await self._load_batch_data(batch)
                self.stocks_data.extend(batch_data)
                
                self.update_status(f"Loaded {len(self.stocks_data)} stocks...")
                await asyncio.sleep(0.5)  # Rate limiting
            
            # Apply current filters
            await self.apply_filters()
            self.update_status(f"Loaded {len(self.stocks_data)} stocks")
            
        except Exception as e:
            self.notify(f"Error loading stock data: {e}")
            self.update_status("Error loading data")
    
    async def _load_batch_data(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """Load fundamental data for a batch of tickers."""
        batch_data = []
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="1y")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    year_start_price = hist['Close'].iloc[0]
                    year_change = ((current_price - year_start_price) / year_start_price) * 100
                else:
                    current_price = info.get('currentPrice', 0)
                    year_change = info.get('52WeekChange', 0) * 100
                
                stock_data = {
                    'symbol': ticker,
                    'name': info.get('longName', ticker)[:20],
                    'price': current_price,
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 0),
                    'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                    'sector': info.get('sector', 'Unknown'),
                    'year_change': year_change,
                }
                
                batch_data.append(stock_data)
                
            except Exception:
                # If data fetch fails, create placeholder entry
                batch_data.append({
                    'symbol': ticker,
                    'name': ticker,
                    'price': 0,
                    'market_cap': 0,
                    'pe_ratio': 0,
                    'dividend_yield': 0,
                    'sector': 'Unknown',
                    'year_change': 0,
                })
        
        return batch_data
    
    async def apply_filters(self) -> None:
        """Apply current filter settings to stock data."""
        try:
            # Get filter values from inputs
            self._update_filters_from_inputs()
            
            # Filter the data
            self.filtered_data = []
            
            for stock in self.stocks_data:
                if self._stock_passes_filters(stock):
                    self.filtered_data.append(stock)
            
            # Update the results table
            self.update_results_table()
            
            self.update_status(f"Showing {len(self.filtered_data)} of {len(self.stocks_data)} stocks")
            
        except Exception as e:
            self.notify(f"Error applying filters: {e}")
    
    def _update_filters_from_inputs(self) -> None:
        """Update filter values from input widgets."""
        try:
            # Market cap filters (in billions)
            min_mc_input = self.query_one("#min-market-cap", Input)
            max_mc_input = self.query_one("#max-market-cap", Input)
            
            self.filters['min_market_cap'] = float(min_mc_input.value) * 1e9 if min_mc_input.value else None
            self.filters['max_market_cap'] = float(max_mc_input.value) * 1e9 if max_mc_input.value else None
            
            # P/E filters
            min_pe_input = self.query_one("#min-pe", Input)
            max_pe_input = self.query_one("#max-pe", Input)
            
            self.filters['min_pe'] = float(min_pe_input.value) if min_pe_input.value else None
            self.filters['max_pe'] = float(max_pe_input.value) if max_pe_input.value else None
            
            # Dividend yield filters
            min_div_input = self.query_one("#min-div-yield", Input)
            max_div_input = self.query_one("#max-div-yield", Input)
            
            self.filters['min_dividend_yield'] = float(min_div_input.value) if min_div_input.value else None
            self.filters['max_dividend_yield'] = float(max_div_input.value) if max_div_input.value else None
            
            # 52-week change filters
            min_52w_input = self.query_one("#min-52w-change", Input)
            max_52w_input = self.query_one("#max-52w-change", Input)
            
            self.filters['min_52w_change'] = float(min_52w_input.value) if min_52w_input.value else None
            self.filters['max_52w_change'] = float(max_52w_input.value) if max_52w_input.value else None
            
        except ValueError:
            self.notify("Invalid filter values - please enter numbers only")
    
    def _stock_passes_filters(self, stock: Dict[str, Any]) -> bool:
        """Check if stock passes all active filters."""
        # Market cap filter
        if self.filters['min_market_cap'] is not None:
            if stock.get('market_cap', 0) < self.filters['min_market_cap']:
                return False
        
        if self.filters['max_market_cap'] is not None:
            if stock.get('market_cap', 0) > self.filters['max_market_cap']:
                return False
        
        # P/E filter
        if self.filters['min_pe'] is not None:
            pe = stock.get('pe_ratio', 0)
            if pe <= 0 or pe < self.filters['min_pe']:
                return False
        
        if self.filters['max_pe'] is not None:
            pe = stock.get('pe_ratio', 0)
            if pe <= 0 or pe > self.filters['max_pe']:
                return False
        
        # Dividend yield filter
        if self.filters['min_dividend_yield'] is not None:
            if stock.get('dividend_yield', 0) < self.filters['min_dividend_yield']:
                return False
        
        if self.filters['max_dividend_yield'] is not None:
            if stock.get('dividend_yield', 0) > self.filters['max_dividend_yield']:
                return False
        
        # 52-week change filter
        if self.filters['min_52w_change'] is not None:
            if stock.get('year_change', 0) < self.filters['min_52w_change']:
                return False
        
        if self.filters['max_52w_change'] is not None:
            if stock.get('year_change', 0) > self.filters['max_52w_change']:
                return False
        
        return True
    
    def update_results_table(self) -> None:
        """Update the results table with filtered data."""
        try:
            table = self.query_one("#results-table", DataTable)
            table.clear()
            
            for stock in self.filtered_data:
                # Format values
                price = f"${stock.get('price', 0):.2f}"
                market_cap = format_number(stock.get('market_cap', 0))
                
                pe = stock.get('pe_ratio', 0)
                pe_str = f"{pe:.1f}" if pe > 0 else "N/A"
                
                div_yield = stock.get('dividend_yield', 0)
                div_str = f"{div_yield:.2f}%" if div_yield > 0 else "0.00%"
                
                year_change = stock.get('year_change', 0)
                if year_change > 0:
                    change_str = f"[green]+{year_change:.1f}%[/green]"
                elif year_change < 0:
                    change_str = f"[red]{year_change:.1f}%[/red]"
                else:
                    change_str = "0.0%"
                
                table.add_row(
                    stock.get('symbol', ''),
                    stock.get('name', '')[:20],
                    price,
                    market_cap,
                    pe_str,
                    div_str,
                    change_str,
                    stock.get('sector', '')[:15]
                )
                
        except Exception as e:
            self.notify(f"Error updating results table: {e}")
    
    def clear_filters(self) -> None:
        """Clear all filter inputs."""
        try:
            # Clear all input fields
            input_ids = ["min-market-cap", "max-market-cap", "min-pe", "max-pe", 
                        "min-div-yield", "max-div-yield", "min-52w-change", "max-52w-change"]
            
            for input_id in input_ids:
                input_widget = self.query_one(f"#{input_id}", Input)
                input_widget.value = ""
            
            # Reset filters dict
            self.filters = {key: None for key in self.filters.keys()}
            
            # Show all data
            self.filtered_data = self.stocks_data.copy()
            self.update_results_table()
            
            self.update_status(f"Filters cleared - showing all {len(self.stocks_data)} stocks")
            
        except Exception as e:
            self.notify(f"Error clearing filters: {e}")
    
    def update_status(self, message: str) -> None:
        """Update status bar."""
        try:
            status_bar = self.query_one("#status-bar", Static)
            status_bar.update(message)
        except Exception:
            pass
    
    def _get_sp500_sample(self) -> List[str]:
        """Get a sample of S&P 500 tickers."""
        # Sample of popular S&P 500 stocks for demonstration
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'V', 'JNJ',
            'WMT', 'UNH', 'XOM', 'JPM', 'PG', 'CVX', 'HD', 'MA', 'ABBV', 'PFE',
            'KO', 'AVGO', 'BAC', 'PEP', 'TMO', 'COST', 'DIS', 'ABT', 'MRK', 'CSCO',
            'VZ', 'ADBE', 'ACN', 'NFLX', 'NKE', 'T', 'CRM', 'INTC', 'WFC', 'LLY',
            'AMD', 'TXN', 'LOW', 'NEE', 'UPS', 'QCOM', 'RTX', 'IBM', 'AMGN', 'HON',
            'SPGI', 'CVS', 'INTU', 'CAT', 'GS', 'AXP', 'BKNG', 'DE', 'BLK', 'GILD',
            'MDT', 'LMT', 'MO', 'ELV', 'SYK', 'ADI', 'TJX', 'MMM', 'VRTX', 'SCHW',
            'BA', 'AMT', 'MDLZ', 'C', 'ZTS', 'NOW', 'PLD', 'CB', 'ISRG', 'SO',
            'TMUS', 'MU', 'DUK', 'PYPL', 'REGN', 'CL', 'EOG', 'BSX', 'NOC', 'AON',
            'APD', 'PNC', 'CSX', 'EQIX', 'SHW', 'CCI', 'GE', 'ATVI', 'ICE', 'USB'
        ]
    
    def action_export_data(self) -> None:
        """Export screener results to CSV."""
        try:
            import csv
            from pathlib import Path
            from datetime import datetime
            
            # Create export directory
            export_dir = Path.home() / "Downloads" / "riveterminal"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_dir / f"screener_results_{timestamp}.csv"
            
            if not self.filtered_data:
                self.notify("No screener results to export")
                return
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Headers
                writer.writerow([
                    'Symbol', 'Company Name', 'Price', 'Market Cap', 'P/E Ratio', 
                    'Dividend Yield %', '52-Week Change %', 'Sector'
                ])
                
                # Data rows
                for stock in self.filtered_data:
                    writer.writerow([
                        stock.get('symbol', ''),
                        stock.get('name', ''),
                        stock.get('price', 0),
                        stock.get('market_cap', 0),
                        stock.get('pe_ratio', 0),
                        stock.get('dividend_yield', 0),
                        stock.get('year_change', 0),
                        stock.get('sector', '')
                    ])
            
            self.notify(f"Screener results exported to {filename}")
            
        except Exception as e:
            self.notify(f"Error exporting screener results: {e}")
    
    async def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "apply-btn":
            await self.apply_filters()
        elif event.button.id == "clear-btn":
            self.clear_filters()
        elif event.button.id == "refresh-btn":
            await self.load_stock_data()