"""News screen for viewing financial news feeds."""

import asyncio
import webbrowser
from textual.widgets import Static, DataTable, Input
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from typing import List, Dict, Any

from ..data.news_feeds import news
from ..utils.formatting import format_time_only, format_datetime


class NewsTable(DataTable):
    """Custom DataTable for news display."""
    
    def __init__(self):
        super().__init__()
        self.news_data = []
        
        # Configure table
        self.cursor_type = "row"
        self.zebra_stripes = True
        
        # Add columns
        self.add_column("Time", width=10)
        self.add_column("Source", width=15)
        self.add_column("Headline", width=80)
    
    async def load_news(self, ticker_filter: str = None):
        """Load news data."""
        try:
            if ticker_filter:
                self.news_data = await news.get_ticker_news(ticker_filter, limit=50)
            else:
                self.news_data = await news.get_all_news()
            
            self.update_display()
            
        except Exception as e:
            self.clear()
            self.add_row("Error", "System", f"Failed to load news: {e}")
    
    def update_display(self):
        """Update the news display."""
        self.clear()
        
        if not self.news_data:
            self.add_row("No news", "System", "No news articles found")
            return
        
        for article in self.news_data:
            time_str = format_datetime(article['published'])
            source = article['source'][:15]
            headline = article['title'][:80]
            
            self.add_row(
                time_str,
                source,
                headline,
                key=article['link']  # Store link as key for opening
            )
    
    def get_selected_article(self) -> Dict[str, Any]:
        """Get currently selected article."""
        if self.cursor_row < len(self.news_data):
            return self.news_data[self.cursor_row]
        return {}
    
    def get_selected_link(self) -> str:
        """Get link of selected article."""
        if self.cursor_row < len(self.rows):
            row_key = self.get_row_at(self.cursor_row).key
            return row_key if row_key else ""
        return ""


class ArticlePreviewWidget(Static):
    """Widget showing preview of selected article."""
    
    def __init__(self):
        super().__init__()
        self.current_article = None
    
    def show_article(self, article: Dict[str, Any]):
        """Display article preview."""
        self.current_article = article
        
        if not article:
            self.update("Select an article to view preview")
            return
        
        preview_text = Text()
        preview_text.append(f"{article['title']}\n\n", style="bold white")
        preview_text.append(f"Source: {article['source']}\n", style="cyan")
        preview_text.append(f"Published: {format_datetime(article['published'])}\n\n", style="dim white")
        
        if article.get('summary'):
            preview_text.append("Summary:\n", style="bold yellow")
            preview_text.append(f"{article['summary']}\n\n", style="white")
        
        preview_text.append(f"Link: {article['link']}", style="blue underline")
        
        panel = Panel(
            preview_text,
            title="📰 Article Preview",
            title_align="left",
            border_style="yellow"
        )
        
        self.update(panel)


