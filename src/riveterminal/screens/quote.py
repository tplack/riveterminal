"""Quote screen for individual stock details."""

import asyncio
from textual.widgets import Static, Input
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from typing import Optional, Dict, Any

from ..data.yahoo import yahoo
from ..data.news_feeds import news
from ..data.sec import sec_provider
from ..utils.formatting import (
    format_price_change, format_currency, format_number, 
    format_ratio, format_time_only, get_change_color
)
from ..utils.charts import create_price_sparkline
from ..db import db


class QuoteDetailWidget(Static):
    """Widget showing detailed quote information."""
    
    def __init__(self):
        super().__init__()
        self.quote_data = None
        self.symbol = None
    
    async def load_quote(self, symbol: str):
        """Load quote data for symbol."""
        self.symbol = symbol.upper()
        try:
            self.quote_data = await yahoo.get_quote(self.symbol)
            self.update_display()
        except Exception as e:
            self.update(f"Error loading quote for {symbol}: {e}")
    
    def update_display(self):
        """Update the display with quote data."""
        if not self.quote_data:
            self.update("No quote data available")
            return
        
        data = self.quote_data
        
        # Main quote info
        main_table = Table(show_header=False, box=None, padding=(0, 2))
        main_table.add_column("", style="bold white", width=20)
        main_table.add_column("", style="white", width=20)
        
        # Company name and symbol
        company_name = data.get('company_name', self.symbol)
        main_table.add_row("Company:", f"{company_name} ({self.symbol})")
        main_table.add_row("Sector:", data.get('sector', 'N/A'))
        
        # Price information
        price = data.get('price', 0)
        change = data.get('change', 0)
        change_pct = data.get('change_percent', 0)
        
        change_color = get_change_color(change)
        price_text = Text()
        price_text.append(f"${price:.2f}", style="bold white")
        change_text = Text()
        change_text.append(f" {change:+.2f} ({change_pct:+.2f}%)", style=change_color)
        
        main_table.add_row("Price:", price_text + change_text)
        main_table.add_row("Open:", f"${data.get('open', 0):.2f}")
        main_table.add_row("High:", f"${data.get('high', 0):.2f}")
        main_table.add_row("Low:", f"${data.get('low', 0):.2f}")
        main_table.add_row("Volume:", format_number(data.get('volume', 0)))
        
        # Create fundamentals table
        fund_table = Table(show_header=False, box=None, padding=(0, 2))
        fund_table.add_column("", style="bold white", width=20)
        fund_table.add_column("", style="white", width=20)
        
        fund_table.add_row("Market Cap:", format_currency(data.get('market_cap', 0)))
        fund_table.add_row("P/E Ratio:", format_ratio(data.get('pe_ratio')))
        fund_table.add_row("EPS:", f"${data.get('eps', 0):.2f}")
        fund_table.add_row("Dividend Yield:", f"{data.get('dividend_yield', 0)*100:.2f}%")
        fund_table.add_row("Beta:", format_ratio(data.get('beta')))
        fund_table.add_row("52W High:", f"${data.get('fifty_two_week_high', 0):.2f}")
        fund_table.add_row("52W Low:", f"${data.get('fifty_two_week_low', 0):.2f}")
        
        # Combine tables side by side
        from rich.columns import Columns
        combined = Columns([main_table, fund_table])
        
        panel = Panel(
            combined,
            title=f"📈 {self.symbol} Quote Details",
            title_align="left",
            border_style="cyan"
        )
        
        self.update(panel)


