"""Economic dashboard screen."""

import asyncio
from typing import Dict, Any
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, DataTable
from textual.screen import Screen
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.align import Align

from ..data.fred import get_fred_provider
from ..utils.formatting import format_number, format_percentage


class EconomicScreen(Screen):
    """Economic indicators and treasury yield dashboard."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("1", "app.show_dashboard", "Dashboard"),
        ("q", "app.quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.fred_provider = get_fred_provider()
        self.auto_refresh = True
        self.refresh_interval = 300  # 5 minutes
    
    def compose(self) -> ComposeResult:
        """Compose the economic dashboard layout."""
        with Vertical():
            with Horizontal():
                # Left column - Economic indicators
                with Vertical():
                    yield Static("", id="economic-indicators")
                    yield Static("", id="treasury-yields")
                
                # Right column - Historical data
                with Vertical():
                    yield Static("", id="yield-history")
                    yield Static("", id="economic-calendar")
    
    async def on_mount(self) -> None:
        """Initialize the screen."""
        await self.refresh_data()
        
        # Start auto-refresh timer
        if self.auto_refresh:
            asyncio.create_task(self._auto_refresh_loop())
    
    async def action_refresh(self) -> None:
        """Refresh economic data."""
        await self.refresh_data()
        self.notify("Economic data refreshed")
    
    async def refresh_data(self) -> None:
        """Refresh all economic data."""
        try:
            # Load data concurrently
            indicators_task = asyncio.create_task(self.fred_provider.get_economic_indicators())
            yields_task = asyncio.create_task(self.fred_provider.get_treasury_yields())
            history_task = asyncio.create_task(self.fred_provider.get_yield_curve_history(30))
            
            indicators, yields, history = await asyncio.gather(
                indicators_task, yields_task, history_task
            )
            
            # Update displays
            self.update_indicators_display(indicators)
            self.update_yields_display(yields)
            self.update_history_display(history)
            self.update_calendar_display()
            
        except Exception as e:
            self.notify(f"Error refreshing data: {e}")
    
    def update_indicators_display(self, indicators: Dict[str, Any]) -> None:
        """Update economic indicators panel."""
        try:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Indicator", style="white", width=20)
            table.add_column("Value", style="green", justify="right", width=15)
            table.add_column("Change", justify="right", width=10)
            table.add_column("Period", style="dim", width=15)
            
            for name, data in indicators.items():
                indicator_name = name.upper().replace("_", " ")
                value_str = f"{data['value']}{self._get_unit_suffix(data.get('unit', ''))}"
                
                change = data.get('change', 0)
                if change > 0:
                    change_str = f"[green]+{change:.2f}%[/green]"
                elif change < 0:
                    change_str = f"[red]{change:.2f}%[/red]"
                else:
                    change_str = "[dim]0.00%[/dim]"
                
                table.add_row(
                    indicator_name,
                    value_str,
                    change_str,
                    data.get('period', 'N/A')
                )
            
            panel = Panel(
                Align.center(table),
                title="📊 Economic Indicators",
                title_align="left",
                border_style="cyan"
            )
            
            indicators_widget = self.query_one("#economic-indicators", Static)
            indicators_widget.update(panel)
            
        except Exception as e:
            self.notify(f"Error updating indicators: {e}")
    
    def update_yields_display(self, yields: Dict[str, float]) -> None:
        """Update treasury yields panel."""
        try:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Maturity", style="white", width=12)
            table.add_column("Yield", style="yellow", justify="right", width=12)
            table.add_column("Visual", width=20)
            
            # Sort yields by maturity
            sorted_yields = sorted(yields.items(), key=lambda x: self._sort_maturity(x[0]))
            
            max_yield = max(yields.values()) if yields else 5.0
            
            for maturity, yield_value in sorted_yields:
                # Create visual bar
                bar_length = int((yield_value / max_yield) * 15) if max_yield > 0 else 0
                bar = "█" * bar_length + "░" * (15 - bar_length)
                
                table.add_row(
                    maturity,
                    f"{yield_value:.3f}%",
                    f"[yellow]{bar}[/yellow]"
                )
            
            panel = Panel(
                Align.center(table),
                title="📈 Treasury Yield Curve",
                title_align="left",
                border_style="yellow"
            )
            
            yields_widget = self.query_one("#treasury-yields", Static)
            yields_widget.update(panel)
            
        except Exception as e:
            self.notify(f"Error updating yields: {e}")
    
    def update_history_display(self, history: Dict[str, Any]) -> None:
        """Update yield history panel."""
        try:
            # Create a simple chart showing recent yield movements
            content = Text()
            content.append("Recent Yield Movement (30 days)\n\n", style="bold cyan")
            
            for maturity in ["2Y", "5Y", "10Y", "30Y"]:
                if maturity in history and history[maturity]:
                    recent_data = history[maturity][-7:]  # Last 7 days
                    if len(recent_data) >= 2:
                        start_yield = recent_data[0]['yield']
                        end_yield = recent_data[-1]['yield']
                        change = end_yield - start_yield
                        
                        if change > 0:
                            change_str = f"+{change:.3f}%"
                            color = "green"
                        elif change < 0:
                            change_str = f"{change:.3f}%"
                            color = "red"
                        else:
                            change_str = "0.000%"
                            color = "dim"
                        
                        # Create sparkline
                        sparkline = self._create_sparkline([d['yield'] for d in recent_data])
                        
                        content.append(f"{maturity:>3}: {end_yield:.3f}% ", style="white")
                        content.append(f"({change_str}) ", style=color)
                        content.append(f"{sparkline}\n", style="blue")
            
            panel = Panel(
                content,
                title="📊 Yield History (30 days)",
                title_align="left",
                border_style="blue"
            )
            
            history_widget = self.query_one("#yield-history", Static)
            history_widget.update(panel)
            
        except Exception as e:
            self.notify(f"Error updating history: {e}")
    
    def update_calendar_display(self) -> None:
        """Update economic calendar panel."""
        try:
            # Mock economic calendar events
            content = Text()
            content.append("Upcoming Economic Events\n\n", style="bold cyan")
            
            events = [
                ("Today", "FOMC Meeting Minutes", "2:00 PM ET"),
                ("Tomorrow", "Jobless Claims", "8:30 AM ET"),
                ("Thursday", "GDP (Advance)", "8:30 AM ET"),
                ("Friday", "PCE Price Index", "8:30 AM ET"),
                ("Next Week", "Non-Farm Payrolls", "8:30 AM ET"),
            ]
            
            for date, event, time in events:
                content.append(f"{date:>10}: ", style="dim")
                content.append(f"{event:<20} ", style="white")
                content.append(f"{time}\n", style="yellow")
            
            panel = Panel(
                content,
                title="📅 Economic Calendar",
                title_align="left",
                border_style="green"
            )
            
            calendar_widget = self.query_one("#economic-calendar", Static)
            calendar_widget.update(panel)
            
        except Exception as e:
            self.notify(f"Error updating calendar: {e}")
    
    def _get_unit_suffix(self, unit: str) -> str:
        """Get short suffix for unit display."""
        if "Trillion" in unit:
            return "T"
        elif "Billion" in unit:
            return "B"
        elif "Percent" in unit:
            return "%"
        elif "Index" in unit:
            return ""
        else:
            return ""
    
    def _sort_maturity(self, maturity: str) -> int:
        """Sort key for maturity periods."""
        order = {"2Y": 1, "5Y": 2, "10Y": 3, "30Y": 4}
        return order.get(maturity, 99)
    
    def _create_sparkline(self, values: list) -> str:
        """Create a simple sparkline from values."""
        if len(values) < 2:
            return "─" * 8
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return "─" * len(values)
        
        # Normalize values to sparkline characters
        chars = "▁▂▃▄▅▆▇█"
        normalized = [(v - min_val) / (max_val - min_val) for v in values]
        return "".join(chars[int(n * (len(chars) - 1))] for n in normalized)
    
    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh data periodically."""
        while self.auto_refresh:
            try:
                await asyncio.sleep(self.refresh_interval)
                if self.auto_refresh:  # Check again in case it was disabled
                    await self.refresh_data()
            except Exception:
                break  # Exit loop on error