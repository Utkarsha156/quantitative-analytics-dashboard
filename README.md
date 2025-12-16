# Quantitative Analytics Dashboard

A comprehensive real-time analytics application for quantitative trading, featuring live data ingestion from Binance, advanced statistical analysis, and interactive visualizations.

## Overview

This application demonstrates end-to-end capabilities from real-time data ingestion to quantitative analytics and interactive visualization. It's designed for traders and researchers at MFT firms involved in statistical arbitrage, risk-premia harvesting, market-making, and term structure analysis.

## Features

### Core Functionality
- **Real-time Data Ingestion**: WebSocket connection to Binance for live tick data
- **Multi-timeframe Sampling**: Automatic resampling to 1s, 1m, and 5m intervals
- **Data Storage**: SQLite database for efficient tick and bar storage
- **Interactive Dashboard**: Streamlit-based frontend with real-time updates

### Analytics
- **Price Statistics**: Mean, std, volatility, skewness, kurtosis
- **OLS Regression**: Hedge ratio estimation via Ordinary Least Squares
- **Robust Regression**: Huber and Theil-Sen estimators for outlier-resistant analysis
- **Spread Analysis**: Hedged and unhedged spread computation
- **Z-Score Calculation**: Rolling z-score for mean-reversion strategies
- **ADF Test**: Augmented Dickey-Fuller test for stationarity
- **Rolling Correlation**: Cross-correlation matrix for multiple symbols
- **Kalman Filter**: Dynamic hedge ratio estimation
- **Mean Reversion Backtest**: Simple backtesting framework

### Advanced Features
- **Custom Alerting**: Rule-based alert system with Python expression evaluation
- **Data Export**: CSV download for processed data and analytics
- **Time-series Statistics Table**: Rolling statistics with export functionality
- **Correlation Heatmaps**: Visual cross-correlation analysis
- **Multiple Symbol Support**: Analyze multiple trading pairs simultaneously

## Architecture

### Design Philosophy
The system is designed with modularity and extensibility in mind:
- **Loose Coupling**: Components interact through clean interfaces
- **Scalability**: Easy to plug in different data sources (CME futures, REST APIs, CSV files)
- **Extensibility**: Straightforward to add new analytics, visualizations, or data sources
- **Clarity**: Simple, readable code over premature optimization

### Component Structure

```
analytics/
├── backend/
│   ├── data_processor.py    # Main pipeline coordinator
│   ├── storage.py           # SQLite data persistence
│   ├── sampler.py           # Timeframe resampling
│   ├── analytics.py        # Core analytics engine
│   ├── alerts.py           # Alert management system
│   └── backtest.py         # Mean-reversion backtesting
├── frontend/
│   └── dashboard.py        # Streamlit dashboard
├── websocket_client/
│   └── binance_client.py   # Binance WebSocket client
├── config.py               # Configuration settings
├── app.py                  # Main entry point
└── requirements.txt        # Python dependencies
```

### Data Flow

1. **Ingestion**: WebSocket client receives tick data from Binance
2. **Storage**: Ticks stored in SQLite database
3. **Resampling**: Background threads resample ticks to OHLC bars
4. **Analytics**: On-demand computation of statistics and metrics
5. **Visualization**: Streamlit dashboard displays results with live updates
6. **Alerts**: Background thread checks alert conditions periodically

## Setup

### Prerequisites
- Python 3.8 or higher
- Internet connection for Binance WebSocket

### Installation

