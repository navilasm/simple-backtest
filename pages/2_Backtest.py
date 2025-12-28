from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import streamlit as st
import yfinance as yf
import time
from datetime import datetime
import pandas as pd
import streamlit as st
from millify import prettify
import strategy
from chart import render_lightweight
from backtest import run_backtest, run_optimizer

st.set_page_config(page_title="Backtester", layout="wide")
st.title("Backtest")

col1, col2, col3, col4, col5 = st.columns([1.5,2.5,1.5,2,2.5])
with col1.container(border=True):
    ticker = st.text_input("Stock Ticker", 'BBRI.JK')
with col3.container(border=True):
    qty = st.number_input("Trades Quantity", step=1, value=10, min_value=1)
with col4.container(border=True):
    cash = st.number_input('Initial Capital', value=1000000, step=1, min_value=10)
with col2.container(border=True):
    date_filter = st.date_input("Time Period",(datetime(2024, 1, 1), datetime.today().date()), 
                                                        min_value=datetime(2020, 1, 1), max_value=datetime.today().date(), format="YYYY.MM.DD")
with col5.container(border=True):
    strategy_name = st.selectbox("Strategy", ["MA Crossover", "RSI", "Parabolic SAR",
                                              "MACD","Bollinger","WilliamsR","Harami"
                                              ])
    strategy_map = {
        "RSI": strategy.StrategyRSI,
        "MA Crossover": strategy.StrategyMACross,
        "Parabolic SAR": strategy.StrategySAR,
        "MACD":strategy.StrategyMACD,
        "Bollinger":strategy.StrategyBollinger,
        "WilliamsR":strategy.StrategyWilliamsR,
        "Harami":strategy.StrategyHarami
    }
    Strategy = strategy_map[strategy_name]
    params = Strategy.params 


def convert_to_range(optimization_ranges):  
    range_dict = {}  
    for key, value in optimization_ranges.items():  
        if isinstance(value, list) and len(value) == 3:  
            range_dict[key] = range(value[0], value[1] + 1, value[2])
        else:  
            raise ValueError(f"Invalid range format for {key}. Expected a list with three elements [start, stop, step].")  
    return range_dict  

def metric_value(df, name, round_val=2, prettify_val=False):
    try:
        row = df.loc[df["metric"] == name, "value"]
        if row.empty:
            return None
        val = row.iloc[0]
        if str(val) == "inf":
            return val
        if isinstance(val, pd.Timedelta):
            return str(val)
        if not isinstance(val, (int, float)):
            return val
        val = round(val, round_val)
        return prettify(val) if prettify_val else val

    except Exception as e:
        return str(val) if "val" in locals() else None

def get_metric(df, name):
    return df.loc[df["metric"] == name, "value"].iloc[0]

def metric_with_delta(opt_df, base_df, name, round_val=2, prettify_val=False):
    try:
        val_opt = get_metric(opt_df, name)
    except Exception:
        return None, None

    delta = None
    if isinstance(base_df, pd.DataFrame):
        try:
            val_base = get_metric(base_df, name)
            if isinstance(val_opt, pd.Timedelta) and isinstance(val_base, pd.Timedelta):
                delta = val_opt - val_base
            elif isinstance(val_opt, (int, float)) and isinstance(val_base, (int, float)):
                delta = val_opt - val_base
            else:
                delta = None
        except Exception:
            delta = None

    def safe_round(value):
        """Round only numeric values; leave others unchanged."""
        if isinstance(value, (int, float)):
            return round(value, round_val)
        return value

    def safe_prettify(value):
        """Apply prettify only to numeric values; convert Timedelta to string."""
        if prettify_val:
            if isinstance(value, (int, float)):
                return prettify(round(value, round_val))
            if isinstance(value, pd.Timedelta):
                return str(value)
            return value
        else:
            if isinstance(value, pd.Timedelta):
                return str(value)
            return safe_round(value)

    val_opt = safe_prettify(val_opt)
    delta = safe_prettify(delta) if delta is not None else None

    return val_opt, delta

