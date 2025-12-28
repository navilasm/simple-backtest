from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import pandas as pd
import backtrader as bt
import numpy as np
import pandas as pd
import time
import streamlit as st

riskfree_annual = 0.01
trading_days_per_year = 365
daily_return = (1 + riskfree_annual) ** (1 / trading_days_per_year) - 1

def run_backtest(Strategy, df, cash, qty, cheating, resampling, optimized=False, best_params_dict=None):
    cerebro = bt.Cerebro()
    if optimized==False:
        cerebro.addstrategy(Strategy)
    else:
        cerebro.addstrategy(Strategy, **best_params_dict)  

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    if resampling==True:
        cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)
    else:
        pass
    
    # Set desired initial capital
    cerebro.broker.setcash(cash)
    cerebro.addsizer(bt.sizers.FixedSize, stake=qty)
    #cerebro.broker.setcommission(commission=0)

    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addobserver(bt.observers.TimeReturn)

    if resampling==False:
        cerebro.addanalyzer(bt.analyzers.PositionsValue, _name='positionsvalue')
    else:
        pass
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days, riskfreerate=daily_return)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')  
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')  
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')   
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions') 
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn') 
    cerebro.addanalyzer(bt.analyzers.Calmar, _name='calmar')

    thestrats = cerebro.run(cheat_on_open=cheating)
    thestrat = thestrats[0]
    if resampling==False:
        positionsvalue = thestrat.analyzers.positionsvalue.get_analysis()
    else:
        pass

    sharpe = thestrat.analyzers.sharpe.get_analysis()  
    drawdown = thestrat.analyzers.drawdown.get_analysis()  
    returns = thestrat.analyzers.returns.get_analysis()  
    trades = thestrat.analyzers.trades.get_analysis()  
    sqn = thestrat.analyzers.sqn.get_analysis() 
    transactions = thestrat.analyzers.transactions.get_analysis() 
    timereturn = thestrat.analyzers.timereturn.get_analysis()  
    calmar = thestrat.analyzers.calmar.get_analysis()  

    #cerebro.plot()

    try:
        indicators_df = pd.DataFrame(thestrat.indicator_values)
        indicators_df.columns = indicators_df.iloc[0]  
        indicators_df = indicators_df[1:].reset_index(drop=True).dropna(axis=1, how='all')
    except:
        indicators_df = 'No indicators'
    try:
        indicators_df = indicators_df.drop(columns=['fromopen']) 
    except:
        pass
    if resampling==True and isinstance(indicators_df, pd.DataFrame) and not indicators_df.empty:  
        indicators_df = indicators_df.drop(columns=['support1','resistance1','high_price','low_price','pp_val']).dropna()
        indicators_df['datetime'] = pd.to_datetime(indicators_df['datetime'])
        indicators_df = df.reset_index()[['Date']].merge(indicators_df, how='left',left_on='Date', right_on='datetime')
        indicators_df = indicators_df[['Date','support2','resistance2']].rename(columns={'Date':'datetime'}).fillna(0).sort_values('datetime',ascending=True).drop_duplicates(subset='datetime',keep='first').reset_index(drop=True)
    else:
        pass

    timereturn_df = pd.DataFrame(list(timereturn.items()), columns=['Date', 'Value'])
    calmar_df = pd.DataFrame.from_dict(calmar, orient='index', columns=['Value']).reset_index()
    
    data = []  
    for date, value in transactions.items():  
        for item in value:  
            data.append([date] + item)  
    columns = ['date', 'amount', 'price', 'sid', 'symbol', 'value'] 
    transaction_df = pd.DataFrame(data, columns=columns)
    transaction_df['signal'] = np.where(transaction_df['amount']<0 & np.array(transaction_df['amount']>0),'sell','buy')

    if resampling==False:
        position_df = pd.DataFrame.from_dict(positionsvalue, orient='index', columns=['Value']).reset_index()
        position_df['index'] = pd.to_datetime(position_df['index'])  
    else:
        position_df = transaction_df[['date','amount','signal']].merge(df.reset_index()[['Date','Close']].rename(columns={'Date':'date'}), on='date', how='outer').sort_values('date',ascending=True).reset_index(drop=True)
        position_df['amount'] = position_df['amount'].ffill().fillna(0).clip(lower=0)  
        position_df['Value'] = position_df['amount']*position_df['Close']
        position_df = position_df.rename(columns={'date':'index'}).drop(columns={'signal','amount'})

    equity_df = position_df.merge(transaction_df[['date','price','amount','signal']], how='left', left_on='index', right_on='date').drop(columns={'date'})
    try:
        #Calculate the cash throughout trades
        try:
            buy_index = equity_df[equity_df['signal'] == 'buy'].index[0]  
            equity_df.loc[buy_index, 'price'] = equity_df.loc[buy_index, 'price'].ffill()  
        except:
            pass
        try:
            sell_index = equity_df[equity_df['signal'] == 'sell'].index[0]  
            equity_df.loc[sell_index, 'price'] = equity_df.loc[sell_index, 'price'].ffill()  
        except:
            pass  

        print(equity_df.info())
        equity_df['cash'] = cash
        for i in range(1, len(equity_df)):
            equity_df.iloc[i, equity_df.columns.get_loc('cash')] = equity_df.iloc[i - 1, equity_df.columns.get_loc('cash')]
            if (
                equity_df.iloc[i, equity_df.columns.get_loc('signal')] == 'buy'
                and not pd.isna(equity_df.iloc[i, equity_df.columns.get_loc('price')])
            ):
                equity_df.iloc[i, equity_df.columns.get_loc('cash')] -= (
                    equity_df.iloc[i, equity_df.columns.get_loc('price')]
                    * equity_df.iloc[i, equity_df.columns.get_loc('amount')]
                )

            elif (
                equity_df.iloc[i, equity_df.columns.get_loc('signal')] == 'sell'
                and not pd.isna(equity_df.iloc[i, equity_df.columns.get_loc('price')])
            ):
                equity_df.iloc[i, equity_df.columns.get_loc('cash')] += (
                    equity_df.iloc[i, equity_df.columns.get_loc('price')]
                    * abs(equity_df.iloc[i, equity_df.columns.get_loc('amount')])
                )

        
        #Calculate the equity
        equity_df.set_index('index', inplace=True)  
        cash_ = equity_df.iloc[0]['cash']
        holdings = 0  
        equity_list = []  
        equity_df['current_return'] = None
        last_buy_price = None
        last_buy_amount = None
        for idx, row in equity_df.iterrows():  
            if row['signal'] == 'buy' and not pd.isna(row['amount']):  
                holdings += row['amount']  
                cash_ -= row['amount'] * row['price']  
                last_buy_price = row['price']  
                last_buy_amount = row['amount']
            elif row['signal'] == 'sell' and not pd.isna(row['amount']):  
                holdings += row['amount']  
                cash_ -= row['amount'] * row['price'] 
                if last_buy_price is not None and last_buy_amount is not None:
                    current_value = row['price'] * -row['amount']
                    equity_df.at[idx, 'current_return'] = ((current_value - (last_buy_price * last_buy_amount)) 
                                                            / (last_buy_price * last_buy_amount)) * 100
                last_buy_price = None
                last_buy_amount = None
            
            if last_buy_price is not None and not pd.isna(row['Value']):                
                current_value = row['Value']  
                equity_df.at[idx, 'current_return'] = ((current_value - (last_buy_price * last_buy_amount)) / (last_buy_price * last_buy_amount)) * 100
            
            equity = cash_ + row['Value']  
            equity_list.append(equity)  
        equity_df['equity'] = equity_list  
        equity_df = equity_df.reset_index()

        #Calculate the drawdown
        equity_df['peak_equity'] = equity_df['equity'].cummax()  
        equity_df['drawdown'] = ((equity_df['equity'] - equity_df['peak_equity']) / equity_df['peak_equity'])*(100)

        #Calculate expectancy %
        win_rate = trades['won']['total'] / trades['total']['closed']
        avg_win = trades['won']['pnl']['average']
        avg_loss = trades['lost']['pnl']['average']
        expectancy = ((win_rate * avg_win) - ((1-win_rate)*abs(avg_loss)))
    except: 
        pass
    
    #Transform transactions data to trades transaction log
    try:
        # Initialize lists to store the results  
        sizes = []  
        entry_prices = []  
        exit_prices = []  
        pnls = []  
        return_pcts = []  
        entry_times = []  
        exit_times = []  
        durations = []
        
        # Iterate through the DataFrame to find pairs of 'buy' and 'sell' signals  
        for i in range(0, len(transaction_df), 2):  
            if i+1 < len(transaction_df):  
                entry_row = transaction_df.iloc[i]  
                exit_row = transaction_df.iloc[i+1]  
                
                size = entry_row['amount']  
                entry_price = entry_row['price']  
                exit_price = exit_row['price']  
                pnl = exit_price - entry_price  
                return_pct = ((exit_price - entry_price) / entry_price) * 100  
                entry_time = entry_row['date']  
                exit_time = exit_row['date']  
                duration = exit_time - entry_time  
                
                sizes.append(size)  
                entry_prices.append(entry_price)  
                exit_prices.append(exit_price)  
                pnls.append(pnl)  
                return_pcts.append(return_pct)  
                entry_times.append(entry_time)  
                exit_times.append(exit_time)  
                durations.append(duration)  
        
        # Create the output DataFrame  
        trades_df = pd.DataFrame({  
            'Size': sizes,  
            'EntryPrice': entry_prices,  
            'ExitPrice': exit_prices,  
            'PnL': pnls,  
            'ReturnPct': return_pcts,  
            'EntryTime': entry_times,  
            'ExitTime': exit_times,  
            'Duration': durations 
        })  
        
        if trades['lost']['pnl']['total'] != 0:  
            profit_factor = trades['won']['pnl']['total'] / abs(trades['lost']['pnl']['total'])
        else:  
            profit_factor = float('inf')
    except:
        pass

    #Performance metrics
    try:
        data = {  
            'START': position_df['index'].min(),  
            'END': position_df['index'].max(),  
            'DURATION': position_df['index'].max() - position_df['index'].min(),
            'EXPOSURE TIME [%]': (trades['len']['total']/(position_df['index'].max() - position_df['index'].min()).days)*100, #hanya closed trades?
            'EQUITY FINAL [IDR]': cerebro.broker.getvalue(), 
            'EQUITY PEAK [IDR]': equity_df['peak_equity'].max(),  
            'RETURN [%]': returns['rtot']*100,  
            'BUY & HOLD RETURN [%]': ((df['Close'].iloc[-1] - df['Close'].iloc[0])/df['Close'].iloc[0])*100, 
            'RETURN (ANN.) [%]': returns['rnorm100'],  
            'RETURN VOLATILITY [%]': (timereturn_df[timereturn_df['Value'] > 0]['Value'].std() * 100),  
            'SHARPE RATIO': sharpe['sharperatio'],  
            'CALMAR RATIO (BACKTRADER)': calmar_df['Value'].iloc[-1],
            'CALMAR RATIO': returns['rnorm100']/drawdown['max']['drawdown'] if drawdown['max']['drawdown'] != 0 else float('inf'),  
            'MAX. DRAWDOWN [%]': drawdown['max']['drawdown'],  
            'AVG. DRAWDOWN [%]': drawdown['drawdown'],  
            'MAX. DRAWDOWN DURATION': drawdown['max']['len'],  
            'AVG. DRAWDOWN DURATION': drawdown['len'],  
            'TOTAL TRADES': trades['total']['total'],  
            'WIN RATE [%]': (trades['won']['total'] / trades['total']['closed']) * 100,
            'BEST TRADE RETURN [%]': trades_df['ReturnPct'].max(),  
            'WORST TRADE RETURN [%]': trades_df['ReturnPct'].min(), 
            'AVG. TRADE RETURN [%]': trades_df['ReturnPct'].mean(), 
            'MAX. TRADE DURATION': trades['len']['max'], # 
            'AVG. TRADE DURATION': trades['len']['average'],  
            'PROFIT FACTOR': profit_factor,  
            'EXPECTANCY RETURN': expectancy,
            'SQN': sqn['sqn']  
        }  
        performance_metrics = pd.DataFrame(list(data.items()), columns=['metric', 'value'])  
        rows_to_format = [  
                'EXPOSURE TIME [%]', 'RETURN [%]','BUY & HOLD RETURN [%]', 'RETURN (ANN.) [%]', 'RETURN VOLATILITY [%]',  
                'SHARPE RATIO', 'CALMAR RATIO', 'MAX. DRAWDOWN [%]',  
                'AVG. DRAWDOWN [%]', 'WIN RATE [%]', 'BEST TRADE RETURN [%]',  
                'WORST TRADE RETURN [%]', 'AVG. TRADE RETURN [%]', 'PROFIT FACTOR',  
                'EXPECTANCY RETURN', 'SQN'
                    ]  

        performance_metrics['value'] = performance_metrics.apply(lambda x: round(float(x['value']), 5) if x['metric'] in rows_to_format else x['value'],  axis=1)    
        performance_metrics = performance_metrics
    except:
        #trades_df = 'no trades'
        performance_metrics = 'no trades'
        #transaction_df = 'no trades'
        #position_df = 'no trades'
    return performance_metrics, trades_df, transaction_df, position_df, timereturn_df, equity_df, indicators_df