1. Clone or extract the project:
```bash
cd analytics
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The application will:
- Start the backend data processor (WebSocket ingestion and resampling)
- Launch the Streamlit dashboard (accessible at http://localhost:8501)

### Configuration

Edit `config.py` to customize:
- Default symbols to track
- Database path
- Sampling timeframes
- Alert check intervals
- Rolling window defaults

## Usage

### Dashboard Navigation

1. **Price Charts**: View real-time price charts for selected symbols
2. **Spread Analysis**: Analyze spread and z-score between two symbols
3. **Correlation**: View rolling correlation matrix heatmap
4. **Statistics**: Time-series statistics table with export
5. **Advanced Analytics**: OLS regression, ADF test, Kalman filter, robust regression, backtesting
6. **Data Export**: Download raw or processed data as CSV

### Setting Up Alerts

1. Navigate to the sidebar "Alerts" section
2. Click "Add Alert Rule"
3. Enter:
   - Alert name
   - Condition (Python expression, e.g., `zscore > 2`)
   - Optional symbol filter
4. Alerts trigger automatically when conditions are met

### Running Backtests

1. Select at least 2 symbols
2. Go to "Advanced Analytics" tab
3. Adjust entry/exit thresholds
4. Click "Run Backtest"
5. View results including equity curve, win rate, and P&L

## Analytics Methodology

### OLS Regression
Computes hedge ratio (β) via `y = α + βx` where y and x are price series. The beta coefficient represents the optimal hedge ratio for pairs trading.

### Z-Score
Calculated as `z = (value - rolling_mean) / rolling_std`. Values > 2 or < -2 suggest potential mean-reversion opportunities.

### ADF Test
Tests for stationarity of the spread series. Stationary spreads are preferred for mean-reversion strategies.

### Kalman Filter
Dynamically estimates hedge ratio, adapting to changing market conditions. Useful when relationships are non-stationary.

### Robust Regression
Huber and Theil-Sen estimators provide outlier-resistant hedge ratio estimates, useful when data contains anomalies.

## Data Storage

- **Ticks Table**: Raw tick data (timestamp, symbol, price, size)
- **Resampled Tables**: OHLC bars for each timeframe (1s_bars, 1m_bars, 5m_bars)
- Database location: `data/tick_data.db` (created automatically)

## Extensibility

### Adding New Analytics

1. Add method to `backend/analytics.py`
2. Import and call from `frontend/dashboard.py`
3. Add visualization in appropriate tab

### Adding New Data Sources

1. Create new client class (similar to `BinanceWebSocketClient`)
2. Implement callback interface: `callback(timestamp, symbol, price, size)`
3. Update `DataProcessor` to use new client

### Adding New Visualizations

1. Create plotting function in `frontend/dashboard.py`
2. Add to appropriate tab or create new tab
3. Use Plotly for interactive charts

## Performance Considerations

- **Database Indexing**: Timestamp and symbol indexes for fast queries
- **Rolling Windows**: Configurable window sizes for memory efficiency
- **Data Limits**: Queries limited to prevent memory issues
- **Background Processing**: Resampling and alerts run in separate threads

## Limitations

- Analytics requiring > 1 day of data are not included (per requirements)
- Designed for local execution (not production-scale)
- SQLite may become slow with very large datasets (consider PostgreSQL for scale)

## Troubleshooting

### No Data Appearing
- Check internet connection
- Verify Binance WebSocket is accessible
- Check `analytics.log` for errors
- Ensure symbols are correctly formatted (lowercase, e.g., 'btcusdt')

### Dashboard Not Loading
- Ensure port 8501 is available
- Check that Streamlit is installed: `pip install streamlit`
- Verify all dependencies are installed

### Alerts Not Triggering
- Ensure sufficient data is collected (minimum 100 ticks)
- Check alert condition syntax (valid Python expression)
- Verify alert is enabled

## Future Enhancements

Potential extensions (not implemented but architecture supports):
- Additional data sources (CME, ICE, REST APIs)
- More sophisticated backtesting (walk-forward, Monte Carlo)
- Portfolio-level analytics
- Real-time order execution integration
- Machine learning models for signal generation
- Risk metrics (VaR, CVaR, Sharpe ratio)

## License

This project is provided as-is for evaluation purposes.

## ChatGPT Usage Transparency

### AI Assistance Used
This project was developed with assistance from ChatGPT (GPT-4) for:
- Initial architecture design and component structure
- Code implementation for WebSocket client, storage layer, and analytics engine
- Streamlit dashboard layout and visualization code
- Documentation and README writing

### Key Prompts Used
- "Design a modular architecture for a real-time quant analytics system"
- "Implement a WebSocket client for Binance tick data"
- "Create a SQLite storage layer with resampling support"
- "Build analytics functions for OLS regression, z-score, ADF test"
- "Design a Streamlit dashboard with interactive charts"
- "Implement a mean-reversion backtest framework"

All code was reviewed, tested, and customized for the specific requirements of this assignment.

