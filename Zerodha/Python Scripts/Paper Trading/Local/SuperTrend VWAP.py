from IPython import get_ipython
get_ipython().magic('reset -sf') 

from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import time
import numpy as np

cwd = os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)

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
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(days), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data

def fetchOHLC_LastCandle(ticker,interval,minutes):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.datetime.today()-dt.timedelta(minutes = minutes), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data


def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR']

def supertrend(DF,n,m):
    """function to calculate Supertrend given historical candle data
        n = n day ATR - usually 7 day ATR is used
        m = multiplier - usually 2 or 3 is used"""
    df = DF.copy()
    df['ATR'] = atr(df,n)
    df["B-U"]=((df['high']+df['low'])/2) + m*df['ATR'] 
    df["B-L"]=((df['high']+df['low'])/2) - m*df['ATR']
    df["U-B"]=df["B-U"]
    df["L-B"]=df["B-L"]
    ind = df.index
    for i in range(n,len(df)):
        if df['close'][i-1]<=df['U-B'][i-1]:
            df.loc[ind[i],'U-B']=min(df['B-U'][i],df['U-B'][i-1])
        else:
            df.loc[ind[i],'U-B']=df['B-U'][i]    
    for i in range(n,len(df)):
        if df['close'][i-1]>=df['L-B'][i-1]:
            df.loc[ind[i],'L-B']=max(df['B-L'][i],df['L-B'][i-1])
        else:
            df.loc[ind[i],'L-B']=df['B-L'][i]  
    df['Strend']=np.nan
    for test in range(n,len(df)):
        if df['close'][test-1]<=df['U-B'][test-1] and df['close'][test]>df['U-B'][test]:
            df.loc[ind[test],'Strend']=df['L-B'][test]
            break
        if df['close'][test-1]>=df['L-B'][test-1] and df['close'][test]<df['L-B'][test]:
            df.loc[ind[test],'Strend']=df['U-B'][test]
            break
    for i in range(test+1,len(df)):
        if df['Strend'][i-1]==df['U-B'][i-1] and df['close'][i]<=df['U-B'][i]:
            df.loc[ind[i],'Strend']=df['U-B'][i]
        elif  df['Strend'][i-1]==df['U-B'][i-1] and df['close'][i]>=df['U-B'][i]:
            df.loc[ind[i],'Strend']=df['L-B'][i]
        elif df['Strend'][i-1]==df['L-B'][i-1] and df['close'][i]>=df['L-B'][i]:
            df.loc[ind[i],'Strend']=df['L-B'][i]
        elif df['Strend'][i-1]==df['L-B'][i-1] and df['close'][i]<=df['L-B'][i]:
            df.loc[ind[i],'Strend']=df['U-B'][i]
    return df['Strend']

def st_dir_refresh(ohlc,ticker):
    """function to check for supertrend reversal"""
    global st_dir
    if ohlc["st1"][-1] > ohlc["close"][-1] and ohlc["st1"][-2] < ohlc["close"][-2]:
        st_dir[ticker][0] = "red"
    if ohlc["st1"][-1] < ohlc["close"][-1] and ohlc["st1"][-2] > ohlc["close"][-2]:
        st_dir[ticker][0] = "green"

def sl_price(ohlc):
    """function to calculate stop loss based on supertrends"""
    sl = ohlc['st1'][-1]
    return round(sl,1)

ord_df = pd.DataFrame(columns = ['timestamp','tradingsymbol','quantity','price', 'SL','Order'])
tickers_traded_current = []

df = fetchOHLC('LT',"2minute",2)
df = df.reset_index()
df_ticks = pd.DataFrame(columns = df.columns.tolist() + ['ticker'])
del df

