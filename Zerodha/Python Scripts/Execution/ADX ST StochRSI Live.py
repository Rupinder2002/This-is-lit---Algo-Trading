from IPython import get_ipython
get_ipython().magic('reset -sf')

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
import requests
import sys

warnings.filterwarnings("ignore")

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

cwd = os.getcwd()

strategy_name = 'BANKNIFTY ADX ST StochRSI'

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
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)

# =============================================================================
# Create function to implement the strategy
# =============================================================================
def strategy(ohlc, ohlc1):
    
    ohlc1['ADX_14'] = ta.adx(ohlc1['high'], ohlc1['low'], ohlc1['close'])['ADX_14']
    ohlc = ohlc.merge(ohlc1[['ADX_14']], left_index = True, right_index = True, how = 'left')
    ohlc['ADX_14'] = ohlc['ADX_14'].fillna(method = 'ffill')
    
    ohlc['ST_Signal'] = ta.supertrend(ohlc['high'], ohlc['low'], ohlc['close'],length = 10, multiplier=3)['SUPERTd_10_3.0']

    ohlc[["stochrsik%","stochrsid%"]] = ta.stochrsi(ohlc['close'],length=14, rsi_length=14, k=3, d=3).values
    
    ohlc.loc[(ohlc['ADX_14'] < 20),'ADX_Signal'] = 'no_trade'
    ohlc.loc[(ohlc['ADX_14'] >= 20),'ADX_Signal'] = 'trade'

    ohlc.loc[(ohlc['stochrsik%'] > ohlc['stochrsid%']),'srsi_signal'] = 'buy'
    ohlc.loc[(ohlc['stochrsik%'] < ohlc['stochrsid%']),'srsi_signal'] = 'sell'
    
    ohlc.loc[(ohlc['ADX_Signal'] == 'trade') & (ohlc['srsi_signal'] == 'buy') & (ohlc['ST_Signal'] == 1), 'signal'] = 'buy'
    ohlc.loc[(ohlc['ADX_Signal'] == 'trade') & (ohlc['srsi_signal'] == 'sell') & (ohlc['ST_Signal'] == -1), 'signal'] = 'sell'
    
    ohlc = ohlc[['open','high','low','close','volume','signal']]
    
    return ohlc

def run_strategy(sl_pct = 0.005,quantity = 1):
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
            ohlc1 = fetchOHLC(ticker = ticker,interval = "15minute",days = 6)
            
            ohlc = strategy(ohlc,ohlc1)
            
            price_dict = kite.ltp(tokenLookup(instrument_df,[ticker]))
            price = price_dict[str(tokenLookup(instrument_df,[ticker])[0])]['last_price']
            ticker_signal = ohlc.iloc[-1]['signal']

            if ticker not in active_tickers:

                if ticker_signal == 'buy' and dt.datetime.now().time() < dt.time(15,16):
                    placeOrder(ticker, ticker_signal, quantity)
                    reason = 'Both Indicators show green'
                    #sl = ohlc['low'][-1] - sl_price(ohlc)
                    sl = ohlc['low'][-1] * (1 - sl_pct)
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif ticker_signal == 'sell' and dt.datetime.now().time() < dt.time(15,16):
                    placeOrder(ticker, ticker_signal, quantity)
                    reason = 'Both Indicators show red'
                    #sl = ohlc['close'][-1] + sl_price(ohlc)
                    sl = ohlc['high'][-1] * (1 + sl_pct)
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])                    
                    active_tickers.append(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
            else:
                
                order = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
                traded_price = all_positions[all_positions["tradingsymbol"]==ticker]["average_price"].values[0]
                if order['Order'] == 'buy':
                    
                    reason = 'Order Modified'
                    
                    if price > traded_price:
                        #sl = ohlc['low'][-1] - sl_price(ohlc)
                        sl = ohlc['low'][-1] * (1 - sl_pct)
                    else:
                        sl = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                        
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])    
                    write_rows_csv(row = trade.iloc[0].tolist())  
                    
                elif order['Order'] == 'sell':
                
                    reason = 'Order Modified'
                    
                    if price < traded_price:
                        #sl = ohlc['close'][-1] + sl_price(ohlc)
                        sl = ohlc['high'][-1] * (1 + sl_pct)
                    else:
                        sl = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                        
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])                        
                    write_rows_csv(row = trade.iloc[0].tolist())  
                    
        except Exception as e:
            try :
                print(e)
            except:
                telegram_bot_sendmessage("API error for ticker : " + ticker)
     
    time_elapsed = time.time() - start_time

def place_sl_target_order(ticks, target_pct = 0.01, quantity = 1):
    
    global active_tickers
    global ord_df
    global tick
    global all_positions
    
    sql = db.cursor()
    
    for tick in ticks:
        try:

            ticker = tickerLookup(int(tick['instrument_token']))
            
            if ticker in active_tickers:
                
                last_trade = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
                stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                price = all_positions[all_positions["tradingsymbol"]==ticker]["average_price"].values[0]

                if dt.datetime.now().hour == 15 and dt.datetime.now().minute == 16:
                    if last_trade['Order'] == 'sell':
                        placeOrder(ticker, 'buy', quantity)
                        reason = '3:16 Exit'
                        trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'buy',reason]],columns = ord_df.columns)
                        ord_df = pd.concat([ord_df,trade])
                        active_tickers.remove(ticker)
                        write_rows_csv(row = trade.iloc[0].tolist())
                        telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                        
                    elif last_trade['Order'] == 'buy':
                        placeOrder(ticker, 'sell', quantity)
                        reason = '3:16 Exit'
                        trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                        ord_df = pd.concat([ord_df,trade])
                        active_tickers.remove(ticker)
                        write_rows_csv(row = trade.iloc[0].tolist())
                        telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif last_trade['Order'] == 'buy' and tick['last_price'] <= stop_loss:
                    placeOrder(ticker, 'sell', quantity)
                    reason = 'Stop Loss Hit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif last_trade['Order'] == 'buy' and tick['last_price'] >= (price * (1 + target_pct)):
                    placeOrder(ticker, 'sell', quantity)
                    reason = 'Target Achieved'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif last_trade['Order'] == 'sell' and tick['last_price'] >= stop_loss:
                    placeOrder(ticker, 'buy', quantity)
                    reason = 'Stop Loss Hit'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    write_rows_csv(row = trade.iloc[0].tolist())
                    telegram_bot_sendmessage(trade[['tradingsymbol','price','Order','Reason']].to_json(orient='records', indent = 1))
                    
                elif last_trade['Order'] == 'sell' and tick['last_price'] <= price * (1 - target_pct):
                    placeOrder(ticker, 'buy', quantity)
                    reason = 'Target Achieved'
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,tick['last_price'],None,'buy',reason]],columns = ord_df.columns)
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
    now = dt.datetime.now()    
    place_sl_target_order(ticks)
    if abs(now.minute - start_minute) >= 5:
        start_minute = now.minute
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

tickers = ['TATAPOWER','BHEL','TATACHEM']

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

kws = KiteTicker(key_secret[0],kite.access_token)
tokens = tokenLookup(instrument_df,tickers)

if os.path.exists('ticks.db'):
  os.remove('ticks.db')

db = sqlite3.connect(os.path.join(cwd,'ticks.db'))

create_tables(tokens)

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
        db.close()
        sys.exit()

telegram_bot_sendmessage('----Session Ended----')