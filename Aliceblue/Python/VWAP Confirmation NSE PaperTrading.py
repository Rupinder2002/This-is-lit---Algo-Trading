from IPython import get_ipython
get_ipython().magic('reset -sf') 

import requests
from alice_blue import AliceBlue,LiveFeedType
import datetime as dt
import pandas as pd
import os
import pandas_ta as ta
import time
import csv
import sys

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading/Aliceblue')
cwd = os.getcwd()

strategy_name = 'VWAP Confirmation'

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
#telegram_bot_sendmessage(message = 'Strategy Running Today: ' + strategy_name)

def write_rows_csv(row):
  with open (filename, "a", newline = "") as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow(row)    

# =============================================================================
# Load Credentials
# =============================================================================

interval = "1_HR"   # ["DAY", "1_HR", "3_HR", "1_MIN", "5_MIN", "15_MIN", "60_MIN"]
ticks = {}

NSE_SCRIPT_LIST = ['ONGC', 'SBILIFE','BAJAJFINSV','COALINDIA','INFY','TATASTEEL']

username = open('Credentials/alice_username.txt','r').read()
password = open('Credentials/alice_pwd.txt','r').read()
twoFA = open('Credentials/alice_twoFA.txt','r').read()
api_key = open('Credentials/api_key_alice.txt','r').read()
api_secret = open('Credentials/api_secret_alice.txt','r').read()
socket_opened = False

def event_handler_quote_update(message):
    ticks[message['instrument'].symbol] = {"LTP": message["ltp"],
                                           "Volume": message["volume"]}
    
def open_callback():
    global socket_opened
    socket_opened = True

def login():
    
    access_token = AliceBlue.login_and_get_access_token(username = username, password = password, twoFA = twoFA, api_secret = api_secret, app_id = api_key)   
    alice = AliceBlue(username=username, password=password,access_token=access_token, master_contracts_to_download=['MCX', 'NSE', 'CDS','NFO'])
    alice.start_websocket(subscribe_callback=event_handler_quote_update,
                          socket_open_callback=open_callback,
                          run_in_background=True)
   
    while(socket_opened == False):   
        pass
    
    return alice

def subscribe_to_live_feed(alice,exchange,ticker_list):
    global exit_signal
    for script in ticker_list:
        alice.subscribe(alice.get_instrument_by_symbol(exchange, script), LiveFeedType.MARKET_DATA)
        exit_signal[script] = None

    return alice
    
def fetchOHLC(instrument, days, interval, indices=False):
    
    to_datetime = dt.datetime.now() 
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

def strategy(ohlc,ticker):
    
    ohlc['VWAP'] = ta.vwap(ohlc['high'], ohlc['low'], ohlc['close'],ohlc['volume']).values
    ohlc[['VWAP_LC','close_LC','open_LC','high_LC']] = ohlc[['VWAP','close','open','high']].shift(1)
    
    ohlc.loc[(ohlc['close_LC'] > ohlc['VWAP_LC']) &
             (ohlc['open_LC'] < ohlc['VWAP_LC']) &
             (ohlc['close'] > ohlc['high_LC']),'signal'] = 'buy'
    
    ohlc = ohlc[['open','high','low','close','volume','signal']]
    
    return ohlc

def run_strategy(ticker_list, exchange, sl_pct = 0.02,quantity = 1):

    global ord_df
    global active_tickers
    global time_elapsed
    global ticks
    global all_positions
    
    a = 0
    while a < 10:
        try:
            all_positions = pd.DataFrame(alice.get_daywise_positions())
            break
        except:
            telegram_bot_sendmessage("can't extract position data..retrying")
            a+=1
    
    start_time = time.time()
    
    for ticker in ticker_list:
            
        print(ticker)
        
        if 'NIFTY' in ticker:
            indices = True
        else:
            indices = False
        
        try:
            
            instrument = alice.get_instrument_by_symbol(exchange, ticker)
            ohlc = fetchOHLC(instrument, 10, interval, indices)
            
            ohlc = strategy(ohlc, ticker)
            
            price = ticks[ticker]['LTP']
            ticker_signal = ohlc.iloc[-1]['signal']
            
            if dt.datetime.now().time() < dt.time(15,16):

                if ticker not in active_tickers and ticker_signal == 'buy':
    
                    #placeOrder(ticker, ticker_signal, quantity)
                    reason = 'Both Indicators show green'
                    sl = price * (1 - sl_pct)
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'buy',reason]],columns = ord_df.columns)
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

def place_sl_target_order(ticks, target_pct = 0.04, quantity = 1):
    
    global active_tickers
    global ord_df
    global all_positions
    
    for ticker in ticks:
        try:

            tick_ltp = ticks[ticker]['LTP']
            
            if ticker in active_tickers:
                
                last_trade = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]
                stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                price = ord_df[ord_df["tradingsymbol"]==ticker]["price"].values[0]

                if dt.datetime.now().hour == 13 and dt.datetime.now().minute == 16 and last_trade['Order'] == 'buy':
                        
                    #placeOrder(ticker, 'sell', quantity)
                    reason = '3:16 Exit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick_ltp,None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif last_trade['Order'] == 'buy' and tick_ltp <= stop_loss:
                    
                    #placeOrder(ticker, 'sell', quantity)
                    reason = 'Stop Loss Hit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick_ltp,None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif last_trade['Order'] == 'buy' and tick_ltp >= (price * (1 + target_pct)):
                    
                    #placeOrder(ticker, 'sell', quantity)
                    reason = 'Target Achieved'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick_ltp,None,'sell',reason]],columns = ord_df.columns)
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

def on_ticks(ticks,ticker_list, exchange):
    global start_minute
    now = dt.datetime.now()    
    place_sl_target_order(ticks)
    if abs(now.minute - start_minute) >= 60:
        start_minute = now.minute
        run_strategy(ticker_list, exchange)

# =============================================================================
# Create DataFrame to store all orders
# =============================================================================

ord_df = pd.DataFrame(columns = ['timestamp','tradingsymbol','price', 'SL','Order','Reason'])
active_tickers = []
exit_signal = {}

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

alice = login()
alice = subscribe_to_live_feed(alice, 'NSE', NSE_SCRIPT_LIST)

# =============================================================================
# Deploy the startegy to run every 10 mins
# =============================================================================
start_minute = dt.datetime.now().minute

while True:
    now = dt.datetime.now()
    if now.hour >= 9 and now.time() <= dt.time(15,16):
        on_ticks(ticks,NSE_SCRIPT_LIST,'NSE')
    if now.time() >= dt.time(15,16):
        sys.exit()

telegram_bot_sendmessage('----Session Ended----')