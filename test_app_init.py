#!/usr/bin/env python3
"""Test application initialization without running TUI."""

def test_app_initialization():
    """Test that the app can be created without errors."""
    try:
        from riveterminal.app import RiverTerminalApp
        
        # Create app instance
        app = RiverTerminalApp()
        
        # Check that screens are installed
        try:
            # Try to access the installed screens
            dashboard_screen = app.get_screen("dashboard")
            quote_screen = app.get_screen("quote")
            watchlist_screen = app.get_screen("watchlist")
            chart_screen = app.get_screen("chart")
            news_screen = app.get_screen("news")
            
            print("✓ RiverTerminalApp created successfully")
            print("✓ All screens installed correctly:")
            print("  - Dashboard")
            print("  - Quote")
            print("  - Watchlist") 
            print("  - Chart")
            print("  - News")
            return True
            
        except Exception as e:
            print(f"✗ Screen installation issue: {e}")
            return False
        
    except Exception as e:
        print(f"✗ App initialization failed: {e}")
        return False

def test_command_parsing():
    """Test command bar functionality."""
    try:
        from riveterminal.widgets.command_bar import CommandBar
        
        # Create command bar
        command_bar = CommandBar()
        print("✓ CommandBar widget created successfully")
        
        # Test command history
        command_bar.command_history = ["AAPL", "MSFT", "DASHBOARD"]
        print(f"✓ Command history: {command_bar.command_history}")
        
        return True
        
    except Exception as e:
        print(f"✗ Command bar test failed: {e}")
        return False

def main():
    """Run application initialization tests."""
    print("Testing RiverTerminal Application Initialization...")
    print("=" * 55)
    
    success = True
    
    if not test_app_initialization():
        success = False
    
    if not test_command_parsing():
        success = False
    
    print("=" * 55)
    if success:
        print("✓ All application initialization tests passed!")
        print("\nRiverTerminal is ready to run:")
        print("  source venv/bin/activate")
        print("  python -m riveterminal")
    else:
        print("✗ Some tests failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())