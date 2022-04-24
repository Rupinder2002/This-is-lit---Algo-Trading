# -*- coding: utf-8 -*-
"""
Created on Tue Feb 22 21:56:06 2022

@author: naman
"""

from IPython import get_ipython
get_ipython().magic('reset -sf')

import pandas as pd
import numpy as np
import os 
import talib
import datetime

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

#historical_df = pd.read_csv('Data/Tickers Historical Data.csv')
historical_df = pd.read_csv('Data/NIFTY BANK.csv')
ticker_df = historical_df.copy()

ticker_df = ticker_df[['date','open','high','low','close']]

ticker_df['timestamp'] = pd.to_datetime(ticker_df['date'])
ticker_df['date'] = pd.to_datetime(ticker_df['date'],dayfirst=True).dt.date

ticker_df.set_index('timestamp',inplace = True)

# =============================================================================
# Resample Data
# =============================================================================

ticker_df_1 = ticker_df.resample('2min').agg({'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last']})  #check if M is minutes or months
ticker_df_1.dropna(how = 'all',inplace = True)
ticker_df_1.columns = ['open','high','low','close']
ticker_df_1['date'] = pd.to_datetime(ticker_df_1.index).date
ticker_df_1['time'] = pd.to_datetime(ticker_df_1.index,dayfirst=True).time

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
    df["B-U"]=((df['high']+df['low'] + df['close'])/3) + m*df['ATR'] 
    df["B-L"]=((df['high']+df['low'] + df['close'])/3) - m*df['ATR']
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

def st_dir_refresh(ohlc):
    """function to check for supertrend reversal"""
    for i in range(20,len(ohlc)):

        if ohlc["st1"][i] > ohlc["close"][i] and ohlc["st1"][i-1] < ohlc["close"][i-1]:
            ohlc['signal_1'][i] = "red"
        if ohlc["st1"][i] < ohlc["close"][i] and ohlc["st1"][i-1] > ohlc["close"][i-1]:
            ohlc['signal_1'][i] = "green"

ticker_df_1['EMA_200'] = talib.EMA(ticker_df_1['close'], timeperiod=200)

ticker_df_2 = ticker_df_1[(ticker_df_1['date'] <= pd.to_datetime('2019-12-31')) & (ticker_df_1['date'] >= pd.to_datetime('2018-01-01'))]

ticker_df_2['st1'] = supertrend(ticker_df_2,10,2)
ticker_df_2['signal_1'] = ""

st_dir_refresh(ticker_df_2)

ticker_df_2 = ticker_df_2.iloc[33:,:]

ticker_df_2 = ticker_df_2[ticker_df_2['time'] <= datetime.time(15,0)]

#Risk Appetite
target_pct = 0.006
stoploss_pct = 0.01

#Zerodha Charges intraday
stt = 0.00025 #on sell
transcation_charges = 0.0000345 #on buy and sell
gst = 0.18
sebi_charges = 10/10000000
stamp_charges = 0.00003

order_df = pd.DataFrame(columns = ['timestamp','order_type','order_reason','trade_price','quantity','balance','target','stop_loss','brokerage','stt_value', 'transcation_charges_value', 'gst_value', 'sebi_value', 'stamp_value'])

balance = 100000
total_charges = 0
order_type = 'No Open Orders'
quantity = 1

