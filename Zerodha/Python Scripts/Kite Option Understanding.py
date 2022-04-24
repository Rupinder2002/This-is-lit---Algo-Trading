# -*- coding: utf-8 -*-
"""
Created on Sat Mar 12 04:06:59 2022

@author: naman
"""
from IPython import get_ipython
get_ipython().magic('reset -sf') 

from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import time
import pandas_ta as ta

cwd = os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
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

def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

instrument_dump = kite.instruments()
instrument_df = pd.DataFrame(instrument_dump)

spot_ohlc = kite.quote("NSE:NIFTY BANK")["NSE:NIFTY BANK"]["ohlc"]
strike = spot_ohlc["open"]

df = instrument_df[(instrument_df["segment"] == "NFO-OPT") &
                (instrument_df["name"] == "BANKNIFTY")]

df = df[df["expiry"] == sorted(list(df["expiry"].unique()))[0]]

df = df[df["strike"] == float(closest(list(df["strike"]),strike))].reset_index(drop = True)

lot_size = None
for i in df.index:
    if lot_size is None:
        lot_size = df["lot_size"][i]
        print(f"Lot size : {lot_size}")
    if df["instrument_type"][i] == "CE":
        opt_ce_symbol = df["tradingsymbol"][i]
        print(f'Opt Symbol added : {df["tradingsymbol"][i]}')
    elif df["instrument_type"][i] == "PE":
        opt_pe_symbol = df["tradingsymbol"][i]
        print(f'Opt Symbol added : {df["tradingsymbol"][i]}')

data = kite.ltp([f"NFO:{opt_ce_symbol}", f"NFO:{opt_pe_symbol}"])

for symbol, values in data.items():
    if symbol[4:] == opt_ce_symbol:
        opt_ce_ltp = values["last_price"]
    if symbol[4:] == opt_pe_symbol:
        opt_pe_ltp = values["last_price"]
        
        
        