# -*- coding: utf-8 -*-
"""
Created on Sat Mar 12 04:06:59 2022

@author: naman
"""
from IPython import get_ipython
get_ipython().magic('reset -sf') 

from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import numpy as np
#from ta import momentum
import talib as ta
import pandas_ta as pta

cwd = os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get dump of all NSE instruments
instrument_dump = kite.instruments()
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

def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

# def atr(DF,n):
#     "function to calculate True Range and Average True Range"
#     df = DF.copy()
#     df['H-L']=abs(df['high']-df['low'])
#     df['H-PC']=abs(df['high']-df['close'].shift(1))
#     df['L-PC']=abs(df['low']-df['close'].shift(1))
#     df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
#     df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
#     return df

spot_ohlc = kite.quote("NSE:NIFTY BANK")["NSE:NIFTY BANK"]["ohlc"]
strike = spot_ohlc["open"]

df = instrument_df[(instrument_df["segment"] == "NFO-OPT") &
                (instrument_df["name"] == "BANKNIFTY")]

df = df[df["expiry"] == sorted(list(df["expiry"].unique()))[0]]

df = df[df["strike"] == float(closest(list(df["strike"]),strike))].reset_index(drop = True)

for i in df.index:
    if df["instrument_type"][i] == "CE":
        opt_ce_symbol = df["tradingsymbol"][i]
        print(f'Opt Symbol added : {df["tradingsymbol"][i]}')
    elif df["instrument_type"][i] == "PE":
        opt_pe_symbol = df["tradingsymbol"][i]
        print(f'Opt Symbol added : {df["tradingsymbol"][i]}')

#data = kite.ltp([f"NFO:{opt_ce_symbol}", f"NFO:{opt_pe_symbol}"])

StockList = [df['tradingsymbol'][0]]

data={} # Dictionary to contain pandas dataframe for all the stocks. This is to avoid creating variable for each stock 
        # to store data
finalData={} # This should contain our final output and that is Renko OHLC data
n=14 # Period for ATR
renkoData={} # It contains information on the lastest bar of renko data for the number of stocks we are working on

for stock in StockList:
    data[stock] = fetchOHLC(stock,interval = "2minute",days = 30)

# for stock in data:
#     data[stock].drop(data[stock][data[stock].volume == 0].index, inplace=True) # Data Cleaning
#     data[stock]['ATR'] = ta.ATR(data[stock]['high'],data[stock]['low'],data[stock]['close'],n)
#     data[stock]=data[stock][['open','high','low','close','ATR']] # Removing unwanted columns
#     data[stock] = data[stock][data[stock]['ATR'].notnull()]

for stock in data:
    renkoData[stock]={'BrickSize':0, 'open':0.0,'close':0.0,'Color':''}
    
for stock in data:
    #renkoData[stock]['BrickSize']=round(data[stock]['ATR'][-1],2) #This can be set manually as well!
    renkoData[stock]['BrickSize']=5 #This can be set manually as well!
    renkoData[stock]['open']=renkoData[stock]['BrickSize']+renkoData[stock]['close'] # This can be done the otherway round
                                                                                    # as well.'Close' = 'BrickSize' - 'Open' 
    renkoData[stock]['Color']='red'    # Should you choose to do the other way round, please change the color to 'green'

for stock in data:
    finalData[stock]=pd.DataFrame()
    finalData[stock].index.name='Date'
    finalData[stock]['ReOpen']=0.0
    finalData[stock]['ReHigh']=0.0
    finalData[stock]['ReLow']=0.0
    finalData[stock]['ReClose']=0.0
    finalData[stock]['Color']=''


