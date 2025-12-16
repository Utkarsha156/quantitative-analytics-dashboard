"""
Data sampling and resampling module for different timeframes.
"""
import pandas as pd
import numpy as np
from typing import Dict
from config import TIMEFRAMES
import logging

logger = logging.getLogger(__name__)


class DataSampler:
    """
    Handles resampling of tick data into OHLC bars for different timeframes.
    """
    
    @staticmethod
    def resample_ticks(ticks: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample tick data into OHLC bars.
        
        Args:
            ticks: DataFrame with columns: timestamp, symbol, price, size
            timeframe: One of '1s', '1m', '5m'
        
        Returns:
            DataFrame with columns: timestamp, symbol, open, high, low, close, volume, trade_count
        """
        if timeframe not in TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        if ticks.empty:
            return pd.DataFrame()
        
        interval_seconds = TIMEFRAMES[timeframe]
        
        # Convert timestamp to datetime for resampling
        ticks = ticks.copy()
        ticks['datetime'] = pd.to_datetime(ticks['timestamp'], unit='ms')
        ticks = ticks.set_index('datetime')
        
        # Group by symbol
        bars_list = []
        for symbol, group in ticks.groupby('symbol'):
            # Resample to timeframe
            resampled = group['price'].resample(f'{interval_seconds}s').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last'
            })
            
            # Calculate volume and trade count
            volume = group['size'].resample(f'{interval_seconds}s').sum()
            trade_count = group['size'].resample(f'{interval_seconds}s').count()
            
            resampled['volume'] = volume
            resampled['trade_count'] = trade_count
            resampled['symbol'] = symbol
            
            # Convert index back to timestamp (milliseconds)
            resampled['timestamp'] = resampled.index.astype(np.int64) // 1_000_000
            
            bars_list.append(resampled.reset_index(drop=True))
        
        if bars_list:
            result = pd.concat(bars_list, ignore_index=True)
            # Reorder columns
            result = result[['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'trade_count']]
            return result.dropna()
        
        return pd.DataFrame()

