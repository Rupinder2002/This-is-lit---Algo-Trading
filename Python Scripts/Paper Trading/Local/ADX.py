# -*- coding: utf-8 -*-
"""
Created on Sun Mar 20 23:37:57 2022

@author: naman
"""

from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import pandas as pd
import datetime as dt
import os
import pandas_ta as ta
import time
import csv
import sqlite3
import warnings
warnings.filterwarnings("ignore")

#os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')
cwd = os.getcwd()
strategy_name = 'BANKNIFTY VWAP StochRSI'
print(cwd)

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
        
def fetchOHLC(ticker,interval,days):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(days), dt.datetime.now(),interval))
    data = data[:-1]
    data.set_index("date",inplace=True)
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

def write_rows_csv(row):
  with open (filename, "a", newline = "") as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow(row)    

def strategy(ohlc,ohlc1):
    ohlc1['ADX_14'] = ta.adx(ohlc1['high'],ohlc1['low'],ohlc1['close'])['ADX_14']
    
    ohlc = ohlc.merge(ohlc1[['ADX_14']],left_index = True, right_index = True, how = 'left')
    ohlc['ADX_14'] = ohlc['ADX_14'].fillna(method = 'ffill')
    
    ohlc["VWAP"] = ta.vwap(ohlc['high'], ohlc['low'], ohlc['close'], ohlc['volume']).values
    ohlc[["stochrsik%","stochrsid%"]] = ta.stochrsi(ohlc['close']).values
    
    ohlc.loc[(ohlc['VWAP'] < ohlc['low']),'vwap_signal'] = 'buy'
    ohlc.loc[(ohlc['VWAP'] > ohlc['high']),'vwap_signal'] = 'sell'
    
    ohlc.loc[(ohlc['stochrsik%'] > ohlc['stochrsid%']),'srsi_signal'] = 'buy'
    ohlc.loc[(ohlc['stochrsik%'] < ohlc['stochrsid%']),'srsi_signal'] = 'sell'
    
    ohlc.loc[(ohlc['vwap_signal'] == 'buy') & (ohlc['srsi_signal'] == 'buy'), 'signal'] = 'buy'
    ohlc.loc[(ohlc['vwap_signal'] == 'sell') & (ohlc['srsi_signal'] == 'sell'), 'signal'] = 'sell'
    
    ohlc = ohlc[['open','high','low','close','volume','signal']]
    
    return ohlc


def run_strategy():
    global ord_df
    global active_tickers
    global time_elapsed
    global ticks
    
    start_time = time.time()
    
    for ticker in tickers:
        
        try:
            ohlc = fetchOHLC(ticker = ticker,interval = "5minute",days = 6)
            ohlc1 = fetchOHLC(ticker = ticker,interval = "15minute",days = 14)
            ohlc = strategy(ohlc,ohlc1)
            
            price_dict = kite.ltp(tokenLookup(instrument_df,[ticker]))
            price = price_dict[str(tokenLookup(instrument_df,[ticker])[0])]['last_price']

            if ticker not in active_tickers:

                if ohlc.iloc[-1]['signal'] == 'buy':
                    reason = 'Both Indicators show green'
                    sl = ohlc['low'][-1] - sl_price(ohlc)
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    print("buy order placed at {} for {}".format(dt.datetime.now().time(),ticker))
                    
                if ohlc.iloc[-1]['signal'] == 'sell':
                    reason = 'Both Indicators show red'
                    sl = ohlc['close'][-1] + sl_price(ohlc)
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])                    
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    print("sell order placed at {} for {}".format(dt.datetime.now().time(),ticker))
                    
            else:
                
                order = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
                
                if order['Order'] == 'buy':
                    
                    reason = 'Order Modified'
                    
                    if price > ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['price']:
                        sl = ohlc['low'][-1] - sl_price(ohlc)
                    else:
                        sl = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                        
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])    
                    write_rows_csv(row = trade.iloc[0].tolist())  
                    
                elif order['Order'] == 'sell':
                
                    reason = 'Order Modified'
                    
                    if price < ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['price']:
                        sl = ohlc['close'][-1] + sl_price(ohlc)
                    else:
                        sl = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                        
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])                        
                    write_rows_csv(row = trade.iloc[0].tolist())  
                    
        except Exception as e:
            print("API error for ticker :",ticker)
            print(e)
     
    time_elapsed = time.time() - start_time
    
    
