# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 23:40:05 2022

@author: naman
"""

# =============================================================================
# Load Credentials
# =============================================================================
from IPython import get_ipython
get_ipython().magic('reset -sf') 

import requests
from alice_blue import AliceBlue
import datetime as dt
import pandas as pd
import os

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading/Aliceblue')
cwd = os.getcwd()

interval = "1_MIN"   # ["DAY", "1_HR", "3_HR", "1_MIN", "5_MIN", "15_MIN", "60_MIN"]

username = open('Credentials/alice_username.txt','r').read()
password = open('Credentials/alice_pwd.txt','r').read()
twoFA = open('Credentials/alice_twoFA.txt','r').read()
api_key = open('Credentials/api_key_alice.txt','r').read()
api_secret = open('Credentials/api_secret_alice.txt','r').read()
socket_opened = False

def login():
    
    access_token = AliceBlue.login_and_get_access_token(username = username, password = password, twoFA = twoFA, api_secret = api_secret, app_id = api_key)   
    alice = AliceBlue(username=username, password=password,access_token=access_token, master_contracts_to_download=['MCX', 'NSE', 'CDS','NFO'])
   
    return alice

def fetchOHLC(instrument, days, to_datetime, interval, indices=False):
    
    from_datetime = to_datetime - dt.timedelta(days = days)
    
    if instrument.exchange == 'NFO':
        exchange = instrument.exchange
    elif indices:
        exchange = 'NSE_INDICES'
    else:
        exchange = instrument.exchange
    
    params = {"token": instrument.token,
              "exchange": exchange,
              "starttime": str(int(from_datetime.timestamp())),
              "endtime": str(int(to_datetime.timestamp())),
              "candletype": 3 if interval.upper() == "DAY" else (2 if interval.upper().split("_")[1] == "HR" else 1),
              "data_duration": None if interval.upper() == "DAY" else interval.split("_")[0]}

    lst = requests.get(" https://ant.aliceblueonline.com/api/v1/charts/tdv?", params=params).json()["data"]["candles"]
    records = []
    for i in lst:
        record = {"date": pd.to_datetime(i[0]), "open": i[1], "high": i[2], "low": i[3], "close": i[4], "volume": i[5]}
        records.append(record)
    
    df = pd.DataFrame(records)
    df = df.set_index("date")
    
    return df

def get_nfo_scripts(exchange,underlying_ticker,to_datetime):
    
    open_price = fetchOHLC(alice.get_instrument_by_symbol(exchange,underlying_ticker),1,to_datetime,'DAY',indices = True)['open'].values[0]
    strike_price = round(open_price,-2)
    s1 = strike_price + 500
    s2 = strike_price - 500
    s3 = strike_price + 300
    s4 = strike_price - 300
    s5 = strike_price + 700
    s6 = strike_price - 700
    
    nfo = []
    if exchange == 'NSE':
        instruments = alice.search_instruments('NFO','BANKNIFTY')
        
    for instrument in instruments:
        if ((str(s1) in instrument.symbol) | (str(s2) in instrument.symbol) |
            (str(s3) in instrument.symbol) | (str(s4) in instrument.symbol) |
            (str(s5) in instrument.symbol) | (str(s6) in instrument.symbol)) and instrument.expiry.month  == 4:
            nfo.append(instrument.symbol)
            
    return nfo

alice = login()
ohlc = pd.DataFrame()

start_date = pd.to_datetime('2022-04-13')
max_date = pd.to_datetime('2022-04-23')

while start_date <= max_date:
    print(start_date)
    try:
        NFO_SCRIP_LIST = get_nfo_scripts(exchange = 'NSE',underlying_ticker = 'Nifty Bank', to_datetime = start_date)
            
        for nfo_scrip in NFO_SCRIP_LIST:
            print(nfo_scrip)
            instrument = alice.get_instrument_by_symbol('NFO', nfo_scrip)
            df = fetchOHLC(instrument, 1, start_date, interval)
            df['date_'] = df.index.date
            total_vol = df.groupby('date_',as_index = False)['volume'].sum()
            total_vol = total_vol[total_vol['volume']>100000]
            df = df[df['date_'].isin(total_vol['date_'].tolist())]
            df = df.drop('date_',axis = 1)
            df['ticker'] = nfo_scrip
            if len(df) > 0:
                ohlc = ohlc.append(df)
    except:
        print('Holiday, Skipping')
            
    start_date = start_date + dt.timedelta(days=1)

ohlc = ohlc.reset_index()
ohlc = ohlc.rename({'date':'timestamp'},axis = 1)
ohlc.to_csv('Option Minute Data.csv',index=False)
