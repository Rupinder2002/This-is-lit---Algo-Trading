import requests
from alice_blue import AliceBlue,LiveFeedType
import datetime as dt
import pandas as pd
import os
import time
import csv
import sys

#os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading/Aliceblue/Credentials')
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

    for script in ticker_list:
        alice.subscribe(alice.get_instrument_by_symbol(exchange, script), LiveFeedType.MARKET_DATA)

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

def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

def get_nfo_scripts(exchange,underlying_ticker):
        
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
        
    df = fetchOHLC(alice.get_instrument_by_symbol(exchange,underlying_ticker_ ),5,'1_MIN',indices = index)

    except_today = df[df.index.date !=  dt.datetime.now().date()]
    max_date = max(except_today.index.date)

    last_day_data = except_today[except_today.index.date ==  max_date]
    
    open_price = df[df.index.time == pd.to_datetime('9:15').time()]['open'][-1]
    
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
             
    return nfo.symbol,close_avg


def run_strategy(ticker_list, exchange, sl_pct = 0.25):

    global ord_df
    global active_tickers
    global time_elapsed
    global ticks
    global previous_buy
    
    start_time = time.time()
    
    for underlying_ticker in ticker_list:
        ticker = ticker_list[underlying_ticker]
        try:
            price = ticks[ticker]['LTP']
            volume = ticks[ticker]['Volume']
            #price_underlying = fetchOHLC(alice.get_instrument_by_symbol('NSE',underlying_ticker),5,'5_MIN')['close'][-1]
            
            if dt.datetime.now().time() < dt.time(15,1):

                if ticker not in active_tickers and previous_buy[ticker] == False and volume >= 10000:
    
                    #placeOrder(ticker, ticker_signal, quantity)
                    reason = 'Price should reverse back to mean'
                    sl = price * (1 - sl_pct)
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    previous_buy[ticker] = True
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                
                # elif ticker in active_tickers and ((price_underlying > close_avg_dict[underlying_ticker] and 'CE' in ticker) | 
                #                                    (price_underlying < close_avg_dict[underlying_ticker] and 'PE' in ticker)):
                    
                #     #placeOrder(ticker, 'sell', quantity)
                #     reason = 'Exit'
                #     trade = pd.DataFrame([[dt.datetime.now(),ticker,price,None,'sell',reason]],columns = ord_df.columns)
                #     ord_df = pd.concat([ord_df,trade])
                #     active_tickers.remove(ticker)
                #     write_rows_csv(row = trade.iloc[0].tolist())
                #     telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
        except:
            telegram_bot_sendmessage("API error for ticker : " + ticker)
     
    time_elapsed = time.time() - start_time

def place_sl_target_order(ticks, target_pct = 0.5):
    
    global active_tickers
    global ord_df
    global tick
    global all_positions
    
    for ticker in ticks:
        try:

            tick_ltp = ticks[ticker]['LTP']
            
            if ticker in active_tickers:

                last_trade = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]
                stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                price = ord_df[ord_df["tradingsymbol"]==ticker]["price"].values[0]

                if dt.datetime.now().hour == 15 and dt.datetime.now().minute == 9 and last_trade['Order'] == 'buy':
                        
                    #placeOrder(ticker, 'sell', quantity)
                    reason = '3:09 Exit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick_ltp,None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    #telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
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
            print(e)               


def on_ticks(ticks,ticker_list, exchange):
    global start_minute
    # now = dt.datetime.now()    
    place_sl_target_order(ticks)
    # if abs(now.minute - start_minute) >= 5:
    #     start_minute = now.minute
    #     run_strategy(ticker_list, exchange)

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

if os.path.exists(filename):
  os.remove(filename)
  
with open (filename, "w", newline="") as csvfile:
    order_book = csv.writer(csvfile)
    order_book.writerow(header)
    
# =============================================================================
# Create live connection to Kite
# =============================================================================

alice = login()

scrips = ['ADANIPORTS','APOLLOHOSP','ASIANPAINT','AXISBANK','BAJAJ-AUTO','BAJFINANCE',
          'BPCL','BHARTIARTL','BRITANNIA','CIPLA','COALINDIA','DIVISLAB',
          'DRREDDY','EICHERMOT','GRASIM','HCLTECH','HDFCBANK','HEROMOTOCO',
          'HINDUNILVR','ICICIBANK','ITC','INFY','JSWSTEEL',
          'KOTAKBANK','M&M','MARUTI','NESTLEIND','ONGC','POWERGRID','RELIANCE',
          'SBILIFE','SHREECEM','SUNPHARMA','TCS','TATAMOTORS',
          'TECHM','TITAN','UPL','ULTRACEMCO','WIPRO']

nfo_scrips_dict = {}
close_avg_dict = {}
for scrip in scrips:
    detail = get_nfo_scripts('NSE',underlying_ticker=scrip)
    nfo_scrips_dict[scrip] = detail[0]
    close_avg_dict[scrip] = detail[1]

nfo_scrips_list = sorted(set(list(nfo_scrips_dict.values())))

alice = subscribe_to_live_feed(alice, 'NFO', nfo_scrips_list)
time.sleep(45)

# =============================================================================
# Deploy the startegy to run every 10 mins
# =============================================================================

start_minute = dt.datetime.now().minute

previous_buy = {}
for i in nfo_scrips_dict:
    previous_buy[nfo_scrips_dict[i]] = False

run_strategy(ticker_list = nfo_scrips_dict,exchange = 'NFO')

while True:
    now = dt.datetime.now()
    if now.time() >= dt.time(9,15) and now.time() <= dt.time(15,14):
        on_ticks(ticks,nfo_scrips_dict,'NFO')
    if now.time() >= dt.time(15,14):
        sys.exit()

telegram_bot_sendmessage('----Session Ended----')