#get Strategy's params
def get_params(strategy_class):  
    return {param_name: getattr(strategy_class.params, param_name) for param_name in strategy_class.params._getkeys()}  


#optimize backtesting
def run_optimizer(Strategy, df, cash, qty, strategy_params):
    data = bt.feeds.PandasData(dataname=df)  
    crbr_opt = bt.Cerebro() 
    crbr_opt.optstrategy(Strategy, **strategy_params)  
    crbr_opt.adddata(data)  
    crbr_opt.broker.set_cash(cash) 
    crbr_opt.addsizer(bt.sizers.FixedSize, stake=qty)

    # Add analyzers  
    crbr_opt.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')  
    crbr_opt.addanalyzer(bt.analyzers.Returns, _name='returns')  
    crbr_opt.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days, riskfreerate=daily_return)

    start_time = time.time()  
    # Run optimization  
    optimized_runs = crbr_opt.run(maxcpus=1)  
    end_time = time.time()  
    st.info(f"Optimization took {end_time - start_time} seconds")  

    # Collect results  
    results_list = []
    for run in optimized_runs:  
        for strategy in run:  
            params = get_params(strategy)
            sharpe_analyzer = strategy.analyzers.sharpe.get_analysis()  
            returns_analyzer = strategy.analyzers.returns.get_analysis()  
            drawdown_analyzer = strategy.analyzers.drawdown.get_analysis()  
            
            result_dict = {  
                    'strategy': params,
                    'sharpe_ratio': sharpe_analyzer['sharperatio'],  
                    'returns (%)': returns_analyzer['rtot']*100,  
                    'max_drawdown (%)': drawdown_analyzer['max']['drawdown']  
                }  
            results_list.append(result_dict)  
    results_df = pd.DataFrame(results_list) 
    results_df = results_df.sort_values('returns (%)',ascending=False).reset_index(drop=True)
    best_params = results_df['strategy'].iloc[0]
    best_params_dict = {key: value for key, value in best_params.items()}  
    st.success(f'\n Best parameter: {best_params_dict}')
    return results_df, best_params_dict