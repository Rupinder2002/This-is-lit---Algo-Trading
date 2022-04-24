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

warnings.filterwarnings("ignore")

cwd = os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')
#cwd = os.getcwd()

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
    """function to calculate stop loss based on ATR"""
    sl = 4 * ta.atr(ohlc['high'],ohlc['low'],ohlc['close'], 20)[-1]
    return round(sl,1)

def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

def strategy(ohlc,ohlc1):

    ohlc1['ADX_14'] = ta.adx(ohlc1['high'], ohlc1['low'], ohlc1['close'])['ADX_14']
    ohlc = ohlc.merge(ohlc1[['ADX_14']], left_index = True, right_index = True, how = 'left')
    ohlc['ADX_14'] = ohlc['ADX_14'].fillna(method = 'ffill')
    
    ohlc['ST_Signal'] = ta.supertrend(ohlc['high'], ohlc['low'], ohlc['close'],length = 10, multiplier=3)['SUPERTd_10_3.0']

    # ohlc["VWAP"] = ta.vwap(ohlc['high'], ohlc['low'], ohlc['close'], ohlc['volume']).values
    ohlc[["stochrsik%","stochrsid%"]] = ta.stochrsi(ohlc['close'],length=14, rsi_length=14, k=3, d=3).values
    
    ohlc.loc[(ohlc['ADX_14'] < 20),'ADX_Signal'] = 'no_trade'
    ohlc.loc[(ohlc['ADX_14'] >= 20),'ADX_Signal'] = 'trade'

    ohlc.loc[(ohlc['stochrsik%'] > ohlc['stochrsid%']),'srsi_signal'] = 'buy'
    ohlc.loc[(ohlc['stochrsik%'] < ohlc['stochrsid%']),'srsi_signal'] = 'sell'
    
    ohlc.loc[(ohlc['ADX_Signal'] == 'trade') & (ohlc['srsi_signal'] == 'buy') & (ohlc['ST_Signal'] == 1), 'signal'] = 'buy'
    ohlc.loc[(ohlc['ADX_Signal'] == 'trade') & (ohlc['srsi_signal'] == 'sell') & (ohlc['ST_Signal'] == -1), 'signal'] = 'sell'
    
    ohlc = ohlc[['open','high','low','close','volume','signal']]
    
    return ohlc

