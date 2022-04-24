# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 22:27:56 2022

@author: naman
"""

#2 Super Trends 10,0.8 and 10,1.6 on 2 mins candle
from IPython import get_ipython
get_ipython().magic('reset -sf') 

from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import pandas_ta as ta
import csv
import sqlite3

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
        
def fetchOHLC(ticker,interval,days,timestamp):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(days), timestamp,interval))
    data.set_index("date",inplace=True)
    return data


# =============================================================================
# Create function to implement the strategy
# =============================================================================

def sl_price(ohlc):
    """function to calculate stop loss based on supertrends"""
    sl = 0.4 * ohlc['st1'][-1] + 0.6 * ohlc['st2'][-1]
    return round(sl,1)

def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

def write_rows_csv(row):
  with open (filename, "a", newline = "") as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow(row)    

def run_strategy(timestamp,tickers):
    global ord_df
    global active_tickers
    
    for ticker in tickers:
        print("Startegy Running at {} On: {}".format(timestamp ,ticker))
        
        try:
            ohlc = fetchOHLC(ticker = ticker,interval = "10minute",days = 6,timestamp = timestamp)
            st1 = ta.supertrend(ohlc['high'],ohlc['low'],ohlc['close'],p1,m1)
            st2 = ta.supertrend(ohlc['high'],ohlc['low'],ohlc['close'],p2,m2)
            ohlc["st1"] = st1['SUPERT_' + str(p1) + '_' + str(float(m1))]
            ohlc["st2"] = st2['SUPERT_' + str(p2) + '_' + str(float(m2))]            
            ohlc["st1_color"] = st1['SUPERTd_' + str(p1) + '_' + str(float(m1))]
            ohlc["st2_color"] = st2['SUPERTd_' + str(p2) + '_' + str(float(m2))]
            ohlc.loc[(ohlc['st1_color'] == -1) & (ohlc['st2_color'] == -1),'signal'] = 'sell'
            ohlc.loc[(ohlc['st1_color'] == 1) & (ohlc['st2_color'] == 1),'signal'] = 'buy'
            
            price = ohlc['close'][-1]

            if ticker not in active_tickers:

                if ohlc.iloc[-1]['signal'] == 'buy':
                    reason = 'Both SuperTrend lines green'
                    trade = pd.DataFrame([[timestamp,ticker,price,sl_price(ohlc) * 1.001,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    print("buy order placed at {} for {}".format(timestamp.time(),ticker))
                    
                if ohlc.iloc[-1]['signal'] == 'sell':
                    reason = 'Both SuperTrend lines red'
                    trade = pd.DataFrame([[timestamp,ticker,price,sl_price(ohlc) * 0.999,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])                    
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    print("sell order placed at {} for {}".format(timestamp,ticker))
                    
            else:
                
                order = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
                
                if order['Order'] == 'buy':
                    
                    if ohlc.iloc[-1]['signal'] == 'sell':
                        reason = 'Both SuperTrend lines reversed red'
                        trade = pd.DataFrame([[timestamp,ticker,price,None,'sell',reason]],columns = ord_df.columns)
                        ord_df = pd.concat([ord_df,trade])                    
                        active_tickers.remove(ticker)
                        print("Position Squared Off at {} for {} by placing Sell Order".format(timestamp,ticker))
        
                    else:
                        reason = 'Order Modified'
                        sl = sl_price(ohlc) * 1.001
                        trade = pd.DataFrame([[timestamp,ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                        ord_df = pd.concat([ord_df,trade])
                        print("Order Modified at {} for {}".format(timestamp,ticker))
                        
                    write_rows_csv(row = trade.iloc[0].tolist())  
                   
                if order['Order'] == 'sell':
                
                    if ohlc.iloc[-1]['signal'] == 'buy':
                        reason = 'Both SuperTrend lines reversed green'
                        trade = pd.DataFrame([[timestamp,ticker,price,None,'buy',reason]],columns = ord_df.columns)
                        ord_df = pd.concat([ord_df,trade])
                        active_tickers.remove(ticker)
                        print("Position Squared Off at {} for {} by placing Buy Order".format(timestamp,ticker))
                        
                    else:
                        reason = 'Order Modified'
                        sl = sl_price(ohlc) * 0.999
                        trade = pd.DataFrame([[timestamp,ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                        ord_df = pd.concat([ord_df,trade])
                        print("Order Modified at {} for {}".format(timestamp,ticker))
                        
                    write_rows_csv(row = trade.iloc[0].tolist())  
                    
        except:
            print("API error for ticker :",ticker)
     
    
def place_sl_hit_order(current_price,ticker,timestamp):
    
    global active_tickers
    global ord_df
        
    if ticker in active_tickers:
        last_trade = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
        stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
        if timestamp.hour == 15 and timestamp.minute == 20:
            if last_trade['Order'] == 'sell':
                reason = '3:20 Exit'
                trade = pd.DataFrame([[timestamp,ticker,current_price,None,'buy',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
                print("Position squared off at 3.20 for {}".format(ticker))
                
            elif last_trade['Order'] == 'buy':
                reason = '3:20 Exit'
                trade = pd.DataFrame([[timestamp,ticker,current_price,None,'sell',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
                print("Position squared off at 3.20 for {}".format(ticker))
            
        elif last_trade['Order'] == 'buy' and current_price <= stop_loss:
            reason = 'Stop Loss Hit'
            trade = pd.DataFrame([[timestamp,ticker,current_price,None,'sell',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)
            print("SL Hit for {}".format(ticker))
            
        elif last_trade['Order'] == 'sell' and current_price >= stop_loss:
            reason = 'Stop Loss Hit'
            trade = pd.DataFrame([[timestamp,ticker,current_price,None,'buy',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)
            print("SL Hit for {}".format(ticker))
                
def get_hist(ticker,db):
    token = instrumentLookup(instrument_df,ticker)
    data = pd.read_sql('''SELECT * FROM TOKEN%s;''' %token, con=db)                
    data = data.set_index(['ts'])
    data.index = pd.to_datetime(data.index)
    #ticks = data.loc[:, ['price']]   
    #df=ticks['price'].resample('1min').ohlc().dropna()
    return data

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

# =============================================================================
# Select tickers to run the strategy on
# =============================================================================

#Get SpotPrice
spot_ohlc = kite.quote("NSE:NIFTY BANK")["NSE:NIFTY BANK"]["ohlc"]
strike = spot_ohlc["open"]

df = instrument_df[(instrument_df["segment"] == "NFO-OPT") & (instrument_df["name"] == "BANKNIFTY")]

#Select closest expiry contracts 
df = df[df["expiry"] == sorted(list(df["expiry"].unique()))[0]]

#Select contracts based on closest Strike Price to the Spot Price
df = df[df["strike"] == float(closest(list(df["strike"]),strike))].reset_index(drop = True)

#Get the Trading Symbol and Lot size
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

#Create list of Options
tickers = ['BANKNIFTY2231736300CE','BANKNIFTY2231736300PE']

# =============================================================================
# Initinalize variables
# =============================================================================

p1 = 10
p2 = 10
m1 = 1
m2 = 2

filename = 'Order Book ' + str(dt.datetime.now().date()) + '.csv'
header = ord_df.columns

with open (filename, "w", newline="") as csvfile:
    order_book = csv.writer(csvfile)
    order_book.writerow(header)

# =============================================================================
# Create live connection to Kite
# =============================================================================

tokens = tokenLookup(instrument_df,tickers)

db = sqlite3.connect('ticks.db')

ticks = pd.DataFrame()
for ticker in tickers:
    tick = get_hist(ticker,db)
    tick['ticker'] = ticker
    ticks = pd.concat([ticks,tick])
# =============================================================================
# Deploy the startegy to run every 10 mins
# =============================================================================
start_minute = dt.datetime(2022,3,17,9,15)

bands = pd.date_range("09:15", "15:30", freq="10min")
for i in range(len(bands)-1):
    print(bands[i])
    run_strategy(timestamp = bands[i], tickers = tickers)
    starttime = bands[i]
    endtime = bands[i+1]
    ticks_filtered = ticks[(ticks.index>starttime) & (ticks.index < endtime)]
    for ticker in tickers:
        tick_ticker = ticks_filtered[ticks_filtered['ticker'] == ticker]
        for index in tick_ticker.index:
            current_price = tick_ticker['price'][index]
            place_sl_hit_order(current_price = current_price,ticker = ticker,timestamp = index)
    

