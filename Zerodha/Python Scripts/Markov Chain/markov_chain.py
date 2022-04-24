# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 22:52:08 2022

@author: naman
"""

from IPython import get_ipython
get_ipython().magic('reset -sf') 

import pandas as pd
import numpy as np
import talib
import os 

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

historical_df = pd.read_csv('Data/abcd.txt')
ticker_df = historical_df.copy()

ticker_df = ticker_df[['date','open','high','low','close']]

ticker_df['timestamp'] = pd.to_datetime(ticker_df['date'])
ticker_df['month'] = pd.to_datetime(ticker_df['date'],dayfirst=True).dt.month
ticker_df['time'] = pd.to_datetime(ticker_df['date'],dayfirst=True).dt.time
ticker_df['hour'] = pd.to_datetime(ticker_df['date'],dayfirst=True).dt.hour
ticker_df['weekday'] = pd.to_datetime(ticker_df['date'],dayfirst=True).dt.weekday
ticker_df['date'] = pd.to_datetime(ticker_df['date'],dayfirst=True).dt.date

ticker_df.set_index('timestamp',inplace = True)

candle = ticker_df.resample('5min').agg({ 'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last']})  #check if M is minutes or months
candle.columns = ['O','H','L','C']
candle.dropna(how = 'all',inplace = True)
candle['diff'] = candle['C'] - candle['O']  

candle['pos_neg'] = candle['diff']/abs(candle['diff'])
candle = candle.fillna(1)

candle_test = candle.copy()

candle_test['key'] = (candle_test['pos_neg'].shift(5)).astype(str) + ',' + (candle_test['pos_neg'].shift(4)).astype(str) + ',' + (candle_test['pos_neg'].shift(3)).astype(str) + ',' + (candle_test['pos_neg'].shift(2)).astype(str) + ',' + (candle_test['pos_neg'].shift(1)).astype(str)

candle_test['lag_diff'] = candle_test['diff'].shift(1).cumsum()

candle_test = candle_test[~candle_test['key'].str.contains('nan')]

next_poss = candle_test.groupby(['key','pos_neg']).size()/candle_test.groupby(['key']).size()
next_poss = next_poss.reset_index()

no_of_cases = candle_test.groupby(['key','pos_neg'],as_index=False).size()

x = candle_test.groupby('key')['diff'].describe(percentiles = [0.01,0.05,0.1,0.25,0.3,0.35,0.4,0.45,0.5,0.75,0.90,0.95,0.99])
x['list_diff'] = candle_test.groupby('key')['diff'].agg(list)

import matplotlib.pyplot as plt
plt.hist(x['list_diff'][15], bins = 10)

new_df = next_poss.merge(no_of_cases)
new_df = new_df.merge(x)

new_df['key'].str.rsplit(',').str[1:] + np.array(new_df['pos_neg'].astype(str))


new_df['next_key'] = (new_df['key'].apply(lambda x: x.rsplit(',')[1:]) + new_df['pos_neg'].apply(lambda x: [str(x)])).apply(','.join)

 
y = new_df['diff'].apply(lambda x: list(pd.DataFrame(x).describe().T))

pd.DataFrame(new_df['diff'][0]).describe().T



trans_matrix = new_df.groupby(['key', 'next_key'])[0].sum().unstack() 
trans_matrix = trans_matrix.fillna(0)
cols = trans_matrix.columns

for i in range(1,50):
    trans_matrix = np.dot(trans_matrix,trans_matrix)
    trans_matrix = pd.DataFrame(trans_matrix, columns = cols)
    trans_matrix.index = cols


steady_state = pd.DataFrame(trans_matrix.T.iloc[:,0])

steady_state['probs'] = (new_df.groupby(['key'])['size'].sum()/new_df['size'].sum())


candle_test['run'] = (candle_test['pos_neg'] != candle_test['pos_neg'].shift()).astype(int).cumsum()

runs = candle_test.groupby('run',as_index=False).agg('size') 

candle_test = candle_test.merge(runs, how = 'left')

candle_test['size'] = candle_test['size'] * candle_test['pos_neg']


x = candle_test[['run','size']].drop_duplicates()
plt.hist(x['size'], bins = 10)

size = x.groupby(['size']).size()

size_new = size.reset_index().sort_values('size',ascending = False)
size_new.columns = ['size','count']

size_new.loc[size_new['size']>0,'cumsum'] = size_new['count'].cumsum()

size_new = size_new.sort_values('size')
size_new.loc[size_new['size']<0,'cumsum'] = size_new['count'].cumsum()
size_new['prob'] = size_new['count'] / size_new['cumsum']

