"""
Configuration settings for the analytics application.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "tick_data.db"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Binance WebSocket configuration
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/"
BINANCE_STREAM_URL = "wss://stream.binance.com:9443/stream"

# Default symbols to track
DEFAULT_SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt"]

# Sampling timeframes (in seconds)
TIMEFRAMES = {
    "1s": 1,
    "1m": 60,
    "5m": 300
}

# Database settings
DB_ECHO = False  # Set to True for SQL query logging

# Analytics settings
DEFAULT_ROLLING_WINDOW = 100  # Default rolling window size
MIN_DATA_POINTS_FOR_REGRESSION = 50  # Minimum points needed for OLS
MIN_DATA_POINTS_FOR_ADF = 30  # Minimum points needed for ADF test

# Alert settings
ALERT_CHECK_INTERVAL = 0.5  # Check alerts every 500ms

# Frontend settings
DASHBOARD_REFRESH_INTERVAL = 0.5  # Streamlit refresh interval in seconds
MAX_DISPLAY_POINTS = 10000  # Maximum points to display in charts

