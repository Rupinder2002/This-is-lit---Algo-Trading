# -*- coding: utf-8 -*-
"""
Created on Thu Feb  3 16:56:34 2022

@author: naman
"""

# importing libraries
from IPython import get_ipython
get_ipython().magic('reset -sf') 

from kiteconnect import KiteConnect
import os
import datetime
import datetime as dt
import pandas as pd
import numpy as np
import talib
import matplotlib.pyplot as plt
# import aiohttp
# import asyncio
# import async_timeout

plt.style.use('fivethirtyeight')
os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

# =============================================================================
# generate trading session
# =============================================================================

access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

# =============================================================================
# get dump of all NSE instruments
# =============================================================================

instrument_dump = kite.instruments()
instrument_df = pd.DataFrame(instrument_dump)

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

def fetchOHLC(ticker,start_date,end_date,interval):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,start_date,end_date,interval))            
    return data

# =============================================================================
# Create Historical Data
# =============================================================================

interval = 'day'

tickers = ['HDFCBANK','ICICIBANK','KOTAKBANK', 'AXISBANK', 'SBIN', 'RELIANCE','TCS','INFY','HINDUNILVR','HDFC','BAJFINANCE','WIPRO','BHARTIARTL','HCLTECH','ASIANPAINT','ITC','LT','ULTRACEMCO',
            'MARUTI','SUNPHARMA','TATASTEEL','JSWSTEEL','TITAN','ADANIPORTS','ONGC','HDFCLIFE','TECHM','DIVISLAB','POWERGRID','SBILIFE','NTPC','BAJAJ-AUTO','BPCL','IOC','M&M','SHREECEM','HINDALCO',
            'GRASIM','BRITANNIA','TATAMOTORS','COALINDIA','TATACONSUM','INDUSINDBK','DRREDDY','CIPLA','EICHERMOT','UPL','NESTLEIND','HEROMOTOCO']

#eq = instrument_df[(instrument_df['instrument_type'] == 'EQ')]
#tickers = list(eq[(eq['segment'] == 'NSE') & (eq['name']!= '') & (eq['tick_size'] == 0.05)]['tradingsymbol'])

# =============================================================================
# if interval == 'day':
#     duration = 2000
# elif interval == 'hour':
#     duration = 365
# elif interval == '30minute':
#     duration = 180
# elif interval == '10minute' or interval == '5minute' or interval == '3minute':
#     duration = 90
# elif interval == 'minute':
#     duration = 30    
#     
# start_date = pd.to_datetime('2020-01-01')
# begin_date = start_date
# 
# while begin_date < dt.date.today():
#     begin_date = pd.to_datetime(begin_date).date()
#     end_date = begin_date + dt.timedelta(duration)
#     end_date = pd.to_datetime(end_date).date()
# 
#     for ticker in tickers:
#         print('Extraction for ',ticker,' from ',begin_date ,' to ',end_date)
#         
#         df = fetchOHLC(ticker = ticker ,interval  = interval ,start_date = begin_date,end_date = end_date)
#         df['ticker'] = ticker
#         if (begin_date == start_date) and (ticker == tickers[0]):
#             historical_df = df
#         else:
#             historical_df = historical_df.append(df)
#                 
#     begin_date = begin_date + dt.timedelta(duration)
# 
# # =============================================================================
# # Write Historical Data to CSV
# # =============================================================================
#         
# historical_df.sort_values(['ticker','date'], inplace = True)
# historical_df['timestamp'] = historical_df['date']
# historical_df['date'] = pd.to_datetime(historical_df['timestamp']).dt.date
# historical_df.to_csv('Data/Tickers Historical Data.csv',index = False)
# 
# =============================================================================
historical_df = pd.read_csv('Data/Tickers Historical Data.csv')
full_df = historical_df.copy()
full_df = full_df[full_df['ticker'] == 'TATASTEEL']
# =============================================================================
# Calculate Lag and Lead Values
# =============================================================================

full_df['next_10_day_price'] = full_df.groupby('ticker')['close'].shift(-10)
full_df['previous_day_close'] = full_df.groupby('ticker')['close'].shift(1)
full_df['previous_day_open'] = full_df.groupby('ticker')['open'].shift(1)
full_df['previous_day_low'] = full_df.groupby('ticker')['low'].shift(1)
full_df['previous_day_high'] = full_df.groupby('ticker')['high'].shift(1)
full_df['previous_5_day_close'] = full_df.groupby('ticker')['close'].shift(5)
full_df['previous_10_day_close'] = full_df.groupby('ticker')['close'].shift(10)

full_df.dropna(inplace = True)

# =============================================================================
# Set target variable if stock moved more than 5% in the next 10 days
# =============================================================================
full_df['10_day_change'] = round(full_df['next_10_day_price']/full_df['close'] - 1,2)

full_df.loc[full_df['10_day_change'] >= 0.05,'target'] = 1
full_df.loc[(full_df['10_day_change'] < 0.05) & (full_df['10_day_change'] >= 0.03),'target'] = 2
full_df.loc[(full_df['10_day_change'] < 0.03) & (full_df['10_day_change'] >= 0),'target'] = 3
full_df.loc[(full_df['10_day_change'] > -0.05) & (full_df['10_day_change'] <= -0.03),'target'] = 4
full_df.loc[(full_df['10_day_change'] > -0.03) & (full_df['10_day_change'] <= 0),'target'] = 5
full_df.loc[full_df['10_day_change'] <= -0.05,'target'] = 6
full_df['target'].fillna(0, inplace = True)
full_df['target'] = full_df['target'].astype(int)
full_df['target'].value_counts()

full_df.drop(['next_10_day_price','10_day_change'],axis = 1, inplace = True)

modified_data = full_df.copy()

