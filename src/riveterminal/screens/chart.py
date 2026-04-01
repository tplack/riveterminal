"""Chart screen for viewing price charts."""

import asyncio
from textual.widgets import Static, Button, Input
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from typing import Optional

from ..data.yahoo import yahoo
from ..utils.formatting import format_time_only
from ..utils.charts import create_line_chart, create_price_sparkline


class ChartWidget(Static):
    """Widget for displaying ASCII charts."""
    
    def __init__(self):
        super().__init__()
        self.symbol = None
        self.timeframe = "1M"
        self.chart_data = None
    
    async def load_chart(self, symbol: str, timeframe: str = "1M"):
        """Load chart data for symbol."""
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        
        try:
            # Map timeframe to yfinance period
            period_map = {
                "1D": "1d",
                "1W": "5d", 
                "1M": "1mo",
                "3M": "3mo",
                "6M": "6mo",
                "1Y": "1y",
                "5Y": "5y"
            }
            
            period = period_map.get(timeframe, "1mo")
            self.chart_data = await yahoo.get_historical_data(self.symbol, period)
            
            if self.chart_data is not None and not self.chart_data.empty:
                self.update_display()
            else:
                self.update("No chart data available")
                
        except Exception as e:
            self.update(f"Error loading chart: {e}")
    
    def update_display(self):
        """Update the chart display."""
        if self.chart_data is None or self.chart_data.empty:
            self.update("No data to display")
            return
        
        # Create the ASCII chart
        title = f"{self.symbol} - {self.timeframe}"
        chart_text = create_line_chart(self.chart_data, title, width=100, height=25)
        
        # Add price summary
        latest_price = self.chart_data['Close'].iloc[-1]
        first_price = self.chart_data['Close'].iloc[0]
        price_change = latest_price - first_price
        price_change_pct = (price_change / first_price) * 100
        
        summary = Text()
        summary.append(f"Latest: ${latest_price:.2f}", style="bold white")
        summary.append(f" | Change: ", style="white")
        
        change_style = "green" if price_change >= 0 else "red"
        summary.append(f"{price_change:+.2f} ({price_change_pct:+.2f}%)", style=change_style)
        
        # Create sparkline for quick view
        prices = self.chart_data['Close'].tolist()
        sparkline = create_price_sparkline(prices, width=50)
        summary.append(f"\nSparkline: {sparkline}", style="cyan")
        
        # Combine chart and summary
        content = Text()
        content.append(chart_text)
        content.append("\n")
        content.append(summary)
        
        panel = Panel(
            content,
            title=f"📊 {title}",
            title_align="left",
            border_style="cyan"
        )
        
        self.update(panel)


