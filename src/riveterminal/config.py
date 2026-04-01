"""Configuration management for RiverTerminal."""

import os
from pathlib import Path
from typing import Dict, Any

# Application directories
APP_DIR = Path.home() / ".riveterminal"
DB_PATH = APP_DIR / "riveterminal.db"
CACHE_DIR = APP_DIR / "cache"

# Ensure directories exist
APP_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "refresh_interval": 5,  # seconds
    "max_news_items": 50,
    "default_chart_timeframe": "1M",
    "theme": "dark",
    "enable_cache": True,
    "cache_ttl": 300,  # 5 minutes
}

# RSS News feeds
NEWS_FEEDS = {
    "Google Finance": "https://news.google.com/rss/search?q=stock+market+finance&hl=en-US&gl=US&ceid=US:en",
    "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
    "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    "Yahoo Finance": "https://news.google.com/rss/search?q=finance+stocks&hl=en-US&gl=US&ceid=US:en",
    "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
    "Investing.com": "https://www.investing.com/rss/news.rss",
}

# Market indices for dashboard
MARKET_INDICES = {
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI", 
    "NASDAQ": "^IXIC",
    "VIX": "^VIX",
    "Russell 2000": "^RUT",
}

# Color scheme
COLORS = {
    "positive": "green",
    "negative": "red",
    "neutral": "white",
    "info": "cyan",
    "warning": "yellow",
    "accent": "bright_blue",
}

def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return DEFAULT_CONFIG.copy()

def get_db_path() -> Path:
    """Get database file path."""
    return DB_PATH

def get_cache_dir() -> Path:
    """Get cache directory path."""
    return CACHE_DIR