try:
    start_time = time.time()
    ticker_data = yf.Ticker(ticker)
    df_raw = ticker_data.history(period='max').reset_index()
    df_raw.columns = df_raw.columns.get_level_values(0)
    df_raw['Date'] = df_raw['Date'].dt.tz_localize(None)
    end_time = time.time() 
    processing = end_time - start_time  

    if strategy_name in ["RSI","MA Crossover","Parabolic SAR","MACD"]:
        optimized = st.checkbox("Optimize the backtesting strategy", label_visibility="visible")
    else:
        optimized = False
    start_date = str(date_filter[0])
    end_date = str(date_filter[1])
    df_raw = df_raw[(df_raw['Date']>=start_date) & (df_raw['Date']<=end_date)]

    resampling = False
    cheating = False

    with st.container(border=True):
        st.write("### Backtesting Strategy")
        st.write("Parameter:")
        st.code({k: getattr(Strategy.params, k) for k in Strategy.params._getkeys()})

        with st.spinner("Running backtesting strategy..."):
            df = df_raw.set_index("Date")

            start_time = time.time()
            perf, trades, tx, pos, timeret, equity, indicators = run_backtest(Strategy, df, cash, qty, cheating, resampling)
            st.info(f"Processed time backtesting: {time.time() - start_time:.4f} seconds")

            # -------------------------
            #  METRICS BLOCK
            # -------------------------
            metric_map = [
                ("EQUITY FINAL [IDR]", 2, True),
                ("RETURN [%]", 2, False),
                ("MAX. DRAWDOWN [%]", 2, False),
                ("SHARPE RATIO", 4, False),
                ("PROFIT FACTOR", 0, False),

                ("DURATION", 0, False),
                ("WIN RATE [%]", 2, False),
                ("BEST TRADE RETURN [%]", 2, False),
                ("WORST TRADE RETURN [%]", 2, False),
                ("EXPECTANCY RETURN", 0, True),
            ]

            col1, col2 = st.columns([5, 5])
            cols_top = st.columns([2, 1, 1, 1, 1])
            cols_bottom = st.columns([2, 1, 1, 1, 1])

            all_cols = cols_top + cols_bottom

            for col, (label, rnd, pretty) in zip(all_cols, metric_map):
                with col.container(border=True):
                    st.metric(
                        label=label,
                        value=metric_value(perf, label, rnd, prettify_val=pretty)
                    )

            # -------------------------
            #  DETAILS EXPANDERS
            # -------------------------
            with st.expander("See Performance Metrics"):
                st.write("#### Performance", perf)

            with st.expander("See Details"):
                st.write(df)
                st.write("#### Trades Log", trades)
                st.write("#### Transaction", tx)
                st.write("#### Equity", equity)
                st.write("#### Indicator", indicators)

            # -------------------------
            #  FINAL CHART RENDER
            # -------------------------
            df = df.reset_index()
            equity = equity.rename(columns={"index": "Date"})

            render_lightweight(df, tx, equity, trades, timeret, indicators, ticker)


    # ------------------------------
    # OPTIMIZATION SECTION
    # ------------------------------
    if optimized:

        with st.container(border=True):

            st.write("#### Optimized Backtesting")

            # Strategy-specific optimization ranges
            optimization_ranges_map = {
                "RSI": {
                    "rsi_period": [10, 20, 1],
                    "rsi_lower": [20, 40, 5],
                    "rsi_upper": [60, 80, 5],
                },
                "MA Crossover": {"fast_ma": [5, 20, 5], "slow_ma": [30, 100, 10]},
                "Parabolic SAR": {"af": [0.02, 0.5, 0.01], "af_max": [0.1, 0.5, 0.1]},
                "MACD": {"fast": [5, 20, 5], "slow": [30, 100, 10], "signal": [5, 12, 1]},
                "Stochastic": {
                    "k_period": [5, 20, 1],
                    "d_period": [2, 10, 1],
                    "slowing": [1, 5, 1],
                    "lower": [10, 30, 5],
                    "upper": [70, 90, 5],
                },
            }

            optimization_ranges = optimization_ranges_map.get(strategy_name, {})

            range_optimization_ranges = convert_to_range(optimization_ranges)
            strategy_params = {k: range_optimization_ranges[k] for k in params.__dict__.keys() if k in range_optimization_ranges}

            st.code(strategy_params)

            # -------------------------------------------
            # RUN OPTIMIZER
            # -------------------------------------------
            with st.spinner("Optimizing backtesting strategy..."):
                results_df, best_params_dict = run_optimizer(
                    Strategy, df_raw.set_index("Date"), cash, qty, strategy_params
                )
                with st.expander("See Details"):
                    st.write(results_df)

            # -------------------------------------------
            # RUN OPTIMIZED BACKTEST
            # -------------------------------------------
            start_time = time.time()
            perf_opt, trades_opt, tx_opt, pos_opt, tre_opt, eq_opt, ind_opt = run_backtest(
                Strategy,
                df_raw.set_index("Date"),
                cash,
                qty,
                cheating,
                resampling,
                best_params_dict=best_params_dict,
                optimized=True,
            )
            st.info(f"Processed time backtesting: {time.time() - start_time:.4f} seconds")

            # -------------------------------------------
            # METRICS DISPLAY (WITH DELTAS)
            # -------------------------------------------
            metric_list = [
                ("EQUITY FINAL [IDR]", 2, True),
                ("RETURN [%]", 2, False),
                ("MAX. DRAWDOWN [%]", 2, False),
                ("SHARPE RATIO", 4, False),
                ("PROFIT FACTOR", 2, False),
                ("DURATION", 0, False),
                ("WIN RATE [%]", 2, False),
                ("BEST TRADE RETURN [%]", 2, False),
                ("WORST TRADE RETURN [%]", 2, False),
                ("EXPECTANCY RETURN", 0, True),
            ]

            cols_top = st.columns([2, 1, 1, 1, 1])
            cols_bottom = st.columns([2, 1, 1, 1, 1])
            all_cols = cols_top + cols_bottom

            for col, (label, rnd, pretty) in zip(all_cols, metric_list):
                val, delta = metric_with_delta(perf_opt, perf, label, rnd, prettify_val=pretty)
                with col.container(border=True):
                    st.metric(label=label, value=val, delta=delta)

            # -------------------------------------------
            # DETAILS
            # -------------------------------------------
            with st.expander("See Performance Metrics"):
                st.write(perf_opt)

            with st.expander("See Details"):
                st.write("#### Trades Log", trades_opt)
                st.write("#### Transaction", tx_opt)
                st.write("#### Equity", eq_opt)
                st.write("#### Indicators", ind_opt)

            # -------------------------------------------
            # RENDER OPTIMIZED CHART
            # -------------------------------------------
            render_lightweight(
                df_raw,
                tx_opt,
                eq_opt.rename(columns={"index": "Date"}),
                trades_opt,
                tre_opt,
                ind_opt,
                ticker,
                render_key="optimized_multipane",
            )
except (Exception) as e:
    st.error(f"{type(e).__name__} - {e}.")            