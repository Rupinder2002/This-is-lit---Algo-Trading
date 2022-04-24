# -*- coding: utf-8 -*-
"""
Created on Fri Jan 28 23:21:09 2022

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

cwd = os.chdir("C:/Users/ANMOL/Desktop/zerodha")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


#get dump of all NSE instruments
instrument_dump = kite.instruments()
instrument_df = pd.DataFrame(instrument_dump)


##########

def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1
    
def tokenLookup(instrument_df,symbol_list):
    """Looks up instrument token for a given script from instrument dump"""
    token_list = []
    for symbol in symbol_list:
        token_list.append(int(instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]))
    return token_list

def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(duration), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data


df_banknifty_fut_current = fetchOHLC('BANKNIFTY22FEBFUT','minute',60)[['close']]
df_banknifty_fut_next = fetchOHLC('BANKNIFTY22MARFUT','minute',60)[['close']]
df_nifty_fut_current = fetchOHLC('NIFTY22FEBFUT','minute',60)[['close']]
df_nifty_fut_next = fetchOHLC('NIFTY22MARFUT','minute',60)[['close']]


b = np.intersect1d(df_banknifty_fut_current.index,np.intersect1d(df_banknifty_fut_next.index,np.intersect1d(df_nifty_fut_current.index,df_nifty_fut_next.index)))


df_banknifty_fut_current = df_banknifty_fut_current [df_banknifty_fut_current.index.isin(b)]

df = df_banknifty_fut_current.merge(df_banknifty_fut_next,
                                    left_index= True,
                                    right_index=True,
                                    how = 'left',
                                    suffixes= ['_bn_current','_bn_next']).merge(df_nifty_fut_current,
                                                                                left_index= True,
                                                                                right_index=True,
                                                                                how = 'left').merge(df_nifty_fut_next,
                                                                                                    left_index= True,
                                                                                                    right_index=True,
                                                                                                    how = 'left')


df.columns=['bn_current','bn_next','n_current','n_next']

##########

df['bn_lot_size'] = 25
df['n_lot_size'] = 50

df['bn_current_value'] = df['bn_lot_size']*df['bn_current']
df['bn_next_value'] = df['bn_lot_size']*df['bn_next']
df['n_current_value'] = df['n_lot_size']*df['n_current']
df['n_next_value'] = df['n_lot_size']*df['n_next']

df['leg_1'] = None
df['leg_2'] = None
df['leg_1'].iloc[0] = 4
df['leg_2'].iloc[0] = 4

df['value_leg_1'] = df['n_current_value'] - df['bn_current_value']
df['value_leg_2'] = df['bn_next_value'] - df['n_next_value']

df['profit_leg_1'] = df['value_leg_1'] - df['value_leg_1'].iloc[0] 
df['profit_leg_2'] = df['value_leg_2'] - df['value_leg_2'].iloc[0] 

######

df['ratio'] = df['bn_current'] / df['n_current']
pos = 4
# df.reset_index(inplace = True)
for i in range(len(df)):
    print(pos)
    if pos == 4:
        if df['profit_leg_1'].iloc[i] >=7500:
            pos = 3   
            df['leg_1'][i] = 3
            df['leg_2'][i] = 5
        elif df['profit_leg_2'].iloc[i] >=7500:
            pos = 5
            df['leg_1'][i] = 5
            df['leg_2'][i] = 3
        else:
            df['leg_1'][i] = pos
            df['leg_2'][i] = 8-pos
    
    elif pos == 3:
        if df['profit_leg_1'].iloc[i] >=12500:
            pos = 2 
            df['leg_1'].iloc[i] = 2
            df['leg_2'].iloc[i] = 6
        elif df['profit_leg_1'].iloc[i] <=7500:
            pos = 4
            df['leg_1'].iloc[i] = 4
            df['leg_2'].iloc[i] = 4
        else:
            df['leg_1'][i] = pos
            df['leg_2'][i] = 8-pos
            
    elif pos == 2:
        if df['profit_leg_1'].iloc[i] >=20000:
            pos = 1 
            df['leg_1'].iloc[i] = 1
            df['leg_2'].iloc[i] = 7
        elif df['profit_leg_1'].iloc[i] <=12500:
            pos = 3
            df['leg_1'].iloc[i] = 3
            df['leg_2'].iloc[i] = 5
        else:
            df['leg_1'][i] = pos
            df['leg_2'][i] = 8-pos
            
    elif pos == 1:
        if df['profit_leg_1'].iloc[i] >=32500:
            pos = 0
            df['leg_1'].iloc[i] = 0
            df['leg_2'].iloc[i] = 8
        elif df['profit_leg_1'].iloc[i] <=20000:
            pos = 2
            df['leg_1'].iloc[i] = 2
            df['leg_2'].iloc[i] = 6
        else:
            df['leg_1'][i] = pos
            df['leg_2'][i] = 8-pos
    elif pos == 0:
        if df['profit_leg_1'].iloc[i] <=32500:
            pos = 1
            df['leg_1'].iloc[i] = 1
            df['leg_2'].iloc[i] = 7
        else:
            df['leg_1'][i] = pos
            df['leg_2'][i] = 8-pos
            
    elif pos == 5:
        if df['profit_leg_2'].iloc[i] >=12500:
            pos = 6 
            df['leg_1'].iloc[i] = 6
            df['leg_2'].iloc[i] = 2
        elif df['profit_leg_2'].iloc[i] <=7500:
            pos = 4
            df['leg_1'].iloc[i] = 4
            df['leg_2'].iloc[i] = 4
        else:
            df['leg_1'][i] = pos
            df['leg_2'][i] = 8-pos
            
    elif pos == 6:
        if df['profit_leg_2'].iloc[i] >=20000:
            pos = 7
            df['leg_1'].iloc[i] = 7
            df['leg_2'].iloc[i] = 1
        elif df['profit_leg_2'].iloc[i] <=12500:
            pos = 5
            df['leg_1'].iloc[i] = 5
            df['leg_2'].iloc[i] = 3
        else:
            df['leg_1'][i] = pos
            df['leg_2'][i] = 8-pos
           
    elif pos == 7:
          if df['profit_leg_2'].iloc[i] >=32500:
              pos = 8 
              df['leg_1'].iloc[i] = 8
              df['leg_2'].iloc[i] = 0
          elif df['profit_leg_2'].iloc[i] <=20000:
              pos = 6
              df['leg_1'].iloc[i] = 6
              df['leg_2'].iloc[i] = 2
          else:
              df['leg_1'][i] = pos
              df['leg_2'][i] = 8-pos

    elif pos == 8:
        if df['profit_leg_2'].iloc[i] <=32500:
            pos = 7
            df['leg_1'].iloc[i] = 7
            df['leg_2'].iloc[i] = 1
        else:
            df['leg_1'][i] = pos
            df['leg_2'][i] = 8-pos
  