modified_data['days'] = modified_data.groupby(['ticker']).cumcount()+1
modified_data['days'] = np.ceil(modified_data['days']/10)

cols = modified_data.drop(['date','ticker','target','days'],axis=1).columns.values
min_cols = cols + '_min'
max_cols = cols + '_max'
norm_cols = cols + '_norm' 

modified_data[min_cols] = modified_data.groupby(['ticker','days'])[cols].transform(min)
modified_data[max_cols] = modified_data.groupby(['ticker','days'])[cols].transform(max)

for i in range(len(cols)):
    modified_data[norm_cols[i]] = (modified_data[cols[i]] - modified_data[min_cols[i]])/(modified_data[max_cols[i]] - modified_data[min_cols[i]])

modified_data.drop(cols,axis = 1, inplace = True)
modified_data.drop(min_cols,axis = 1, inplace = True)
modified_data.drop(max_cols,axis = 1, inplace = True)

modified_data.columns = modified_data.columns.str.replace('_norm', '')
# =============================================================================
# Calculate Pivot Points
# =============================================================================

modified_data['PP'] = (modified_data['previous_day_close'] + modified_data['previous_day_high'] + modified_data['previous_day_low'])/3
modified_data['sup_1'] = modified_data['PP'] * 2 - modified_data['previous_day_high']
modified_data['sup_2'] = modified_data['PP'] - (modified_data['previous_day_high'] - modified_data['previous_day_low'])

modified_data['res_1'] = modified_data['PP'] * 2 - modified_data['previous_day_low']
modified_data['res_2'] = modified_data['PP'] + (modified_data['previous_day_high'] - modified_data['previous_day_low'])

# =============================================================================
# Calculate MACD
# =============================================================================

modified_data["MA_Fast"]=modified_data["close"].ewm(span=10,min_periods=10).mean()
modified_data["MA_Slow"]=modified_data["close"].ewm(span=21,min_periods=21).mean()
modified_data["MACD"]=modified_data["MA_Fast"]-modified_data["MA_Slow"]
modified_data["Signal"]=modified_data["MACD"].ewm(span=9,min_periods=9).mean()
modified_data = modified_data.drop(['MA_Fast','MA_Slow'],axis = 1)

# =============================================================================
# Create Bollinger Bands (ddof=0 is required since we want to take the standard deviation of the population and not sample)
# =============================================================================

n = 23
modified_data["MA"] = modified_data['close'].rolling(n).mean()
modified_data["BB_up"] = modified_data["MA"] + 2*modified_data['close'].rolling(n).std(ddof=0) 
modified_data["BB_dn"] = modified_data["MA"] - 2*modified_data['close'].rolling(n).std(ddof=0)
modified_data["BB_width"] = modified_data["BB_up"] - modified_data["BB_dn"]

# =============================================================================
# Create SMA crossovers
# =============================================================================

modified_data['sma5'] = talib.SMA(modified_data['close'],5)
modified_data['sma20'] = talib.SMA(modified_data['close'],20)
modified_data.loc[modified_data['sma5'] > modified_data['sma20'],'cross'] = 'over'
modified_data.loc[modified_data['sma5'] < modified_data['sma20'],'cross'] = 'under'

modified_data.dropna(inplace = True)
modified_data['target'].value_counts()

# =============================================================================
# Feature Engineering
# =============================================================================

model_data = modified_data.copy()

model_data['year'] = pd.DatetimeIndex(model_data['date']).year
model_data['month'] = pd.DatetimeIndex(model_data['date']).month
model_data['day'] = pd.DatetimeIndex(model_data['date']).day
model_data['date'] = pd.DatetimeIndex(model_data['date']).date
model_data['weekday'] = pd.DatetimeIndex(model_data['date']).weekday
model_data['quarter'] = pd.DatetimeIndex(model_data['date']).quarter
model_data['is_month_start'] = pd.DatetimeIndex(model_data['date']).is_month_start.astype(int)
model_data['is_month_end'] = pd.DatetimeIndex(model_data['date']).is_month_end.astype(int)
model_data = pd.get_dummies(model_data, columns=['cross'], prefix='cross')
model_data = pd.get_dummies(model_data, columns=['ticker'], prefix='ticker')


# =============================================================================
# Train Test Split 
# =============================================================================

train_date = model_data.date.max() - dt.timedelta(10)

model_data.loc[model_data['date'] <= train_date,'class'] = 'train'
model_data.loc[model_data['date'] > train_date,'class'] = 'test'

model_data.drop(['date'], axis = 1, inplace = True)

train_df = model_data[model_data["class"] == "train"] 
test_df = model_data[model_data["class"] == "test"] 
train = train_df.drop(['class'], axis = 1)
test = test_df.drop(['class'], axis = 1)

target_column_train = ['target'] 
predictors_train = list(set(list(train.columns))-set(target_column_train))

X_train = train[predictors_train].values
y_train = train[target_column_train].values

print(X_train.shape)
print(y_train.shape)

target_column_test = ['target'] 
predictors_test = list(set(list(test.columns))-set(target_column_test))

X_test = test[predictors_test].values
y_test = test[target_column_test].values

print(X_test.shape)
print(y_test.shape)


# =============================================================================
# Model Fitting 
# =============================================================================

from sklearn import model_selection
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
from math import sqrt
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

# =============================================================================
# fit model no training data
# =============================================================================

model = XGBClassifier()
model.fit(X_train, y_train)

# =============================================================================
# make predictions for test data
# =============================================================================

y_pred = model.predict(X_test)
predictions = y_pred
test_df['y_pred'] = y_pred
# =============================================================================
# evaluate predictions
# =============================================================================

accuracy = accuracy_score(y_test, predictions)
print("Accuracy: %.2f%%" % (accuracy * 100.0))

