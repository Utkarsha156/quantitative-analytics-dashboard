"""
Binance WebSocket client for real-time tick data ingestion.
"""
import json
import threading
import time
from typing import Callable, List, Optional
import websocket
import logging

logger = logging.getLogger(__name__)


class BinanceWebSocketClient:
    """
    WebSocket client for Binance tick data streams.
    Handles connection, reconnection, and data streaming.
    """
    
    def __init__(self, symbols: List[str], callback: Callable):
        """
        Initialize WebSocket client.
        
        Args:
            symbols: List of trading symbols (e.g., ['btcusdt', 'ethusdt'])
            callback: Function to call with each tick: callback(timestamp, symbol, price, size)
        """
        self.symbols = [s.lower() for s in symbols]
        self.callback = callback
        self.ws = None
        self.running = False
        self.reconnect_interval = 5
        self._lock = threading.Lock()
        
    def _build_stream_url(self) -> str:
        """Build WebSocket stream URL for multiple symbols."""
        streams = [f"{symbol}@trade" for symbol in self.symbols]
        stream_names = "/".join(streams)
        return f"wss://stream.binance.com:9443/stream?streams={stream_names}"
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            if 'data' in data:
                trade = data['data']
                symbol = trade.get('s', '').lower()
                price = float(trade.get('p', 0))
                size = float(trade.get('q', 0))
                timestamp = int(trade.get('T', time.time() * 1000))
                
                if symbol and price > 0:
                    self.callback(timestamp, symbol, price, size)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        logger.info("WebSocket connection closed")
        if self.running:
            logger.info(f"Attempting to reconnect in {self.reconnect_interval} seconds...")
            time.sleep(self.reconnect_interval)
            self._connect()
    
    def _on_open(self, ws):
        """Handle WebSocket open."""
        logger.info(f"WebSocket connected. Streaming {len(self.symbols)} symbols: {self.symbols}")
    
    def _connect(self):
        """Establish WebSocket connection."""
        url = self._build_stream_url()
        logger.info(f"Connecting to: {url}")
        
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        # Run forever (handles reconnection)
        self.ws.run_forever()
    
    def start(self):
        """Start the WebSocket client in a background thread."""
        if self.running:
            logger.warning("WebSocket client already running")
            return
        
        self.running = True
        thread = threading.Thread(target=self._connect, daemon=True)
        thread.start()
        logger.info("WebSocket client started")
    
    def stop(self):
        """Stop the WebSocket client."""
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("WebSocket client stopped")

