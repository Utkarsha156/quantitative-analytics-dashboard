# Detailed Testing Guide - Step by Step

## Prerequisites Check

### Step 1: Verify Python Installation
```bash
python --version
```
**Expected**: Python 3.8 or higher

If Python is not installed, download from [python.org](https://www.python.org/downloads/)

### Step 2: Verify You're in the Correct Directory
```bash
cd d:\analytics
dir
```
**Expected**: You should see files like `app.py`, `requirements.txt`, `README.md`, etc.

---

## Installation Steps

### Step 3: Create Virtual Environment (Recommended)
```bash
python -m venv venv
```

### Step 4: Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**On Mac/Linux:**
```bash
source venv/bin/activate
```

**Expected**: Your prompt should show `(venv)` prefix

### Step 5: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected Output**: Packages installing successfully. Should see:
```
Successfully installed streamlit-x.x.x pandas-x.x.x numpy-x.x.x ...
```

**Troubleshooting**: If you get errors:
- Try: `pip install --upgrade pip` first
- On Windows, you might need: `python -m pip install -r requirements.txt`

### Step 6: Verify Installation
```bash
python -c "import streamlit; import pandas; import numpy; print('All packages installed!')"
```

**Expected**: "All packages installed!" message

---

## Running the Application

### Step 7: Start the Application
```bash
python app.py
```

**Expected Output**:
```
INFO - Starting Analytics Application...
INFO - Initializing backend components...
INFO - Database initialized at data\tick_data.db
INFO - Backend started for symbols: ['btcusdt', 'ethusdt', 'bnbusdt']
INFO - Waiting for backend initialization...
INFO - Launching Streamlit dashboard...
INFO - Dashboard will be available at http://localhost:8501

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://127.0.0.1:8501
```

**Important**: 
- Keep this terminal window open (the app is running)
- A browser window should automatically open
- If browser doesn't open, manually navigate to: http://localhost:8501

---

## Testing the Application - Feature by Feature

### Test 1: Verify Data Collection

**Steps:**
1. Wait 10-15 seconds after the app starts
2. In the dashboard, check the sidebar
3. Look for symbols in the "Select Symbols" dropdown
4. You should see: `btcusdt`, `ethusdt`, `bnbusdt`

**Expected**: Symbols appear in the dropdown (data is being collected)

**If symbols don't appear:**
- Check your internet connection
- Check the terminal for WebSocket connection errors
- Wait a bit longer (30-60 seconds)
- Check `analytics.log` file for errors

---

### Test 2: Price Charts

**Steps:**
1. In the sidebar, select at least one symbol (e.g., `btcusdt`)
2. Select timeframe: `1m` (1 minute)
3. Go to the **"Price Charts"** tab (first tab)
4. Wait a few seconds for data to accumulate

**Expected**:
- A candlestick chart appears showing price movements
- Chart updates in real-time
- You can zoom, pan, and hover over data points

**Test Different Timeframes:**
- Change to `ticks` - should show line chart
- Change to `5m` - should show 5-minute bars
- Change to `1s` - should show 1-second bars

---

### Test 3: Spread Analysis

**Steps:**
1. Select **two symbols** in the sidebar (e.g., `btcusdt` and `ethusdt`)
2. Go to **"Spread Analysis"** tab
3. Wait 30-60 seconds for enough data to accumulate
4. Check "Use OLS Hedge Ratio" checkbox

**Expected**:
- Two charts appear:
  - Top: Spread chart (blue line)
  - Bottom: Z-Score chart (red line) with ±2σ thresholds
- Metrics displayed: Current Spread, Current Z-Score, Spread Mean
- Z-score should fluctuate around 0

**Verify Z-Score Calculation:**
- Z-score should be between -3 and +3 most of the time
- When z-score > 2 or < -2, it indicates potential mean-reversion opportunity

---

### Test 4: Correlation Analysis

**Steps:**
1. Select **at least 2 symbols** (preferably 3: `btcusdt`, `ethusdt`, `bnbusdt`)
2. Go to **"Correlation"** tab
3. Wait 1-2 minutes for data to accumulate

**Expected**:
- A heatmap appears showing correlation matrix
- Colors: Red = positive correlation, Blue = negative correlation
- Diagonal should be all 1.0 (symbols correlate with themselves)
- Values range from -1 to +1

**Verify**:
- Crypto pairs usually show high positive correlation (0.7-0.9)
- Hover over cells to see exact correlation values

---

### Test 5: Statistics Table

**Steps:**
1. Go to **"Statistics"** tab
2. Select a symbol from dropdown (e.g., `btcusdt`)
3. Wait for data to accumulate

**Expected**:
- A table appears with columns:
  - Timestamp
  - Price
  - Rolling Mean
  - Rolling Std
  - Rolling Min/Max
  - Returns
  - Volatility (Annualized)
- Table updates as new data arrives
- "Download CSV" button appears at bottom

**Test Export:**
1. Click "Download CSV" button
2. File should download with name like: `btcusdt_1m_stats_20241216_123456.csv`
3. Open in Excel/CSV viewer to verify data

---

### Test 6: Advanced Analytics - OLS Regression

**Steps:**
1. Select **two symbols** (e.g., `btcusdt` and `ethusdt`)
2. Go to **"Advanced Analytics"** tab
3. Wait 1-2 minutes for sufficient data (need at least 50 data points)

**Expected**:
- **OLS Regression Analysis** section shows:
  - Alpha (α): Intercept value
  - Beta (β): Hedge ratio (usually between 0.5 and 2.0)
  - R²: Goodness of fit (should be > 0.5 for correlated pairs)
  - P-value: Statistical significance (should be < 0.05)

**Verify**:
- Beta represents how many units of symbol2 to hedge 1 unit of symbol1
- R² > 0.7 indicates strong relationship
- P-value < 0.05 means relationship is statistically significant

---

### Test 7: ADF Test (Stationarity)

**Steps:**
1. In **"Advanced Analytics"** tab (with 2 symbols selected)
2. Scroll to **"ADF Test (Stationarity)"** section
3. Wait for data to accumulate (need at least 30 points)

**Expected**:
- Three metrics displayed:
  - ADF Statistic: Negative value (more negative = more stationary)
  - P-value: Should be < 0.05 for stationarity
  - Stationary: "Yes" or "No"
- Critical values shown in JSON format

**Interpretation**:
- If "Stationary" = Yes: Spread is mean-reverting (good for pairs trading)
- If "Stationary" = No: Spread is trending (not ideal for mean-reversion)

---

### Test 8: Kalman Filter

**Steps:**
1. In **"Advanced Analytics"** tab
2. Scroll to **"Kalman Filter Hedge Ratio"** section
3. Click **"Compute Kalman Filter"** button
4. Wait a few seconds for computation

**Expected**:
- A line chart appears showing dynamic hedge ratio over time
- Line should fluctuate (showing how hedge ratio changes)
- "Current Hedge Ratio" metric displayed

**Compare with OLS**:
- OLS gives static hedge ratio
- Kalman gives dynamic hedge ratio that adapts to market conditions
- Kalman ratio should be similar to OLS initially but may diverge over time

---

### Test 9: Robust Regression

**Steps:**
1. In **"Advanced Analytics"** tab
2. Scroll to **"Robust Regression"** section
3. Select method: "huber" or "theilsen"
4. Click **"Compute Robust Regression"** button

**Expected**:
- Alpha and Beta values displayed
- Values should be similar to OLS but may differ if outliers present
- Huber: Good for moderate outliers
- Theil-Sen: Good for many outliers

---

### Test 10: Mean Reversion Backtest

**Steps:**
1. In **"Advanced Analytics"** tab
2. Scroll to **"Mean Reversion Backtest"** section
3. Set parameters:
   - Entry Z-Score Threshold: 2.0 (default)
   - Exit Z-Score Threshold: 0.0 (default)
4. Click **"Run Backtest"** button
5. Wait for computation (may take 10-30 seconds)

**Expected**:
- Metrics displayed:
  - Total Trades: Number of trades executed
  - Win Rate: Percentage of winning trades
  - Total P&L: Profit/Loss in dollars
  - Return: Percentage return
  - Avg Win / Avg Loss: Average profit/loss per trade
  - Max Drawdown: Maximum peak-to-trough decline
- Equity curve chart showing account value over time

**Interpretation**:
- Win Rate > 50% is good
- Positive Total P&L means profitable strategy
- Max Drawdown shows risk (lower is better)
- Equity curve should trend upward if strategy is profitable

**Note**: Backtest requires sufficient historical data. If you just started, wait 5-10 minutes for data to accumulate.

---

### Test 11: Alert System

**Steps:**
1. In the **sidebar**, scroll to **"Alerts"** section
2. Click **"Add Alert Rule"** expander
3. Fill in:
   - Alert Name: "Test High Z-Score"
   - Condition: `zscore > 2`
   - Symbol: Leave as "None" (for all symbols) or select specific symbol
4. Click **"Add Alert"** button

**Expected**:
- Alert appears in "Active Alerts" list
- Alert shows: "Test High Z-Score: zscore > 2"

**Test Alert Triggering:**
1. Wait for z-score to exceed 2 (may take a few minutes)
2. Check "Recent Triggers" section in sidebar
3. Should see: "⚠️ Test High Z-Score - btcusdt - [timestamp]"

**Test Alert Removal:**
1. Click "Remove" button next to an alert
2. Alert should disappear from list

**Test More Alert Conditions:**
- `zscore < -2` (low z-score)
- `price > 50000` (price threshold)
- `zscore > 2.5` (more extreme)

---

### Test 12: Data Export

**Steps:**
1. Go to **"Data Export"** tab
2. Select a symbol (e.g., `btcusdt`)
3. Select timeframe (e.g., `1m`)
4. Click **"Export Data"** button

**Expected**:
- "Download CSV" button appears
- Click to download file
- File name format: `btcusdt_1m_20241216_123456.csv`

**Verify Exported Data:**
1. Open downloaded CSV in Excel/Notepad
2. Should contain columns: timestamp, symbol, price, size (for ticks) or OHLCV (for bars)
3. Data should match what you see in dashboard

---

## Testing Real-Time Updates

### Test 13: Verify Live Updates

**Steps:**
1. Open **"Price Charts"** tab
2. Select `btcusdt` with `1m` timeframe
3. Watch the chart for 2-3 minutes

**Expected**:
- New candlesticks appear every minute
- Chart automatically updates
- Latest price reflects current market price

**Test Tick Updates:**
1. Change timeframe to `ticks`
2. Chart should update very frequently (multiple times per second)
3. Line should be smooth and continuous

---

## Troubleshooting Common Issues

### Issue: "No data available"
**Solution:**
- Wait longer (30-60 seconds)
- Check internet connection
- Verify Binance WebSocket is accessible
- Check `analytics.log` for errors
- Try restarting the application

### Issue: "Port 8501 already in use"
**Solution:**
```bash
# Find process using port 8501
netstat -ano | findstr :8501

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change port in app.py
```

### Issue: "WebSocket connection failed"
**Solution:**
- Check firewall settings
- Verify internet connection
- Try accessing Binance API directly: https://api.binance.com/api/v3/ping
- Check if corporate proxy is blocking WebSocket connections

### Issue: "Import errors"
**Solution:**
```bash
# Reinstall packages
pip install --upgrade -r requirements.txt

# Or reinstall specific package
pip install --upgrade streamlit pandas numpy plotly
```

### Issue: "Charts not updating"
**Solution:**
- Refresh the browser page (F5)
- Check if backend is running (look at terminal)
- Verify data is being collected (check Statistics tab)
- Increase rolling window size

### Issue: "Backtest shows 0 trades"
**Solution:**
- Need more historical data (wait 5-10 minutes)
- Adjust entry/exit thresholds (make them smaller)
- Ensure spread z-score actually reaches threshold values

---

## Performance Testing

### Test 14: Multiple Symbols

**Steps:**
1. Select all 3 default symbols: `btcusdt`, `ethusdt`, `bnbusdt`
2. Open multiple tabs simultaneously
3. Monitor system resources (Task Manager)

**Expected**:
- Application handles multiple symbols smoothly
- CPU usage reasonable (< 50% on modern systems)
- Memory usage stable
- No crashes or freezes

---

## Validation Checklist

After completing all tests, verify:

- [ ] Data is being collected (symbols appear in dropdown)
- [ ] Price charts display and update
- [ ] Spread analysis shows z-score chart
- [ ] Correlation heatmap displays
- [ ] Statistics table populates
- [ ] OLS regression computes successfully
- [ ] ADF test runs and shows results
- [ ] Kalman filter computes
- [ ] Robust regression works
- [ ] Backtest executes (may need more data)
- [ ] Alerts can be added and trigger
- [ ] Data export downloads CSV
- [ ] Real-time updates work
- [ ] No errors in terminal or `analytics.log`

---

## Next Steps After Testing

1. **Customize Configuration**: Edit `config.py` to add more symbols or change timeframes
2. **Add Custom Analytics**: Extend `backend/analytics.py` with your own metrics
3. **Create Custom Alerts**: Add more sophisticated alert conditions
4. **Analyze Results**: Export data and analyze in Excel/Python for deeper insights
5. **Extend Functionality**: Add new visualizations or analytics based on your needs

---

## Support

If you encounter issues not covered here:
1. Check `analytics.log` file for detailed error messages
2. Review terminal output for warnings/errors
3. Verify all dependencies are installed correctly
4. Ensure Python version is 3.8+

---

**Congratulations!** If all tests pass, your analytics application is working correctly! 🎉