class ChartScreen(Screen):
    """Chart screen for viewing price charts."""
    
    BINDINGS = [
        ("f1", "show_dashboard", "Dashboard"),
        ("f2", "show_quote", "Quote"),
        ("f3", "show_watchlist", "Watchlist"),
        ("f4", "show_chart", "Chart"),
        ("f6", "show_news", "News"),
        ("1", "timeframe_1d", "1D"),
        ("2", "timeframe_1w", "1W"),
        ("3", "timeframe_1m", "1M"),
        ("4", "timeframe_3m", "3M"),
        ("5", "timeframe_6m", "6M"),
        ("6", "timeframe_1y", "1Y"),
        ("7", "timeframe_5y", "5Y"),
        ("r", "refresh", "Refresh"),
        ("escape", "back", "Back"),
    ]
    
    def __init__(self, symbol: str = "AAPL"):
        super().__init__()
        self.current_symbol = symbol.upper()
        self.current_timeframe = "1M"
    
    def compose(self):
        """Compose the chart screen layout."""
        with Vertical():
            # Header
            yield Static(self._get_header(), id="header")
            
            # Symbol input and timeframe controls
            with Horizontal(id="controls"):
                yield Static("Symbol: ", shrink=True)
                yield Input(
                    placeholder="Enter ticker symbol",
                    value=self.current_symbol,
                    id="symbol_input"
                )
                yield Static(" | Timeframe: ", shrink=True)
                with Horizontal(id="timeframe_buttons"):
                    yield Button("1D", id="btn_1d", variant="default")
                    yield Button("1W", id="btn_1w", variant="default")
                    yield Button("1M", id="btn_1m", variant="primary")  # Default
                    yield Button("3M", id="btn_3m", variant="default")
                    yield Button("6M", id="btn_6m", variant="default")
                    yield Button("1Y", id="btn_1y", variant="default")
                    yield Button("5Y", id="btn_5y", variant="default")
            
            # Chart display
            yield ChartWidget()
            
            # Instructions
            yield Static(self._get_instructions(), id="instructions")
    
    def _get_header(self) -> Panel:
        """Get header panel."""
        current_time = format_time_only()
        header_text = Text()
        header_text.append("RiverTerminal", style="bold cyan")
        header_text.append(" | ", style="white")
        header_text.append(f"Charts - {self.current_symbol}", style="bold white")
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
        instructions.append("📈 Chart Controls:\n\n", style="bold cyan")
        instructions.append("• Enter symbol above and press Enter\n", style="white")
        instructions.append("• Number keys 1-7: Change timeframe\n", style="white")
        instructions.append("• R: Refresh chart\n", style="white")
        instructions.append("• F2: View quote for current symbol\n", style="white")
        
        return Panel(
            instructions,
            title="ℹ️ Instructions",
            title_align="left",
            border_style="green",
            height=8
        )
    
    async def on_mount(self):
        """Initialize the screen."""
        await self.load_chart()
        # Update header clock every second
        self.set_interval(1.0, self.update_header)
    
    async def on_input_submitted(self, event):
        """Handle symbol input submission."""
        if event.input.id == "symbol_input":
            new_symbol = event.input.value.strip().upper()
            if new_symbol and new_symbol != self.current_symbol:
                self.current_symbol = new_symbol
                await self.load_chart()
                self.update_header()
    
    async def on_button_pressed(self, event):
        """Handle timeframe button presses."""
        timeframe_map = {
            "btn_1d": "1D",
            "btn_1w": "1W", 
            "btn_1m": "1M",
            "btn_3m": "3M",
            "btn_6m": "6M",
            "btn_1y": "1Y",
            "btn_5y": "5Y"
        }
        
        new_timeframe = timeframe_map.get(event.button.id)
        if new_timeframe and new_timeframe != self.current_timeframe:
            # Update button styles
            self._update_timeframe_buttons(new_timeframe)
            
            self.current_timeframe = new_timeframe
            await self.load_chart()
    
    def _update_timeframe_buttons(self, active_timeframe: str):
        """Update timeframe button styles."""
        button_map = {
            "1D": "btn_1d",
            "1W": "btn_1w",
            "1M": "btn_1m", 
            "3M": "btn_3m",
            "6M": "btn_6m",
            "1Y": "btn_1y",
            "5Y": "btn_5y"
        }
        
        for timeframe, button_id in button_map.items():
            button = self.query_one(f"#{button_id}", Button)
            if timeframe == active_timeframe:
                button.variant = "primary"
            else:
                button.variant = "default"
    
    async def load_chart(self):
        """Load chart data."""
        chart_widget = self.query_one(ChartWidget)
        await chart_widget.load_chart(self.current_symbol, self.current_timeframe)
    
    def update_header(self):
        """Update the header."""
        header_widget = self.query_one("#header", Static)
        header_widget.update(self._get_header())
    
    def action_refresh(self):
        """Manual refresh action."""
        asyncio.create_task(self.load_chart())
    
    def action_timeframe_1d(self):
        """Switch to 1D timeframe."""
        self._trigger_timeframe_change("1D")
    
    def action_timeframe_1w(self):
        """Switch to 1W timeframe."""
        self._trigger_timeframe_change("1W")
    
    def action_timeframe_1m(self):
        """Switch to 1M timeframe."""
        self._trigger_timeframe_change("1M")
    
    def action_timeframe_3m(self):
        """Switch to 3M timeframe."""
        self._trigger_timeframe_change("3M")
    
    def action_timeframe_6m(self):
        """Switch to 6M timeframe."""
        self._trigger_timeframe_change("6M")
    
    def action_timeframe_1y(self):
        """Switch to 1Y timeframe."""
        self._trigger_timeframe_change("1Y")
    
    def action_timeframe_5y(self):
        """Switch to 5Y timeframe."""
        self._trigger_timeframe_change("5Y")
    
    def _trigger_timeframe_change(self, timeframe: str):
        """Trigger timeframe change."""
        if timeframe != self.current_timeframe:
            self._update_timeframe_buttons(timeframe)
            self.current_timeframe = timeframe
            asyncio.create_task(self.load_chart())
    
    def action_back(self):
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_show_dashboard(self):
        """Switch to dashboard screen."""
        self.app.pop_screen()
    
    def action_show_quote(self):
        """Switch to quote screen with current symbol."""
        from .quote import QuoteScreen
        self.app.push_screen(QuoteScreen(self.current_symbol))
    
    def action_show_watchlist(self):
        """Switch to watchlist screen."""
        self.app.push_screen("watchlist")
    
    def action_show_chart(self):
        """Stay on chart screen."""
        pass
    
    def action_show_news(self):
        """Switch to news screen."""
        self.app.push_screen("news")
    
    def set_symbol(self, symbol: str):
        """Set the current symbol and refresh chart."""
        self.current_symbol = symbol.upper()
        symbol_input = self.query_one("#symbol_input", Input)
        symbol_input.value = self.current_symbol
        asyncio.create_task(self.load_chart())
        self.update_header()