from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import pandas as pd
import numpy as np
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts
import json
import streamlit as st


def buysell_markers(df):
    markers = []
    for _, row in df.iterrows():
        if row['signal'] == 'buy':
            marker = {
                "time": row['time'],
                "position": 'belowBar',
                #"color":'rgba(38,166,154,0.9)', #green
                "color":'#3f51b5',
                "shape": 'arrowUp',
                "text": 'BUY'
            }
            markers.append(marker)
        elif row['signal'] == 'sell':
            marker = {
                "time": row['time'],
                "position": 'aboveBar',
                #"color":'rgba(239,83,80,0.9)', #red
                "color":'#e81e63',
                "shape": 'arrowDown',
                "text": 'SELL'
            }
            markers.append(marker)
    return markers

def pnl_markers(df):
    markers = []
    for _, row in df.iterrows():
        if row['PnL']>=0:
            marker = {
                "time": row['time'],
                "position": 'aboveBar',
                "color":'#009688', #blue
                "shape": 'circle',
                "text": 'PROFIT'
            }
            markers.append(marker)
        elif row['PnL']<0:
            marker = {
                "time": row['time'],
                "position": 'aboveBar',
                "color":'#f44336', #red
                "shape": 'circle',
                "text": 'LOSS'
            }
            markers.append(marker)
    return markers