class QuoteNewsWidget(Static):
    """Widget showing news for the current quote."""
    
    def __init__(self):
        super().__init__()
        self.news_data = []
        self.symbol = None
    
    async def load_news(self, symbol: str):
        """Load news for symbol."""
        self.symbol = symbol.upper()
        try:
            self.news_data = await news.get_ticker_news(self.symbol, limit=5)
            self.update_display()
        except Exception as e:
            self.update(f"Error loading news: {e}")
    
    def update_display(self):
        """Update the display with news."""
        if not self.news_data:
            self.update("No recent news found")
            return
        
        news_text = Text()
        for i, article in enumerate(self.news_data[:5]):
            news_text.append(f"• {article['title']}\n", style="white")
            news_text.append(f"  {article['source']} - {article['published'].strftime('%H:%M')}\n\n", 
                           style="dim white")
        
        panel = Panel(
            news_text,
            title=f"📰 Recent News - {self.symbol}",
            title_align="left",
            border_style="yellow"
        )
        
        self.update(panel)


class QuoteSECWidget(Static):
    """Widget showing SEC filings for the symbol."""
    
    def __init__(self):
        super().__init__()
        self.filings_data = None
        self.symbol = None
    
    async def load_filings(self, symbol: str):
        """Load SEC filings for symbol."""
        self.symbol = symbol.upper()
        try:
            self.filings_data = await sec_provider.search_filings(
                symbol, 
                filing_types=["10-K", "10-Q", "8-K"], 
                limit=10
            )
            self.update_display()
        except Exception as e:
            self.update(f"Error loading SEC filings: {e}")
    
    def update_display(self):
        """Update the display with filings data."""
        if not self.filings_data:
            self.update("No SEC filings found")
            return
        
        content = Text()
        content.append("🏛️  Recent SEC Filings\n\n", style="bold cyan")
        
        for filing in self.filings_data[:8]:  # Show last 8 filings
            form = filing.get("form", "")
            file_date = filing.get("file_date", "")
            description = filing.get("file_description", "")
            
            # Format date nicely
            try:
                from datetime import datetime
                date_obj = datetime.strptime(file_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%m/%d/%y")
            except:
                formatted_date = file_date
            
            content.append(f"{form:>8}: ", style="bold white")
            content.append(f"{formatted_date}\n", style="yellow")
            
            # Truncate description
            if description and len(description) > 50:
                description = description[:47] + "..."
            content.append(f"         {description}\n\n", style="dim white")
        
        panel = Panel(
            content,
            title=f"🏛️  SEC Filings - {self.symbol}",
            title_align="left",
            border_style="green"
        )
        
        self.update(panel)


class QuoteScreen(Screen):
    """Quote screen for individual stock details."""
    
    BINDINGS = [
        ("f1", "show_dashboard", "Dashboard"),
        ("f2", "show_quote", "Quote"),
        ("f3", "show_watchlist", "Watchlist"), 
        ("f4", "show_chart", "Chart"),
        ("f6", "show_news", "News"),
        ("r", "refresh", "Refresh"),
        ("a", "add_to_watchlist", "Add to Watchlist"),
        ("s", "view_sec_filings", "SEC Filings"),
        ("escape", "back", "Back"),
    ]
    
    def __init__(self, symbol: str = "AAPL"):
        super().__init__()
        self.current_symbol = symbol.upper()
    
    def compose(self):
        """Compose the quote screen layout."""
        with Vertical():
            # Header
            yield Static(self._get_header(), id="header")
            
            # Symbol input
            with Horizontal(id="symbol_input"):
                yield Static("Symbol: ", shrink=True)
                yield Input(
                    placeholder="Enter ticker symbol (e.g., AAPL)", 
                    value=self.current_symbol,
                    id="symbol_entry"
                )
            
            with Horizontal():
                # Main quote details
                yield QuoteDetailWidget()
                
                # Right column with news and SEC filings
                with Vertical():
                    yield QuoteNewsWidget()
                    yield QuoteSECWidget()
    
    def _get_header(self) -> Panel:
        """Get header panel."""
        current_time = format_time_only()
        header_text = Text()
        header_text.append("RiverTerminal", style="bold cyan")
        header_text.append(" | ", style="white")
        header_text.append(f"Quote - {self.current_symbol}", style="bold white")
        header_text.append(" | ", style="white")
        header_text.append(f"🕒 {current_time}", style="yellow")
        
        return Panel(
            Align.center(header_text),
            height=3,
            style="bold",
            border_style="blue"
        )
    
    async def on_mount(self):
        """Initialize the screen."""
        await self.load_quote_data()
        # Set up auto-refresh every 30 seconds
        self.set_interval(30.0, self.load_quote_data)
        # Update header clock every second
        self.set_interval(1.0, self.update_header)
    
    async def on_input_submitted(self, event):
        """Handle symbol input submission."""
        if event.input.id == "symbol_entry":
            new_symbol = event.input.value.strip().upper()
            if new_symbol and new_symbol != self.current_symbol:
                self.current_symbol = new_symbol
                await self.load_quote_data()
                self.update_header()
    
    async def load_quote_data(self):
        """Load quote, news, and SEC filings data."""
        quote_widget = self.query_one(QuoteDetailWidget)
        news_widget = self.query_one(QuoteNewsWidget)
        sec_widget = self.query_one(QuoteSECWidget)
        
        # Load quote, news, and SEC filings in parallel
        await asyncio.gather(
            quote_widget.load_quote(self.current_symbol),
            news_widget.load_news(self.current_symbol),
            sec_widget.load_filings(self.current_symbol),
            return_exceptions=True
        )
    
    def update_header(self):
        """Update the header."""
        header_widget = self.query_one("#header", Static)
        header_widget.update(self._get_header())
    
    def action_refresh(self):
        """Manual refresh action."""
        asyncio.create_task(self.load_quote_data())
    
    def action_add_to_watchlist(self):
        """Add current symbol to watchlist."""
        try:
            watchlist_id = db.get_default_watchlist_id()
            success = db.add_to_watchlist(watchlist_id, self.current_symbol)
            if success:
                self.notify(f"Added {self.current_symbol} to watchlist")
            else:
                self.notify(f"{self.current_symbol} already in watchlist")
        except Exception as e:
            self.notify(f"Error adding to watchlist: {e}")
    
    def action_view_sec_filings(self):
        """View SEC filings for current symbol."""
        try:
            sec_widget = self.query_one(QuoteSECWidget)
            asyncio.create_task(sec_widget.load_filings(self.current_symbol))
            self.notify(f"Loading SEC filings for {self.current_symbol}...")
        except Exception as e:
            self.notify(f"Error loading SEC filings: {e}")
    
    def action_export_data(self):
        """Export quote data to CSV."""
        try:
            import csv
            from pathlib import Path
            from datetime import datetime
            
            # Create export directory
            export_dir = Path.home() / "Downloads" / "riveterminal"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_dir / f"quote_{self.current_symbol}_{timestamp}.csv"
            
            # Get current quote data
            quote_widget = self.query_one(QuoteDetailWidget)
            if quote_widget.quote_data:
                quote = quote_widget.quote_data
                
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Field', 'Value'])
                    
                    # Write quote data
                    for key, value in quote.items():
                        writer.writerow([key, value])
                
                self.notify(f"Quote data exported to {filename}")
            else:
                self.notify("No quote data to export")
                
        except Exception as e:
            self.notify(f"Error exporting: {e}")
    
    def action_back(self):
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_show_dashboard(self):
        """Switch to dashboard screen."""
        self.app.pop_screen()
    
    def action_show_quote(self):
        """Stay on quote screen."""
        pass
    
    def action_show_watchlist(self):
        """Switch to watchlist screen."""
        self.app.push_screen("watchlist")
    
    def action_show_chart(self):
        """Switch to chart screen with current symbol."""
        from .chart import ChartScreen
        self.app.push_screen(ChartScreen(self.current_symbol))
    
    def action_show_news(self):
        """Switch to news screen."""
        self.app.push_screen("news")
    
    def set_symbol(self, symbol: str):
        """Set the current symbol and refresh data."""
        self.current_symbol = symbol.upper()
        symbol_input = self.query_one("#symbol_entry", Input)
        symbol_input.value = self.current_symbol
        asyncio.create_task(self.load_quote_data())
        self.update_header()