import requests
from alice_blue import AliceBlue,LiveFeedType,TransactionType,OrderType,ProductType
import datetime as dt
import pandas as pd
import os
import time
import csv
import sys

cwd = os.getcwd()

strategy_name = 'Mean Reversion Long Option Trading'

# =============================================================================
# Send Alerts on Telegram (DE Functions)
# =============================================================================

def telegram_bot_sendmessage(message):
    bot_token = '5173424624:AAGWIHX1xrGfX8doCYtskOHnxhtxVr1PMCI'
    bot_ChatID = 'algo_trading_bot_trades'
    send_message = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=@' + bot_ChatID + \
                   '&parse_mode = MarkdownV2&text=' + message
    
    requests.get(send_message)

telegram_bot_sendmessage(message = '------New Trading Session Started------')
telegram_bot_sendmessage(message = 'Strategy Running Today: ' + strategy_name)

def write_rows_csv(row):
  with open (filename, "a", newline = "") as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow(row)    

# =============================================================================
# Load Credentials
# =============================================================================

interval = "5_MIN"   # ["DAY", "1_HR", "3_HR", "1_MIN", "5_MIN", "15_MIN", "60_MIN"]
ticks = {}

username = open('alice_username.txt','r').read()
password = open('alice_pwd.txt','r').read()
twoFA = open('alice_twoFA.txt','r').read()
api_key = open('api_key_alice.txt','r').read()
api_secret = open('api_secret_alice.txt','r').read()
socket_opened = False

def event_handler_quote_update(message):
    ticks[message['instrument'].symbol] = {"LTP": message["best_bid_price"],
                                           "best_ask_price": message["best_ask_price"],
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
    

def place_order(alice, ticker, exchange, quantity, stop_loss, square_off, trailing_sl):
       alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol(exchange, ticker),
                     quantity = quantity,
                     order_type = OrderType.Market,
                     product_type = ProductType.Intraday,
                     stop_loss = stop_loss,
                     square_off = square_off,
                     trailing_sl = trailing_sl)



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


def get_nfo_scripts(exchange,underlying_ticker,index = True):
    
    global close_avg
    
    df = fetchOHLC(alice.get_instrument_by_symbol(exchange,underlying_ticker),5,'1_MIN',indices = index)

    except_today = df[df.index.date !=  dt.datetime.now().date()]
    max_date = max(except_today.index.date)

    last_day_data = except_today[except_today.index.date ==  max_date]

    close_avg = last_day_data['close'].mean()
    strike_price = round(close_avg,-2)
    
    open_price = df[df.index.time == pd.to_datetime('9:15').time()]['open'][-1]
    
    if open_price > close_avg:
        contract_type = 'PE'
    elif open_price < close_avg:
        contract_type = 'CE'
    
    nfo = []
    if exchange == 'NSE':
        instruments = alice.search_instruments('NFO','BANKNIFTY')
        
    expiry = []
    for instrument in instruments:
        if contract_type in instrument.symbol: 
            expiry.append(instrument.expiry)

    expiry = min(set(expiry))
            
    for instrument in instruments:
        if (str(strike_price) in instrument.symbol) and (str(contract_type) in instrument.symbol) and instrument.expiry == expiry :
            nfo.append(instrument.symbol)
            telegram_bot_sendmessage('Strategy Running on: ' + str(instrument.symbol))
            
    return nfo


def run_strategy(ticker_list, exchange, sl_pct = 0.2,quantity = 25):

    global ord_df
    global active_tickers
    global time_elapsed
    global ticks
    
    start_time = time.time()
    
    for ticker in ticker_list:
                    
        try:
            price = ticks[ticker]['LTP']
            price_underlying = fetchOHLC(alice.get_instrument_by_symbol('NSE','Nifty Bank'),5,'5_MIN',indices = True)['close'][-1]
            if dt.datetime.now().time() < dt.time(14,1):

                if ticker not in active_tickers:
    
                    #placeOrder()
                    reason = 'Price should reverse back to mean'
                    sl = price * (1 - sl_pct)
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                
                elif ticker in active_tickers and ((price_underlying > close_avg and 'CE' in ticker) | 
                                                   (price_underlying < close_avg and 'PE' in ticker)):
                    
                    #placeOrder(ticker, 'sell', quantity)
                    reason = 'Exit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
        except:
            telegram_bot_sendmessage("API error for ticker : " + ticker)
     
    time_elapsed = time.time() - start_time

def place_sl_target_order(ticks, target_pct = 0.5, quantity = 25):
    
    global active_tickers
    global ord_df
    global tick
    global all_positions
    
    for ticker in ticks:
        try:

            tick_ltp = ticks[ticker]['best_ask_price']
            
            if ticker in active_tickers:
                
                last_trade = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]
                stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                price = ord_df[ord_df["tradingsymbol"]==ticker]["price"].values[0]

                if dt.datetime.now().hour == 15 and dt.datetime.now().minute == 14 and last_trade['Order'] == 'buy':
                        
                    #placeOrder(ticker, 'sell', quantity)
                    reason = '3:14 Exit'
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
                    
        except:
            telegram_bot_sendmessage('Error in Place SL Target Order Function')
            pass               


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
NFO_SCRIPT_LIST = get_nfo_scripts('NSE','Nifty Bank')
alice = subscribe_to_live_feed(alice, 'NFO', NFO_SCRIPT_LIST)
time.sleep(30)

# =============================================================================
# Deploy the startegy to run every 10 mins
# =============================================================================

start_minute = dt.datetime.now().minute
run_strategy(ticker_list = NFO_SCRIPT_LIST,exchange = 'NFO')

while True:
    now = dt.datetime.now()
    if now.time() >= dt.time(9,15) and now.time() <= dt.time(15,14):
        place_sl_target_order(ticks)
    if now.time() >= dt.time(15,14):
        sys.exit()

telegram_bot_sendmessage('----Session Ended----')