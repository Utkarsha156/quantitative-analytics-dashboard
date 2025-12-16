"""
Simple mean-reversion backtest module.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class MeanReversionBacktest:
    """
    Simple mean-reversion backtest strategy.
    Entry: z-score > entry_threshold (e.g., 2)
    Exit: z-score < exit_threshold (e.g., 0)
    """
    
    def __init__(self, entry_threshold: float = 2.0, exit_threshold: float = 0.0):
        """
        Initialize backtest.
        
        Args:
            entry_threshold: Z-score threshold for entry (long when z < -threshold, short when z > threshold)
            exit_threshold: Z-score threshold for exit
        """
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
    
    def run(self, spread: pd.Series, prices1: pd.Series, prices2: pd.Series,
            hedge_ratio: float = 1.0, window: int = 100) -> Dict:
        """
        Run backtest on spread series.
        
        Args:
            spread: Spread series
            prices1: Price series for first asset
            prices2: Price series for second asset
            hedge_ratio: Hedge ratio for position sizing
            window: Window for z-score calculation
        
        Returns:
            Dictionary with backtest results
        """
        if len(spread) < window:
            return {}
        
        # Compute z-score
        from backend.analytics import AnalyticsEngine
        zscore = AnalyticsEngine.compute_zscore(spread, window=window)
        
        # Initialize positions
        position = 0  # 1 = long spread, -1 = short spread, 0 = flat
        trades = []
        equity_curve = []
        current_equity = 100000  # Starting capital
        
        for i in range(window, len(spread)):
            z = zscore.iloc[i]
            prev_z = zscore.iloc[i-1] if i > window else 0
            
            # Entry logic
            if position == 0:
                if z < -self.entry_threshold:  # Spread too low, go long
                    position = 1
                    entry_price = spread.iloc[i]
                    entry_time = spread.index[i]
                    trades.append({
                        'type': 'LONG',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'entry_zscore': z
                    })
                elif z > self.entry_threshold:  # Spread too high, go short
                    position = -1
                    entry_price = spread.iloc[i]
                    entry_time = spread.index[i]
                    trades.append({
                        'type': 'SHORT',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'entry_zscore': z
                    })
            
            # Exit logic
            elif position != 0:
                if (position == 1 and z >= self.exit_threshold) or \
                   (position == -1 and z <= -self.exit_threshold):
                    exit_price = spread.iloc[i]
                    exit_time = spread.index[i]
                    
                    # Calculate P&L
                    if position == 1:
                        pnl = (exit_price - trades[-1]['entry_price']) * 100  # Assume 100 units
                    else:
                        pnl = (trades[-1]['entry_price'] - exit_price) * 100
                    
                    current_equity += pnl
                    
                    trades[-1].update({
                        'exit_time': exit_time,
                        'exit_price': exit_price,
                        'exit_zscore': z,
                        'pnl': pnl
                    })
                    
                    position = 0
            
            equity_curve.append(current_equity)
        
        # Close any open positions
        if position != 0 and trades:
            exit_price = spread.iloc[-1]
            if position == 1:
                pnl = (exit_price - trades[-1]['entry_price']) * 100
            else:
                pnl = (trades[-1]['entry_price'] - exit_price) * 100
            
            current_equity += pnl
            trades[-1].update({
                'exit_time': spread.index[-1],
                'exit_price': exit_price,
                'exit_zscore': zscore.iloc[-1],
                'pnl': pnl
            })
            equity_curve[-1] = current_equity
        
        # Calculate statistics
        if not trades:
            return {
                'total_trades': 0,
                'equity_curve': equity_curve,
                'trades': []
            }
        
        completed_trades = [t for t in trades if 'pnl' in t]
        pnls = [t['pnl'] for t in completed_trades]
        
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]
        
        total_pnl = sum(pnls)
        win_rate = len(winning_trades) / len(completed_trades) if completed_trades else 0
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        profit_factor = abs(sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) != 0 else 0
        
        return {
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'final_equity': current_equity,
            'return_pct': (current_equity - 100000) / 100000 * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': self._calculate_max_drawdown(equity_curve),
            'equity_curve': equity_curve,
            'trades': trades
        }
    
    @staticmethod
    def _calculate_max_drawdown(equity_curve: list) -> float:
        """Calculate maximum drawdown."""
        if not equity_curve:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd

