"""
Main data processing pipeline that coordinates ingestion, storage, and sampling.
"""
import threading
import time
import logging
from typing import List, Optional
from collections import deque

from websocket_client.binance_client import BinanceWebSocketClient
from backend.storage import DataStorage
from backend.sampler import DataSampler
from backend.alerts import AlertManager
from config import TIMEFRAMES, ALERT_CHECK_INTERVAL

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Main data processing pipeline.
    Coordinates WebSocket ingestion, storage, resampling, and alert checking.
    """
    
    def __init__(self, symbols: List[str], storage: DataStorage, 
                 alert_manager: Optional[AlertManager] = None):
        """
        Initialize data processor.
        
        Args:
            symbols: List of symbols to track
            storage: DataStorage instance
            alert_manager: Optional AlertManager instance
        """
        self.symbols = symbols
        self.storage = storage
        self.alert_manager = alert_manager
        
        # Recent tick buffer for resampling
        self.tick_buffers: dict = {symbol: deque(maxlen=10000) for symbol in symbols}
        self._lock = threading.Lock()
        
        # WebSocket client
        self.ws_client = None
        
        # Resampling threads
        self.resampling_threads = {}
        self.running = False
    
    def _tick_callback(self, timestamp: int, symbol: str, price: float, size: float):
        """Callback for incoming WebSocket ticks."""
        # Store tick
        self.storage.insert_tick(timestamp, symbol, price, size)
        
        # Add to buffer
        with self._lock:
            if symbol in self.tick_buffers:
                self.tick_buffers[symbol].append({
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'price': price,
                    'size': size
                })
    
    def _resample_worker(self, timeframe: str, interval: int):
        """Worker thread for periodic resampling."""
        import pandas as pd
        
        while self.running:
            try:
                time.sleep(interval)
                
                if not self.running:
                    break
                
                with self._lock:
                    # Collect ticks from buffers
                    all_ticks = []
                    for symbol, buffer in self.tick_buffers.items():
                        if buffer:
                            all_ticks.extend(list(buffer))
                    
                    if not all_ticks:
                        continue
                    
                    ticks_df = pd.DataFrame(all_ticks)
                
                # Resample
                bars = DataSampler.resample_ticks(ticks_df, timeframe)
                
                if not bars.empty:
                    self.storage.insert_bars(timeframe, bars)
                    logger.debug(f"Resampled {len(bars)} bars for timeframe {timeframe}")
            
            except Exception as e:
                logger.error(f"Error in resampling worker for {timeframe}: {e}")
    
    def _alert_check_worker(self):
        """Worker thread for checking alerts."""
        from backend.analytics import AnalyticsEngine
        
        while self.running:
            try:
                time.sleep(ALERT_CHECK_INTERVAL)
                
                if not self.running or not self.alert_manager:
                    continue
                
                # Check alerts for each symbol
                for symbol in self.symbols:
                    try:
                        # Get recent ticks
                        ticks = self.storage.get_ticks(symbol, limit=1000)
                        if len(ticks) < 100:
                            continue
                        
                        prices = ticks['price']
                        
                        # Compute basic metrics for alerts
                        stats = AnalyticsEngine.compute_price_stats(prices)
                        zscore = AnalyticsEngine.compute_zscore(prices, window=100)
                        
                        context = {
                            'symbol': symbol,
                            'price': float(prices.iloc[-1]) if len(prices) > 0 else 0,
                            'zscore': float(zscore.iloc[-1]) if len(zscore) > 0 else 0,
                            **stats
                        }
                        
                        self.alert_manager.check_alerts(context)
                    
                    except Exception as e:
                        logger.error(f"Error checking alerts for {symbol}: {e}")
            
            except Exception as e:
                logger.error(f"Error in alert check worker: {e}")
    
    def start(self):
        """Start the data processing pipeline."""
        if self.running:
            logger.warning("Data processor already running")
            return
        
        self.running = True
        
        # Start WebSocket client
        self.ws_client = BinanceWebSocketClient(self.symbols, self._tick_callback)
        self.ws_client.start()
        
        # Start resampling threads
        for timeframe, interval in TIMEFRAMES.items():
            thread = threading.Thread(
                target=self._resample_worker,
                args=(timeframe, interval),
                daemon=True
            )
            thread.start()
            self.resampling_threads[timeframe] = thread
        
        # Start alert checking thread
        if self.alert_manager:
            alert_thread = threading.Thread(target=self._alert_check_worker, daemon=True)
            alert_thread.start()
        
        logger.info("Data processor started")
    
    def stop(self):
        """Stop the data processing pipeline."""
        self.running = False
        
        if self.ws_client:
            self.ws_client.stop()
        
        logger.info("Data processor stopped")

