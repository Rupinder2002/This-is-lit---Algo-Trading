# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 21:56:06 2022

@author: naman
"""

from IPython import get_ipython
get_ipython().magic('reset -sf')


from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import time
import pandas_ta as ta

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

cwd = os.getcwd()

strategy_name = 'BANKNIFTY ADX ST StochRSI'

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
    
    ohlc = ohlc[['date','open','high','low','close','signal']]
    
    return ohlc

def run_strategy(row,sl_amt = 50,quantity = 1):
    
    global ord_df
    global active_tickers
    global time_elapsed
    
    start_time = time.time()
    
    for ticker in tickers:
        try:
            ticker_signal = row['signal']
            price = row['close']

            if ticker not in active_tickers:

                if ticker_signal == 'buy' and row.name.time() < dt.time(15,16):
                    reason = 'Both Indicators show green'
                    #sl = ohlc['low'][-1] - sl_price(ohlc)
                    sl = row['low'] - sl_amt
                    trade = pd.DataFrame([[row.name,ticker,price,sl,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.append(ticker)
                    
                elif ticker_signal == 'sell' and row.name.time() < dt.time(15,16):
                    reason = 'Both Indicators show red'
                    #sl = ohlc['close'][-1] + sl_price(ohlc)
                    sl = row['high'] + sl_amt
                    trade = pd.DataFrame([[row.name,ticker,price,sl,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])                    
                    active_tickers.append(ticker)
                    
            else:
                
                order = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
                traded_price = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['price']

                if order['Order'] == 'buy':
                    
                    reason = 'Order Modified'
                    
                    if price > traded_price:
                        #sl = ohlc['low'][-1] - sl_price(ohlc)
                        sl = row['low'] - sl_amt
                    else:
                        sl = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                        
                    trade = pd.DataFrame([[row.name,ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])    
                    
                elif order['Order'] == 'sell':
                
                    reason = 'Order Modified'
                    
                    if price < traded_price:
                        #sl = ohlc['close'][-1] + sl_price(ohlc)
                        sl = row['high'] + sl_amt
                    else:
                        sl = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
                        
                    trade = pd.DataFrame([[row.name,ticker,price,sl,'Modify',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])                        
                    
        except Exception as e:
            try :
                print(e)
            except:
                print("API error for ticker : " + ticker)
     
    time_elapsed = time.time() - start_time

def place_sl_target_order(tick, target_amt = 100, quantity = 1):
    
    global active_tickers
    global ord_df
    
    try:

        ticker = 'BANKNIFTY'
        
        if ticker in active_tickers:
            
            last_trade = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].iloc[-1]
            stop_loss = ord_df[(ord_df["tradingsymbol"]==ticker)].iloc[-1]['SL']
            price = last_trade['price']

            if tick.name.hour == 15 and tick.name.minute == 16:
                if last_trade['Order'] == 'sell':
                    reason = '3:16 Exit'
                    trade = pd.DataFrame([[tick.name,ticker,tick['close'],None,'buy',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                    
                elif last_trade['Order'] == 'buy':
                    reason = '3:16 Exit'
                    trade = pd.DataFrame([[tick.name,ticker,tick['close'],None,'sell',reason]],columns = ord_df.columns)
                    ord_df = pd.concat([ord_df,trade])
                    active_tickers.remove(ticker)
                
            elif last_trade['Order'] == 'buy' and tick['low'] <= stop_loss:
                reason = 'Stop Loss Hit'
                trade = pd.DataFrame([[tick.name,ticker,stop_loss,None,'sell',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
                
            elif last_trade['Order'] == 'buy' and tick['high'] >= (price + target_amt):
                reason = 'Target Achieved'
                trade = pd.DataFrame([[tick.name,ticker,(price + target_amt),None,'sell',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
                
            elif last_trade['Order'] == 'sell' and tick['high'] >= stop_loss:
                reason = 'Stop Loss Hit'
                trade = pd.DataFrame([[tick.name,ticker,stop_loss,None,'buy',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
                
            elif last_trade['Order'] == 'sell' and tick['low'] <= (price - target_amt):
                reason = 'Target Achieved'
                trade = pd.DataFrame([[tick.name,ticker,(price - target_amt),None,'buy',reason]],columns = ord_df.columns)
                ord_df = pd.concat([ord_df,trade])
                active_tickers.remove(ticker)
                
    except Exception as e:
        try:
            print(e)
        except:
            print('Error in Place SL Target Order Function')
        pass

#historical_df = pd.read_csv('Data/Tickers Historical Data.csv')

historical_df = pd.read_csv('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading Material/Data/NIFTY BANK.csv')
ticks = historical_df.copy()

ticks = ticks[['date','open','high','low','close']]
ticks['timestamp'] = pd.to_datetime(ticks['date'])
ticks['date'] = pd.to_datetime(ticks['date'],dayfirst=True).dt.date
ticks['time'] = pd.to_datetime(ticks.index).time
ticks['ticker'] = 'BANKNIFTY'
ticks.set_index('timestamp',inplace = True)

# =============================================================================
# Resample Data
# =============================================================================

ohlc = ticks.resample('5min').agg({'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last']})  #check if M is minutes or months
ohlc.dropna(how = 'all',inplace = True)
ohlc.columns = ['open','high','low','close']
ohlc['date'] = ohlc.index.date
ohlc1 = ticks.resample('15min').agg({'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last']})  #check if M is minutes or months
ohlc1.dropna(how = 'all',inplace = True)
ohlc1.columns = ['open','high','low','close']
ohlc1['date'] = ohlc1.index.date

ohlc = strategy(ohlc, ohlc1)
tickers = ['BANKNIFTY']

ord_df = pd.DataFrame(columns = ['timestamp','tradingsymbol','price', 'SL','Order','Reason'])
active_tickers = []

min_date = pd.to_datetime('2020-01-01')
start_date = min_date.date()
max_date = pd.to_datetime(ohlc.index.max())

while start_date <= max_date.date():
    print(start_date)
    data = ohlc[ohlc['date'] == start_date]
    for index,row in data.iterrows():
        run_strategy(row)
        starttime = row.name
        endtime = starttime + dt.timedelta(minutes=5)
        ticks_filtered = ticks[(ticks.index > starttime) & (ticks.index < endtime)]
        for index_1,row_1 in ticks_filtered.iterrows():
            place_sl_target_order(row_1)

    start_date = start_date + dt.timedelta(days=1)
    
ads = ord_df[ord_df['Order']!='Modify']
print(ads.Reason.value_counts())


ord_df1 = ord_df.reset_index(drop = True)
trade_df = ord_df1[(ord_df1['Order']!='Modify')].reset_index(drop = True)
trade_df.loc[trade_df['Order'] == 'buy','new_price'] = -1 * trade_df['price']
trade_df.loc[trade_df['Order'] == 'sell','new_price'] = 1 * trade_df['price']
trade_df['ltp'] = trade_df['new_price'].shift(1)
trade_df['pnl'] = trade_df['ltp'] + trade_df['new_price']
trade_df = trade_df[~trade_df['Reason'].str.contains('show')]

trade_df['Date'] = trade_df['timestamp'].dt.date
pnl_day = trade_df.groupby(['Date'],as_index = False)['pnl'].sum()
print(sum(pnl_day['pnl']))