"""Database operations for RiverTerminal."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from .config import get_db_path


class Database:
    """SQLite database manager for RiverTerminal."""
    
    def __init__(self):
        self.db_path = get_db_path()
        self._init_db()
    
    def _init_db(self):
        """Initialize database with required tables."""
        try:
            with self.get_connection() as conn:
                # Watchlists table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS watchlists (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Watchlist items
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS watchlist_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        watchlist_id INTEGER,
                        ticker TEXT NOT NULL,
                        position INTEGER DEFAULT 0,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (watchlist_id) REFERENCES watchlists (id) ON DELETE CASCADE
                    )
                """)
                
                # Portfolio positions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT NOT NULL,
                        shares REAL NOT NULL,
                        cost_basis REAL NOT NULL,
                        purchase_date DATE NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Dividend tracking table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS dividends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        position_id INTEGER,
                        ticker TEXT NOT NULL,
                        amount REAL NOT NULL,
                        ex_date DATE NOT NULL,
                        payment_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (position_id) REFERENCES portfolio_positions (id) ON DELETE CASCADE
                    )
                """)
                
                # Create default watchlist if none exists
                cursor = conn.execute("SELECT COUNT(*) FROM watchlists")
                if cursor.fetchone()[0] == 0:
                    conn.execute("INSERT INTO watchlists (name) VALUES (?)", ("Default",))
                
                conn.commit()
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get_watchlists(self) -> List[Dict[str, Any]]:
        """Get all watchlists."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM watchlists ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def create_watchlist(self, name: str) -> int:
        """Create new watchlist, return ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("INSERT INTO watchlists (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid
    
    def delete_watchlist(self, watchlist_id: int):
        """Delete watchlist and all its items."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM watchlists WHERE id = ?", (watchlist_id,))
            conn.commit()
    
    def get_watchlist_items(self, watchlist_id: int) -> List[Dict[str, Any]]:
        """Get all tickers in a watchlist."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM watchlist_items 
                WHERE watchlist_id = ? 
                ORDER BY position, added_at
            """, (watchlist_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_to_watchlist(self, watchlist_id: int, ticker: str) -> bool:
        """Add ticker to watchlist. Returns False if already exists."""
        with self.get_connection() as conn:
            # Check if already exists
            cursor = conn.execute("""
                SELECT id FROM watchlist_items 
                WHERE watchlist_id = ? AND ticker = ?
            """, (watchlist_id, ticker.upper()))
            
            if cursor.fetchone():
                return False
            
            # Get next position
            cursor = conn.execute("""
                SELECT COALESCE(MAX(position), 0) + 1 
                FROM watchlist_items 
                WHERE watchlist_id = ?
            """, (watchlist_id,))
            position = cursor.fetchone()[0]
            
            # Add ticker
            conn.execute("""
                INSERT INTO watchlist_items (watchlist_id, ticker, position) 
                VALUES (?, ?, ?)
            """, (watchlist_id, ticker.upper(), position))
            
            conn.commit()
            return True
    
    def remove_from_watchlist(self, watchlist_id: int, ticker: str):
        """Remove ticker from watchlist."""
        with self.get_connection() as conn:
            conn.execute("""
                DELETE FROM watchlist_items 
                WHERE watchlist_id = ? AND ticker = ?
            """, (watchlist_id, ticker.upper()))
            conn.commit()
    
    def get_default_watchlist_id(self) -> int:
        """Get the default watchlist ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT id FROM watchlists WHERE name = ?", ("Default",))
            row = cursor.fetchone()
            return row["id"] if row else 1
    
    # Portfolio methods
    def get_portfolio_positions(self) -> List[Dict[str, Any]]:
        """Get all portfolio positions."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM portfolio_positions 
                ORDER BY ticker
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def add_portfolio_position(self, ticker: str, shares: float, cost_basis: float, 
                             purchase_date: str, notes: str = "") -> int:
        """Add new portfolio position."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO portfolio_positions 
                (ticker, shares, cost_basis, purchase_date, notes) 
                VALUES (?, ?, ?, ?, ?)
            """, (ticker.upper(), shares, cost_basis, purchase_date, notes))
            conn.commit()
            return cursor.lastrowid
    
    def update_portfolio_position(self, position_id: int, shares: float, 
                                cost_basis: float, purchase_date: str, notes: str = ""):
        """Update existing portfolio position."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE portfolio_positions 
                SET shares = ?, cost_basis = ?, purchase_date = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (shares, cost_basis, purchase_date, notes, position_id))
            conn.commit()
    
    def delete_portfolio_position(self, position_id: int):
        """Delete portfolio position."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM portfolio_positions WHERE id = ?", (position_id,))
            conn.commit()
    
    def add_dividend(self, position_id: int, ticker: str, amount: float, 
                    ex_date: str, payment_date: str = None):
        """Add dividend record."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO dividends 
                (position_id, ticker, amount, ex_date, payment_date) 
                VALUES (?, ?, ?, ?, ?)
            """, (position_id, ticker.upper(), amount, ex_date, payment_date))
            conn.commit()
    
    def get_dividends_for_position(self, position_id: int) -> List[Dict[str, Any]]:
        """Get dividends for a specific position."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM dividends 
                WHERE position_id = ? 
                ORDER BY ex_date DESC
            """, (position_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_dividends(self) -> List[Dict[str, Any]]:
        """Get all dividend records."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT d.*, p.ticker as position_ticker 
                FROM dividends d
                LEFT JOIN portfolio_positions p ON d.position_id = p.id
                ORDER BY d.ex_date DESC
            """)
            return [dict(row) for row in cursor.fetchall()]


# Global database instance
db = Database()