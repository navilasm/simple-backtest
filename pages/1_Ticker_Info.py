from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import streamlit as st
import yfinance as yf
import time
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


st.set_page_config(page_title="Backtester", layout="wide")
st.title("Ticker Fundamental")

col1, col2, col3, col4, col5 = st.columns([1.5,2.5,1.5,2,2.5])
with col1.container(border=True):
    ticker = st.text_input("Enter Stock Code 👇", 'BBRI.JK')
ticker_data = yf.Ticker(ticker)
with col2.container(border=True):
    date_filter = st.date_input("Select time period 👇",(datetime(2022, 1, 1), datetime.today().date()), 
                                                        min_value=datetime(2020, 1, 1), max_value=datetime.today().date(), format="YYYY.MM.DD")
try:
    try:
        quarterly_income_stmt = ticker_data.quarterly_income_stmt.reset_index()
        quarterly_income_stmt.rename(columns={'index':'Variable'}, inplace=True)
        quarterly_income_stmt = quarterly_income_stmt.set_index('Variable')
        st.write(quarterly_income_stmt)
    except:
        pass

    try:
        ticker_fuds = ticker_data.funds_data
    except:
        pass

    start_time = time.time()
    df_raw = ticker_data.history(period='max').reset_index()
    df_raw.columns = df_raw.columns.get_level_values(0)
    df_raw['Date'] = df_raw['Date'].dt.tz_localize(None)
    end_time = time.time() 
    processing = end_time - start_time  
    st.markdown("""
    # 🧠 Simple Beginner Checklist

    **Good business usually shows:**

    * 📈 Revenue ↑
    * 📈 Normalized income ↑
    * 📈 Diluted EPS ↑
    * 📉 SG&A % ↓
    * ➖ Share count stable

    **Danger signs:**

    * Profits up but EPS flat
    * Revenue up but operating income down
    * “One-time” gains every year
    * Heavy dilution

                """)

    col_a1, col_b1 = st.columns(2)
    with col_a1.container(border=True):
        st.write('#### 1. Profitability & Earnings (Is the business actually making money?)')
        st.markdown('These tell you **whether profits exist, how stable they are, and whether they belong to shareholders**.')
        profitability = quarterly_income_stmt.T[['Net Income','Net Income Common Stockholders','Diluted EPS','Basic EPS',
                                         'Diluted NI Availto Com Stockholders','Pretax Income','Tax Provision','Normalized Income'
                                        ]].reset_index().rename( columns={'index':'Date'})
        profitability['Date'] = pd.to_datetime(profitability['Date'])
        profitability = profitability.set_index('Date')
        columns = ['Net Income','Net Income Common Stockholders','Diluted EPS','Basic EPS',
                   'Diluted NI Availto Com Stockholders','Pretax Income','Tax Provision','Normalized Income']
        
        for i, col in enumerate(columns):
            # --- Create figure ---
            fig = go.Figure()
            fig.add_trace(go.Scatter( x=profitability.index, y=profitability[col], mode="lines+markers", name=col))
            fig.update_layout(title=col, height=300, showlegend=False, margin=dict(l=40, r=20, t=40, b=40))

            # --- Show chart ---
            st.plotly_chart(fig, use_container_width=True, key=f"shares_chart_{i}_{col}")

            # --- Expander explanation ---
            with st.expander(f"How to read: {col}"):
                if col == "Net Income":
                    st.markdown("""
                    **What it means:**
                    Profit after **all expenses, interest, and taxes**.
                                
                    **How to read it:**
                    * Look at **trend over time**, not one year.
                    * Compare against revenue growth.
                                
                    **🟢 Green flags**
                    * Consistently positive
                    * Growing steadily year over year
                                
                    **🔴 Red flags**
                    * Frequent losses
                    * Large swings without clear reason
                    * Profit grows slower than revenue (margin compression)""")
                elif col == "Net Income Common Stockholders":
                    st.markdown("""
                    **What it means:**
                    Profit **actually attributable to common shareholders** (after preferred dividends).
                                
                    **Why it matters:**
                    This is the profit that can **support EPS and dividends**.
                                
                    **🟢 Green flags**
                    * Close to Net Income
                    * Stable or rising
                                
                    **🔴 Red flags**
                    * Much lower than Net Income (heavy preferred obligations)""")
                elif col == "Diluted EPS" or col == "Basic EPS":
                    st.markdown("""
                    **What it means:**
                    Profit **per share**.
                                
                    * **Basic EPS** → current shares
                    * **Diluted EPS** → assumes options, RSUs, convertibles become shares
                                
                    **Beginner rule:**
                    👉 **Always trust Diluted EPS more**
                                
                    **🟢 Green flags**
                    * Diluted EPS growing over time
                    * Small gap between basic and diluted EPS
                                
                    **🔴 Red flags**
                    * EPS flat while Net Income grows (share dilution)
                    * Large gap between basic and diluted EPS""")
                elif col == "Diluted NI Availto Com Stockholders":
                    st.markdown("""
                    **What it means:**
                    Net income available to common shareholders **after dilution effects**.
                                
                    **🟢 Green flags**
                    * Matches trend of Diluted EPS
                    * Growing steadily
                                
                    **🔴 Red flags**
                    * Falling even when company reports “record profits”""")
                elif col == "Pretax Income":
                    st.markdown("""
                    **What it means:**
                    Profit **before taxes**.
                                
                    **Why it matters:**
                    Shows **true operating profitability**, independent of tax tricks.
                                
                    **🟢 Green flags**
                    * Stable growth
                    * Pretax margin improving
                                
                    **🔴 Red flags**
                    * Strong revenue but weak pretax income
                    * Heavy reliance on tax credits to stay profitable""")
                elif col == "Tax Provision":
                    st.markdown("""
                    **What it means:**
                    Taxes paid or owed.
                                
                    **Use it to calculate:**
                    👉 **Effective Tax Rate = Tax Provision / Pretax Income**
                                
                    **🟢 Green flags**
                    * Reasonable and stable tax rate
                    * Slightly lower than statutory rate (normal optimization)
                                
                    **🔴 Red flags**
                    * Extremely low or negative tax for many years
                    * Big tax benefits propping up profits""")
                elif col == "Normalized Income":
                    st.markdown("""
                    **What it means:**
                    Profit **after removing one-off events** (asset sales, legal settlements, restructuring).
                                
                    **Beginner tip:**
                    👉 **This is the “real” profit**
                                
                    **🟢 Green flags**
                    * Close to reported Net Income
                    * Stable trend
                                
                    **🔴 Red flags**
                    * Huge gap vs Net Income
                    * Profits depend on “one-time” gains every year""")
    with col_b1.container(border=True):
        st.write('#### 2. Operating Performance (How efficiently the business runs)')
        st.markdown('These show **cost control and scalability**.')
        operating = quarterly_income_stmt.T[['Operating Expense', 'Selling General And Administration',
                                     'General And Administrative Expense','Depreciation And Amortization In Income Statement', 
                                     'Depreciation Income Statement','Operating Revenue'
                                        ]].reset_index().rename( columns={'index':'Date'})
        operating['Date'] = pd.to_datetime(operating['Date'])
        operating = operating.set_index('Date')
        columns = ['Operating Expense', 'Selling General And Administration',
                    'General And Administrative Expense','Depreciation And Amortization In Income Statement', 
                    'Depreciation Income Statement','Operating Revenue'
                    ]
        for i, col in enumerate(columns):
            # --- Create figure ---
            fig = go.Figure()
            fig.add_trace(go.Scatter( x=operating.index, y=operating[col], mode="lines+markers", name=col))
            fig.update_layout(title=col, height=300, showlegend=False, margin=dict(l=40, r=20, t=40, b=40))

            # --- Show chart ---
            st.plotly_chart(fig, use_container_width=True, key=f"shares_chart_{i}_{col}")

            # --- Expander explanation ---
            with st.expander(f"How to read: {col}"):
                if col == "Operating Expense":
                    st.markdown("""
                                **What it means:**
                                All costs needed to run the business.
                                                    
                                **Beginner rule:**
                                👉 Expenses should grow **slower than revenue**.
                                                    
                                **🟢 Green flags**
                                * Expense growth < revenue growth
                                * Stable operating margin
                                                    
                                **🔴 Red flags**
                                * Expenses grow faster than revenue
                                * Sudden cost spikes without explanation""")
                elif col == "Selling General And Administration":
                    st.markdown("""
                                **What it means:**
                                Marketing, salaries, HQ costs, admin.
                                                    
                                **🟢 Green flags**
                                * SG&A % of revenue declining over time
                                * Scales well as company grows
                                                    
                                **🔴 Red flags**
                                * SG&A growing faster than revenue
                                * Excessive executive compensation""")
                elif col == "General And Administrative Expense":
                    st.markdown("""
                                **What it means:**
                                Non-sales overhead costs.
                                                    
                                **🟢 Green flags**
                                * Stable as % of revenue
                                                    
                                **🔴 Red flags**
                                * Rising overhead without revenue growth""")
                elif col == "Depreciation And Amortization In Income Statement":
                    st.markdown("""
                                **What it means:**
                                Accounting cost for long-term assets.
                                                    
                                **How to read it:**
                                * High D&A is normal for **capital-intensive industries**
                                * Low D&A in asset-heavy business is suspicious
                                                    
                                **🟢 Green flags**
                                * Consistent with business model
                                * Matches capex history
                                                    
                                **🔴 Red flags**
                                * Very low D&A for asset-heavy firms
                                * Large jumps without asset expansion""")
                elif col == "Depreciation Income Statement":
                    st.markdown(""".""")
                elif col == "Operating Revenue":
                    st.markdown("""
                                **What it means:**
                                Revenue from **core business only**.
                                                    
                                **🟢 Green flags**
                                * Steady growth
                                * More predictable than Total Revenue
                                                    
                                **🔴 Red flags**
                                * Flat or declining while Total Revenue rises (non-core dependency)""")

    col_a2, col_b2 = st.columns(2)
    with col_a2.container(border=True):
        st.write('#### 3. Revenue (Is growth real?)')
        revenue = quarterly_income_stmt.T[['Total Revenue', 'Operating Revenue']].reset_index().rename( columns={'index':'Date'})
        revenue['Date'] = pd.to_datetime(revenue['Date'])
        revenue = revenue.set_index('Date')

        columns = ['Total Revenue', 'Operating Revenue']
        for i, col in enumerate(columns):
            # --- Create figure ---
            fig = go.Figure()
            fig.add_trace(go.Scatter( x=revenue.index, y=revenue[col], mode="lines+markers", name=col))
            fig.update_layout(title=col, height=300, showlegend=False, margin=dict(l=40, r=20, t=40, b=40))

            # --- Show chart ---
            st.plotly_chart(fig, use_container_width=True, key=f"shares_chart_{i}_{col}")

            # --- Expander explanation ---
            with st.expander(f"How to read: {col}"):
                if col == "Total Revenue":
                    st.markdown("""
                    **What it means:**
                    All income sources combined.
                                
                    **🟢 Green flags**
                    * Consistent growth
                    * Matches operating revenue trend
                                
                    **🔴 Red flags**
                    * Volatile
                    * Growth driven by one-off items
                    """)
                elif col == "Operating Revenue":
                    st.markdown("""
                    **What it means:**
                    Revenue from main business.
                    
                    **Beginner rule:**
                    👉 **Operating Revenue > Total Revenue quality matters more**
                    
                    **🟢 Green flags**
                    * Majority of revenue is operating
                    * Predictable growth
                                
                    **🔴 Red flags**
                    * Core revenue stagnant
                    * Reliance on non-operating income
                    """)
    with col_b2.container(border=True):
        st.write('#### 1. 4. Shares (Are shareholders being diluted?)')
        shares = quarterly_income_stmt.T[['Diluted Average Shares', 'Basic Average Shares']].reset_index().rename(columns={'index':'Date'})
        shares['Date'] = pd.to_datetime(shares['Date'])
        shares = shares.set_index('Date')

        columns = ['Diluted Average Shares', 'Basic Average Shares']
        for i, col in enumerate(columns):
            # --- Create figure ---
            fig = go.Figure()
            fig.add_bar(x=shares.index, y=shares[col], name=col)
            fig.update_layout(title=col, height=300, showlegend=False, margin=dict(l=40, r=20, t=40, b=40))

            # --- Show chart ---
            st.plotly_chart(fig, use_container_width=True, key=f"shares_chart_{i}_{col}")

            # --- Expander explanation ---
            with st.expander(f"How to read: {col}"):
                if col == "Diluted Average Shares":
                    st.markdown("""
                    **What it means:**
                    Shares assuming options & convertibles exercised.
                    
                    **Beginner rule:**
                    👉 **Watch the trend, not the number**
                                
                    **🟢 Green flags**
                    * Flat or slowly declining
                    * Buybacks offset stock compensation
                    
                    **🔴 Red flags**
                    * Diluted shares rising faster than profits
                    * EPS growth only from accounting tricks
                    """)
                elif col == "Basic Average Shares":
                    st.markdown("""
                    **What it means:**
                    Current share count.
                                
                    **🟢 Green flags**
                    * Stable or declining (buybacks)
                                
                    **🔴 Red flags**
                    * Rapid increase year after year
                    """)


    col_a3, col_b3 = st.columns(2)
    with col_a3.container(border=True):
        st.write('#### Dividends')
        dividends_df = df_raw[df_raw['Dividends']>0].copy().reset_index(drop=True)
        dividends_df['Date'] = dividends_df['Date'].astype(str)
        st.bar_chart(dividends_df, x='Date',y='Dividends')
    with col_b3.container(border=True):    
        st.write('#### Stock Splits')
        stocksplits_df = df_raw[df_raw['Stock Splits']>0].copy().reset_index(drop=True)
        stocksplits_df['Date'] = stocksplits_df['Date'].astype(str)
        st.bar_chart(stocksplits_df, x='Date',y='Stock Splits')

    
except (Exception) as e:
    st.error(f"{type(e).__name__} - {e}.")
