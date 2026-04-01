"""CoinGecko API integration for crypto data."""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class CoinGeckoAPI:
    """CoinGecko API client for cryptocurrency data."""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request to CoinGecko."""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API request failed: {response.status}")
        except Exception as e:
            raise Exception(f"CoinGecko API error: {e}")
    
    async def get_top_coins(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top coins by market cap."""
        try:
            data = await self._make_request(
                "coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": limit,
                    "page": 1,
                    "sparkline": False
                }
            )
            
            return [
                {
                    "rank": i + 1,
                    "symbol": coin["symbol"].upper(),
                    "name": coin["name"],
                    "price": coin["current_price"],
                    "market_cap": coin["market_cap"],
                    "volume_24h": coin["total_volume"],
                    "change_24h": coin["price_change_percentage_24h"] or 0.0,
                    "image": coin["image"],
                }
                for i, coin in enumerate(data)
            ]
        except Exception as e:
            # Return mock data if API fails
            return self._get_mock_top_coins(limit)
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """Get global cryptocurrency statistics."""
        try:
            data = await self._make_request("global")
            global_data = data.get("data", {})
            
            return {
                "total_market_cap": global_data.get("total_market_cap", {}).get("usd", 0),
                "total_volume_24h": global_data.get("total_volume", {}).get("usd", 0),
                "bitcoin_dominance": global_data.get("market_cap_percentage", {}).get("btc", 0),
                "active_cryptocurrencies": global_data.get("active_cryptocurrencies", 0),
                "markets": global_data.get("markets", 0),
                "market_cap_change_24h": global_data.get("market_cap_change_percentage_24h_usd", 0),
            }
        except Exception as e:
            # Return mock data if API fails
            return self._get_mock_global_stats()
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get Fear & Greed Index from alternative API."""
        session = await self._get_session()
        
        try:
            async with session.get("https://api.alternative.me/fng/") as response:
                if response.status == 200:
                    data = await response.json()
                    if data["data"]:
                        latest = data["data"][0]
                        return {
                            "value": int(latest["value"]),
                            "classification": latest["value_classification"],
                            "timestamp": datetime.fromtimestamp(
                                int(latest["timestamp"]), 
                                tz=timezone.utc
                            ).strftime("%Y-%m-%d"),
                        }
        except Exception:
            pass
        
        # Return mock data if API fails
        return {"value": 50, "classification": "Neutral", "timestamp": datetime.now().strftime("%Y-%m-%d")}
    
    async def get_coin_details(self, coin_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific coin."""
        try:
            data = await self._make_request(f"coins/{coin_id}")
            
            market_data = data.get("market_data", {})
            
            return {
                "id": data.get("id"),
                "symbol": data.get("symbol", "").upper(),
                "name": data.get("name"),
                "description": data.get("description", {}).get("en", "")[:500],
                "price": market_data.get("current_price", {}).get("usd", 0),
                "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                "volume_24h": market_data.get("total_volume", {}).get("usd", 0),
                "change_24h": market_data.get("price_change_percentage_24h", 0),
                "change_7d": market_data.get("price_change_percentage_7d", 0),
                "change_30d": market_data.get("price_change_percentage_30d", 0),
                "all_time_high": market_data.get("ath", {}).get("usd", 0),
                "all_time_low": market_data.get("atl", {}).get("usd", 0),
                "circulating_supply": market_data.get("circulating_supply", 0),
                "total_supply": market_data.get("total_supply", 0),
                "max_supply": market_data.get("max_supply"),
            }
        except Exception as e:
            # Return mock data if API fails
            return self._get_mock_coin_details(coin_id)
    
    def _get_mock_top_coins(self, limit: int) -> List[Dict[str, Any]]:
        """Get mock top coins data for offline/fallback."""
        mock_coins = [
            {"rank": 1, "symbol": "BTC", "name": "Bitcoin", "price": 70000, "market_cap": 1380000000000, "volume_24h": 25000000000, "change_24h": 2.5},
            {"rank": 2, "symbol": "ETH", "name": "Ethereum", "price": 3500, "market_cap": 420000000000, "volume_24h": 15000000000, "change_24h": 1.8},
            {"rank": 3, "symbol": "BNB", "name": "BNB", "price": 600, "market_cap": 89000000000, "volume_24h": 2000000000, "change_24h": -0.5},
            {"rank": 4, "symbol": "SOL", "name": "Solana", "price": 200, "market_cap": 89000000000, "volume_24h": 3000000000, "change_24h": 3.2},
            {"rank": 5, "symbol": "XRP", "name": "XRP", "price": 0.6, "market_cap": 33000000000, "volume_24h": 1500000000, "change_24h": -1.2},
        ]
        
        # Extend with more mock data if needed
        while len(mock_coins) < limit:
            mock_coins.append({
                "rank": len(mock_coins) + 1,
                "symbol": f"COIN{len(mock_coins) + 1}",
                "name": f"Mock Coin {len(mock_coins) + 1}",
                "price": 10.0,
                "market_cap": 1000000000,
                "volume_24h": 100000000,
                "change_24h": 0.0,
            })
        
        return mock_coins[:limit]
    
    def _get_mock_global_stats(self) -> Dict[str, Any]:
        """Get mock global stats for offline/fallback."""
        return {
            "total_market_cap": 2500000000000,
            "total_volume_24h": 80000000000,
            "bitcoin_dominance": 52.5,
            "active_cryptocurrencies": 10000,
            "markets": 800,
            "market_cap_change_24h": 1.2,
        }
    
    def _get_mock_coin_details(self, coin_id: str) -> Dict[str, Any]:
        """Get mock coin details for offline/fallback."""
        return {
            "id": coin_id,
            "symbol": "BTC",
            "name": "Bitcoin",
            "description": "Bitcoin is a decentralized cryptocurrency.",
            "price": 70000,
            "market_cap": 1380000000000,
            "volume_24h": 25000000000,
            "change_24h": 2.5,
            "change_7d": 5.2,
            "change_30d": 12.8,
            "all_time_high": 73800,
            "all_time_low": 67.81,
            "circulating_supply": 19700000,
            "total_supply": 19700000,
            "max_supply": 21000000,
        }


# Global instance
_coingecko_api = None

async def get_coingecko_api() -> CoinGeckoAPI:
    """Get global CoinGecko API instance."""
    global _coingecko_api
    if _coingecko_api is None:
        _coingecko_api = CoinGeckoAPI()
    return _coingecko_api

async def cleanup_coingecko():
    """Cleanup CoinGecko API resources."""
    global _coingecko_api
    if _coingecko_api:
        await _coingecko_api.close()
        _coingecko_api = None