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


def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

def get_nfo_scripts(exchange,underlying_ticker,to_datetime):
        
    if 'NIFTY' in underlying_ticker.upper():
        index = True
    else:
        index = False
        
    if underlying_ticker == 'BANKNIFTY':
        underlying_ticker_ = 'Nifty Bank'
    elif underlying_ticker == 'NIFTY':
        underlying_ticker_ = 'Nifty 50'
    else:
        underlying_ticker_ = underlying_ticker
        
    df = fetchOHLC(alice.get_instrument_by_symbol(exchange,underlying_ticker_),5,to_datetime,'1_MIN',indices = index)

    except_today = df[df.index.date !=  dt.datetime.now().date()]
    max_date = max(except_today.index.date)

    last_day_data = except_today[except_today.index.date ==  max_date]

    close_avg = last_day_data['close'].mean()
    
    open_price = df[df.index.time == pd.to_datetime('9:15').time()]['open'][-1]
    
    if open_price > close_avg:
        is_CE = False
    elif open_price < close_avg:
        is_CE = True
        
    if exchange == 'NSE':
        instruments = alice.search_instruments('NFO',underlying_ticker)

    expiry = []
    strike_prices = []
    for instrument in instruments:
        if 'FUT' not in instrument.symbol:
            expiry.append(instrument.expiry)
            strike_prices.append(round(int(instrument.symbol.split(' ')[2].split('.')[0]),-1))
            
    strike = closest(strike_prices,close_avg)
    expiry = min(set(expiry))
    
    nfo = alice.get_instrument_for_fno(underlying_ticker, expiry, is_fut = False, strike = strike, is_CE = is_CE, exchange = 'NFO')
           
    return nfo.symbol,close_avg,int(nfo.lot_size)

alice = login()
ohlc = pd.DataFrame()

start_date = pd.to_datetime(dt.date.today())
max_date = (start_date + dt.timedelta(days=1)).date()
scrips = ['ADANIPORTS','APOLLOHOSP','ASIANPAINT','AXISBANK','BAJAJ-AUTO','BAJFINANCE',
          'BPCL','BHARTIARTL','BRITANNIA','CIPLA','COALINDIA','DIVISLAB',
          'DRREDDY','EICHERMOT','GRASIM','HCLTECH','HDFCBANK','HEROMOTOCO',
          'HINDUNILVR','ICICIBANK','ITC','INFY','JSWSTEEL',
          'KOTAKBANK','M&M','MARUTI','NESTLEIND','ONGC','POWERGRID','RELIANCE',
          'SBILIFE','SHREECEM','SUNPHARMA','TCS','TATAMOTORS',
          'TECHM','TITAN','UPL','ULTRACEMCO','WIPRO']

nfo_scrips_dict = {}
close_avg_dict = {}
lot_size_dict = {}

while start_date <= max_date:
    print('\n')
    print(start_date)
    print('Data Extracting for: \n')
    
    try:
        for scrip in scrips:
            
            print(scrip)
            
            detail = get_nfo_scripts(exchange = 'NSE',underlying_ticker = scrip,to_datetime = start_date)

            if detail[0] != '':
                
                nfo_scrips_dict[scrip] = detail[0]
                close_avg_dict[scrip] = detail[1]
                lot_size_dict[scrip] = detail[2]
                
                instrument = alice.get_instrument_by_symbol('NFO', nfo_scrips_dict[scrip])
                instrument_underlying = alice.get_instrument_by_symbol('NSE', scrip)
                try:
                    df_underlying = fetchOHLC(instrument_underlying, 1, start_date, interval)
                    df = fetchOHLC(instrument, 1, start_date, interval)
                except:
                    print('Passing scrip: ', scrip)
                    continue
                
                df['date_'] = df.index.date
                total_vol = df.groupby('date_',as_index = False)['volume'].sum()
                total_vol = total_vol[total_vol['volume']>100000]
                df = df[df['date_'].isin(total_vol['date_'].tolist())]
                df = df.drop('date_',axis = 1)
                df['ticker'] = nfo_scrips_dict[scrip]
                df['lot_size'] = lot_size_dict[scrip]
                df['underlying_ticker'] = scrip
                df['close_avg'] = close_avg_dict[scrip]
                
                df = df.merge(df_underlying['close'],right_index = True, left_index = True)
                
                if len(df) > 0:
                    ohlc = ohlc.append(df)
    except:
        print('Holiday, Skipping')
            
    start_date = start_date + dt.timedelta(days=1)


ohlc = ohlc.reset_index()
ohlc = ohlc.rename({'date':'timestamp','close_x':'close','close_y':'close_underlying'},axis = 1)
ohlc.to_csv('Option Minute Data.csv',index=False)