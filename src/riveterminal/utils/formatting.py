"""Formatting utilities for financial data display."""

from typing import Union, Optional
from datetime import datetime
from rich.text import Text
from rich.style import Style

from ..config import COLORS


def format_currency(value: Union[float, int], decimals: int = 2) -> str:
    """Format value as currency."""
    if value == 0:
        return "$0.00"
    
    abs_value = abs(value)
    
    # Format large numbers with suffixes
    if abs_value >= 1_000_000_000_000:  # Trillions
        formatted = f"${abs_value/1_000_000_000_000:.{decimals}f}T"
    elif abs_value >= 1_000_000_000:  # Billions
        formatted = f"${abs_value/1_000_000_000:.{decimals}f}B"
    elif abs_value >= 1_000_000:  # Millions
        formatted = f"${abs_value/1_000_000:.{decimals}f}M"
    elif abs_value >= 1_000:  # Thousands
        formatted = f"${abs_value/1_000:.{decimals}f}K"
    else:
        formatted = f"${abs_value:.{decimals}f}"
    
    return f"-{formatted}" if value < 0 else formatted


def format_number(value: Union[float, int], decimals: int = 2) -> str:
    """Format large numbers with suffixes."""
    if value == 0:
        return "0"
    
    abs_value = abs(value)
    
    if abs_value >= 1_000_000_000_000:  # Trillions
        formatted = f"{abs_value/1_000_000_000_000:.{decimals}f}T"
    elif abs_value >= 1_000_000_000:  # Billions
        formatted = f"{abs_value/1_000_000_000:.{decimals}f}B"
    elif abs_value >= 1_000_000:  # Millions
        formatted = f"{abs_value/1_000_000:.{decimals}f}M"
    elif abs_value >= 1_000:  # Thousands
        formatted = f"{abs_value/1_000:.{decimals}f}K"
    else:
        formatted = f"{abs_value:,.{decimals}f}"
    
    return f"-{formatted}" if value < 0 else formatted


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage value."""
    if value == 0:
        return "0.00%"
    return f"{value:+.{decimals}f}%"


def format_price_change(price: float, change: float, change_pct: float) -> Text:
    """Format price with change, colored appropriately."""
    price_str = f"{price:.2f}"
    change_str = f"{change:+.2f}"
    pct_str = f"({change_pct:+.2f}%)"
    
    # Determine color
    if change > 0:
        color = COLORS["positive"]
    elif change < 0:
        color = COLORS["negative"]
    else:
        color = COLORS["neutral"]
    
    text = Text()
    text.append(price_str, style=Style(color=COLORS["neutral"]))
    text.append(f" {change_str} {pct_str}", style=Style(color=color))
    
    return text


def format_volume(volume: int) -> str:
    """Format trading volume."""
    return format_number(volume, 1)


def format_market_cap(market_cap: int) -> str:
    """Format market capitalization."""
    return format_currency(market_cap, 1)


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    if diff.days > 7:
        return dt.strftime("%Y-%m-%d")
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now"


def format_time_only() -> str:
    """Format current time for header display."""
    return datetime.now().strftime("%H:%M:%S")


def get_change_color(change: float) -> str:
    """Get color for price change."""
    if change > 0:
        return COLORS["positive"]
    elif change < 0:
        return COLORS["negative"]
    else:
        return COLORS["neutral"]


def format_ticker_symbol(symbol: str) -> Text:
    """Format ticker symbol with accent color."""
    return Text(symbol.upper(), style=Style(color=COLORS["accent"], bold=True))


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_ratio(value: Optional[float], decimals: int = 2) -> str:
    """Format ratio values (P/E, etc.)."""
    if value is None or value == 0:
        return "N/A"
    return f"{value:.{decimals}f}"


# Alias for backward compatibility
get_color_for_change = get_change_color