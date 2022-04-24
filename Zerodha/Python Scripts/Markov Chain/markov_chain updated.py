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

historical_df = pd.read_csv('Data/NIFTY BANK.csv')
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

candle1 = candle.reset_index()
candle1['date'] = candle1['timestamp'].dt.date

candle_train = candle1[candle1['date'] >= pd.to_datetime('2021-01-01')]
candle_test = candle1[candle1['date'] < pd.to_datetime('2021-01-01')]

def calc_probs(data):
    data['key'] = (data['pos_neg'].shift(5)).astype(str) + ',' + (data['pos_neg'].shift(4)).astype(str) + ',' + (data['pos_neg'].shift(3)).astype(str) + ',' + (data['pos_neg'].shift(2)).astype(str) + ',' + (data['pos_neg'].shift(1)).astype(str)
    data['lag_diff'] = data['diff'].shift(1).cumsum()
    
    data = data[~data['key'].str.contains('nan')]
    
    next_poss = data.groupby(['key','pos_neg']).size()/data.groupby(['key']).size()
    next_poss = next_poss.reset_index()
    
    next_poss['next_key'] = next_poss['key'].apply(lambda x: x.split(',',1)[1])
    next_poss['next_key'] = next_poss['next_key'] + ',' + next_poss['pos_neg'].astype(str)
    
    cols = next_poss['next_key'].drop_duplicates().values
    
    matrix = next_poss.set_index(['key','next_key'])[0].unstack()
    matrix = matrix.fillna(0)
    
    for i in range(1,10):
        matrix = np.dot(matrix, matrix)
        
    matrix = pd.DataFrame(matrix, index = cols)
    
    matrix_1 = pd.DataFrame(matrix.T.iloc[:,0])
    matrix_1['key'] = cols
    
    next_poss.groupby(['key'])[0].sum()/sum(next_poss[0])
    
    
    prob = pd.DataFrame(data.groupby(['key']).size()/len(data))
    prob = prob.reset_index()
    
    
    prob_comp = prob.merge(matrix_1)
    prob_comp.columns = ['key','candle','ss']

    return prob_comp

prob_train = calc_probs(candle_train)
prob_train.columns = ['key','candle_train','SS_Train']

prob_test = calc_probs(candle_test)
prob_test.columns = ['key','candle_test','SS_Test']


full_probs = prob_test.merge(prob_train)
full_probs['% Diff'] = round((full_probs['SS_Train']/full_probs['SS_Test'] - 1) * 100,2)
                                                
                        
                        
                    