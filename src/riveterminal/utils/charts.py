"""ASCII chart utilities using plotext."""

import plotext as plt
import pandas as pd
from typing import List, Tuple, Optional
from io import StringIO
import sys


class ChartRenderer:
    """ASCII chart renderer using plotext."""
    
    def __init__(self, width: int = 80, height: int = 20):
        self.width = width
        self.height = height
    
    def render_line_chart(
        self, 
        data: pd.DataFrame, 
        title: str = "",
        color: str = "green"
    ) -> str:
        """Render line chart from price data."""
        if data.empty:
            return "No data available"
        
        try:
            plt.clear_data()
            plt.clear_figure()
            
            # Set up plot
            plt.plot_size(self.width, self.height)
            plt.title(title)
            
            # Plot closing prices
            dates = data.index.strftime('%m/%d')
            prices = data['Close'].values
            
            plt.plot(dates, prices, color=color, marker="dot")
            
            # Configure axes
            plt.xlabel("Date")
            plt.ylabel("Price")
            
            # Show only every Nth date label to avoid crowding
            step = max(1, len(dates) // 8)
            plt.xticks(range(0, len(dates), step), [dates[i] for i in range(0, len(dates), step)])
            
            # Capture plot output
            old_stdout = sys.stdout
            sys.stdout = buffer = StringIO()
            
            plt.show()
            
            sys.stdout = old_stdout
            result = buffer.getvalue()
            
            # Clean up
            plt.clear_data()
            plt.clear_figure()
            
            return result
            
        except Exception as e:
            return f"Error rendering chart: {e}"
    
    def render_sparkline(self, prices: List[float], width: int = 20) -> str:
        """Render simple ASCII sparkline."""
        if not prices or len(prices) < 2:
            return "─" * width
        
        # Normalize prices to fit in sparkline
        min_price = min(prices)
        max_price = max(prices)
        
        if max_price == min_price:
            return "─" * width
        
        # Unicode sparkline characters
        chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        # Sample prices to fit width
        if len(prices) > width:
            step = len(prices) / width
            sampled = [prices[int(i * step)] for i in range(width)]
        else:
            sampled = prices
        
        # Convert to sparkline
        sparkline = ""
        for price in sampled:
            normalized = (price - min_price) / (max_price - min_price)
            char_index = min(int(normalized * len(chars)), len(chars) - 1)
            sparkline += chars[char_index]
        
        # Pad to desired width
        while len(sparkline) < width:
            sparkline += "─"
        
        return sparkline[:width]
    
    def render_volume_bars(self, volumes: List[float], width: int = 40, height: int = 8) -> str:
        """Render simple volume bars."""
        if not volumes:
            return ""
        
        try:
            plt.clear_data()
            plt.clear_figure()
            
            plt.plot_size(width, height)
            plt.title("Volume")
            
            # Create bar chart
            x_vals = list(range(len(volumes)))
            plt.bar(x_vals, volumes, color="cyan")
            
            plt.xlabel("Time")
            plt.ylabel("Volume")
            
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = buffer = StringIO()
            
            plt.show()
            
            sys.stdout = old_stdout
            result = buffer.getvalue()
            
            # Clean up
            plt.clear_data()
            plt.clear_figure()
            
            return result
            
        except Exception as e:
            return f"Error rendering volume: {e}"
    
    def render_multi_line(
        self, 
        datasets: List[Tuple[str, List[float], str]], 
        title: str = "",
        x_labels: Optional[List[str]] = None
    ) -> str:
        """Render multiple line series on same chart."""
        if not datasets:
            return "No data available"
        
        try:
            plt.clear_data()
            plt.clear_figure()
            
            plt.plot_size(self.width, self.height)
            plt.title(title)
            
            # Plot each dataset
            for name, data, color in datasets:
                if x_labels:
                    plt.plot(x_labels, data, color=color, label=name, marker="dot")
                else:
                    plt.plot(data, color=color, label=name, marker="dot")
            
            plt.xlabel("Time")
            plt.ylabel("Value")
            
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = buffer = StringIO()
            
            plt.show()
            
            sys.stdout = old_stdout
            result = buffer.getvalue()
            
            # Clean up
            plt.clear_data()
            plt.clear_figure()
            
            return result
            
        except Exception as e:
            return f"Error rendering multi-line chart: {e}"


def create_price_sparkline(prices: List[float], width: int = 20) -> str:
    """Create a simple price sparkline."""
    renderer = ChartRenderer()
    return renderer.render_sparkline(prices, width)


def create_line_chart(data: pd.DataFrame, title: str = "", width: int = 80, height: int = 20) -> str:
    """Create a line chart from DataFrame."""
    renderer = ChartRenderer(width, height)
    return renderer.render_line_chart(data, title)