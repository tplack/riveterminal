"""Yahoo Finance data provider."""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor


class YahooFinanceProvider:
    """Yahoo Finance data provider."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current quote for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(self.executor, lambda: ticker.info)
            hist = await loop.run_in_executor(
                self.executor, 
                lambda: ticker.history(period="2d", interval="1d")
            )
            
            if hist.empty or not info:
                return None
            
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            # Calculate change
            change = latest['Close'] - prev['Close']
            change_pct = (change / prev['Close']) * 100 if prev['Close'] != 0 else 0
            
            return {
                'symbol': symbol.upper(),
                'price': latest['Close'],
                'change': change,
                'change_percent': change_pct,
                'volume': latest['Volume'],
                'open': latest['Open'],
                'high': latest['High'],
                'low': latest['Low'],
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'beta': info.get('beta', 0),
                'eps': info.get('trailingEps', 0),
                'company_name': info.get('longName', symbol.upper()),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'last_updated': datetime.now(),
            }
        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            return None
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get quotes for multiple symbols."""
        tasks = [self.get_quote(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        quotes = {}
        for symbol, result in zip(symbols, results):
            if not isinstance(result, Exception) and result is not None:
                quotes[symbol.upper()] = result
        
        return quotes
    
    async def get_market_overview(self) -> Dict[str, Dict[str, Any]]:
        """Get market overview data."""
        indices = ['^GSPC', '^DJI', '^IXIC', '^VIX', '^RUT']
        return await self.get_multiple_quotes(indices)
    
    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """Get historical price data."""
        try:
            ticker = yf.Ticker(symbol)
            loop = asyncio.get_event_loop()
            hist = await loop.run_in_executor(
                self.executor,
                lambda: ticker.history(period=period)
            )
            return hist if not hist.empty else None
        except Exception as e:
            print(f"Error fetching history for {symbol}: {e}")
            return None
    
    async def get_top_movers(self, count: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Get top gainers and losers (simplified version)."""
        # This is a simplified version - in a real implementation,
        # you might use a stock screener API or maintain a list of popular stocks
        popular_stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 
            'META', 'NVDA', 'NFLX', 'AMD', 'BABA',
            'JPM', 'JNJ', 'V', 'PG', 'UNH',
            'HD', 'MA', 'DIS', 'ADBE', 'PYPL'
        ]
        
        quotes = await self.get_multiple_quotes(popular_stocks)
        
        # Sort by change percent
        sorted_quotes = sorted(
            quotes.values(),
            key=lambda x: x.get('change_percent', 0),
            reverse=True
        )
        
        gainers = sorted_quotes[:count]
        losers = sorted_quotes[-count:]
        
        return {
            'gainers': gainers,
            'losers': losers
        }
    
    async def search_symbol(self, query: str) -> List[Dict[str, Any]]:
        """Search for symbols (simplified - returns exact match if valid)."""
        quote = await self.get_quote(query)
        return [quote] if quote else []
    
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get options chain data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            loop = asyncio.get_event_loop()
            
            # Get expiry dates
            expiry_dates = await loop.run_in_executor(
                self.executor, 
                lambda: ticker.options
            )
            
            if not expiry_dates:
                return None
            
            # Get current stock price
            info = await loop.run_in_executor(self.executor, lambda: ticker.info)
            current_price = info.get('currentPrice', 0)
            
            if not current_price:
                # Try to get from recent history
                hist = await loop.run_in_executor(
                    self.executor,
                    lambda: ticker.history(period="1d", interval="1d")
                )
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Get options data for each expiry
            options_data = {}
            
            for expiry in expiry_dates[:10]:  # Limit to first 10 expiries for performance
                try:
                    option_chain = await loop.run_in_executor(
                        self.executor,
                        lambda exp=expiry: ticker.option_chain(exp)
                    )
                    
                    calls_data = []
                    puts_data = []
                    
                    # Process calls
                    if not option_chain.calls.empty:
                        for _, row in option_chain.calls.iterrows():
                            calls_data.append({
                                'strike': float(row.get('strike', 0)),
                                'lastPrice': float(row.get('lastPrice', 0)),
                                'bid': float(row.get('bid', 0)),
                                'ask': float(row.get('ask', 0)),
                                'volume': int(row.get('volume', 0)),
                                'openInterest': int(row.get('openInterest', 0)),
                                'impliedVolatility': float(row.get('impliedVolatility', 0)),
                                'delta': float(row.get('delta', 0)) if 'delta' in row else 0,
                                'gamma': float(row.get('gamma', 0)) if 'gamma' in row else 0,
                                'theta': float(row.get('theta', 0)) if 'theta' in row else 0,
                                'vega': float(row.get('vega', 0)) if 'vega' in row else 0,
                                'rho': float(row.get('rho', 0)) if 'rho' in row else 0,
                                'bidSize': int(row.get('bidSize', 0)) if 'bidSize' in row else 0,
                                'askSize': int(row.get('askSize', 0)) if 'askSize' in row else 0,
                            })
                    
                    # Process puts
                    if not option_chain.puts.empty:
                        for _, row in option_chain.puts.iterrows():
                            puts_data.append({
                                'strike': float(row.get('strike', 0)),
                                'lastPrice': float(row.get('lastPrice', 0)),
                                'bid': float(row.get('bid', 0)),
                                'ask': float(row.get('ask', 0)),
                                'volume': int(row.get('volume', 0)),
                                'openInterest': int(row.get('openInterest', 0)),
                                'impliedVolatility': float(row.get('impliedVolatility', 0)),
                                'delta': float(row.get('delta', 0)) if 'delta' in row else 0,
                                'gamma': float(row.get('gamma', 0)) if 'gamma' in row else 0,
                                'theta': float(row.get('theta', 0)) if 'theta' in row else 0,
                                'vega': float(row.get('vega', 0)) if 'vega' in row else 0,
                                'rho': float(row.get('rho', 0)) if 'rho' in row else 0,
                                'bidSize': int(row.get('bidSize', 0)) if 'bidSize' in row else 0,
                                'askSize': int(row.get('askSize', 0)) if 'askSize' in row else 0,
                            })
                    
                    options_data[expiry] = {
                        'calls': calls_data,
                        'puts': puts_data
                    }
                    
                except Exception as e:
                    print(f"Error processing expiry {expiry}: {e}")
                    continue
            
            return {
                'symbol': symbol.upper(),
                'underlying_price': current_price,
                'expiry_dates': expiry_dates,
                'options': options_data,
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            print(f"Error fetching options chain for {symbol}: {e}")
            return None
    
    async def get_historical_with_sma(self, symbol: str, period: str = "1mo", 
                                    sma_periods: List[int] = [20, 50, 200]) -> Optional[pd.DataFrame]:
        """Get historical data with SMA overlays."""
        try:
            hist = await self.get_historical_data(symbol, period)
            if hist is None or hist.empty:
                return None
            
            # Calculate SMAs
            for sma_period in sma_periods:
                if len(hist) >= sma_period:
                    hist[f'SMA{sma_period}'] = hist['Close'].rolling(window=sma_period).mean()
            
            return hist
            
        except Exception as e:
            print(f"Error calculating SMAs for {symbol}: {e}")
            return None


# Alias for backwards compatibility
YahooDataProvider = YahooFinanceProvider

# Global provider instance
yahoo = YahooFinanceProvider()