def run_strategy(timestamp,tickers):
    global ord_df
    global active_tickers
    
    for ticker in tickers:
        
        try:
            ohlc = fetchOHLC(ticker = ticker,interval = "5minute",days = 6,timestamp = timestamp)
            ohlc1 = fetchOHLC(ticker = 'NIFTY BANK',interval = "15minute",days = 6,timestamp = timestamp)
            
            ohlc = strategy(ohlc,ohlc1)            
            
            price = ohlc['close'][-1]

            if ticker not in active_tickers:

                if ohlc.iloc[-1]['signal'] == 'buy' and timestamp.time() < dt.time(15,16):
                    reason = 'Both Indicators show green'
                    sl = ohlc['low'][-1] - sl_price(ohlc)
                    trade = pd.DataFrame([[timestamp,ticker,price,sl,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.append(ticker)
                    
                elif ohlc.iloc[-1]['signal'] == 'sell' and timestamp.time() < dt.time(15,16):
                    reason = 'Both Indicators show red'
                    sl = ohlc['close'][-1] + sl_price(ohlc)
                    trade = pd.DataFrame([[timestamp,ticker,price,sl,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])                    
                    active_tickers.append(ticker)
                    
            else:
                
                order = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
                
                if order['Order'] == 'buy':
                    
                    reason = 'Order Modified'
                    if price > ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['price']:
                        sl = ohlc['low'][-1] - sl_price(ohlc)
                    else:
                        sl = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                        
                    trade = pd.DataFrame([[timestamp,ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                   
                if order['Order'] == 'sell':
                
                    reason = 'Order Modified'
                    if price < ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['price']:
                        sl = ohlc['close'][-1] + sl_price(ohlc)
                    else:
                        sl = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']

                    trade = pd.DataFrame([[timestamp,ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    
        except Exception as e:
            print(e)

def place_sl_hit_order(current_price,ticker,timestamp,target_pct = 0.25):
    
    global active_tickers
    global ord_df
        
    if ticker in active_tickers:
        last_trade = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
        stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
        price = last_trade['price']
        if timestamp.hour == 15 and timestamp.minute == 16:
            if last_trade['Order'] == 'sell':
                reason = '3:16 Exit'
                trade = pd.DataFrame([[timestamp,ticker,current_price,None,'buy',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
                
            elif last_trade['Order'] == 'buy':
                reason = '3:16 Exit'
                trade = pd.DataFrame([[timestamp,ticker,current_price,None,'sell',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
            
        elif last_trade['Order'] == 'buy' and current_price <= stop_loss:
            reason = 'Stop Loss Hit'
            trade = pd.DataFrame([[timestamp,ticker,current_price,None,'sell',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)
            
        elif last_trade['Order'] == 'buy' and current_price >= price * (1 + target_pct):
            reason = 'Target Achieved'
            trade = pd.DataFrame([[timestamp,ticker,current_price,None,'sell',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)
            
        elif last_trade['Order'] == 'sell' and current_price >= stop_loss:
            reason = 'Stop Loss Hit'
            trade = pd.DataFrame([[timestamp,ticker,current_price,None,'buy',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)
            
        elif last_trade['Order'] == 'sell' and current_price <= price * (1 - target_pct):
            reason = 'Target Achieved'
            trade = pd.DataFrame([[timestamp,ticker,current_price,None,'buy',reason]],columns = ord_df.columns)
            ord_df = pd.concat([ord_df,trade])
            active_tickers.remove(ticker)
                
def get_hist(ticker,db):
    token = instrumentLookup(instrument_df,ticker)
    data = pd.read_sql('''SELECT * FROM TOKEN%s;''' %token, con=db)                
    data = data.set_index(['ts'])
    data.index = pd.to_datetime(data.index)
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
df = instrument_df[(instrument_df["segment"] == "NFO-OPT") & (instrument_df["name"] == 'BANKNIFTY')]

#Select closest expiry contracts 
df = df[df["expiry"] == sorted(list(df["expiry"].unique()))[1]]

s1 = 35700
s2 = s1 + 500
s3 = s1 - 500

df = df[df["strike"].isin([s1,s2,s3])].reset_index(drop = True)

#Get the Trading Symbol and Lot size
lot_size = None
tickers = []
for i in df.index:
    if lot_size is None:
        lot_size = df["lot_size"][i]
        print(f"Lot size : {lot_size}")
    if df["instrument_type"][i] == "CE":
        tickers.append(df["tradingsymbol"][i])
        print(f'Opt Symbol added : {df["tradingsymbol"][i]}')
    elif df["instrument_type"][i] == "PE":
        tickers.append(df["tradingsymbol"][i])
        print(f'Opt Symbol added : {df["tradingsymbol"][i]}')

# =============================================================================
# Initinalize variables
# =============================================================================

filename = 'Order Book ' + str(dt.datetime.now().date()) + '.csv'
header = ord_df.columns

with open (filename, "w", newline="") as csvfile:
    order_book = csv.writer(csvfile)
    order_book.writerow(header)

# =============================================================================
# Create live connection to Kite
# =============================================================================

tokens = tokenLookup(instrument_df,tickers)

db = sqlite3.connect('ticks_banknifty.db')

ticks = pd.DataFrame()
for ticker in tickers:
    tick = get_hist(ticker,db)
    tick['ticker'] = ticker
    ticks = pd.concat([ticks,tick])
    
# =============================================================================
# Deploy the startegy to run every 10 mins
# =============================================================================

bands = pd.date_range("2022-03-25 9:30", "2022-03-25 15:20", freq="5min")
for i in range(len(bands)-1):
    starttime = bands[i]
    endtime = bands[i+1]
    ticks_filtered = ticks[(ticks.index>starttime) & (ticks.index < endtime)]
    for ticker in tickers:
        tick_ticker = ticks_filtered[ticks_filtered['ticker'] == ticker]
        for index in tick_ticker.index:
            current_price = tick_ticker['price'][index]
            place_sl_hit_order(current_price = current_price,ticker = ticker,timestamp = index)

    timestamp = bands[i]    
    run_strategy(timestamp = timestamp, tickers = tickers)

# =============================================================================
# Calculate Profit Per Lot
# =============================================================================
if(len(ord_df)>0):
    ord_df1 = ord_df.reset_index(drop = True)
    ord_df1 = ord_df1[ord_df1['timestamp'].dt.time<=dt.time(15,16)]
    
    for ticker in tickers:
        trade_df = ord_df1[(ord_df1["tradingsymbol"]==ticker) & (ord_df1['Order']!='Modify')].reset_index(drop = True)
        trade_df.loc[trade_df['Order'] == 'buy','new_price'] = -1 * trade_df['price']
        trade_df.loc[trade_df['Order'] == 'sell','new_price'] = 1 * trade_df['price']
        trade_df['lot_size'] = 25
        trade_df['ltp'] = trade_df['new_price'].shift(1)
        trade_df['pnl'] = trade_df['ltp'] + trade_df['new_price']
        trade_df = trade_df[~trade_df['Reason'].str.contains('show')]
        print('Total Profit as of ' + str(bands[i].date()) + ' for ' + ticker + ' : ' + str(round(sum(trade_df['pnl'] * trade_df['lot_size']))))
