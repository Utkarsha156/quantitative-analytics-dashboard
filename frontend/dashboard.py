"""
Streamlit dashboard for interactive analytics visualization.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
import time
from datetime import datetime

from backend.storage import DataStorage
from backend.analytics import AnalyticsEngine
from backend.alerts import AlertManager, AlertRule
from backend.backtest import MeanReversionBacktest
from config import DB_PATH, TIMEFRAMES, DEFAULT_SYMBOLS, DEFAULT_ROLLING_WINDOW

# Page config
st.set_page_config(
    page_title="Quant Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'storage' not in st.session_state:
    st.session_state.storage = DataStorage(DB_PATH)

if 'alert_manager' not in st.session_state:
    st.session_state.alert_manager = AlertManager()
    
    # Add default alert rules
    from backend.alerts import AlertRule
    default_rules = [
        AlertRule(
            rule_id="default_zscore_high",
            name="High Z-Score",
            condition="zscore > 2",
            enabled=True
        ),
        AlertRule(
            rule_id="default_zscore_low",
            name="Low Z-Score",
            condition="zscore < -2",
            enabled=True
        ),
    ]
    for rule in default_rules:
        st.session_state.alert_manager.add_rule(rule)

if 'selected_symbols' not in st.session_state:
    st.session_state.selected_symbols = DEFAULT_SYMBOLS[:2]  # Default to first 2 symbols

if 'timeframe' not in st.session_state:
    st.session_state.timeframe = '1m'

if 'rolling_window' not in st.session_state:
    st.session_state.rolling_window = DEFAULT_ROLLING_WINDOW


def load_data(symbol: str, timeframe: str, limit: Optional[int] = None) -> pd.DataFrame:
    """Load data for a symbol."""
    if timeframe == 'ticks':
        return st.session_state.storage.get_ticks(symbol, limit=limit)
    else:
        return st.session_state.storage.get_bars(symbol, timeframe, limit=limit)


def plot_price_chart(symbol: str, timeframe: str, window: int = 5000):
    """Plot price chart with OHLC or line."""
    df = load_data(symbol, timeframe, limit=window)
    
    if df.empty:
        st.warning(f"No data available for {symbol}")
        return
    
    fig = go.Figure()
    
    if timeframe == 'ticks':
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df['timestamp'], unit='ms'),
            y=df['price'],
            mode='lines',
            name='Price',
            line=dict(color='blue', width=1)
        ))
    else:
        # OHLC candlestick chart
        fig.add_trace(go.Candlestick(
            x=pd.to_datetime(df['timestamp'], unit='ms'),
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC'
        ))
    
    fig.update_layout(
        title=f"{symbol.upper()} Price Chart ({timeframe})",
        xaxis_title="Time",
        yaxis_title="Price",
        height=400,
        hovermode='x unified',
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_spread_and_zscore(symbol1: str, symbol2: str, timeframe: str, 
                           rolling_window: int, use_hedge: bool = False):
    """Plot spread and z-score between two symbols."""
    df1 = load_data(symbol1, timeframe, limit=5000)
    df2 = load_data(symbol2, timeframe, limit=5000)
    
    if df1.empty or df2.empty:
        st.warning("Insufficient data for spread analysis")
        return
    
    # Get price series
    if timeframe == 'ticks':
        prices1 = df1.set_index('timestamp')['price']
        prices2 = df2.set_index('timestamp')['price']
    else:
        prices1 = df1.set_index('timestamp')['close']
        prices2 = df2.set_index('timestamp')['close']
    
    # Align series
    aligned = pd.DataFrame({'p1': prices1, 'p2': prices2}).dropna()
    if len(aligned) < 50:
        st.warning("Insufficient overlapping data")
        return
    
    # Compute hedge ratio if requested
    hedge_ratio = None
    if use_hedge:
        ols_result = AnalyticsEngine.compute_ols_regression(
            aligned['p1'], aligned['p2']
        )
        if ols_result:
            hedge_ratio = ols_result.get('beta', 1.0)
            st.info(f"Hedge Ratio (β): {hedge_ratio:.4f} | R²: {ols_result.get('r_squared', 0):.4f}")
    
    # Compute spread
    spread = AnalyticsEngine.compute_spread(
        aligned['p1'], aligned['p2'], hedge_ratio
    )
    
    # Compute z-score
    zscore = AnalyticsEngine.compute_zscore(spread, window=rolling_window)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Spread', 'Z-Score'),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4]
    )
    
    # Plot spread
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(aligned.index, unit='ms'),
            y=spread.values,
            mode='lines',
            name='Spread',
            line=dict(color='blue')
        ),
        row=1, col=1
    )
    
    # Plot z-score
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(aligned.index, unit='ms'),
            y=zscore.values,
            mode='lines',
            name='Z-Score',
            line=dict(color='red')
        ),
        row=2, col=1
    )
    
    # Add z-score thresholds
    fig.add_hline(y=2, line_dash="dash", line_color="green", 
                  annotation_text="+2σ", row=2, col=1)
    fig.add_hline(y=-2, line_dash="dash", line_color="green", 
                  annotation_text="-2σ", row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
    
    fig.update_layout(
        title=f"Spread & Z-Score: {symbol1.upper()} vs {symbol2.upper()}",
        height=600,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Spread", row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display current values
    if len(spread) > 0 and len(zscore) > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Spread", f"{spread.iloc[-1]:.4f}")
        with col2:
            st.metric("Current Z-Score", f"{zscore.iloc[-1]:.2f}")
        with col3:
            st.metric("Spread Mean", f"{spread.mean():.4f}")


def plot_correlation(symbols: List[str], timeframe: str, rolling_window: int):
    """Plot rolling correlation matrix."""
    if len(symbols) < 2:
        st.warning("Need at least 2 symbols for correlation")
        return
    
    # Load data for all symbols
    price_data = {}
    for symbol in symbols:
        df = load_data(symbol, timeframe, limit=5000)
        if not df.empty:
            if timeframe == 'ticks':
                price_data[symbol] = df.set_index('timestamp')['price']
            else:
                price_data[symbol] = df.set_index('timestamp')['close']
    
    if len(price_data) < 2:
        st.warning("Insufficient data for correlation")
        return
    
    # Compute correlation matrix
    corr_matrix = AnalyticsEngine.compute_cross_correlation_matrix(
        price_data, window=rolling_window
    )
    
    if corr_matrix.empty:
        st.warning("Could not compute correlation matrix")
        return
    
    # Plot heatmap
    fig = px.imshow(
        corr_matrix,
        labels=dict(x="Symbol", y="Symbol", color="Correlation"),
        x=corr_matrix.columns,
        y=corr_matrix.index,
        color_continuous_scale="RdBu",
        aspect="auto",
        title="Rolling Correlation Matrix"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_stats_table(symbol: str, timeframe: str):
    """Display time-series statistics table."""
    df = load_data(symbol, timeframe, limit=1000)
    
    if df.empty:
        st.warning(f"No data for {symbol}")
        return
    
    # Get price series
    if timeframe == 'ticks':
        prices = df['price']
    else:
        prices = df['close']
    
    # Compute rolling statistics
    window = 60  # 60 periods
    if len(prices) < window:
        st.warning("Insufficient data for statistics")
        return
    
    stats_df = pd.DataFrame({
        'timestamp': pd.to_datetime(df['timestamp'], unit='ms'),
        'price': prices.values,
        'rolling_mean': prices.rolling(window).mean().values,
        'rolling_std': prices.rolling(window).std().values,
        'rolling_min': prices.rolling(window).min().values,
        'rolling_max': prices.rolling(window).max().values,
    })
    
    # Add returns
    stats_df['returns'] = stats_df['price'].pct_change()
    stats_df['rolling_volatility'] = stats_df['returns'].rolling(window).std() * np.sqrt(252 * 24 * 60)
    
    # Filter to show only rows with valid rolling stats
    stats_df = stats_df[stats_df['rolling_mean'].notna()].copy()
    
    # Format for display
    display_df = stats_df[['timestamp', 'price', 'rolling_mean', 'rolling_std', 
                          'rolling_min', 'rolling_max', 'returns', 'rolling_volatility']].copy()
    display_df.columns = ['Timestamp', 'Price', 'Rolling Mean', 'Rolling Std', 
                          'Rolling Min', 'Rolling Max', 'Returns', 'Volatility (Annualized)']
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{symbol}_{timeframe}_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def main():
    """Main dashboard function."""
    st.title("Quantitative Analytics Dashboard")
    st.markdown("Real-time market data analytics and visualization")
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Symbol selection
        available_symbols = st.session_state.storage.get_symbols()
        if not available_symbols:
            available_symbols = DEFAULT_SYMBOLS
        
        selected_symbols = st.multiselect(
            "Select Symbols",
            options=available_symbols,
            default=st.session_state.selected_symbols
        )
        st.session_state.selected_symbols = selected_symbols if selected_symbols else available_symbols[:2]
        
        # Timeframe selection
        timeframe_options = ['ticks'] + list(TIMEFRAMES.keys())
        timeframe = st.selectbox(
            "Timeframe",
            options=timeframe_options,
            index=timeframe_options.index(st.session_state.timeframe) if st.session_state.timeframe in timeframe_options else 1
        )
        st.session_state.timeframe = timeframe
        
        # Rolling window
        rolling_window = st.slider(
            "Rolling Window",
            min_value=10,
            max_value=500,
            value=st.session_state.rolling_window,
            step=10
        )
        st.session_state.rolling_window = rolling_window
        
        st.divider()
        
        # Alert management
        st.header("🔔 Alerts")
        
        # Add new alert
        with st.expander("Add Alert Rule"):
            alert_name = st.text_input("Alert Name")
            alert_condition = st.text_input("Condition (e.g., zscore > 2)", 
                                           help="Use variables: price, zscore, symbol, etc.")
            alert_symbol = st.selectbox("Symbol (optional)", 
                                       options=[None] + st.session_state.selected_symbols)
            
            if st.button("Add Alert"):
                if alert_name and alert_condition:
                    rule_id = f"rule_{int(time.time())}"
                    rule = AlertRule(
                        rule_id=rule_id,
                        name=alert_name,
                        condition=alert_condition,
                        symbol=alert_symbol,
                        enabled=True
                    )
                    st.session_state.alert_manager.add_rule(rule)
                    st.success(f"Alert '{alert_name}' added!")
                    st.rerun()
        
        # List alerts
        st.subheader("Active Alerts")
        rules = st.session_state.alert_manager.get_rules()
        for rule in rules:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"{rule.name}: {rule.condition}")
            with col2:
                if st.button("Remove", key=f"remove_{rule.rule_id}"):
                    st.session_state.alert_manager.remove_rule(rule.rule_id)
                    st.rerun()
        
        # Recent alerts
        recent_alerts = st.session_state.alert_manager.get_active_alerts(limit=10)
        if recent_alerts:
            st.subheader("Recent Triggers")
            for alert in recent_alerts[-5:]:
                st.warning(f"⚠️ {alert['name']} - {alert['symbol']} - {alert['timestamp']}")
    
    # Main content
    if not st.session_state.selected_symbols:
        st.warning("Please select at least one symbol")
        return
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Price Charts", "Spread Analysis", "Correlation", 
        "Statistics", "Advanced Analytics", "Data Export"
    ])
    
    with tab1:
        st.header("Price Charts")
        for symbol in st.session_state.selected_symbols:
            plot_price_chart(symbol, timeframe, window=5000)
    
    with tab2:
        st.header("Spread & Z-Score Analysis")
        if len(st.session_state.selected_symbols) >= 2:
            use_hedge = st.checkbox("Use OLS Hedge Ratio", value=False)
            plot_spread_and_zscore(
                st.session_state.selected_symbols[0],
                st.session_state.selected_symbols[1],
                timeframe,
                rolling_window,
                use_hedge
            )
        else:
            st.warning("Select at least 2 symbols for spread analysis")
    
    with tab3:
        st.header("Correlation Analysis")
        if len(st.session_state.selected_symbols) >= 2:
            plot_correlation(st.session_state.selected_symbols, timeframe, rolling_window)
        else:
            st.warning("Select at least 2 symbols for correlation")
    
    with tab4:
        st.header("Price Statistics")
        symbol_for_stats = st.selectbox(
            "Select Symbol for Statistics",
            options=st.session_state.selected_symbols
        )
        display_stats_table(symbol_for_stats, timeframe)
    
    with tab5:
        st.header("Advanced Analytics")
        
        if len(st.session_state.selected_symbols) >= 2:
            symbol1 = st.session_state.selected_symbols[0]
            symbol2 = st.session_state.selected_symbols[1]
            
            # OLS Regression
            st.subheader("OLS Regression Analysis")
            df1 = load_data(symbol1, timeframe, limit=1000)
            df2 = load_data(symbol2, timeframe, limit=1000)
            
            if not df1.empty and not df2.empty:
                if timeframe == 'ticks':
                    prices1 = df1.set_index('timestamp')['price']
                    prices2 = df2.set_index('timestamp')['price']
                else:
                    prices1 = df1.set_index('timestamp')['close']
                    prices2 = df2.set_index('timestamp')['close']
                
                aligned = pd.DataFrame({'p1': prices1, 'p2': prices2}).dropna()
                
                if len(aligned) >= 50:
                    ols_result = AnalyticsEngine.compute_ols_regression(
                        aligned['p1'], aligned['p2']
                    )
                    
                    if ols_result:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Alpha (α)", f"{ols_result.get('alpha', 0):.6f}")
                        with col2:
                            st.metric("Beta (β)", f"{ols_result.get('beta', 0):.6f}")
                        with col3:
                            st.metric("R²", f"{ols_result.get('r_squared', 0):.4f}")
                        with col4:
                            st.metric("P-value", f"{ols_result.get('pvalue', 0):.6f}")
                    
                    # ADF Test
                    st.subheader("ADF Test (Stationarity)")
                    spread = AnalyticsEngine.compute_spread(
                        aligned['p1'], aligned['p2'], 
                        ols_result.get('beta') if ols_result else None
                    )
                    
                    if len(spread) >= 30:
                        adf_result = AnalyticsEngine.compute_adf_test(spread)
                        if adf_result:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("ADF Statistic", f"{adf_result.get('adf_statistic', 0):.4f}")
                            with col2:
                                st.metric("P-value", f"{adf_result.get('pvalue', 0):.6f}")
                            with col3:
                                is_stationary = adf_result.get('is_stationary', False)
                                st.metric("Stationary", "Yes" if is_stationary else "No")
                            
                            st.json(adf_result.get('critical_values', {}))
                    
                    # Kalman Filter
                    st.subheader("Kalman Filter Hedge Ratio")
                    if st.button("Compute Kalman Filter"):
                        hedge_ratios, kalman_spread = AnalyticsEngine.compute_kalman_hedge_ratio(
                            aligned['p1'], aligned['p2']
                        )
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=pd.to_datetime(aligned.index, unit='ms'),
                            y=hedge_ratios.values,
                            mode='lines',
                            name='Dynamic Hedge Ratio'
                        ))
                        fig.update_layout(
                            title="Kalman Filter Hedge Ratio",
                            xaxis_title="Time",
                            yaxis_title="Hedge Ratio (β)",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.metric("Current Hedge Ratio", f"{hedge_ratios.iloc[-1]:.4f}")
                    
                    # Robust Regression
                    st.subheader("Robust Regression")
                    robust_method = st.selectbox("Method", ["huber", "theilsen"])
                    if st.button("Compute Robust Regression"):
                        robust_result = AnalyticsEngine.compute_robust_regression(
                            aligned['p1'], aligned['p2'], method=robust_method
                        )
                        if robust_result:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Alpha", f"{robust_result.get('alpha', 0):.6f}")
                            with col2:
                                st.metric("Beta", f"{robust_result.get('beta', 0):.6f}")
                    
                    # Mean Reversion Backtest
                    st.subheader("Mean Reversion Backtest")
                    entry_threshold = st.slider("Entry Z-Score Threshold", 1.0, 5.0, 2.0, 0.5)
                    exit_threshold = st.slider("Exit Z-Score Threshold", -1.0, 1.0, 0.0, 0.5)
                    
                    if st.button("Run Backtest"):
                        with st.spinner("Running backtest..."):
                            backtest = MeanReversionBacktest(
                                entry_threshold=entry_threshold,
                                exit_threshold=exit_threshold
                            )
                            
                            hedge_ratio = ols_result.get('beta', 1.0) if ols_result else 1.0
                            result = backtest.run(
                                spread, aligned['p1'], aligned['p2'],
                                hedge_ratio=hedge_ratio,
                                window=rolling_window
                            )
                            
                            if result and result.get('total_trades', 0) > 0:
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Total Trades", result['total_trades'])
                                with col2:
                                    st.metric("Win Rate", f"{result['win_rate']*100:.1f}%")
                                with col3:
                                    st.metric("Total P&L", f"${result['total_pnl']:.2f}")
                                with col4:
                                    st.metric("Return", f"{result['return_pct']:.2f}%")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Avg Win", f"${result['avg_win']:.2f}")
                                with col2:
                                    st.metric("Avg Loss", f"${result['avg_loss']:.2f}")
                                with col3:
                                    st.metric("Max Drawdown", f"{result['max_drawdown']:.2f}%")
                                
                                # Equity curve
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    y=result['equity_curve'],
                                    mode='lines',
                                    name='Equity Curve',
                                    line=dict(color='green', width=2)
                                ))
                                fig.add_hline(y=100000, line_dash="dash", line_color="gray",
                                            annotation_text="Starting Capital")
                                fig.update_layout(
                                    title="Backtest Equity Curve",
                                    xaxis_title="Trade #",
                                    yaxis_title="Equity ($)",
                                    height=400
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No trades generated in backtest")
        else:
            st.warning("Select at least 2 symbols for advanced analytics")
    
    with tab6:
        st.header("Data Export")
        export_symbol = st.selectbox(
            "Select Symbol",
            options=st.session_state.selected_symbols
        )
        export_timeframe = st.selectbox(
            "Select Timeframe",
            options=timeframe_options
        )
        
        if st.button("Export Data"):
            df = load_data(export_symbol, export_timeframe)
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{export_symbol}_{export_timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")


if __name__ == "__main__":
    main()