for j in range(1,len(ticker_df_2)):
    
    if order_type == 'No Open Orders':
    
        if (ticker_df_2['EMA_200'][j] > ticker_df_2['close'][j]) and (ticker_df_2['signal_1'][j] == 'green'):
    
            timestamp = ticker_df_2.index[j]
            order_type = 'BUY CALL'
            order_reason = 'Supertrend Buy'
            trade_price = ticker_df_2['close'][j]
            target = ticker_df_2['close'][j] * (1 + target_pct)
            stop_loss = ticker_df_2['close'][j] * (1 - stoploss_pct)
            #quantity = np.floor(balance/trade_price)
            #quantity = 1
            brokerage = None
            transcation_value = None
            stt_value = None
            transcation_charges_value = None
            gst_value = None
            sebi_value = None
            stamp_value = None
            total_charges = None

            #balance = balance - (trade_price * quantity)
    
            trade = pd.DataFrame([[timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,brokerage,
                                   stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)

            order_df = order_df.append(trade)
            
        elif (ticker_df_2['EMA_200'][j] < ticker_df_2['close'][j]) and (ticker_df_2['signal_1'][j] == 'red'):
    
            timestamp = ticker_df_2.index[j]
            order_type = 'BUY PUT'
            order_reason = 'Supertrend Sell'
            trade_price = ticker_df_2['close'][j]
            target = ticker_df_2['close'][j] * (1 - target_pct)
            stop_loss = ticker_df_2['close'][j] * (1 + stoploss_pct)
            #quantity = np.floor(balance/trade_price)
            #quantity = 1
            transcation_value = None
            stt_value = None
            transcation_charges_value = None
            gst_value = None
            sebi_value = None
            stamp_value = None
            total_charges = None

            #balance = balance - (trade_price * quantity)
    
            trade = pd.DataFrame([[timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,brokerage,
                                   stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)

            order_df = order_df.append(trade)
            
        else:
            order_type = 'No Open Orders'
        
    elif order_type == 'BUY CALL' or order_type == 'BUY CALL ON':
        current_price = ticker_df_2['close'].iloc[j]
        
        if ticker_df_2['time'][j] == datetime.time(15,0):
            timestamp = ticker_df_2.index[j]
            order_type = 'SELL CALL'
            order_reason = '3PM Exit'
            trade_price = current_price
            target = None
            stop_loss = None
            transcation_value = (trade_price + trade['trade_price'][0]) * quantity
            brokerage = min(20,0.0003 * trade_price * quantity) * 2
            stt_value = stt * trade_price
            transcation_charges_value = transcation_charges * transcation_value
            gst_value = gst * (transcation_charges_value + brokerage)
            sebi_value = sebi_charges * transcation_value 
            stamp_value = trade['trade_price'][0] * stamp_charges * quantity
            total_charges = stt_value + transcation_charges_value + gst_value + sebi_value + stamp_value

            #balance = balance + (trade_price * quantity) - total_charges
    
            trade = pd.DataFrame([[timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,brokerage,
                                   stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
            
            order_df = order_df.append(trade)
            total_charges = 0
            order_type = 'No Open Orders'
                         
        elif current_price < stop_loss:
            timestamp = ticker_df_2.index[j]
            order_type = 'SELL CALL'
            order_reason = 'Stop Loss Hit'
            trade_price = stop_loss
            target = None
            stop_loss = None
            transcation_value = (trade_price + trade['trade_price'][0]) * quantity
            brokerage = min(20,0.0003 * trade_price * quantity) * 2
            stt_value = stt * trade_price
            transcation_charges_value = transcation_charges * transcation_value
            gst_value = gst * (transcation_charges_value + brokerage)
            sebi_value = sebi_charges * transcation_value 
            stamp_value = trade['trade_price'][0] * stamp_charges * quantity
            total_charges = stt_value + transcation_charges_value + gst_value + sebi_value + stamp_value

            #balance = balance + (trade_price * quantity) - total_charges
    
            trade = pd.DataFrame([[timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,brokerage,
                                   stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
            
            order_df = order_df.append(trade)
            
            total_charges = 0
            order_type = 'No Open Orders'
            
        elif current_price > target:
            timestamp = ticker_df_2.index[j]
            order_type = 'BUY CALL ON'
            stop_loss = round(target * (1 - stoploss_pct), 2)
            target = round(target * (1 + stoploss_pct), 2)
             
            trade = pd.DataFrame([[timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,brokerage,
                                   stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
            
            order_df = order_df.append(trade)
            
        else :
            order_type = 'BUY CALL ON'
            
    elif order_type == 'BUY PUT' or order_type == 'BUY PUT ON':
        current_price = ticker_df_2['close'].iloc[j]
        
        if ticker_df_2['time'][j] == datetime.time(15,0):
            timestamp = ticker_df_2.index[j]
            order_type = 'SELL PUT'
            order_reason = '3PM Exit'
            trade_price = current_price
            target = None
            stop_loss = None
            transcation_value = (trade_price + trade['trade_price'][0]) * quantity
            brokerage = min(20,0.0003 * trade_price * quantity) * 2
            stt_value = stt * trade_price
            transcation_charges_value = transcation_charges * transcation_value
            gst_value = gst * (transcation_charges_value + brokerage)
            sebi_value = sebi_charges * transcation_value 
            stamp_value = trade['trade_price'][0] * stamp_charges * quantity
            total_charges = stt_value + transcation_charges_value + gst_value + sebi_value + stamp_value

            #balance = balance + (trade_price * quantity) - total_charges
    
            trade = pd.DataFrame([[timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,brokerage,
                                   stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
            
            order_df = order_df.append(trade)
            total_charges = 0
            order_type = 'No Open Orders'
                         
        elif current_price > stop_loss:
            timestamp = ticker_df_2.index[j]
            order_type = 'SELL PUT'
            order_reason = 'Stop Loss Hit'
            trade_price = stop_loss
            target = None
            stop_loss = None
            transcation_value = (trade_price + trade['trade_price'][0]) * quantity
            brokerage = min(20,0.0003 * trade_price * quantity) * 2
            stt_value = stt * trade_price
            transcation_charges_value = transcation_charges * transcation_value
            gst_value = gst * (transcation_charges_value + brokerage)
            sebi_value = sebi_charges * transcation_value 
            stamp_value = trade['trade_price'][0] * stamp_charges * quantity
            total_charges = stt_value + transcation_charges_value + gst_value + sebi_value + stamp_value

            #balance = balance + (trade_price * quantity) - total_charges
    
            trade = pd.DataFrame([[timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,brokerage,
                                   stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
            
            order_df = order_df.append(trade)
            
            total_charges = 0
            order_type = 'No Open Orders'
            
        elif current_price < target:
            timestamp = ticker_df_2.index[j]
            order_type = 'BUY PUT ON'
            stop_loss = round(target * (1 - stoploss_pct), 2)
            target = round(target * (1 + stoploss_pct), 2)
             
            trade = pd.DataFrame([[timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,brokerage,
                                   stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
            
            order_df = order_df.append(trade)
            
        else :
            order_type = 'BUY PUT ON'
    
order_df['date'] = pd.to_datetime(order_df.timestamp).dt.date
order_df['last_tp'] = order_df.groupby('date')['trade_price'].shift(1)

order_df = order_df.reset_index(drop = True)

order_df.loc[order_df['order_type'] == 'SELL CALL','pnl'] = order_df['trade_price'] - order_df['last_tp']
order_df.loc[order_df['order_type'] == 'SELL PUT','pnl'] = order_df['last_tp'] - order_df['trade_price']

profits = order_df[~order_df['pnl'].isnull()]
profits['total_charges'] = profits['brokerage'] + profits['stt_value'] + profits['transcation_charges_value'] + profits['gst_value'] + profits['sebi_value'] + profits['stamp_value']
profits['net pnl'] = profits['pnl'] - profits['total_charges'] 
profits['pnl'].sum()
profits['net pnl'].sum()
