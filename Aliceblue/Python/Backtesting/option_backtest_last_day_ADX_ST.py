# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 15:50:41 2022
@author: naman
"""

from IPython import get_ipython
get_ipython().magic('reset -sf')

import pandas as pd
import numpy as np
import datetime as dt
import os
import time
import pandas_ta as ta
import warnings
warnings.filterwarnings('ignore')

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading/Aliceblue')

cwd = os.getcwd()

strategy_name = 'BANKNIFTY ADX ST StochRSI'

# =============================================================================
# Create function to implement the strategy
# =============================================================================

def strategy(ohlc):
    
    ohlc['ADX_14'] = ta.adx(ohlc['high'], ohlc['low'], ohlc['close'])['ADX_14']
    ohlc[['DMP','DMN']] = ta.dm(ohlc['high'], ohlc['low'])
    ohlc[['ADX_lc','DMP_lc','DMN_lc']] = ohlc[['ADX_14','DMP','DMN']].shift(1)
    
    ohlc.loc[(ohlc['ADX_14'] > ohlc['DMN']) & (ohlc['ADX_lc'] <= ohlc['DMN_lc']),'ADX_Signal'] = 'buy'
    ohlc['ST_Signal'] = ta.supertrend(ohlc['high'], ohlc['low'], ohlc['close'],length = 7, multiplier=3)['SUPERTd_7_3.0']

    ohlc.loc[(ohlc['ADX_Signal'] == 'buy') & (ohlc['ST_Signal'] == 1), 'signal'] = 'buy'
    
    ohlc.loc[(ohlc['DMP'] > ohlc['DMN']) & (ohlc['DMP_lc'] < ohlc['DMN_lc']),'exit_signal'] = 'sell'    
    ohlc = ohlc[['ticker','date','open','high','low','close','volume','signal','exit_signal']]
    ohlc['next_open'] = ohlc['open'].shift(-1)

    return ohlc

def run_strategy(row,ticker,sl_pct = 0.2):
    
    global ord_df
    global active_tickers
    global time_elapsed
    
    start_time = time.time()
    
    ticker_signal = row['signal']
    price = row['next_open']

    if ticker not in active_tickers:

        if ticker_signal == 'buy' and row.name.time() >= dt.time(9,15) and row.name.time() < dt.time(14,0):
            reason = 'Both Indicators show green'
            #sl = ohlc['low'][-1] - sl_price(ohlc)
            sl = row['next_open'] * (1 - sl_pct)
            trade = pd.DataFrame([[row.name,ticker,price,sl,'buy',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.append(ticker)
            
        elif ticker in active_tickers and row.exit_signal == 'sell':
            
            #placeOrder(ticker, 'sell', quantity)
            reason = 'Exit'
            trade = pd.DataFrame([[dt.datetime.now(),ticker,price,None,'buy',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)

    time_elapsed = time.time() - start_time

def place_sl_target_order(tick, ticker, target_pct = 0.5):
    
    global active_tickers
    global ord_df
    
    if ticker in active_tickers:
        
        last_trade = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]
        stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
        price = last_trade['price']

        if tick.name.hour == 15 and tick.name.minute == 9:
            if last_trade['Order'] == 'buy':
                reason = '3:09 Exit'
                trade = pd.DataFrame([[tick.name,ticker,tick['close'],None,'sell',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
            
        elif last_trade['Order'] == 'buy' and tick['low'] <= stop_loss:
            reason = 'Stop Loss Hit'
            trade = pd.DataFrame([[tick.name,ticker,stop_loss,None,'sell',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)
            
        elif last_trade['Order'] == 'buy' and tick['high'] >= (price * (1 + target_pct)):
            reason = 'Target Achieved'
            trade = pd.DataFrame([[tick.name,ticker,(price * (1 + target_pct)),None,'sell',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)                


# =============================================================================
# Read Data
# =============================================================================

ord_df = pd.DataFrame(columns = ['timestamp','tradingsymbol','price', 'SL','Order','Reason'])

historical_df = pd.read_csv('Option Minute Data.csv')

#ticks = historical_df[historical_df['ticker'].isin(['INFY','RELIANCE'])]
ticks = historical_df.copy()
ticks = ticks[['timestamp','open','high','low','close','volume','ticker']]
ticks['timestamp'] = pd.to_datetime(ticks['timestamp'])
ticks['date'] = pd.to_datetime(ticks['timestamp'],dayfirst=True).dt.date
ticks['time'] = pd.to_datetime(ticks['timestamp']).dt.time
ticks.set_index('timestamp',inplace = True)

# =============================================================================
# Resample Data
# =============================================================================

ohlc = ticks.groupby('ticker').resample('5min').agg({'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last'], 'volume' : ['sum']})  #check if M is minutes or months
ohlc.columns = ['open','high','low','close','volume']
ohlc.loc[ohlc['volume'] == 0,'volume'] = np.nan
ohlc.dropna(how = 'all',inplace = True)
ohlc = ohlc.reset_index()
ohlc['date'] = ohlc['timestamp'].dt.date
ohlc = ohlc.set_index('timestamp')
ohlc['volume'] = ohlc['volume'].fillna(0)

ticker_df = pd.DataFrame(columns=['ticker','date','open','high','low','close','volume','signal','exit_signal','next_open'])
tickers = sorted(ticks['ticker'].drop_duplicates().values.tolist())

# =============================================================================
# Apply Strategy
# =============================================================================

for ticker in tickers:
    print(ticker)
    a = ohlc[ohlc['ticker'] == ticker]
    ticker_df = ticker_df.append(strategy(a))

active_tickers = []

# =============================================================================
# Set to run the strategy
# =============================================================================

min_date = pd.to_datetime('2022-04-26')
start_date = min_date.date()
max_date = pd.to_datetime(ohlc.index.max())

while start_date <= max_date.date():
    print(start_date)
    previous_buy = {}

    for ticker in tickers:
        previous_buy[ticker] = False
        #print(ticker)
        data = ticker_df[(ticker_df['date'] == start_date) & (ticker_df['ticker'] == ticker)]
        if len(data)>0:
            for index,row in data.iterrows():
                run_strategy(row,ticker)
                starttime = row.name
                endtime = starttime + dt.timedelta(minutes=5)
                ticks_filtered = ticks[(ticks.index > starttime) & (ticks.index < endtime) & (ticks['ticker'] == ticker)]
                for index_1,row_1 in ticks_filtered.iterrows():
                    place_sl_target_order(row_1,ticker)

    start_date = start_date + dt.timedelta(days=1)

# =============================================================================
# Calculate Profit
# =============================================================================
    
ads = ord_df[ord_df['Order']!='Modify']
print(ads.Reason.value_counts())

ord_df1 = ord_df.reset_index(drop = True)
trade_df = ord_df1[(ord_df1['Order']!='Modify')].reset_index(drop = True)
trade_df.loc[trade_df['Order'] == 'buy','new_price'] = -1 * trade_df['price']
trade_df.loc[trade_df['Order'] == 'sell','new_price'] = 1 * trade_df['price']
trade_df['ltp'] = trade_df.groupby('tradingsymbol')['new_price'].shift(1)
trade_df['pnl'] = (trade_df['ltp'] + trade_df['new_price'])
trade_df = trade_df[~trade_df['Reason'].str.contains('show')]

trade_df['Date'] = trade_df['timestamp'].dt.date

trade_df.loc[trade_df['pnl'] > 0,'streak'] = 1
trade_df.loc[trade_df['pnl'] < 0,'streak'] = -1
trade_df.loc[trade_df['pnl'] == 0,'streak'] = 0

summary = pd.DataFrame(columns = ['ticker','Total Profit','PnL%','Total Number of Signals',
                                  'Total Number of Wins','Total Number of Losses','Winning Streak',
                                  'Losing Streak','Max Gain','Max Loss','Avg gain/winning trade','Avg loss/losing trade'])

for ticker in tickers:
    #print('Calculating metrics for: ', ticker)
    ticker_trade_df = trade_df[trade_df['tradingsymbol'] == ticker]
    if len(ticker_trade_df)!=0:
        grouper = (ticker_trade_df.streak != ticker_trade_df.streak.shift()).cumsum()
        ticker_trade_df['cum_streak'] = ticker_trade_df.groupby(grouper)['streak'].cumsum()
        
        average_price = abs(ticker_trade_df['ltp'].mean())
        
        total_profit = round(sum(ticker_trade_df['pnl'] * 25),2)
        pnl_pct = round(sum(ticker_trade_df['pnl'])/average_price * 100,2)
        no_of_signals = len(ticker_trade_df)
        no_of_wins = len(ticker_trade_df[ticker_trade_df['pnl']>0])
        no_of_losses = len(ticker_trade_df[ticker_trade_df['pnl']<0])
        winning_streak = int(max(ticker_trade_df['cum_streak']))
        losing_streak = int(min(ticker_trade_df['cum_streak']))
        max_gain = round(max(ticker_trade_df['pnl'] * 25),2)
        max_loss = round(min(ticker_trade_df['pnl'] * 25),2)
        avg_gain_per_win = round(ticker_trade_df[ticker_trade_df['pnl'] > 0]['pnl'].mean() * 25,2)
        avg_loss_per_win = round(ticker_trade_df[ticker_trade_df['pnl'] < 0]['pnl'].mean() * 25,2)
        
        ticker_summary = pd.DataFrame([[ticker,total_profit,pnl_pct,no_of_signals,no_of_wins,
                                       no_of_losses,winning_streak,losing_streak,max_gain,
                                       max_loss,avg_gain_per_win,avg_loss_per_win]],
                                      columns = summary.columns.tolist())
        
        summary = summary.append(ticker_summary)


print('Total Profit: ',sum(summary['Total Profit']))
print('Total Profit Per Day: \n',trade_df.groupby('Date')['pnl'].sum() * 25)
