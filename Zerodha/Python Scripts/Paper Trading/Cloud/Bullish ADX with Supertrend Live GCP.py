from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import pandas as pd
import datetime as dt
import os
import pandas_ta as ta
import time
import csv
import warnings
import requests
import sys

warnings.filterwarnings("ignore")

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

cwd = os.getcwd()

strategy_name = 'Bullish ADX with Supertrend'

# =============================================================================
# Send Alerts on Telegram (DE Functions)
# =============================================================================

def telegram_bot_sendmessage(message):
    bot_token = '5173424624:AAGWIHX1xrGfX8doCYtskOHnxhtxVr1PMCI'
    bot_ChatID = 'algo_trading_bot_trades'
    send_message = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=@' + bot_ChatID + \
                   '&parse_mode = MarkdownV2&text=' + message
    
    requests.get(send_message)

#telegram_bot_sendmessage(message = '------New Trading Session Started------')

def write_rows_csv(row):
  with open (filename, "a", newline = "") as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow(row)    

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

def placeOrder(symbol,buy_sell,quantity):    
    # Place an intraday stop loss order on NSE
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NFO,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)

# =============================================================================
# Create function to implement the strategy
# =============================================================================
def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

def strategy(ohlc,ticker):

    global exit_signal
    
    ohlc['ADX_14'] = ta.adx(ohlc['high'], ohlc['low'], ohlc['close'])['ADX_14']
    ohlc[['DMP','DMN']] = ta.dm(ohlc['high'], ohlc['low'])
    ohlc[['ADX_lc','DMP_lc','DMN_lc']] = ohlc[['ADX_14','DMP','DMN']].shift(1)
    
    ohlc.loc[(ohlc['ADX_14'] > ohlc['DMN']) & (ohlc['ADX_lc'] <= ohlc['DMN_lc']),'ADX_Signal'] = 'buy'
    ohlc['ST_Signal'] = ta.supertrend(ohlc['high'], ohlc['low'], ohlc['close'],length = 7, multiplier=3)['SUPERTd_7_3.0']

    ohlc.loc[(ohlc['ADX_Signal'] == 'buy') & (ohlc['ST_Signal'] == 1), 'signal'] = 'buy'
    
    last_candle = ohlc.iloc[-1]
    
    if last_candle['DMP'] > last_candle['DMN'] and last_candle['DMP_lc'] < last_candle['DMN_lc']:
        exit_signal[ticker] = 'sell'
    
    ohlc = ohlc[['open','high','low','close','volume','signal']]
    
    return ohlc

