"""Enhanced chart screen for viewing price charts with SMA overlays and volume."""

import asyncio
from textual.widgets import Static, Button, Input, Checkbox
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from typing import Optional, List, Dict
import pandas as pd

from ..data.yahoo import yahoo
from ..utils.formatting import format_time_only
from ..utils.charts import create_line_chart, create_price_sparkline, create_candlestick_chart, create_volume_chart


class ChartWidget(Static):
    """Enhanced widget for displaying ASCII charts with SMA overlays and volume."""
    
    def __init__(self):
        super().__init__()
        self.symbols = []  # Support multiple tickers
        self.timeframe = "1M"
        self.chart_data = {}  # Dict of symbol -> DataFrame
        self.show_sma = [True, True, True]  # [20, 50, 200]
        self.show_volume = True
        self.chart_style = "line"  # "line" or "candlestick"
    
    async def load_chart(self, symbols: str, timeframe: str = "1M"):
        """Load chart data for symbol(s). Supports comma-separated tickers."""
        # Parse symbols (support comma-separated list)
        if "," in symbols:
            self.symbols = [s.strip().upper() for s in symbols.split(",")]
        else:
            self.symbols = [symbols.upper()]
        
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
            
            # Load data for all symbols
            self.chart_data = {}
            for symbol in self.symbols:
                # Get historical data with SMA overlays
                data = await yahoo.get_historical_with_sma(symbol, period, [20, 50, 200])
                if data is not None and not data.empty:
                    self.chart_data[symbol] = data
            
            if self.chart_data:
                self.update_display()
            else:
                self.update("No chart data available for any symbols")
                
        except Exception as e:
            self.update(f"Error loading chart: {e}")
    
    def set_sma_visibility(self, sma_20: bool, sma_50: bool, sma_200: bool):
        """Set which SMA lines to show."""
        self.show_sma = [sma_20, sma_50, sma_200]
        self.update_display()
    
    def set_volume_visibility(self, show: bool):
        """Set volume bar visibility."""
        self.show_volume = show
        self.update_display()
    
    def set_chart_style(self, style: str):
        """Set chart style: 'line' or 'candlestick'."""
        self.chart_style = style
        self.update_display()
    
    def update_display(self):
        """Update the chart display with enhanced features."""
        if not self.chart_data:
            self.update("No data to display")
            return
        
        try:
            # Multi-symbol support
            if len(self.symbols) == 1:
                symbol = self.symbols[0]
                data = self.chart_data[symbol]
                content = self._create_single_chart(symbol, data)
            else:
                content = self._create_comparison_chart()
            
            panel = Panel(
                content,
                title=f"📊 {' vs '.join(self.symbols)} - {self.timeframe}",
                title_align="left",
                border_style="cyan"
            )
            
            self.update(panel)
            
        except Exception as e:
            self.update(f"Error updating chart: {e}")
    
    def _create_single_chart(self, symbol: str, data: pd.DataFrame) -> Text:
        """Create enhanced chart for single symbol with SMA and volume."""
        content = Text()
        
        # Main price chart with SMA overlays
        if self.chart_style == "candlestick":
            try:
                chart_text = create_candlestick_chart(data, symbol, width=120, height=20)
            except:
                # Fallback to line chart if candlestick fails
                chart_text = self._create_line_with_sma(data, symbol)
        else:
            chart_text = self._create_line_with_sma(data, symbol)
        
        content.append(chart_text)
        
        # Volume chart below if enabled
        if self.show_volume and 'Volume' in data.columns:
            content.append("\n\n")
            volume_chart = create_volume_chart(data, width=120, height=8)
            content.append("📊 VOLUME:\n", style="bold cyan")
            content.append(volume_chart)
        
        # Summary statistics
        content.append("\n\n")
        content.append(self._create_summary(symbol, data))
        
        return content
    
    def _create_line_with_sma(self, data: pd.DataFrame, symbol: str) -> str:
        """Create line chart with SMA overlays."""
        try:
            # Create base chart
            chart_lines = []
            
            # Get price data
            prices = data['Close'].tolist()
            
            # Simple ASCII line chart
            width = 120
            height = 20
            
            if not prices:
                return "No price data"
            
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price
            
            if price_range == 0:
                return f"{symbol}: Constant price ${min_price:.2f}"
            
            # Create chart grid
            chart_grid = [[' ' for _ in range(width)] for _ in range(height)]
            
            # Plot main price line
            for i, price in enumerate(prices):
                if i < width:
                    y = int((1 - (price - min_price) / price_range) * (height - 1))
                    y = max(0, min(height - 1, y))
                    chart_grid[y][i] = '█'
            
            # Plot SMA lines if enabled
            sma_chars = ['▓', '▒', '░']  # Different shading for different SMAs
            sma_periods = [20, 50, 200]
            
            for sma_idx, period in enumerate(sma_periods):
                if self.show_sma[sma_idx] and f'SMA{period}' in data.columns:
                    sma_values = data[f'SMA{period}'].dropna().tolist()
                    char = sma_chars[sma_idx]
                    
                    for i, sma_val in enumerate(sma_values):
                        if i < width and not pd.isna(sma_val):
                            y = int((1 - (sma_val - min_price) / price_range) * (height - 1))
                            y = max(0, min(height - 1, y))
                            if chart_grid[y][i] == ' ':
                                chart_grid[y][i] = char
            
            # Convert grid to text
            chart_text = ""
            for row in chart_grid:
                chart_text += ''.join(row) + "\n"
            
            # Add legend
            legend = f"\n{symbol}: █ Price"
            if self.show_sma[0] and 'SMA20' in data.columns:
                legend += "  ▓ SMA20"
            if self.show_sma[1] and 'SMA50' in data.columns:
                legend += "  ▒ SMA50" 
            if self.show_sma[2] and 'SMA200' in data.columns:
                legend += "  ░ SMA200"
            
            chart_text += legend
            
            return chart_text
            
        except Exception as e:
            return f"Error creating chart: {e}"
    
    def _create_comparison_chart(self) -> Text:
        """Create comparison chart for multiple symbols."""
        content = Text()
        
        # Normalize all prices to percentage change from first data point
        normalized_data = {}
        colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan']
        
        content.append("📈 COMPARISON CHART (Normalized to % Change)\n\n", style="bold cyan")
        
        # Calculate normalized returns for each symbol
        for i, symbol in enumerate(self.symbols):
            if symbol in self.chart_data:
                data = self.chart_data[symbol]
                if not data.empty:
                    first_price = data['Close'].iloc[0]
                    normalized_returns = ((data['Close'] / first_price) - 1) * 100
                    normalized_data[symbol] = normalized_returns.tolist()
                    
                    # Add summary for this symbol
                    color = colors[i % len(colors)]
                    latest_return = normalized_returns.iloc[-1]
                    content.append(f"{symbol}: ", style=f"bold {color}")
                    content.append(f"{latest_return:+.2f}%\n", 
                                 style=color if latest_return >= 0 else "red")
        
        # Create simple comparison chart
        if normalized_data:
            content.append("\n")
            content.append(self._create_simple_comparison_chart(normalized_data))
        
        return content
    
    def _create_simple_comparison_chart(self, normalized_data: Dict[str, List[float]]) -> str:
        """Create simple ASCII comparison chart."""
        try:
            width = 100
            height = 15
            
            # Find min/max across all series
            all_values = []
            for values in normalized_data.values():
                all_values.extend([v for v in values if not pd.isna(v)])
            
            if not all_values:
                return "No data to chart"
            
            min_val = min(all_values)
            max_val = max(all_values)
            val_range = max_val - min_val
            
            if val_range == 0:
                return "No variation in data"
            
            # Create chart
            chart_lines = []
            symbols = list(normalized_data.keys())
            chars = ['█', '▓', '▒', '░', '▪', '▫']
            
            # Initialize grid
            grid = [[' ' for _ in range(width)] for _ in range(height)]
            
            # Plot each symbol
            for sym_idx, symbol in enumerate(symbols):
                values = normalized_data[symbol]
                char = chars[sym_idx % len(chars)]
                
                for i, val in enumerate(values):
                    if i < width and not pd.isna(val):
                        y = int((1 - (val - min_val) / val_range) * (height - 1))
                        y = max(0, min(height - 1, y))
                        grid[y][i] = char
            
            # Convert to string
            chart_text = ""
            for row in grid:
                chart_text += ''.join(row) + "\n"
            
            # Add legend
            legend = "\nLegend: "
            for i, symbol in enumerate(symbols):
                char = chars[i % len(chars)]
                legend += f"{char} {symbol}  "
            
            chart_text += legend
            return chart_text
            
        except Exception as e:
            return f"Error creating comparison: {e}"
    
    def _create_summary(self, symbol: str, data: pd.DataFrame) -> Text:
        """Create summary statistics."""
        summary = Text()
        
        try:
            latest_price = data['Close'].iloc[-1]
            first_price = data['Close'].iloc[0]
            price_change = latest_price - first_price
            price_change_pct = (price_change / first_price) * 100
            
            high = data['High'].max()
            low = data['Low'].min()
            avg_volume = data['Volume'].mean()
            
            summary.append(f"📊 {symbol} SUMMARY\n", style="bold white")
            summary.append(f"Current: ${latest_price:.2f}", style="bold white")
            summary.append(f" | Change: ", style="white")
            
            change_style = "green" if price_change >= 0 else "red"
            summary.append(f"{price_change:+.2f} ({price_change_pct:+.2f}%)", style=change_style)
            
            summary.append(f"\nRange: ${low:.2f} - ${high:.2f}", style="white")
            summary.append(f" | Avg Volume: {avg_volume:,.0f}", style="white")
            
            # SMA values if available
            sma_text = "\nSMAs: "
            sma_added = False
            for period in [20, 50, 200]:
                col_name = f'SMA{period}'
                if col_name in data.columns and not data[col_name].isna().all():
                    latest_sma = data[col_name].iloc[-1]
                    if not pd.isna(latest_sma):
                        if sma_added:
                            sma_text += " | "
                        sma_text += f"SMA{period}: ${latest_sma:.2f}"
                        sma_added = True
            
            if sma_added:
                summary.append(sma_text, style="cyan")
            
        except Exception as e:
            summary.append(f"Error creating summary: {e}", style="red")
        
        return summary


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
        """Compose the enhanced chart screen layout."""
        with Vertical():
            # Header
            yield Static(self._get_header(), id="header")
            
            # Symbol input and timeframe controls
            with Horizontal(id="controls"):
                yield Static("Symbols: ", shrink=True)
                yield Input(
                    placeholder="AAPL,MSFT,GOOGL (comma-separated)",
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
            
            # Chart options
            with Horizontal(id="chart_options"):
                yield Static("Options: ", shrink=True)
                yield Checkbox("SMA20", value=True, id="sma20_check")
                yield Checkbox("SMA50", value=True, id="sma50_check") 
                yield Checkbox("SMA200", value=True, id="sma200_check")
                yield Static(" | ", shrink=True)
                yield Checkbox("Volume", value=True, id="volume_check")
                yield Static(" | Style: ", shrink=True)
                yield Button("Line", id="btn_line", variant="primary")
                yield Button("Candle", id="btn_candle", variant="default")
            
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
        """Get enhanced instructions panel."""
        instructions = Text()
        instructions.append("📈 Enhanced Chart Controls:\n\n", style="bold cyan")
        instructions.append("• Enter symbol(s) above and press Enter\n", style="white")
        instructions.append("• Multi-ticker: Use comma-separated list (AAPL,MSFT,GOOGL)\n", style="white")
        instructions.append("• Number keys 1-7: Change timeframe\n", style="white")
        instructions.append("• Toggle SMA overlays and volume with checkboxes\n", style="white")
        instructions.append("• Switch between Line/Candlestick style\n", style="white")
        instructions.append("• R: Refresh chart | E: Export data\n", style="white")
        
        return Panel(
            instructions,
            title="ℹ️ Instructions",
            title_align="left",
            border_style="green",
            height=10
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
        """Handle button presses."""
        button_id = event.button.id
        
        # Timeframe buttons
        timeframe_map = {
            "btn_1d": "1D",
            "btn_1w": "1W", 
            "btn_1m": "1M",
            "btn_3m": "3M",
            "btn_6m": "6M",
            "btn_1y": "1Y",
            "btn_5y": "5Y"
        }
        
        if button_id in timeframe_map:
            new_timeframe = timeframe_map[button_id]
            if new_timeframe != self.current_timeframe:
                # Update button styles
                self._update_timeframe_buttons(new_timeframe)
                self.current_timeframe = new_timeframe
                await self.load_chart()
        
        # Chart style buttons
        elif button_id == "btn_line":
            self._update_style_buttons("line")
            chart_widget = self.query_one(ChartWidget)
            chart_widget.set_chart_style("line")
        elif button_id == "btn_candle":
            self._update_style_buttons("candlestick")
            chart_widget = self.query_one(ChartWidget)
            chart_widget.set_chart_style("candlestick")
    
    async def on_checkbox_changed(self, event):
        """Handle checkbox changes."""
        checkbox_id = event.checkbox.id
        chart_widget = self.query_one(ChartWidget)
        
        if checkbox_id in ["sma20_check", "sma50_check", "sma200_check"]:
            # Update SMA visibility
            sma20 = self.query_one("#sma20_check", Checkbox).value
            sma50 = self.query_one("#sma50_check", Checkbox).value
            sma200 = self.query_one("#sma200_check", Checkbox).value
            chart_widget.set_sma_visibility(sma20, sma50, sma200)
        
        elif checkbox_id == "volume_check":
            # Update volume visibility
            show_volume = event.checkbox.value
            chart_widget.set_volume_visibility(show_volume)
    
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
    
    def _update_style_buttons(self, active_style: str):
        """Update chart style button styles."""
        line_btn = self.query_one("#btn_line", Button)
        candle_btn = self.query_one("#btn_candle", Button)
        
        if active_style == "line":
            line_btn.variant = "primary"
            candle_btn.variant = "default"
        else:
            line_btn.variant = "default"
            candle_btn.variant = "primary"
    
    async def load_chart(self):
        """Load chart data."""
        chart_widget = self.query_one(ChartWidget)
        symbols = self.query_one("#symbol_input", Input).value.strip()
        if symbols:
            await chart_widget.load_chart(symbols, self.current_timeframe)
            # Update current_symbol for backward compatibility
            if "," not in symbols:
                self.current_symbol = symbols.upper()
    
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