#lightweight
def render_lightweight(df, transaction_df, equity_df, trades_df, timereturn_df, indicators_df, ticker, render_key='multipane'):
    try:
        df.columns = ['Date','open','high','low','close','volume', 'dividends', 'stock splits'] 
    except:
        df.columns = ['Date','open','high','low','close','volume'] 
    COLOR_BULL = 'rgba(38,166,154,0.9)' 
    COLOR_BEAR = 'rgba(239,83,80,0.9)'  
    df['time'] = df['Date'].dt.strftime('%Y-%m-%d') 
    df['color'] = np.where(df['open'] > df['close'], COLOR_BEAR, COLOR_BULL)
    candles = json.loads(df.to_json(orient = "records"))
    #st.write(df)

    #transaction_df = transaction_df.rename(columns={'date':'time'})
    try:
        transaction_df['time'] = transaction_df['date'].dt.strftime('%Y-%m-%d') 
    except:
        pass
    #st.write(transaction_df)

    #equity_df = equity_df.rename(columns={'Date':'time'})
    equity_df['time'] = pd.to_datetime(equity_df['Date'], errors='coerce')
    equity_df['time'] = equity_df['time'].dt.strftime('%Y-%m-%d') 
    equity_df['equity'] = equity_df['equity'].bfill()
    equity_df['cash'] = equity_df['cash'].bfill()
    equity_df['negative_return'] = equity_df['current_return'].apply(lambda x: x if (x is not None and x < 0) else np.nan)
    portfolio = json.loads(equity_df[['time','equity']].rename(columns={'equity':'value'}).to_json(orient='records'))
    cash_balance = json.loads(equity_df[['time','cash']].rename(columns={'cash':'value'}).to_json(orient='records'))
    drawdown_json = json.loads(equity_df[['time','drawdown']].rename(columns={'drawdown':'value'}).to_json(orient='records'))
    negative_returns_json = json.loads(equity_df[['time','negative_return']].rename(columns={'negative_return':'value'}).to_json(orient='records'))
    returns_json = json.loads(equity_df[['time','current_return']].rename(columns={'current_return':'value'}).to_json(orient='records'))
    #st.write(equity_df)

    trades_df['time'] = pd.to_datetime(trades_df['ExitTime'], errors='coerce')
    trades_df['time'] = trades_df['time'].dt.strftime('%Y-%m-%d') 

    timereturn_df['time'] = pd.to_datetime(timereturn_df['Date'], errors='coerce')
    timereturn_df['time'] = timereturn_df['time'].dt.strftime('%Y-%m-%d') 
    #returns_json = json.loads(timereturn_df[['time','Value']].rename(columns={'Value':'value'}).to_json(orient='records'))

    try:
        indicators_df['time'] = pd.to_datetime(indicators_df['datetime'], errors='coerce')
        indicators_df['time'] = indicators_df['time'].dt.strftime('%Y-%m-%d') 
        indicators_df = indicators_df.merge(equity_df[['time']], how='outer', on='time').drop(columns='datetime').sort_values('time',ascending=True).dropna(axis=1, how='all')
    except:
        pass

    chartMultipaneOptions = [
            {"height": 200,
                "layout": {"background": {"type": "solid","color": 'transparent'},"textColor": "black"},
                "grid": {"vertLines": {"color": "rgba(197, 203, 206, 0)"},
                        "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}},
                "timeScale": {"visible": False},
                "watermark": {"visible": True,"fontSize": 18,
                            "horzAlign": 'left',"vertAlign": 'top',
                            "color": 'rgba(171, 71, 188, 0.7)',
                            "text": 'Equity & Cash',}},
            {"height": 400,
                "layout": {"background": {"type": "solid","color": 'white'},"textColor": "black"},
                "grid": {"vertLines": {"color": "rgba(197, 203, 206, 0.5)"},
                        "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}},
                "crosshair": {"mode": 0},
                "priceScale": {"borderColor": "rgba(197, 203, 206, 0.8)"},
                "timeScale": {"borderColor": "rgba(197, 203, 206, 0.8)","barSpacing": 15},
                "watermark": {"visible": True,"fontSize": 48,
                            "horzAlign": 'center',"vertAlign": 'center',
                            "color": 'rgba(171, 71, 188, 0.3)',
                            "text": ticker,}},
            #{"height": 100,
            #    "layout": {"background": {"type": "solid","color": 'transparent'},"textColor": "black"},
            #    "grid": {"vertLines": {"color": "rgba(197, 203, 206, 0)"},
            #            "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}},
            #    "timeScale": {"visible": False, "timeVisible":False},
            #    "watermark": {"visible": True,"fontSize": 18,
            #                "horzAlign": 'left',"vertAlign": 'top',
            #                "color": 'rgba(171, 71, 188, 0.7)',
            #                "text": 'Returns (%)',}},
            #{"height": 100,
            #    "layout": {"background": {"type": "solid","color": 'transparent'},"textColor": "black"},
            #    "grid": {"vertLines": {"color": "rgba(197, 203, 206, 0)"},
            #            "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}},
            #    "timeScale": {"visible": False, "timeVisible":False},
            #    "watermark": {"visible": True,"fontSize": 18,
            #                "horzAlign": 'left',"vertAlign": 'top',
            #                "color": 'rgba(171, 71, 188, 0.7)',
            #                "text": 'Drawdown (%)',}},
            {"height": 150,
                "layout": {"background": {"type": "solid","color": 'transparent'},"textColor": "black"},
                "grid": {"vertLines": {"color": "rgba(197, 203, 206, 0)"},
                        "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}},
                "timeScale": {"visible": False, "timeVisible":False},
                "watermark": {"visible": True,"fontSize": 18,
                            "horzAlign": 'left',"vertAlign": 'top',
                            "color": 'rgba(171, 71, 188, 0.7)',
                            "text": 'Indicators',}},
        ]
    seriesPortfolioChart = [
        {"type": 'Line',"data": portfolio, 
        "options":{"color":'#3f51b5',#'rgba(38,166,154,0.9)',
                    "priceFormat": {"type": 'volume',}},
        "markers": pnl_markers(trades_df[['time','PnL']])
        },
        {"type": 'Line',"data": cash_balance,  
        "options":{"color":'#e81e63',#'rgba(255, 192, 0, 1)',#'rgba(239,83,80,0.9)',
                    "priceFormat": {"type": 'volume',}}
        }
        ]
    seriesCandlestickChart = [
            {"type": 'Candlestick',
            "data": candles,
            "options": {"upColor": COLOR_BULL,"downColor": COLOR_BEAR,"borderVisible": False,
                        "wickUpColor": COLOR_BULL,"wickDownColor": COLOR_BEAR},
            "markers": buysell_markers(transaction_df)
            },
        ]
    seriesReturnsChart = [
        {"type": 'Line',"data": returns_json, 
        "options":{"color":'rgba(38,166,154,0.9)',
                    "priceFormat": {"type": 'volume',}},
        },
        ]
    seriesDrawdownChart = [
        {"type": 'Line',"data": drawdown_json,  
        "options":{"color":'rgba(239,83,80,0.9)',
                    "priceFormat": {"type": 'volume',}}
        },
        #{"type": 'Line',"data": negative_returns_json,  
        #"options":{"color":'rgba(38,166,154,0.9)',
        #            "priceFormat": {"type": 'volume',}}
        #}
        ]
    try:
        seriesIndicatorsChart = []
        color_options = ["#8fc0cf", "#e7998f", "#f9d269", ]
        for i in range(0, indicators_df.set_index('time').shape[1]):
            #st.write(indicators_df.set_index('time').columns[i])
            seriesIndicatorsChart.append({
            "type": "Line",
            "data": json.loads(indicators_df[['time', indicators_df.set_index('time').columns[i]]].rename(columns={indicators_df.set_index('time').columns[i]:'value'}).to_json(orient='records')),
            "options": {"color": color_options[i % len(color_options)] ,
                        "lineWidth": 2},
            #"name": indicators_df.set_index('time').columns[i]
            })
        #seriesIndicatorsChart = [
        #    {"type": 'Line',"data": ind_1, "name":'rsi_val',
        #    "options":{"priceFormat": {"type": 'volume',}},
        #    },
        #    ]
        renderLightweightCharts([
                {"chart": chartMultipaneOptions[0],"series": seriesPortfolioChart},
                {"chart": chartMultipaneOptions[1],"series": seriesCandlestickChart},
                #{"chart": chartMultipaneOptions[2],"series": seriesReturnsChart},
                #{"chart": chartMultipaneOptions[3],"series": seriesDrawdownChart},
                {"chart": chartMultipaneOptions[2],"series": seriesIndicatorsChart},
                ],
                    render_key
            )
    except:
        renderLightweightCharts([
            {"chart": chartMultipaneOptions[0],"series": seriesPortfolioChart},
            {"chart": chartMultipaneOptions[1],"series": seriesCandlestickChart},
            #{"chart": chartMultipaneOptions[2],"series": seriesReturnsChart},
            #{"chart": chartMultipaneOptions[3],"series": seriesDrawdownChart},
            ],
                render_key
        )