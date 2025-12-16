"""
Data storage layer for tick data and sampled aggregates.
"""
import sqlite3
import threading
import time
from datetime import datetime
from typing import List, Optional, Tuple
import pandas as pd
import logging
from pathlib import Path

from config import DB_PATH, TIMEFRAMES

logger = logging.getLogger(__name__)


class DataStorage:
    """
    SQLite-based storage for tick data and resampled aggregates.
    Thread-safe operations for concurrent writes.
    """
    
    def __init__(self, db_path: Path = DB_PATH):
        """Initialize storage with database connection."""
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Raw tick data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        
        # Create index for ticks table
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
            ON ticks(symbol, timestamp)
        """)
        
        # Resampled data tables for each timeframe
        for timeframe_name in TIMEFRAMES.keys():
            # Quote table names that start with numbers (like "1s_bars")
            table_name_clean = timeframe_name + "_bars"
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS "{table_name_clean}" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    trade_count INTEGER NOT NULL,
                    UNIQUE(symbol, timestamp)
                )
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{timeframe_name}_symbol_timestamp 
                ON "{table_name_clean}"(symbol, timestamp)
            """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def insert_tick(self, timestamp: int, symbol: str, price: float, size: float):
        """Insert a single tick into the database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ticks (timestamp, symbol, price, size, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, symbol, price, size, time.time()))
            conn.commit()
            conn.close()
    
    def insert_bars(self, timeframe: str, bars: pd.DataFrame):
        """
        Insert resampled bars for a given timeframe.
        
        Args:
            timeframe: One of '1s', '1m', '5m'
            bars: DataFrame with columns: timestamp, symbol, open, high, low, close, volume, trade_count
        """
        if timeframe not in TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            table_name = f'"{timeframe}_bars"'
            
            for _, row in bars.iterrows():
                conn.execute(f"""
                    INSERT OR REPLACE INTO {table_name} 
                    (timestamp, symbol, open, high, low, close, volume, trade_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['timestamp']),
                    row['symbol'],
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume'],
                    int(row.get('trade_count', 0))
                ))
            
            conn.commit()
            conn.close()
    
    def get_ticks(self, symbol: str, start_time: Optional[int] = None, 
                  end_time: Optional[int] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """Retrieve tick data for a symbol."""
        query = "SELECT timestamp, symbol, price, size FROM ticks WHERE symbol = ?"
        params = [symbol]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df = df.sort_values('timestamp')
        return df
    
    def get_bars(self, symbol: str, timeframe: str, 
                 start_time: Optional[int] = None, 
                 end_time: Optional[int] = None,
                 limit: Optional[int] = None) -> pd.DataFrame:
        """Retrieve resampled bars for a symbol."""
        if timeframe not in TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        table_name = f'"{timeframe}_bars"'
        query = f"SELECT * FROM {table_name} WHERE symbol = ?"
        params = [symbol]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df = df.sort_values('timestamp')
            df = df.drop('id', axis=1, errors='ignore')
        
        return df
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT price FROM ticks 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (symbol,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_symbols(self) -> List[str]:
        """Get list of all symbols in the database."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM ticks")
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        return symbols
    
    def get_data_range(self, symbol: str) -> Tuple[Optional[int], Optional[int]]:
        """Get the time range of available data for a symbol."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp) 
            FROM ticks 
            WHERE symbol = ?
        """, (symbol,))
        result = cursor.fetchone()
        conn.close()
        return result if result else (None, None)

