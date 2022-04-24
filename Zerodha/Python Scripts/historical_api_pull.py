# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 17:30:05 2022

@author: naman
"""

from IPython import get_ipython
get_ipython().magic('reset -sf')

from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

cwd = os.getcwd()

strategy_name = 'BANKNIFTY ADX ST StochRSI'

# =============================================================================
# Generate trading session
# =============================================================================

access_token = open(os.path.join(cwd,"access_token.txt"),'r').read().rstrip()
key_secret = open(os.path.join(cwd,"api_key.txt"),'r').read().split()
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
        
def fetchOHLC(ticker,interval,startdate):
    """extracts historical data and outputs in the form of dataframe"""
    global enddate
    
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
    
    instrument = instrumentLookup(instrument_df,ticker)
    enddate = (pd.to_datetime(startdate) + dt.timedelta(days = duration)).date()
    data = pd.DataFrame(kite.historical_data(instrument,startdate, enddate, interval))
    data.set_index("date",inplace=True)
    return data

instrument_dump = kite.instruments()
instrument_df = pd.DataFrame(instrument_dump)
instrument_df = instrument_df[instrument_df['exchange'] == 'NSE']

tickers = ['HDFCBANK','ICICIBANK','KOTAKBANK', 'AXISBANK', 'SBIN', 'RELIANCE','TCS','INFY','HINDUNILVR','HDFC','BAJFINANCE','WIPRO','BHARTIARTL','HCLTECH','ASIANPAINT','ITC','LT','ULTRACEMCO',
            'MARUTI','SUNPHARMA','TATASTEEL','JSWSTEEL','TITAN','ADANIPORTS','ONGC','HDFCLIFE','TECHM','DIVISLAB','POWERGRID','SBILIFE','NTPC','BAJAJ-AUTO','BPCL','IOC','M&M','SHREECEM','HINDALCO',
            'GRASIM','BRITANNIA','TATAMOTORS','COALINDIA','TATACONSUM','INDUSINDBK','DRREDDY','CIPLA','EICHERMOT','UPL','NESTLEIND','HEROMOTOCO']

start_date = pd.to_datetime('2021-01-01').date()
df = fetchOHLC('NIFTY BANK', 'minute', start_date)
df['ticker'] = 'NIFTY BANK'
df = pd.DataFrame(columns = df.columns)

while start_date <= dt.date.today():
    print(start_date)
    for ticker in tickers:
        #print(ticker)
        hist_data = fetchOHLC(ticker, 'minute', start_date )
        hist_data['ticker'] = ticker
        df = df.append(hist_data)
    start_date  = enddate + dt.timedelta(days = 1)

df = df.reset_index()
df.columns = ['timestamp','open', 'high', 'low', 'close', 'volume', 'ticker']
df.to_csv('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading Material/Data/Historical Minute Data.csv',index = False)
