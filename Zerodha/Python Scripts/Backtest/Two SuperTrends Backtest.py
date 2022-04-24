# -*- coding: utf-8 -*-
"""
Created on Sat Mar 12 01:01:47 2022

@author: naman
"""
#2 Super Trends 10,0.8 and 10,1.6 on 5 min candle
from IPython import get_ipython
get_ipython().magic('reset -sf') 

from kiteconnect import KiteTicker,KiteConnect
import pandas as pd
import datetime as dt
import os
import pandas_ta as ta
import sys

cwd = os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get dump of all NSE instruments
instrument_dump = kite.instruments()
instrument_df = pd.DataFrame(instrument_dump)

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
        
def fetchOHLC(ticker,interval,days):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(days), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data

def fetchOHLC_LastCandle(ticker,interval,minutes):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.datetime.today()-dt.timedelta(minutes = minutes), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data

def sl_price(ohlc):
    """function to calculate stop loss based on supertrends"""
    sl = ohlc['st1'][-1]
    return round(sl,1)

#####################update ticker list######################################
ticker = 'BANKNIFTY2231734300CE'
p1 = 10
p2 = 10
m1 = 0.8
m2 = 1.6
ohlc = fetchOHLC(ticker = ticker,interval = "2minute",days = 4)
st1 = ta.supertrend(ohlc['high'],ohlc['low'],ohlc['close'],p1,m1)
st2 = ta.supertrend(ohlc['high'],ohlc['low'],ohlc['close'],p2,m2)
ohlc["st1"] = st1['SUPERT_' + str(p1) + '_' + str(float(m1))]
ohlc["st2"] = st2['SUPERT_' + str(p2) + '_' + str(float(m2))]            
ohlc["st1_color"] = st1['SUPERTd_' + str(p1) + '_' + str(float(m1))]
ohlc["st2_color"] = st2['SUPERTd_' + str(p2) + '_' + str(float(m2))]
ohlc.loc[(ohlc['st1_color'] == -1) & (ohlc['st2_color'] == -1),'signal'] = 'sell'
ohlc.loc[(ohlc['st1_color'] == 1) & (ohlc['st2_color'] == 1),'signal'] = 'buy'