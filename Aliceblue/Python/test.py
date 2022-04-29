# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 17:56:12 2022

@author: naman
"""

import pandas as pd
import numpy as np

instrument = alice.get_instrument_by_symbol('NSE', 'Nifty Bank')
df = fetchOHLC(instrument, 100, pd.to_datetime('2022-04-26'), '1_MIN', indices=True)
df['DATE'] = df.index.date
mean_df = df.groupby('DATE',as_index = False)['close'].mean()
mean_df.columns = ['DATE','Avg_close']

day_df = df.groupby('DATE').agg({'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last'], 'volume' : ['sum']})
day_df.columns = ['open_day','high_day','low_day','close_day','volume_day']
day_df = day_df.reset_index()

df1 = df.merge(mean_df, on = 'DATE').merge(day_df, on ='DATE')
df1.index = df.index

min_dates = df1.reset_index().groupby('DATE')['date'].min().tolist()
df2 = df1[df1.index.isin(min_dates)]
df2['prev_avg'] = df2['Avg_close'].shift(1)
df2['diff_op'] = df2['open'] > df2['prev_avg']
df2['diff_cp'] = df2['close_day'] > df2['prev_avg']






