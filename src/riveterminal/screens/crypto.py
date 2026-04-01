"""Crypto dashboard screen."""

import asyncio
from typing import Dict, List, Any
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, DataTable
from textual.screen import Screen
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.align import Align

from ..data.coingecko import get_coingecko_api
from ..utils.formatting import format_number, format_percentage


class CryptoScreen(Screen):
    """Cryptocurrency dashboard with top coins, stats, and Fear & Greed."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("1", "app.show_dashboard", "Dashboard"),
        ("enter", "view_coin_details", "View Details"),
        ("q", "app.quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.selected_coin = None
        self.coins_data = []
        self.auto_refresh = True
        self.refresh_interval = 60  # 1 minute
    
    def compose(self) -> ComposeResult:
        """Compose the crypto dashboard layout."""
        with Vertical():
            # Top row - Stats and Fear & Greed
            with Horizontal():
                yield Static("", id="global-stats")
                yield Static("", id="fear-greed")
            
            # Main content - Top coins table
            with Horizontal():
                # Left: Top 50 coins table
                with Vertical():
                    yield DataTable(id="coins-table")
                
                # Right: Selected coin details
                with Vertical():
                    yield Static("Select a coin for details", id="coin-details")
    
    async def on_mount(self) -> None:
        """Initialize the screen."""
        await self.refresh_data()
        self.setup_coins_table()
        
        # Start auto-refresh timer
        if self.auto_refresh:
            asyncio.create_task(self._auto_refresh_loop())
    
    def setup_coins_table(self) -> None:
        """Setup the coins data table."""
        table = self.query_one("#coins-table", DataTable)
        table.add_column("Rank", width=6)
        table.add_column("Symbol", width=8)
        table.add_column("Name", width=15)
        table.add_column("Price", width=12)
        table.add_column("24h %", width=10)
        table.add_column("Market Cap", width=15)
        table.add_column("Volume 24h", width=15)
        table.cursor_type = "row"
    
    async def action_refresh(self) -> None:
        """Refresh crypto data."""
        await self.refresh_data()
        self.notify("Crypto data refreshed")
    
    async def action_view_coin_details(self) -> None:
        """View details for selected coin."""
        table = self.query_one("#coins-table", DataTable)
        if table.cursor_row >= 0 and table.cursor_row < len(self.coins_data):
            coin = self.coins_data[table.cursor_row]
            await self.show_coin_details(coin)
    
    async def refresh_data(self) -> None:
        """Refresh all crypto data."""
        try:
            api = await get_coingecko_api()
            
            # Load data concurrently
            coins_task = asyncio.create_task(api.get_top_coins(50))
            stats_task = asyncio.create_task(api.get_global_stats())
            fear_greed_task = asyncio.create_task(api.get_fear_greed_index())
            
            self.coins_data, global_stats, fear_greed = await asyncio.gather(
                coins_task, stats_task, fear_greed_task
            )
            
            # Update displays
            self.update_coins_table(self.coins_data)
            self.update_global_stats(global_stats)
            self.update_fear_greed(fear_greed)
            
        except Exception as e:
            self.notify(f"Error refreshing crypto data: {e}")
    
    def update_coins_table(self, coins: List[Dict[str, Any]]) -> None:
        """Update the coins table with new data."""
        try:
            table = self.query_one("#coins-table", DataTable)
            table.clear()
            
            for coin in coins:
                # Format price
                price = coin.get('price', 0)
                if price >= 1:
                    price_str = f"${price:,.2f}"
                elif price >= 0.01:
                    price_str = f"${price:.4f}"
                else:
                    price_str = f"${price:.8f}"
                
                # Format 24h change with color
                change_24h = coin.get('change_24h', 0)
                if change_24h > 0:
                    change_str = f"[green]+{change_24h:.2f}%[/green]"
                elif change_24h < 0:
                    change_str = f"[red]{change_24h:.2f}%[/red]"
                else:
                    change_str = "0.00%"
                
                # Format market cap and volume
                market_cap = format_number(coin.get('market_cap', 0))
                volume = format_number(coin.get('volume_24h', 0))
                
                table.add_row(
                    str(coin.get('rank', '')),
                    coin.get('symbol', ''),
                    coin.get('name', '')[:15],
                    price_str,
                    change_str,
                    market_cap,
                    volume
                )
                
        except Exception as e:
            self.notify(f"Error updating coins table: {e}")
    
    def update_global_stats(self, stats: Dict[str, Any]) -> None:
        """Update global cryptocurrency statistics."""
        try:
            content = Text()
            
            # Total market cap
            total_mc = stats.get('total_market_cap', 0)
            content.append("Total Market Cap: ", style="white")
            content.append(f"${format_number(total_mc)}\n", style="cyan bold")
            
            # 24h volume
            volume_24h = stats.get('total_volume_24h', 0)
            content.append("24h Volume: ", style="white")
            content.append(f"${format_number(volume_24h)}\n", style="cyan")
            
            # Bitcoin dominance
            btc_dom = stats.get('bitcoin_dominance', 0)
            content.append("Bitcoin Dominance: ", style="white")
            content.append(f"{btc_dom:.1f}%\n", style="orange")
            
            # Active cryptocurrencies
            active_cryptos = stats.get('active_cryptocurrencies', 0)
            content.append("Active Coins: ", style="white")
            content.append(f"{active_cryptos:,}\n", style="white")
            
            # Markets
            markets = stats.get('markets', 0)
            content.append("Markets: ", style="white")
            content.append(f"{markets:,}\n", style="white")
            
            # Market cap change
            mc_change = stats.get('market_cap_change_24h', 0)
            if mc_change > 0:
                content.append("24h Change: ", style="white")
                content.append(f"+{mc_change:.2f}%", style="green")
            elif mc_change < 0:
                content.append("24h Change: ", style="white")
                content.append(f"{mc_change:.2f}%", style="red")
            else:
                content.append("24h Change: 0.00%", style="white")
            
            panel = Panel(
                content,
                title="🌍 Global Crypto Stats",
                title_align="left",
                border_style="cyan"
            )
            
            stats_widget = self.query_one("#global-stats", Static)
            stats_widget.update(panel)
            
        except Exception as e:
            self.notify(f"Error updating global stats: {e}")
    
    def update_fear_greed(self, fear_greed: Dict[str, Any]) -> None:
        """Update Fear & Greed Index display."""
        try:
            value = fear_greed.get('value', 50)
            classification = fear_greed.get('classification', 'Neutral')
            timestamp = fear_greed.get('timestamp', '')
            
            content = Text()
            
            # Value with large display
            content.append(f"{value}\n", style="bold yellow", justify="center")
            
            # Classification
            color = self._get_fear_greed_color(value)
            content.append(f"{classification}\n\n", style=f"bold {color}")
            
            # Visual gauge
            gauge = self._create_fear_greed_gauge(value)
            content.append(f"{gauge}\n\n", style="white")
            
            # Scale reference
            content.append("0=Extreme Fear  100=Extreme Greed\n", style="dim")
            content.append(f"Updated: {timestamp}", style="dim")
            
            panel = Panel(
                content,
                title="😨 Fear & Greed Index",
                title_align="left",
                border_style="yellow"
            )
            
            fear_widget = self.query_one("#fear-greed", Static)
            fear_widget.update(panel)
            
        except Exception as e:
            self.notify(f"Error updating fear & greed: {e}")
    
    async def show_coin_details(self, coin: Dict[str, Any]) -> None:
        """Show detailed information for selected coin."""
        try:
            # For now, show basic details. In a full implementation,
            # we'd fetch more detailed data from CoinGecko
            content = Text()
            
            symbol = coin.get('symbol', 'N/A')
            name = coin.get('name', 'N/A')
            
            content.append(f"{symbol} - {name}\n\n", style="bold cyan")
            
            # Price info
            price = coin.get('price', 0)
            if price >= 1:
                price_str = f"${price:,.2f}"
            elif price >= 0.01:
                price_str = f"${price:.4f}"
            else:
                price_str = f"${price:.8f}"
            
            content.append("Price: ", style="white")
            content.append(f"{price_str}\n", style="yellow bold")
            
            # 24h change
            change_24h = coin.get('change_24h', 0)
            if change_24h > 0:
                content.append("24h Change: ", style="white")
                content.append(f"+{change_24h:.2f}%\n", style="green")
            elif change_24h < 0:
                content.append("24h Change: ", style="white")
                content.append(f"{change_24h:.2f}%\n", style="red")
            else:
                content.append("24h Change: 0.00%\n", style="white")
            
            # Market cap
            market_cap = coin.get('market_cap', 0)
            content.append("Market Cap: ", style="white")
            content.append(f"${format_number(market_cap)}\n", style="cyan")
            
            # Volume
            volume_24h = coin.get('volume_24h', 0)
            content.append("24h Volume: ", style="white")
            content.append(f"${format_number(volume_24h)}\n", style="cyan")
            
            # Rank
            rank = coin.get('rank', 'N/A')
            content.append("Rank: ", style="white")
            content.append(f"#{rank}\n", style="white")
            
            panel = Panel(
                content,
                title="📊 Coin Details",
                title_align="left",
                border_style="green"
            )
            
            details_widget = self.query_one("#coin-details", Static)
            details_widget.update(panel)
            
        except Exception as e:
            self.notify(f"Error showing coin details: {e}")
    
    def _get_fear_greed_color(self, value: int) -> str:
        """Get color for Fear & Greed value."""
        if value <= 20:
            return "red"
        elif value <= 40:
            return "yellow"
        elif value <= 60:
            return "white"
        elif value <= 80:
            return "green"
        else:
            return "bright_green"
    
    def _create_fear_greed_gauge(self, value: int) -> str:
        """Create visual gauge for Fear & Greed Index."""
        # Create a 20-character gauge
        gauge_length = 20
        filled = int((value / 100) * gauge_length)
        empty = gauge_length - filled
        
        return "█" * filled + "░" * empty
    
    async def on_data_table_row_selected(self, event) -> None:
        """Handle row selection in coins table."""
        if event.data_table.id == "coins-table":
            row_index = event.cursor_row
            if 0 <= row_index < len(self.coins_data):
                coin = self.coins_data[row_index]
                await self.show_coin_details(coin)
    
    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh data periodically."""
        while self.auto_refresh:
            try:
                await asyncio.sleep(self.refresh_interval)
                if self.auto_refresh:  # Check again in case it was disabled
                    await self.refresh_data()
            except Exception:
                break  # Exit loop on error