class NewsScreen(Screen):
    """News screen for viewing financial news."""
    
    BINDINGS = [
        ("f1", "show_dashboard", "Dashboard"),
        ("f2", "show_quote", "Quote"),
        ("f3", "show_watchlist", "Watchlist"),
        ("f4", "show_chart", "Chart"),
        ("f6", "show_news", "News"),
        ("enter", "open_article", "Open Article"),
        ("r", "refresh", "Refresh"),
        ("c", "clear_filter", "Clear Filter"),
        ("escape", "back", "Back"),
    ]
    
    def __init__(self):
        super().__init__()
        self.current_filter = None
        self.filter_mode = False
    
    def compose(self):
        """Compose the news screen layout."""
        with Vertical():
            # Header
            yield Static(self._get_header(), id="header")
            
            # Filter input
            with Horizontal(id="filter_container"):
                yield Static("Filter by ticker: ", shrink=True)
                yield Input(
                    placeholder="Enter ticker symbol to filter news (e.g., AAPL)",
                    id="filter_input"
                )
            
            with Horizontal():
                # News table (left side)
                with Vertical(id="news_column"):
                    yield NewsTable()
                
                # Article preview (right side)
                with Vertical(id="preview_column"):
                    yield ArticlePreviewWidget()
            
            # Instructions
            yield Static(self._get_instructions(), id="instructions")
    
    def _get_header(self) -> Panel:
        """Get header panel."""
        current_time = format_time_only()
        header_text = Text()
        header_text.append("RiverTerminal", style="bold cyan")
        header_text.append(" | ", style="white")
        
        if self.current_filter:
            header_text.append(f"News - {self.current_filter}", style="bold white")
        else:
            header_text.append("News - All Sources", style="bold white")
        
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
        instructions.append("📰 News Controls:\n\n", style="bold cyan")
        instructions.append("• ↑↓: Navigate articles\n", style="white")
        instructions.append("• Enter: Open article in browser\n", style="white")
        instructions.append("• Filter input: Show only news for specific ticker\n", style="white")
        instructions.append("• C: Clear ticker filter\n", style="white")
        instructions.append("• R: Refresh news\n", style="white")
        
        return Panel(
            instructions,
            title="ℹ️ Instructions",
            title_align="left",
            border_style="green",
            height=10
        )
    
    async def on_mount(self):
        """Initialize the screen."""
        # Hide filter input initially
        filter_container = self.query_one("#filter_container")
        filter_container.display = False
        
        await self.load_news()
        
        # Set up auto-refresh every 5 minutes
        self.set_interval(300.0, self.load_news)
        # Update header clock every second
        self.set_interval(1.0, self.update_header)
    
    async def on_input_submitted(self, event):
        """Handle filter input submission."""
        if event.input.id == "filter_input":
            ticker = event.input.value.strip().upper()
            if ticker:
                self.current_filter = ticker
                await self.load_news()
                self.update_header()
                self._hide_filter_input()
    
    async def on_data_table_row_selected(self, event):
        """Handle news table row selection."""
        if isinstance(event.data_table, NewsTable):
            article = event.data_table.get_selected_article()
            preview_widget = self.query_one(ArticlePreviewWidget)
            preview_widget.show_article(article)
    
    async def load_news(self):
        """Load news data."""
        news_table = self.query_one(NewsTable)
        await news_table.load_news(self.current_filter)
        
        # Show first article preview
        if news_table.news_data:
            preview_widget = self.query_one(ArticlePreviewWidget)
            preview_widget.show_article(news_table.news_data[0])
    
    def update_header(self):
        """Update the header with current time."""
        header_widget = self.query_one("#header", Static)
        header_widget.update(self._get_header())
    
    def _show_filter_input(self):
        """Show filter input."""
        filter_container = self.query_one("#filter_container")
        filter_container.display = True
        filter_input = self.query_one("#filter_input", Input)
        filter_input.focus()
        self.filter_mode = True
    
    def _hide_filter_input(self):
        """Hide filter input."""
        filter_container = self.query_one("#filter_container")
        filter_container.display = False
        news_table = self.query_one(NewsTable)
        news_table.focus()
        self.filter_mode = False
    
    def action_refresh(self):
        """Manual refresh action."""
        asyncio.create_task(self.load_news())
    
    def action_clear_filter(self):
        """Clear ticker filter."""
        if self.current_filter:
            self.current_filter = None
            filter_input = self.query_one("#filter_input", Input)
            filter_input.value = ""
            asyncio.create_task(self.load_news())
            self.update_header()
        else:
            # Show filter input to add filter
            self._show_filter_input()
    
    def action_open_article(self):
        """Open selected article in browser."""
        news_table = self.query_one(NewsTable)
        link = news_table.get_selected_link()
        if link:
            try:
                webbrowser.open(link)
                self.notify("Opened article in browser")
            except Exception as e:
                self.notify(f"Error opening link: {e}")
        else:
            self.notify("No article selected")
    
    def action_back(self):
        """Go back to previous screen."""
        if self.filter_mode:
            self._hide_filter_input()
        else:
            self.app.pop_screen()
    
    def action_show_dashboard(self):
        """Switch to dashboard screen."""
        self.app.pop_screen()
    
    def action_show_quote(self):
        """Switch to quote screen."""
        self.app.push_screen("quote")
    
    def action_show_watchlist(self):
        """Switch to watchlist screen."""
        self.app.push_screen("watchlist")
    
    def action_show_chart(self):
        """Switch to chart screen."""
        self.app.push_screen("chart")
    
    def action_show_news(self):
        """Stay on news screen."""
        pass
    
    async def on_key(self, event: events.Key):
        """Handle key events."""
        if event.key == "escape" and self.filter_mode:
            self._hide_filter_input()
            event.prevent_default()
        elif event.key == "/" and not self.filter_mode:
            # Quick search
            self._show_filter_input()
            event.prevent_default()
        else:
            await super().on_key(event)