def main(capital,count):
    global ord_df
    global tickers_traded_current
    global df_ticks
    for ticker in tickers:
        print("Startegy Running On: ",ticker)
        try:
            if count == 1:                
                ohlc = fetchOHLC(ticker = ticker,interval = "2minute",days = 2)
                ohlc1 = ohlc.reset_index()
                ohlc1['ticker'] = ticker
                df_ticks = df_ticks.append(ohlc1)
            else:
                ohlc = fetchOHLC_LastCandle(ticker = ticker,interval = "2minute",minutes = 2)
                ohlc1 = ohlc.reset_index()
                ohlc1['ticker'] = ticker
                df_ticks = df_ticks.append(ohlc1)
            
            ohlc = fetchOHLC(ticker = ticker,interval = "2minute",days = 2)
            ohlc["st1"] = supertrend(ohlc,10,2)
            ohlc['price*vol'] = ((ohlc['high'] + ohlc['low'] + ohlc['close'])/3) * ohlc['volume']
            ohlc['day'] = ohlc.index.date
            ohlc['vwap'] = ohlc.groupby('day')['price*vol'].cumsum()/ohlc.groupby('day')['volume'].cumsum()
            st_dir_refresh(ohlc,ticker)
            price_dict = kite.ltp(tokenLookup(instrument_df,[ticker]))
            price = price_dict[str(tokenLookup(instrument_df,[ticker])[0])]['last_price']
            quantity = int(capital/price)

            if len(tickers_traded_current)==0:
                if st_dir[ticker] == ["green"] and ohlc['close'][-1] > ohlc['vwap'][-1]:
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,quantity,price,sl_price(ohlc) * 1.001,'buy']],columns = ord_df.columns)
                    ord_df = ord_df.append(trade)
                    tickers_traded_current.append(ticker)
                    print("buy order placed for {}".format(ticker))
                if st_dir[ticker] == ["red"]:
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,quantity,price,sl_price(ohlc) * 0.999,'sell']],columns = ord_df.columns)
                    ord_df = ord_df.append(trade)                    
                    tickers_traded_current.append(ticker)
                    print("sell order placed for {}".format(ticker))
            elif len(tickers_traded_current)!=0 and ticker not in tickers_traded_current:
                if st_dir[ticker] == ["green"] and ohlc['close'][-1] > ohlc['vwap'][-1]:
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,quantity,price,sl_price(ohlc) * 1.001,'buy']],columns = ord_df.columns)
                    ord_df = ord_df.append(trade)
                    tickers_traded_current.append(ticker)
                    print("buy order placed for {}".format(ticker))
                if st_dir[ticker] == ["red"]:
                    trade = pd.DataFrame([[dt.datetime.now(),ticker,quantity,price,sl_price(ohlc) * 1.999,'sell']],columns = ord_df.columns)
                    ord_df = ord_df.append(trade)
                    tickers_traded_current.append(ticker)
                    print("sell order placed for {}".format(ticker))
            elif len(tickers_traded_current)!=0 and ticker in tickers_traded_current:
                if ord_df[ord_df["tradingsymbol"]==ticker]["quantity"].sum() == 0:
                    if st_dir[ticker] == ["green"] and ohlc['close'][-1] > ohlc['vwap'][-1]:
                        trade = pd.DataFrame([[dt.datetime.now(),ticker,quantity,price,sl_price(ohlc) * 1.001,'buy']],columns = ord_df.columns)
                        ord_df = ord_df.append(trade)
                        tickers_traded_current.append(ticker)
                        print("buy order placed for {}".format(ticker))
                    if st_dir[ticker] == ["red"]:
                        trade = pd.DataFrame([[dt.datetime.now(),ticker,quantity,price,sl_price(ohlc) * 0.999,'sell']],columns = ord_df.columns)
                        ord_df = ord_df.append(trade)
                        tickers_traded_current.append(ticker)
                        print("sell order placed for {}".format(ticker))
                if ord_df[ord_df["tradingsymbol"]==ticker]["quantity"].sum() != 0:
                    order = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
                    if order['Order'] == 'buy' and price < order['SL']:
                        trade = pd.DataFrame([[dt.datetime.now(),ticker,order['quantity'],price,None,'sell']],columns = ord_df.columns)
                        ord_df = ord_df.append(trade)
                        tickers_traded_current.remove(ticker)

                    if order['Order'] == 'sell' and price > order['SL']:
                        trade = pd.DataFrame([[dt.datetime.now(),ticker,order['quantity'],price,None,'buy']],columns = ord_df.columns)
                        ord_df = ord_df.append(trade)
                        tickers_traded_current.remove(ticker)
                        
                    else: 
                        if order['Order'] == 'sell':
                            sl = sl_price(ohlc) * 0.999
                        elif order['Order'] == 'buy':
                            sl = sl_price(ohlc) * 0.1001
                            trade = pd.DataFrame([[dt.datetime.now(),ticker,order['quantity'],price,sl,'Modifiy']],columns = ord_df.columns)
                            ord_df = ord_df.append(trade)
                            print("Order Modified for {}".format(ticker))
                    
        except:
            print("API error for ticker :",ticker)
    
#####################update ticker list######################################
tickers = sorted(["ZEEL","WIPRO","VEDL","ULTRACEMCO","UPL","TITAN","TECHM","TATASTEEL",
           "TATAMOTORS","TCS","SUNPHARMA","SBIN","SHREECEM","RELIANCE","POWERGRID",
           "ONGC","NESTLEIND","NTPC","MARUTI","M&M","LT","KOTAKBANK","JSWSTEEL","INFY",
           "INDUSINDBK","IOC","ITC","ICICIBANK","HDFC","HINDUNILVR","HINDALCO",
           "HEROMOTOCO","HDFCBANK","HCLTECH","GRASIM","GAIL","EICHERMOT","DRREDDY",
           "COALINDIA","CIPLA","BRITANNIA","BHARTIARTL","BPCL","BAJAJFINSV",
           "BAJFINANCE","BAJAJ-AUTO","AXISBANK","ASIANPAINT","ADANIPORTS"])

#############################################################################
capital = 10000 #position size
st_dir = {} #directory to store super trend status for each ticker
for ticker in tickers:
    st_dir[ticker] = ["None"]    

count = 1
starttime=time.time()
timeout = time.time() + 60*60*1  # 60 seconds times 360 meaning 6 hrs
while time.time() <= timeout:
    try:
        main(capital,count)
        count = count + 1
        time.sleep(120 - ((time.time() - starttime) % 120.0))
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()        

# #create KiteTicker object
# kws = KiteTicker(key_secret[0],kite.access_token)
# tokens = tokenLookup(instrument_df,tickers)

# start_minute = dt.datetime.now().minute
# def on_ticks(ws,ticks):
#     global start_minute
#     renkoOperation(ticks)
#     now_minute = dt.datetime.now().minute
#     if abs(now_minute - start_minute) >= 1:
#         start_minute = now_minute
#         main(capital)

# def on_connect(ws,response):
#     ws.subscribe(tokens)
#     ws.set_mode(ws.MODE_LTP,tokens)

# while True:
#     now = dt.datetime.now()
#     if (now.hour >= 9 and now.minute >= 15 ):
#         kws.on_ticks=on_ticks
#         kws.on_connect=on_connect
#         kws.connect()
#     if (now.hour >= 14 and now.minute >= 30):
#         sys.exit()