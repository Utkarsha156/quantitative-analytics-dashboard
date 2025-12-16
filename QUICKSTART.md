# Quick Start Guide

## Prerequisites
- Python 3.8 or higher
- Internet connection (for Binance WebSocket)

## Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected**: All packages install successfully. If you see errors, try:
```bash
pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

**What happens:**
- Backend starts collecting data from Binance (WebSocket)
- Streamlit dashboard opens at http://localhost:8501
- Browser should open automatically

**Keep the terminal window open** - the app is running there!

## First Steps (Wait 30-60 seconds after startup)

### Step 3: Verify Data Collection
1. Check the sidebar "Select Symbols" dropdown
2. You should see: `btcusdt`, `ethusdt`, `bnbusdt`
3. If symbols appear = data is being collected ✅

### Step 4: Explore the Dashboard

**Tab 1: Price Charts**
- Select a symbol (e.g., `btcusdt`)
- Choose timeframe: `1m`
- See real-time price candlesticks

**Tab 2: Spread Analysis**
- Select 2 symbols (e.g., `btcusdt` and `ethusdt`)
- See spread and z-score charts
- Check "Use OLS Hedge Ratio" for hedged spread

**Tab 3: Correlation**
- Select multiple symbols
- See correlation heatmap

**Tab 4: Statistics**
- Select a symbol
- View rolling statistics table
- Download CSV

**Tab 5: Advanced Analytics**
- OLS Regression: Hedge ratio calculation
- ADF Test: Stationarity test
- Kalman Filter: Dynamic hedge ratio
- Robust Regression: Outlier-resistant analysis
- Backtest: Mean-reversion strategy testing

**Tab 6: Data Export**
- Select symbol and timeframe
- Download raw data as CSV

### Step 5: Test Alerts
1. In sidebar, click "Add Alert Rule"
2. Enter:
   - Name: "High Z-Score"
   - Condition: `zscore > 2`
3. Click "Add Alert"
4. Wait for z-score to exceed 2
5. Check "Recent Triggers" section

## Testing the WebSocket Connection

Open the HTML file in your browser:
```
websocket_client/binance_websocket.html
```

This shows raw WebSocket data streaming from Binance.

## Troubleshooting

**No data appearing?**
- Wait 30-60 seconds (needs time to collect data)
- Check internet connection
- Check `analytics.log` for errors
- Verify Binance WebSocket is accessible

**Port 8501 in use?**
- Stop other Streamlit instances
- Or change port in `app.py` line 105

**Import errors?**
```bash
pip install --upgrade -r requirements.txt
```

**Charts not updating?**
- Refresh browser (F5)
- Check terminal for errors
- Verify backend is running

## Default Configuration

- **Symbols**: BTCUSDT, ETHUSDT, BNBUSDT (edit in `config.py`)
- **Timeframes**: 1s, 1m, 5m
- **Database**: `data/tick_data.db` (auto-created)
- **Logs**: `analytics.log`

## Detailed Testing

For comprehensive testing instructions, see **TESTING_GUIDE.md**

## Next Steps

- Customize symbols in `config.py`
- Add custom alert rules
- Run backtests (wait 5-10 min for data)
- Export data for analysis
- Extend with your own analytics

