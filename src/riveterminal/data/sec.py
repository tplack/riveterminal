"""SEC EDGAR API data provider for financial filings."""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


class SECDataProvider:
    """SEC EDGAR API data provider."""
    
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.search_url = "https://efts.sec.gov/LATEST/search-index"
        self.headers = {
            "User-Agent": "RiverTerminal/1.0 (financial-research@example.com)"  # SEC requires proper User-Agent
        }
    
    async def search_filings(self, ticker: str, filing_types: List[str] = None, 
                           start_date: str = None, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Search for filings by ticker symbol."""
        try:
            # Default filing types
            if filing_types is None:
                filing_types = ["10-K", "10-Q", "8-K", "13F-HR"]
            
            # Default start date (1 year ago)
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            params = {
                "q": ticker.upper(),
                "dateRange": "custom",
                "startdt": start_date,
                "forms": ",".join(filing_types),
                "count": limit
            }
            
            async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
                response = await client.get(self.search_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    filings = data.get("hits", {}).get("hits", [])
                    
                    processed_filings = []
                    for filing in filings:
                        source = filing.get("_source", {})
                        processed_filings.append({
                            "ticker": source.get("tickers", [ticker.upper()])[0] if source.get("tickers") else ticker.upper(),
                            "form": source.get("form", ""),
                            "file_date": source.get("file_date", ""),
                            "period_end": source.get("period_end", ""),
                            "company_name": source.get("display_names", [""])[0] if source.get("display_names") else "",
                            "accession_no": source.get("accession_no", ""),
                            "file_description": source.get("file_description", ""),
                            "document_url": f"https://www.sec.gov/Archives/edgar/data/{source.get('cik', '')}/{source.get('accession_no', '').replace('-', '')}/{source.get('root_form', '')}"
                        })
                    
                    return processed_filings
                else:
                    print(f"SEC API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error fetching SEC filings for {ticker}: {e}")
            return None
    
    async def get_company_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company information from SEC submissions."""
        try:
            # This is a simplified approach - in reality, you'd need to map ticker to CIK first
            # For now, we'll use the search API to get basic company info
            filings = await self.search_filings(ticker, ["10-K"], limit=1)
            
            if filings:
                filing = filings[0]
                return {
                    "ticker": filing.get("ticker", ""),
                    "company_name": filing.get("company_name", ""),
                    "latest_filing_date": filing.get("file_date", ""),
                    "latest_period_end": filing.get("period_end", "")
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching company info for {ticker}: {e}")
            return None
    
    def format_filings_for_display(self, filings: List[Dict[str, Any]]) -> str:
        """Format filings list for terminal display."""
        if not filings:
            return "No filings found"
        
        lines = []
        lines.append("🏛️  SEC FILINGS")
        lines.append("=" * 50)
        
        for filing in filings:
            form = filing.get("form", "")
            file_date = filing.get("file_date", "")
            period_end = filing.get("period_end", "")
            description = filing.get("file_description", "")[:50]  # Truncate long descriptions
            
            lines.append(f"{form:>8} | {file_date:>12} | {period_end:>12}")
            if description:
                lines.append(f"         {description}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_filing_types_description(self) -> Dict[str, str]:
        """Get descriptions of common filing types."""
        return {
            "10-K": "Annual report with comprehensive company overview",
            "10-Q": "Quarterly report with financial statements", 
            "8-K": "Current report of major corporate events",
            "13F-HR": "Institutional investment manager holdings report",
            "DEF 14A": "Proxy statement with executive compensation",
            "S-1": "Registration statement for new securities",
            "S-3": "Simplified registration for seasoned issuers",
            "424B": "Prospectus supplement",
            "SC 13G": "Schedule 13G beneficial ownership report"
        }


# Global instance
sec_provider = SECDataProvider()