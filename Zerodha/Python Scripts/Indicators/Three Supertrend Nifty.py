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

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

#historical_df = pd.read_csv('Data/Tickers Historical Data.csv')
historical_df = pd.read_csv('Data/NIFTY_2008_2020.csv')
ticker_df = historical_df.copy()

ticker_df = ticker_df.reset_index(drop = True)
ticker_df['date'] = pd.to_datetime(ticker_df['date'],format = '%Y%m%d').dt.date
ticker_df['time'] = pd.to_datetime(ticker_df['time'],format = '%H:%M').dt.time
ticker_df = ticker_df[pd.to_datetime(ticker_df['time'],format = '%H:%M:%S').dt.time>=pd.to_datetime('09:15',format = '%H:%M').time()]
ticker_df['timestamp'] = pd.to_datetime(ticker_df['date'].astype(str) +' ' + ticker_df['time'].astype(str))
ticker_df.set_index('timestamp',inplace = True)

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

ticker_df_1 = ticker_df.resample('5min').agg({'ticker':['first'],'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last']})  #check if M is minutes or months
ticker_df_1.dropna(how = 'all',inplace = True)
ticker_df_1.columns = ['ticker','open','high','low','close']
ticker_df_1['date'] = pd.to_datetime(ticker_df_1.index).date

ticker_df_2 = ticker_df_1[(ticker_df_1['date'] <= pd.to_datetime('2018-01-01')) & (ticker_df_1['date'] >= pd.to_datetime('2016-01-01'))]

ticker_df_2['st1'] = supertrend(ticker_df_2,10,1)
ticker_df_2['st2'] = supertrend(ticker_df_2,11,2)
ticker_df_2['st3'] = supertrend(ticker_df_2,12,3)

ticker_df_2['signal_1'] = ""
ticker_df_2['signal_2'] = ""
ticker_df_2['signal_3'] = ""

def st_dir_refresh(ohlc):
    """function to check for supertrend reversal"""
    for i in range(2,len(ohlc)):

        if ohlc["st1"][i] > ohlc["close"][i] and ohlc["st1"][i-1] < ohlc["close"][i-1]:
            ohlc['signal_1'][i] = "red"
        if ohlc["st2"][i] > ohlc["close"][i] and ohlc["st2"][i-1] < ohlc["close"][i-1]:
            ohlc['signal_2'][i] = "red"
        if ohlc["st3"][i] > ohlc["close"][i] and ohlc["st3"][i-1] < ohlc["close"][i-1]:
            ohlc['signal_3'][i] = "red"
        if ohlc["st1"][i] < ohlc["close"][i] and ohlc["st1"][i-1] > ohlc["close"][i-1]:
            ohlc['signal_1'][i] = "green"
        if ohlc["st2"][i] < ohlc["close"][i] and ohlc["st2"][i-1] > ohlc["close"][i-1]:
            ohlc['signal_2'][i] = "green"
        if ohlc["st3"][i] < ohlc["close"][i] and ohlc["st3"][i-1] > ohlc["close"][i-1]:
            ohlc['signal_3'][i] = "green"

st_dir_refresh(ticker_df_2)

three_greens = ticker_df_2[(ticker_df_2['signal_1'] == 'green') & (ticker_df_2['signal_2'] == 'green') & (ticker_df_2['signal_3'] == 'green')]
three_reds = ticker_df_2[(ticker_df_2['signal_1'] == 'red') & (ticker_df_2['signal_2'] == 'red') & (ticker_df_2['signal_3'] == 'red')]