def place_sl_target_order(ticks,target_pct = 0.5):
    
    global active_tickers
    global ord_df
    global tick
    
    sql = db.cursor()
    
    for tick in ticks:
        try:

            ticker = tickerLookup(int(tick['instrument_token']))
            
            if ticker in active_tickers:
                last_trade = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
                stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                price = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['price']
                if dt.datetime.now().hour == 15 and dt.datetime.now().minute == 16:
                    if last_trade['Order'] == 'sell':
                        reason = '3:16 Exit'
                        trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'buy',reason]],columns = ord_df.columns)
                        ord_df = pd.concat([ord_df,trade])
                        active_tickers.remove(ticker)
                        print("Position squared off at 3.16 for {}".format(ticker))
                        
                    elif last_trade['Order'] == 'buy':
                        reason = '3:16 Exit'
                        trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                        ord_df = pd.concat([ord_df,trade])
                        active_tickers.remove(ticker)
                        print("Position squared off at 3.16 for {}".format(ticker))
                    
                elif last_trade['Order'] == 'buy' and tick['last_price'] <= stop_loss:
                    reason = 'Stop Loss Hit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    print("SL Hit at {} for {}".format(dt.datetime.now().time(),ticker))
                    
                elif last_trade['Order'] == 'buy' and tick['last_price'] >= price * (1 + target_pct):
                    reason = 'Target Achieved'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    print("Target Achieved at {} for {}".format(dt.datetime.now().time(),ticker))
                    
                elif last_trade['Order'] == 'sell' and tick['last_price'] >= stop_loss:
                    reason = 'Stop Loss Hit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    print("SL Hit at {} for {}".format(dt.datetime.now().time(),ticker))
                    
                elif last_trade['Order'] == 'sell' and tick['last_price'] <= price * (1 - target_pct):
                    reason = 'Target Achieved'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    print("Target Achieved at {} for {}".format(dt.datetime.now().time(),ticker))
        except Exception as e:
            print(e)
            pass               
        
        try:
            tok = "TOKEN"+str(tick['instrument_token'])
            vals = [tick['exchange_timestamp'],tick['last_price']]
            query = "INSERT INTO {}(ts,price) VALUES (?,?)".format(tok)
            sql.execute(query,vals)
        except:
            pass
        
    try:
        db.commit()
    except:
        db.rollback()    

def on_ticks(ws,ticks):       
    global start_minute
    place_sl_target_order(ticks)
    now_minute = dt.datetime.now().minute    
    if abs(now_minute - start_minute) >= 5:
        start_minute = now_minute
        run_strategy()

def on_connect(ws,response):
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL,tokens)

def create_tables(tokens):
    sql = db.cursor()
    for i in tokens:
        sql.execute("CREATE TABLE IF NOT EXISTS TOKEN{} (ts datetime primary key,price real(15,5))".format(i))
    try:
        db.commit()
    except:
        db.rollback()

# =============================================================================
# Get dump of all NFO instruments
# =============================================================================

instrument_dump = kite.instruments()
instrument_df = pd.DataFrame(instrument_dump)

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
s1 = float(closest(list(df["strike"]),strike))
s2 = s1 + 200
s3 = s1 - 200

df = df[df["strike"].isin([s1,s2,s3])].reset_index(drop = True)

#Get the Trading Symbol and Lot size
tickers = []
for i in df.index:
    if df["instrument_type"][i] == "CE":
        tickers.append(df["tradingsymbol"][i])
        print(f'Opt Symbol added : {df["tradingsymbol"][i]}')
    elif df["instrument_type"][i] == "PE":
        tickers.append(df["tradingsymbol"][i])
        print(f'Opt Symbol added : {df["tradingsymbol"][i]}')

# =============================================================================
# Create DataFrame to store all orders
# =============================================================================

ord_df = pd.DataFrame(columns = ['timestamp','tradingsymbol','price', 'SL','Order','Reason'])
active_tickers = []

# =============================================================================
# Initinalize variables
# =============================================================================
filename = os.path.join(cwd,strategy_name + ' Order Book ' + str(dt.datetime.now().date()) + '.csv')
header = ord_df.columns

with open (filename, "w", newline="") as csvfile:
    order_book = csv.writer(csvfile)
    order_book.writerow(header)
# =============================================================================
# Create live connection to Kite
# =============================================================================

kws = KiteTicker(key_secret[0],kite.access_token)
tokens = tokenLookup(instrument_df,tickers)

db = sqlite3.connect(os.path.join(cwd,'ticks_banknifty.db'))

create_tables(tokens)

# =============================================================================
# Deploy the startegy to run every 10 mins
# =============================================================================
count = 1
start_minute = dt.datetime.now().minute

while True:
    now = dt.datetime.now()
    if (now.hour >= 9):
        kws.on_ticks=on_ticks
        kws.on_connect=on_connect
        kws.connect()
    if (now.hour >= 15 and now.minute >= 16):
        break
        
db.close()

# =============================================================================
# Calculate Profit Per Lot
# =============================================================================

ord_df = ord_df.reset_index(drop = True)

ord_df.loc[ord_df['Order'] == 'sell','new_price'] = 1 * ord_df['price']
ord_df.loc[ord_df['Order'] == 'buy','new_price'] = -1 * ord_df['price']
ord_df['lot_size'] = 25
for ticker in tickers:
    trade_df = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].reset_index(drop = True)
    trade_df['ltp'] = trade_df['new_price'].shift(1)
    trade_df['pnl'] = trade_df['ltp'] + trade_df['new_price']
    trade_df = trade_df[~trade_df['Reason'].str.contains('show')]
    print(ticker,':',sum(trade_df['pnl'] * trade_df['lot_size']))
