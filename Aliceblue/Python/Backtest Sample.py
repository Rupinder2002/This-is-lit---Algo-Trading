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

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

cwd = os.getcwd()

strategy_name = 'BANKNIFTY ADX ST StochRSI'

# =============================================================================
# Create function to implement the strategy
# =============================================================================

def strategy(ohlc):
    
    ohlc['VWAP'] = ta.vwap(ohlc['high'], ohlc['low'], ohlc['close'],ohlc['volume']).values
    ohlc[['VWAP_LC','close_LC','open_LC','high_LC']] = ohlc[['VWAP','close','open','high']].shift(1)
    
    ohlc.loc[(ohlc['close_LC'] > ohlc['VWAP_LC']) &
             (ohlc['open_LC'] < ohlc['VWAP_LC']) &
             (ohlc['close'] > ohlc['high_LC']),'signal'] = 'buy'
    
    ohlc = ohlc[['ticker','date','open','high','low','close','volume','signal']]
    ohlc['next_open'] = ohlc['open'].shift(-1)

    return ohlc

def run_strategy(row,ticker,sl_pct = 0.01):
    
    global ord_df
    global active_tickers
    global time_elapsed
    
    start_time = time.time()
    
    ticker_signal = row['signal']
    price = row['next_open']

    if ticker not in active_tickers:

        if ticker_signal == 'buy' and row.name.time() >= dt.time(9,15):
            reason = 'Both Indicators show green'
            #sl = ohlc['low'][-1] - sl_price(ohlc)
            sl = row['next_open'] * (1 - sl_pct)
            trade = pd.DataFrame([[row.name,ticker,price,sl,'buy',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.append(ticker)

    time_elapsed = time.time() - start_time

def place_sl_target_order(tick, ticker, target_pct = 0.02):
    
    global active_tickers
    global ord_df
    
    if ticker in active_tickers:
        
        last_trade = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]
        stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
        price = last_trade['price']

        if tick.name.hour == 15 and tick.name.minute == 15:
            if last_trade['Order'] == 'buy':
                reason = '3:15 Exit'
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

historical_df = pd.read_csv('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading Material/Data/Historical Minute Data.csv')

ticks = historical_df[historical_df['ticker'].isin(['INFY','RELIANCE'])]
#ticks = historical_df.copy()
ticks = ticks[['timestamp','open','high','low','close','volume','ticker']]
ticks['timestamp'] = pd.to_datetime(ticks['timestamp'])
ticks['date'] = pd.to_datetime(ticks['timestamp'],dayfirst=True).dt.date
ticks['time'] = pd.to_datetime(ticks['timestamp']).dt.time
ticks.set_index('timestamp',inplace = True)

# =============================================================================
# Resample Data
# =============================================================================

ohlc = ticks.groupby('ticker').resample('60min').agg({'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last'], 'volume' : ['sum']})  #check if M is minutes or months
ohlc.columns = ['open','high','low','close','volume']
ohlc.loc[ohlc['volume'] == 0,'volume'] = np.nan
ohlc.dropna(how = 'all',inplace = True)
ohlc = ohlc.reset_index()
ohlc['date'] = ohlc['timestamp'].dt.date
ohlc = ohlc.set_index('timestamp')
ticker_df = pd.DataFrame(columns=['ticker','date','open','high','low','close','volume','signal','next_open'])
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

min_date = pd.to_datetime('2022-01-01')
start_date = min_date.date()
max_date = pd.to_datetime(ohlc.index.max())

while start_date <= max_date.date():
    print(start_date)
    for ticker in tickers:
        #print(ticker)
        data = ticker_df[(ticker_df['date'] == start_date) & (ticker_df['ticker'] == ticker)]
        for index,row in data.iterrows():
            run_strategy(row,ticker)
            starttime = row.name
            endtime = starttime + dt.timedelta(minutes=60)
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
trade_df['pnl'] = trade_df['ltp'] + trade_df['new_price']
trade_df = trade_df[~trade_df['Reason'].str.contains('show')]

trade_df['Date'] = trade_df['timestamp'].dt.date

trade_df.loc[trade_df['pnl'] > 0,'streak'] = 1
trade_df.loc[trade_df['pnl'] < 0,'streak'] = -1


for ticker in tickers:
    print('Calculating metrics for: ', ticker)
    ticker_trade_df = trade_df[trade_df['tradingsymbol'] == ticker]
    grouper = (ticker_trade_df.streak != ticker_trade_df.streak.shift()).cumsum()
    ticker_trade_df['cum_streak'] = ticker_trade_df.groupby(grouper)['streak'].cumsum()
    
    average_price = abs(ticker_trade_df['ltp'].mean())
    
    print('Total Profit: ',str(round(sum(ticker_trade_df['pnl']),2)))
    print('PnL%: ' ,str(round(sum(ticker_trade_df['pnl'])/average_price * 100,2)))
    print('Total Number of Signals: ' + str(len(ticker_trade_df)))
    print('Total Number of Wins: ' + str(len(ticker_trade_df[ticker_trade_df['pnl']>0])))
    print('Total Number of Losses: ' + str(len(ticker_trade_df[ticker_trade_df['pnl']<0])))
    print('Winning Streak: ' + str(int(max(ticker_trade_df['cum_streak']))))
    print('Losing Streak: ' + str(abs(int(min(ticker_trade_df['cum_streak'])))))
    print('Max Gain: ' + str(round(max(ticker_trade_df['pnl']),2)))
    print('Max Loss: ' + str(round(min(ticker_trade_df['pnl']),2)))
    print('Avg gain/winning trade: ', str(round(ticker_trade_df[ticker_trade_df['pnl'] > 0]['pnl'].mean(),2)))
    print('Avg loss/losing trade: ', str(round(ticker_trade_df[ticker_trade_df['pnl'] < 0]['pnl'].mean(),2)))
