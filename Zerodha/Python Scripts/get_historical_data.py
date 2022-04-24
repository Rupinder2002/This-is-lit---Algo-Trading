# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 22:27:56 2022

@author: naman
"""

from IPython import get_ipython
get_ipython().magic('reset -sf') 

from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import pandas_ta as ta
import csv
import sqlite3
import warnings
import requests

warnings.filterwarnings("ignore")

cwd = os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')
# =============================================================================
# Generate trading session
# =============================================================================

access_token = open("access_token.txt",'r').read().rstrip()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

# =============================================================================
# Create function to fetch OHLC data
# =============================================================================

def tokenLookup(instrument_df,symbol_list):
    """Looks up instrument token for a given script from instrument dump"""
    token_list = []
    for symbol in symbol_list:
        token_list.append(int(instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]))
    return token_list

def tickerLookup(token):
    global instrument_df
    return instrument_df[instrument_df.instrument_token==token].tradingsymbol.values[0] 

def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1
        
def fetchOHLC(ticker,start_date,end_date,interval):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,start_date,end_date,interval))            
    return data

# =============================================================================
# Create function to implement the strategy
# =============================================================================

def sl_price(ohlc):
    """function to calculate stop loss based on ATR"""
    sl = 2 * ta.atr(ohlc['high'],ohlc['low'],ohlc['close'], 20)[-1]
    return round(sl,1)

def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

def strategy(ohlc):
    ohlc["VWAP"] = ta.vwap(ohlc['high'], ohlc['low'], ohlc['close'], ohlc['volume']).values
    ohlc[["stochrsik%","stochrsid%"]] = ta.stochrsi(ohlc['close'],length=14, rsi_length=14, k=3, d=3).values
    
    ohlc.loc[(ohlc['VWAP'] < ohlc['low']),'vwap_signal'] = 'buy'
    ohlc.loc[(ohlc['VWAP'] > ohlc['high']),'vwap_signal'] = 'sell'

    ohlc.loc[(ohlc['stochrsik%'] > ohlc['stochrsid%']),'srsi_signal'] = 'buy'
    ohlc.loc[(ohlc['stochrsik%'] < ohlc['stochrsid%']),'srsi_signal'] = 'sell'
    
    ohlc.loc[(ohlc['vwap_signal'] == 'buy') & (ohlc['srsi_signal'] == 'buy'), 'signal'] = 'buy'
    ohlc.loc[(ohlc['vwap_signal'] == 'sell') & (ohlc['srsi_signal'] == 'sell'), 'signal'] = 'sell'
    
    ohlc = ohlc[['open','high','low','close','volume','signal']]
    
    return ohlc

# =============================================================================
# Get dump of all NFO instruments
# =============================================================================

instrument_dump = kite.instruments()
instrument_df = pd.DataFrame(instrument_dump)

# =============================================================================
# Create DataFrame to store all orders
# =============================================================================

ord_df = pd.DataFrame(columns = ['timestamp','tradingsymbol','price', 'SL','Order','Reason'])
active_tickers = []

interval = 'minute'

# tickers = ['HDFCBANK','ICICIBANK','KOTAKBANK', 'AXISBANK', 'SBIN', 'RELIANCE','TCS','INFY','HINDUNILVR','HDFC','BAJFINANCE','WIPRO','BHARTIARTL','HCLTECH','ASIANPAINT','ITC','LT','ULTRACEMCO',
#             'MARUTI','SUNPHARMA','TATASTEEL','JSWSTEEL','TITAN','ADANIPORTS','ONGC','HDFCLIFE','TECHM','DIVISLAB','POWERGRID','SBILIFE','NTPC','BAJAJ-AUTO','BPCL','IOC','M&M','SHREECEM','HINDALCO',
#             'GRASIM','BRITANNIA','TATAMOTORS','COALINDIA','TATACONSUM','INDUSINDBK','DRREDDY','CIPLA','EICHERMOT','UPL','NESTLEIND','HEROMOTOCO']


tickers = ['BANKNIFTY22MAR36000CE','BANKNIFTY22MAR36000PE']
#tickers = ['HDFCBANK']
#=============================================================================
if interval == 'day':
    duration = 2000
elif interval == 'hour':
    duration = 365
elif interval == '30minute':
    duration = 180
elif interval == '10minute' or interval == '5minute' or interval == '3minute':
    duration = 90
elif interval == 'minute':
    duration = 30    
    
start_date = pd.to_datetime('2022-03-01 09:15')
begin_date = start_date
historical_df = pd.DataFrame()
while begin_date < dt.date.today():
    begin_date = pd.to_datetime(begin_date)
    end_date = begin_date + dt.timedelta(minutes = duration)
    end_date = pd.to_datetime(end_date)

    for ticker in tickers:
        print('Extraction for ',ticker,' from ',begin_date ,' to ',end_date)
        
        df = fetchOHLC(ticker = ticker ,interval  = interval ,start_date = begin_date,end_date = end_date)
        df['ticker'] = ticker
        historical_df = historical_df.append(df)
                
    begin_date = begin_date + dt.timedelta(minutes = duration)

# =============================================================================
# Write Historical Data to CSV
# =============================================================================
        
historical_df.sort_values(['ticker','date'], inplace = True)
historical_df['timestamp'] = historical_df['date']
historical_df['date'] = pd.to_datetime(historical_df['timestamp']).dt.date
historical_df.to_csv('Data/Tickers Historical Data.csv',index = False)

#=============================================================================