for stock in data: # This loops thorugh all the stocks in the data dictionary
    for index,row in data[stock].iterrows(): # One may choose to use Pure python instead of Iterrows to loop though each n 
                                         # every row to improve performace if datasets are large.
        if renkoData[stock]['open'] > renkoData[stock]['close']: 
            while row['close'] > renkoData[stock]['open']+renkoData[stock]['BrickSize']:
                renkoData[stock]['open']+=renkoData[stock]['BrickSize']
                renkoData[stock]['close']+=renkoData[stock]['BrickSize']
                finalData[stock].loc[index]=row
                finalData[stock]['ReOpen'].loc[index]= renkoData[stock]['close']         
                finalData[stock]['ReHigh'].loc[index]=renkoData[stock]['open']
                finalData[stock]['ReLow'].loc[index]=renkoData[stock]['close']
                finalData[stock]['ReClose'].loc[index]=renkoData[stock]['open']
                finalData[stock]['Color'].loc[index]='green'

            while row['close'] < renkoData[stock]['close']-renkoData[stock]['BrickSize']:
                renkoData[stock]['open']-=renkoData[stock]['BrickSize']
                renkoData[stock]['close']-=renkoData[stock]['BrickSize']
                finalData[stock].loc[index]=row
                finalData[stock]['ReOpen'].loc[index]= renkoData[stock]['open']         
                finalData[stock]['ReHigh'].loc[index]=renkoData[stock]['open']
                finalData[stock]['ReLow'].loc[index]=renkoData[stock]['close']
                finalData[stock]['ReClose'].loc[index]=renkoData[stock]['close']
                finalData[stock]['Color'].loc[index]='red'
                
        else:
            while row['close']< renkoData[stock]['open']-renkoData[stock]['BrickSize']:
                renkoData[stock]['open']-=renkoData[stock]['BrickSize']
                renkoData[stock]['close']-=renkoData[stock]['BrickSize']
                finalData[stock].loc[index]=row
                finalData[stock]['ReOpen'].loc[index]= renkoData[stock]['close']         
                finalData[stock]['ReHigh'].loc[index]=renkoData[stock]['close']
                finalData[stock]['ReLow'].loc[index]=renkoData[stock]['open']
                finalData[stock]['ReClose'].loc[index]=renkoData[stock]['open']
                finalData[stock]['Color'].loc[index]='red'
                
            while row['close'] > renkoData[stock]['close']+renkoData[stock]['BrickSize']:
                renkoData[stock]['open']+=renkoData[stock]['BrickSize']
                renkoData[stock]['close']+=renkoData[stock]['BrickSize']
                finalData[stock].loc[index]=row
                finalData[stock]['ReOpen'].loc[index]= renkoData[stock]['open'] 
                finalData[stock]['ReHigh'].loc[index]=renkoData[stock]['close']
                finalData[stock]['ReLow'].loc[index]=renkoData[stock]['open']
                finalData[stock]['ReClose'].loc[index]=renkoData[stock]['close']
                finalData[stock]['Color'].loc[index]='green'


finalData[stock]['Calc_AO'] = ta.MA((finalData[stock]['ReHigh'] + finalData[stock]['ReLow'])/2, timeperiod = 5) - ta.MA((finalData[stock]['ReHigh'] + finalData[stock]['ReLow'])/2, timeperiod = 34)
finalData[stock].loc[finalData[stock]['Calc_AO'] > finalData[stock]['Calc_AO'].shift(1),'AO Color'] = 'green'
finalData[stock].loc[finalData[stock]['Calc_AO'] < finalData[stock]['Calc_AO'].shift(1),'AO Color'] = 'red'
finalData[stock].drop(['Calc_AO'],axis = 1, inplace = True)


p1 = 10
m1 = 2
st1 = pta.supertrend(finalData[stock]['ReHigh'],finalData[stock]['ReLow'],finalData[stock]['ReClose'],p1,m1)
finalData[stock]["st1"] = st1['SUPERT_' + str(p1) + '_' + str(float(m1))]
finalData[stock]["st1_color"] = st1['SUPERTd_' + str(p1) + '_' + str(float(m1))]

