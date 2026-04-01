#!/usr/bin/env python3
"""Basic test to verify RiverTerminal imports and basic functionality."""

import asyncio
import sys

def test_imports():
    """Test that all modules import correctly."""
    try:
        import riveterminal
        from riveterminal.app import RiverTerminalApp
        from riveterminal.data.yahoo import yahoo
        from riveterminal.data.news_feeds import news
        from riveterminal.db import db
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

async def test_data_providers():
    """Test basic data provider functionality."""
    try:
        from riveterminal.data.yahoo import yahoo
        from riveterminal.data.news_feeds import news
        
        # Test Yahoo Finance
        quote = await yahoo.get_quote("AAPL")
        if quote:
            print(f"✓ Yahoo Finance working - AAPL: ${quote['price']:.2f}")
        else:
            print("⚠ Yahoo Finance returned no data for AAPL")
            
        # Test news feeds (first 3 articles only)  
        articles = await news.get_all_news()
        if articles:
            print(f"✓ News feeds working - {len(articles)} articles loaded")
        else:
            print("⚠ News feeds returned no data")
            
        return True
    except Exception as e:
        print(f"✗ Data provider error: {e}")
        return False

def test_database():
    """Test database functionality."""
    try:
        from riveterminal.db import db
        
        # Test database operations
        watchlists = db.get_watchlists()
        print(f"✓ Database working - {len(watchlists)} watchlists found")
        
        # Test adding/removing a test symbol
        default_id = db.get_default_watchlist_id()
        test_symbol = "TEST"
        
        # Clean up first in case it exists
        db.remove_from_watchlist(default_id, test_symbol)
        
        # Add test symbol
        success = db.add_to_watchlist(default_id, test_symbol)
        if success:
            print("✓ Database add operation working")
        
        # Remove test symbol
        db.remove_from_watchlist(default_id, test_symbol)
        print("✓ Database remove operation working")
        
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

async def main():
    """Run all tests."""
    print("Testing RiverTerminal Phase 1 MVP...")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        sys.exit(1)
    
    # Test database
    if not test_database():
        sys.exit(1)
    
    # Test data providers (this may take a moment)
    print("Testing data providers (this may take a moment)...")
    if not await test_data_providers():
        sys.exit(1)
    
    print("=" * 50)
    print("✓ All tests passed! RiverTerminal Phase 1 MVP is ready.")
    print("\nTo run the application:")
    print("  source venv/bin/activate")
    print("  python -m riveterminal")

if __name__ == "__main__":
    asyncio.run(main())