# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 13:25:34 2022

@author: ANMOL
"""

from kiteconnect import KiteConnect
import os
import datetime
import datetime as dt
import pandas as pd
import numpy as np
import talib
from itertools import combinations
from datetime import timedelta

cwd = os.chdir("/Users/divijshah/Desktop/Work/Algo/Zerodha")

df_nse = pd.read_csv('/Users/divijshah/Desktop/Work/Algo/Data/NIFTY BANK.csv')
df_nfo = pd.read_csv('/Users/divijshah/Desktop/Work/Algo/Data/FUT/BANKNIFTY_CURRENT.csv')

df_nfo['Date'] = df_nfo['Date'].apply(lambda x : str(x)[:4] + '-' + str(x)[4:6] + '-' + str(x)[-2:]   )
df_nfo['timestamp'] = df_nfo['Date'] + ' ' + df_nfo['Time'] + '+05:30'


df_nfo = df_nfo [ df_nfo['timestamp'].isin(df_nse['date'])]
df_nse = df_nse [ df_nse['date'].isin(df_nfo['timestamp'])]
df_nfo['timestamp'] = pd.to_datetime(df_nfo['timestamp'],dayfirst=True)
df_nse['date'] = pd.to_datetime(df_nse['date'],dayfirst=True)
df_nse.set_index('date',inplace = True)

############

df_nse['timestamp'] = df_nse.index
df_nse['date'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.date
df_nse['month'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.month
df_nse['time'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.time
df_nse['hour'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.hour
df_nse['weekday'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.weekday

df_nse['nfo_price'] = df_nfo['Close'].values
# df_nse.rename( columns = { 'date' : 'timestamp' } , inplace = True)
df_nse.dropna(how = 'any' , inplace=True)

# df['date'] = pd.to_datetime(df['trigger_time'],dayfirst=True).dt.date

########

df_nse['move'] = None
in_trade = 'OFF'     # OFF , CALL_BUY , CALL_BUY_ON , CALL_SELL,  PUT_BUY , PUT_BUY_ON , PUT_SELL
df_nse['buying_price'] = None
df_nse['stoploss'] = None
df_nse['target'] = None
df_nse['exit_reason'] = None



###############

candle = df_nse.resample('5min').agg({ 'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last']})  #check if M is minutes or months
candle.columns = ['O','H','L','C']
candle.dropna(how = 'all',inplace = True)
candle['diff'] = candle['C'] - candle['O']

last_candle = None


# candle[candle.index == df_nse.index[j] - timedelta(minutes = 5)]

for j in range (len(df_nse)) :

    print (j)    
    
    if (in_trade == 'OFF' or in_trade == 'SELL_CALL' or in_trade == 'SELL_PUT')   :
        
        if (df_nse['timestamp'].iloc[j] in candle.index) and (df_nse.index[j].time() < datetime.time(15,0)) and j >=5 and (df_nse.index[j].time() >= datetime.time(9,20)):
        
            # if (candle[candle.index == df_nse.index[j-5]]['C'][0] - candle[candle.index == df_nse.index[j-5]]['O'][0] > 100)  :

            if (candle[candle.index == df_nse.index[j] - timedelta(minutes = 5)]['diff'][0]) > 100 and last_candle != candle[candle.index == df_nse.index[j] - timedelta(minutes = 5)].index :
                
                # ltpc  = df_nse['close'].iloc[j]
                # # print("Current BankNifty Spot price :", ltpc)        
                
                # tradable_strike_for_today = round(ltpc - 450,-2)        
                # strike = int(tradable_strike_for_today) 
                
                # name1 = name + wseries + str(strike) + 'CE'
                
                # df_nfo = fetchOHLC( name1  , 'minute' , 60)
                
                # ltp1  = df_nfo[ df_nfo.index == df_nse.index[j] ]['close'][0]
                ltp1 = df_nse['nfo_price'].iloc[j]
    
                in_trade = 'BUY_CALL'
                stoploss = round((ltp1 - 20),2)
                target = round((ltp1 + 50),2)
                
                df_nse['buying_price'].iloc[j] = ltp1
                df_nse['stoploss'].iloc[j] = stoploss
                df_nse['target'].iloc[j] = target
                df_nse['move'].iloc[j] = in_trade
                # df_nse['nfo_price'].iloc[j] = ltp1

                last_candle = candle[candle.index == df_nse.index[j-5]].index
                                    
            # elif (candle[candle.index == df_nse.index[j-5]]['C'][0] - candle[candle.index == df_nse.index[j-5]]['O'][0] < -100) : 
            elif (candle[candle.index == df_nse.index[j] - timedelta(minutes = 5)]['diff'][0]) < -100 and last_candle != candle[candle.index == df_nse.index[j] - timedelta(minutes = 5)].index :
                # ltpc  = df_nse['close'].iloc[j]
                # # print("Current BankNifty Spot price :", ltpc)        
                
                # tradable_strike_for_today = round(ltpc + 450,-2)        
                # strike = int(tradable_strike_for_today) 
                
                # name1 = name + wseries + str(strike) + 'PE'
                
                # df_nfo = fetchOHLC( name1  , 'minute' , 60)
                
                ltp1 = df_nse['nfo_price'].iloc[j]
    
                in_trade = 'BUY_PUT'
                stoploss = round((ltp1 + 20),2)
                target = round((ltp1- 50),2)
                
                df_nse['buying_price'].iloc[j] = ltp1
                df_nse['stoploss'].iloc[j] = stoploss
                df_nse['target'].iloc[j] = target
                df_nse['move'].iloc[j] = in_trade
                # df_nse['nfo_price'].iloc[j] = ltp1

                last_candle = candle[candle.index == df_nse.index[j-5]].index
            
            else :
                
                in_trade = 'OFF'
        else :
            in_trade = 'OFF'

    elif in_trade == 'BUY_CALL' or in_trade == 'BUY_CALL_ON' :
        
        current_price = df_nse['nfo_price'].iloc[j]
        # df_nse['nfo_price'] = current_price        

        if current_price < stoploss :
            in_trade = 'SELL_CALL'
            df_nse['exit_reason'].iloc[j] = 'stoploss'
        elif current_price > target :
            in_trade = 'BUY_CALL_ON'              
            stoploss = round(target - 10,2)
            target = round(target + 10)
        # elif (df_nse['timestamp'].iloc[j] in candle.index) and df_nse['close'].iloc[j] > df_nse['EMA'].iloc[j] :
        #     in_trade = 'SELL_CALL'            
        elif df_nse.index[j] == datetime.time(15,0) :
            in_trade = 'SELL_CALL'
            df_nse['exit_reason'].iloc[j] = '3pm'
        else :
            in_trade = 'BUY_CALL_ON'
    
        df_nse['buying_price'].iloc[j] = ltp1    
        df_nse['stoploss'].iloc[j] = stoploss
        df_nse['target'].iloc[j] = target
        
    elif in_trade == 'BUY_PUT' or in_trade == 'BUY_PUT_ON' :

        current_price = df_nse['nfo_price'].iloc[j]
        # df_nse['nfo_price'].iloc[j] = current_price        

        if current_price > stoploss :
            in_trade = 'SELL_PUT'
            df_nse['exit_reason'].iloc[j] = 'stoploss'
        elif current_price < target :
            in_trade = 'BUY_PUT_ON'              
            stoploss = round(target + 10,2)
            target = round(target - 10)
        # elif (df_nse['timestamp'].iloc[j] in candle.index) and df_nse['close'].iloc[j] < df_nse['EMA'].iloc[j] :
        #     in_trade = 'SELL_PUT'
        elif df_nse.index[j] == datetime.time(15,0) :
            in_trade = 'SELL_PUT'
            df_nse['exit_reason'].iloc[j] = '3pm'
        else :
            in_trade = 'BUY_PUT_ON'

        df_nse['buying_price'].iloc[j] = ltp1    
        df_nse['stoploss'].iloc[j] = stoploss
        df_nse['target'].iloc[j] = target
    

                
    df_nse['move'].iloc[j] = in_trade 





############# SUMARY #########    

summary = df_nse[ (df_nse['move'] == 'BUY_CALL') | (df_nse['move'] == 'BUY_PUT') | (df_nse['move'] == 'SELL_CALL') | (df_nse['move'] == 'SELL_PUT')  ] 
    
summary.loc[ (summary['exit_reason'] == 'stoploss') & (summary['move'] == 'SELL_CALL')   , 'diff'] = summary['stoploss'] - summary['buying_price'] 
summary.loc[ (summary['exit_reason'] == 'stoploss') & (summary['move'] == 'SELL_PUT')  , 'diff'] = summary['buying_price'] - summary['stoploss']  
summary.loc[ (summary['exit_reason'] == '3pm') & (summary['move'] == 'SELL_CALL')  , 'diff'] = summary['nfo_price'] - summary['buying_price'] 
summary.loc[ (summary['exit_reason'] == '3pm') & (summary['move'] == 'SELL_PUT')  , 'diff'] =  summary['buying_price'] - summary['nfo_price']  

summary.to_csv('summary_candle_100_fut_banknifty_5years.csv')

summary['diff'].sum()

