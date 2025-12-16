"""
Analytics engine for computing quantitative metrics.
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.stattools import adfuller
from scipy import stats
from sklearn.linear_model import HuberRegressor, TheilSenRegressor
import logging

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Core analytics engine for computing various quantitative metrics.
    """
    
    @staticmethod
    def compute_price_stats(prices: pd.Series) -> Dict:
        """Compute basic price statistics."""
        if len(prices) < 2:
            return {}
        
        returns = prices.pct_change().dropna()
        
        return {
            'mean': float(prices.mean()),
            'std': float(prices.std()),
            'min': float(prices.min()),
            'max': float(prices.max()),
            'current': float(prices.iloc[-1]),
            'return_mean': float(returns.mean()) if len(returns) > 0 else 0.0,
            'return_std': float(returns.std()) if len(returns) > 0 else 0.0,
            'volatility': float(returns.std() * np.sqrt(252 * 24 * 60)) if len(returns) > 0 else 0.0,  # Annualized
            'skewness': float(returns.skew()) if len(returns) > 0 else 0.0,
            'kurtosis': float(returns.kurtosis()) if len(returns) > 0 else 0.0,
        }
    
    @staticmethod
    def compute_ols_regression(y: pd.Series, x: pd.Series) -> Dict:
        """
        Compute OLS regression: y = alpha + beta * x
        
        Returns hedge ratio (beta) and other regression statistics.
        """
        if len(y) < 2 or len(x) < 2 or len(y) != len(x):
            return {}
        
        # Align series
        aligned = pd.DataFrame({'y': y, 'x': x}).dropna()
        if len(aligned) < 2:
            return {}
        
        try:
            x_with_const = pd.DataFrame({'const': 1, 'x': aligned['x']})
            model = OLS(aligned['y'], x_with_const).fit()
            
            return {
                'alpha': float(model.params['const']),
                'beta': float(model.params['x']),  # Hedge ratio
                'r_squared': float(model.rsquared),
                'pvalue': float(model.pvalues['x']),
                'std_err': float(model.bse['x']),
                'residuals': model.resid.values.tolist()
            }
        except Exception as e:
            logger.error(f"OLS regression error: {e}")
            return {}
    
    @staticmethod
    def compute_robust_regression(y: pd.Series, x: pd.Series, method: str = 'huber') -> Dict:
        """
        Compute robust regression (Huber or Theil-Sen).
        
        Args:
            y: Dependent variable
            x: Independent variable
            method: 'huber' or 'theilsen'
        """
        if len(y) < 2 or len(x) < 2 or len(y) != len(x):
            return {}
        
        aligned = pd.DataFrame({'y': y, 'x': x}).dropna()
        if len(aligned) < 2:
            return {}
        
        try:
            X = aligned['x'].values.reshape(-1, 1)
            y_vals = aligned['y'].values
            
            if method == 'huber':
                model = HuberRegressor(epsilon=1.35)
            elif method == 'theilsen':
                model = TheilSenRegressor()
            else:
                raise ValueError(f"Unknown method: {method}")
            
            model.fit(X, y_vals)
            
            return {
                'alpha': float(model.intercept_),
                'beta': float(model.coef_[0]),
                'method': method
            }
        except Exception as e:
            logger.error(f"Robust regression error: {e}")
            return {}
    
    @staticmethod
    def compute_spread(price1: pd.Series, price2: pd.Series, 
                      hedge_ratio: Optional[float] = None) -> pd.Series:
        """
        Compute spread between two price series.
        If hedge_ratio is provided, computes hedged spread: price1 - hedge_ratio * price2
        Otherwise, computes simple spread: price1 - price2
        """
        if len(price1) == 0 or len(price2) == 0:
            return pd.Series(dtype=float)
        
        # Align series
        aligned = pd.DataFrame({'p1': price1, 'p2': price2}).dropna()
        if len(aligned) == 0:
            return pd.Series(dtype=float)
        
        if hedge_ratio is not None:
            spread = aligned['p1'] - hedge_ratio * aligned['p2']
        else:
            spread = aligned['p1'] - aligned['p2']
        
        return spread
    
    @staticmethod
    def compute_zscore(series: pd.Series, window: int = 100) -> pd.Series:
        """
        Compute rolling z-score: (value - rolling_mean) / rolling_std
        """
        if len(series) < window:
            return pd.Series(dtype=float)
        
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        zscore = (series - rolling_mean) / rolling_std
        
        return zscore
    
    @staticmethod
    def compute_adf_test(series: pd.Series) -> Dict:
        """
        Augmented Dickey-Fuller test for stationarity.
        """
        if len(series) < 10:
            return {}
        
        try:
            result = adfuller(series.dropna())
            return {
                'adf_statistic': float(result[0]),
                'pvalue': float(result[1]),
                'critical_values': {k: float(v) for k, v in result[4].items()},
                'is_stationary': result[1] < 0.05,  # p-value < 0.05 suggests stationarity
                'used_lag': int(result[2]),
                'n_obs': int(result[3])
            }
        except Exception as e:
            logger.error(f"ADF test error: {e}")
            return {}
    
    @staticmethod
    def compute_rolling_correlation(series1: pd.Series, series2: pd.Series, 
                                   window: int = 100) -> pd.Series:
        """Compute rolling correlation between two series."""
        if len(series1) == 0 or len(series2) == 0:
            return pd.Series(dtype=float)
        
        # Align series
        aligned = pd.DataFrame({'s1': series1, 's2': series2}).dropna()
        if len(aligned) < window:
            return pd.Series(dtype=float)
        
        return aligned['s1'].rolling(window=window).corr(aligned['s2'])
    
    @staticmethod
    def compute_kalman_hedge_ratio(prices1: pd.Series, prices2: pd.Series, 
                                   initial_beta: float = 1.0,
                                   process_variance: float = 0.01,
                                   measurement_variance: float = 0.1) -> Tuple[pd.Series, pd.Series]:
        """
        Dynamic hedge ratio estimation using Kalman Filter.
        
        Returns:
            Tuple of (hedge_ratios, spreads)
        """
        if len(prices1) < 2 or len(prices2) < 2:
            return pd.Series(dtype=float), pd.Series(dtype=float)
        
        aligned = pd.DataFrame({'p1': prices1, 'p2': prices2}).dropna()
        if len(aligned) < 2:
            return pd.Series(dtype=float), pd.Series(dtype=float)
        
        n = len(aligned)
        betas = np.zeros(n)
        beta = initial_beta
        P = 1.0  # State covariance
        
        betas[0] = beta
        
        for i in range(1, n):
            # Prediction step
            P_pred = P + process_variance
            
            # Update step
            y = aligned['p1'].iloc[i]
            x = aligned['p2'].iloc[i]
            residual = y - beta * x
            
            S = x * P_pred * x + measurement_variance  # Innovation covariance
            K = P_pred * x / S  # Kalman gain
            
            beta = beta + K * residual
            P = (1 - K * x) * P_pred
            
            betas[i] = beta
        
        hedge_ratios = pd.Series(betas, index=aligned.index)
        spreads = aligned['p1'] - hedge_ratios * aligned['p2']
        
        return hedge_ratios, spreads
    
    @staticmethod
    def compute_cross_correlation_matrix(prices_dict: Dict[str, pd.Series], 
                                        window: int = 100) -> pd.DataFrame:
        """
        Compute rolling cross-correlation matrix for multiple symbols.
        """
        symbols = list(prices_dict.keys())
        if len(symbols) < 2:
            return pd.DataFrame()
        
        # Align all series
        df = pd.DataFrame(prices_dict).dropna()
        if len(df) < window:
            return pd.DataFrame()
        
        # Compute rolling correlations
        corr_matrix = df.rolling(window=window).corr().iloc[-1]
        
        # Reshape to matrix format
        n = len(symbols)
        matrix = np.zeros((n, n))
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if sym1 == sym2:
                    matrix[i][j] = 1.0
                else:
                    try:
                        matrix[i][j] = corr_matrix.loc[sym1, sym2]
                    except:
                        matrix[i][j] = 0.0
        
        return pd.DataFrame(matrix, index=symbols, columns=symbols)

