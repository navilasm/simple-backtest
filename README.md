# Simple Backtesting Tool

An interactive Streamlit application for backtesting trading strategies using the Backtrader.
Market data is automatically fetched from yfinance with a daily timeframe (1d).
The app supports popular technical indicator strategies such as RSI, Stochastic, Moving Average, and MACD.

The app consists of:
- Backtesting strategy
- Predefined parameter optimization (grid search)
- Trade-level hypothetical P&L calculator

[Link to Streamlit App](https://simple-backtest.streamlit.app/)

         
## Data

- Source: yfinance
- Frequency: Daily (1d)
- Fields: OHLCV
- Execution: Next-bar market orders


## Required Inputs

Configurable from the Streamlit interface:
- **Ticker symbol:** Yahoo Finance symbol, e.g., `AAPL`, `BBCA.JK`
- **Date range:** Start and end dates of historical data used for backtest.
- **Qty:** Fixed number of units per trade. Every trade (entry and exit) is executed using the same quantity.
- **Initial capital:** Remains fixed during strategy execution and optimization.
- **Built-in strategies:**
    - MA Crossover (available to optimize)
    - RSI (available to optimize)
    - MACD (available to optimize)
    - Parabolic SAR (available to optimize)
    - Bollinger
    - WilliamsR
    - Harami
                                                     
         

## Execution Assumptions & Limitations
- Rate limit on retrieving yfinance data
- Fixed trade quantity across all trades
- Initial capital remains fixed during backtest execution
- Market orders executed on next bar
- Daily OHLCV data only
- Identical assumptions applied to single-run backtests and parameter optimization runs
- Does not takes into account the comission fee

         
## Requirements
```
backtrader==1.9.78.123
millify==0.1.1
numpy==2.4.0
pandas==2.3.3
plotly==5.9.0
streamlit==1.40.1
streamlit_lightweight_charts==0.7.20
yfinance==0.2.37
```


## Strategy 

### 🔹 RSI (Relative Strength Index)

**Strategy Type:** Mean reversion
**Signal Logic:**

* Enter long when RSI falls below the lower threshold
* Exit when RSI rises above the upper threshold

**Optimization Parameters:**

| Parameter    | Range Definition | Description          |
| ------------ | ---------------- | -------------------- |
| `rsi_period` | 10 → 20 (step 1) | RSI lookback window  |
| `rsi_lower`  | 20 → 40 (step 5) | Oversold threshold   |
| `rsi_upper`  | 60 → 80 (step 5) | Overbought threshold |


### 🔹 Moving Average Crossover

**Strategy Type:** Trend-following
**Signal Logic:**

* Enter long when fast MA crosses above slow MA
* Exit when fast MA crosses below slow MA

**Optimization Parameters:**

| Parameter | Range Definition   | Description               |
| --------- | ------------------ | ------------------------- |
| `fast_ma` | 5 → 20 (step 5)    | Short-term moving average |
| `slow_ma` | 30 → 100 (step 10) | Long-term moving average  |


### 🔹 Parabolic SAR

**Strategy Type:** Trend-following / stop-and-reverse
**Signal Logic:**

* Long when price is above SAR
* Exit or reverse when price crosses SAR

**Optimization Parameters:**

| Parameter | Range Definition        | Description          |
| --------- | ----------------------- | -------------------- |
| `af`      | 0.02 → 0.50 (step 0.01) | Acceleration factor  |
| `af_max`  | 0.10 → 0.50 (step 0.10) | Maximum acceleration |


### 🔹 MACD (Moving Average Convergence Divergence)

**Strategy Type:** Momentum
**Signal Logic:**

* Enter long when MACD crosses above signal line
* Exit when MACD crosses below signal line

**Optimization Parameters:**

| Parameter | Range Definition   | Description     |
| --------- | ------------------ | --------------- |
| `fast`    | 5 → 20 (step 5)    | Fast EMA period |
| `slow`    | 30 → 100 (step 10) | Slow EMA period |
| `signal`  | 5 → 12 (step 1)    | Signal line EMA |