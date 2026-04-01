"""News feed data provider."""

import asyncio
import feedparser
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from ..config import NEWS_FEEDS


class NewsProvider:
    """RSS news feed provider."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def fetch_feed(self, url: str, source: str) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse feed in thread pool
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(
                self.executor,
                feedparser.parse,
                response.text
            )
            
            articles = []
            for entry in feed.entries[:20]:  # Limit to 20 articles per feed
                # Parse published date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                else:
                    published = datetime.now(timezone.utc)
                
                # Clean up summary/description
                summary = getattr(entry, 'summary', '')
                if len(summary) > 200:
                    summary = summary[:200] + '...'
                
                article = {
                    'title': entry.title,
                    'link': entry.link,
                    'summary': summary,
                    'published': published,
                    'source': source,
                }
                articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"Error fetching {source} feed: {e}")
            return []
    
    async def get_all_news(self) -> List[Dict[str, Any]]:
        """Fetch news from all configured feeds."""
        tasks = []
        for source, url in NEWS_FEEDS.items():
            task = self.fetch_feed(url, source)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all articles
        all_articles = []
        for articles in results:
            if not isinstance(articles, Exception):
                all_articles.extend(articles)
        
        # Sort by published date (newest first)
        all_articles.sort(key=lambda x: x['published'], reverse=True)
        
        return all_articles[:100]  # Limit to 100 total articles
    
    async def get_ticker_news(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get news articles mentioning a specific ticker."""
        all_news = await self.get_all_news()
        
        # Filter articles that mention the ticker
        ticker_upper = ticker.upper()
        ticker_news = []
        
        for article in all_news:
            title_upper = article['title'].upper()
            summary_upper = article['summary'].upper()
            
            if (ticker_upper in title_upper or 
                ticker_upper in summary_upper or
                f"${ticker_upper}" in title_upper or
                f"${ticker_upper}" in summary_upper):
                ticker_news.append(article)
                
                if len(ticker_news) >= limit:
                    break
        
        return ticker_news
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global news provider instance
news = NewsProvider()