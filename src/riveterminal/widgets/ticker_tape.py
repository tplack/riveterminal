"""Scrolling ticker tape widget for news and prices."""

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style
from typing import List, Dict, Any
from datetime import datetime

from ..config import COLORS


class TickerTape(Static):
    """Scrolling ticker tape for news headlines and price updates."""
    
    DEFAULT_CSS = """
    TickerTape {
        dock: bottom;
        height: 1;
        background: black;
        color: white;
        text-style: bold;
    }
    """
    
    scroll_position = reactive(0)
    
    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.items = []
        self.scroll_speed = 1
        self.max_width = 200
    
    def add_news_item(self, title: str, source: str = ""):
        """Add a news item to the ticker tape."""
        timestamp = datetime.now().strftime("%H:%M")
        if source:
            item = f"📰 [{timestamp}] {source}: {title}"
        else:
            item = f"📰 [{timestamp}] {title}"
        
        self.items.append(item)
        self._update_display()
    
    def add_price_update(self, symbol: str, price: float, change: float):
        """Add a price update to the ticker tape."""
        change_symbol = "▲" if change >= 0 else "▼"
        color = COLORS["positive"] if change >= 0 else COLORS["negative"]
        
        item = f"💹 {symbol}: ${price:.2f} {change_symbol}{abs(change):.2f}"
        self.items.append((item, color))
        self._update_display()
    
    def set_items(self, items: List[str]):
        """Set all ticker items at once."""
        self.items = items
        self._update_display()
    
    def _update_display(self):
        """Update the ticker display."""
        if not self.items:
            self.update("RiverTerminal - Real-time financial data")
            return
        
        # Create scrolling text
        separator = " • "
        
        # Convert items to text objects if they aren't already
        text_items = []
        for item in self.items:
            if isinstance(item, tuple):
                text_items.append(Text(item[0], style=Style(color=item[1])))
            else:
                text_items.append(Text(str(item), style=Style(color="white")))
        
        # Create full ticker text
        full_text = Text()
        for i, item in enumerate(text_items):
            if i > 0:
                full_text.append(separator, style=Style(color="dim white"))
            full_text.append(item)
        
        # Add padding to make scrolling smooth
        padding = " " * 50
        full_text = Text(padding) + full_text + Text(padding)
        
        self.update(full_text)
    
    def scroll_ticker(self):
        """Scroll the ticker tape (called by timer)."""
        if len(self.items) > 0:
            self.scroll_position = (self.scroll_position + self.scroll_speed) % 100
            self._update_display()
    
    def clear_items(self):
        """Clear all ticker items."""
        self.items = []
        self._update_display()
    
    def add_market_summary(self, market_data: Dict[str, Dict[str, Any]]):
        """Add market summary to ticker."""
        for symbol, data in market_data.items():
            if 'price' in data and 'change' in data:
                self.add_price_update(
                    symbol.replace("^", ""),
                    data['price'],
                    data['change']
                )
    
    def add_breaking_news(self, headlines: List[str]):
        """Add breaking news headlines."""
        for headline in headlines[:5]:  # Limit to 5 headlines
            self.add_news_item(headline)