def run_strategy(sl_pct = 0.15,quantity = 25):
    global ord_df
    global active_tickers
    global time_elapsed
    global ticks
    global all_positions
    
    a = 0
    while a < 10:
        try:
            all_positions = pd.DataFrame(kite.positions()["day"])
            break
        except:
            print("can't extract position data..retrying")
            a+=1
    
    start_time = time.time()
    
    print(start_time)
    
    for ticker in tickers:
        print(ticker)
        try:
            ohlc = fetchOHLC(ticker = ticker,interval = "5minute",days = 6)
            
            ohlc = strategy(ohlc, ticker)
            
            price_dict = kite.ltp(tokenLookup(instrument_df,[ticker]))
            price = price_dict[str(tokenLookup(instrument_df,[ticker])[0])]['last_price']
            ticker_signal = ohlc.iloc[-1]['signal']

            if ticker not in active_tickers:

                if ticker_signal == 'buy' and dt.datetime.now().time() < dt.time(15,16):
                    #placeOrder(ticker, ticker_signal, quantity)
                    reason = 'Both Indicators show green'
                    sl = price * (1 - sl_pct)
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
            
            elif exit_signal[ticker] == 'sell' and dt.datetime.now().time() < dt.time(15,16):
                #placeOrder(ticker, 'sell', quantity)
                reason = 'Exit'
                trade = pd.DataFrame([[dt.datetime.now(),ticker,price,None,'buy',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.append(ticker)
                write_rows_csv(row = trade.iloc[0].tolist())
                telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
        except Exception as e:
            try :
                print(e)
            except:
                telegram_bot_sendmessage("API error for ticker : " + ticker)
     
    time_elapsed = time.time() - start_time

def place_sl_target_order(ticks, target_pct = 0.3, quantity = 25):
    
    global active_tickers
    global ord_df
    global tick
    global all_positions
    
    for tick in ticks:
        try:

            ticker = tickerLookup(int(tick['instrument_token']))
            
            if ticker in active_tickers:
                
                last_trade = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]
                stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                price = all_positions[all_positions["tradingsymbol"]==ticker]["average_price"].values[0]

                if dt.datetime.now().hour == 15 and dt.datetime.now().minute == 16 and last_trade['Order'] == 'buy':
                        
                    #placeOrder(ticker, 'sell', quantity)
                    reason = '3:16 Exit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif last_trade['Order'] == 'buy' and tick['last_price'] <= stop_loss:
                    #placeOrder(ticker, 'sell', quantity)
                    reason = 'Stop Loss Hit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif last_trade['Order'] == 'buy' and tick['last_price'] >= (price * (1 + target_pct)):
                    #placeOrder(ticker, 'sell', quantity)
                    reason = 'Target Achieved'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
        except Exception as e:
            try:
                print(e)
            except:
                telegram_bot_sendmessage('Error in Place SL Target Order Function')
            pass               
        

def on_ticks(ws,ticks):
    global start_minute
    now = dt.datetime.now()    
    place_sl_target_order(ticks)
    if abs(now.minute - start_minute) >= 5:
        start_minute = now.minute
        run_strategy()

def on_connect(ws,response):
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL,tokens)

# =============================================================================
# Get dump of all NFO instruments
# =============================================================================

instrument_dump = kite.instruments()
instrument_df = pd.DataFrame(instrument_dump)

# =============================================================================
# Select tickers to run the strategy on
# =============================================================================

spot_ohlc = kite.quote("NSE:NIFTY 50")["NSE:NIFTY 50"]["ohlc"]
strike = spot_ohlc["open"]

df = instrument_df[(instrument_df["segment"] == "NFO-OPT") & (instrument_df["name"] == "NIFTY")]
# df['expiry_month'] = pd.to_datetime(df['expiry']).dt.month
# df['expiry_year'] = pd.to_datetime(df['expiry']).dt.year

# df = df[df.groupby(['expiry_year','expiry_month'])['expiry'].transform('max') == df['expiry']]

#Select closest expiry contracts 
df = df[df["expiry"] == sorted(list(df["expiry"].unique()))[0]]

#Select contracts based on closest Strike Price to the Spot Price
atm = float(closest(list(df["strike"]),strike))
itm = atm * 1.2
otm = atm * 0.8

df = df[df["strike"].isin([atm,itm,otm])].reset_index(drop = True)

#Get the Trading Symbol and Lot size
tickers = []
for i in df.index:
    if df["instrument_type"][i] == "CE":
        tickers.append(df["tradingsymbol"][i])
        #telegram_bot_sendmessage(f'Opt Symbol added : {df["tradingsymbol"][i]}')
    elif df["instrument_type"][i] == "PE":
        tickers.append(df["tradingsymbol"][i])
        #telegram_bot_sendmessage(f'Opt Symbol added : {df["tradingsymbol"][i]}')

# =============================================================================
# Create DataFrame to store all orders
# =============================================================================

ord_df = pd.DataFrame(columns = ['timestamp','tradingsymbol','price', 'SL','Order','Reason'])
active_tickers = []

exit_signal = {}

for ticker in tickers:
    exit_signal[ticker] = None

# =============================================================================
# Initinalize variables
# =============================================================================
filename = os.path.join(cwd,strategy_name + ' Order Book ' + str(dt.datetime.now().date()) + '.csv')

header = ord_df.columns

if os.path.exists(filename):
  os.remove(filename)
  
with open (filename, "w", newline="") as csvfile:
    order_book = csv.writer(csvfile)
    order_book.writerow(header)
    
# =============================================================================
# Create live connection to Kite
# =============================================================================

kws = KiteTicker(key_secret[0],kite.access_token)
tokens = tokenLookup(instrument_df,tickers)

# =============================================================================
# Deploy the startegy to run every 10 mins
# =============================================================================
start_minute = dt.datetime.now().minute

while True:
    now = dt.datetime.now()
    if now.hour >= 9 and now.time() <= dt.time(15,16):
        kws.on_ticks=on_ticks
        kws.on_connect=on_connect
        kws.connect()
    if now.time() >= dt.time(15,16):
        sys.exit()

telegram_bot_sendmessage('----Session Ended----')