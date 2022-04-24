# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 22:37:53 2022

@author: naman
"""

from IPython import get_ipython
get_ipython().magic('reset -sf') 

from kiteconnect import KiteConnect
import os
import datetime
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.offline import plot
plt.style.use('fivethirtyeight')

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get dump of all NSE instruments
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

def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(duration), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data

nifty_bank = fetchOHLC('NIFTY BANK' ,'hour' , 8)
nifty_bank = nifty_bank.reset_index()
nifty_bank['date'] = nifty_bank['date'].dt.tz_localize(None)

plt.figure(figsize=(12.2,4.5)) #width = 12.2in, height = 4.5
plt.plot(nifty_bank.close, color='blue')
plt.title('Stock Close Price')
plt.xlabel('Date')
plt.ylabel('Price')
plt.show()

fig = go.Figure(data=[go.Candlestick(x=nifty_bank.index,
                open=nifty_bank['open'],
                high=nifty_bank['high'],
                low=nifty_bank['low'],
                close=nifty_bank['close'])])

plot(fig)

#Calculate the max and min close price
maximum_price = nifty_bank['close'].max()
max_price_ts = nifty_bank.loc[nifty_bank['close'] == maximum_price,'date'].values[0] 

minimum_price = nifty_bank['close'].min()
min_price_ts = nifty_bank.loc[nifty_bank['close'] == minimum_price,'date'].values[0] 

if(max_price_ts < min_price_ts):
    print("uptrend")
    trend = "uptrend"
    difference = maximum_price - minimum_price
    first_level = maximum_price - difference * 0.236   
    second_level = maximum_price - difference * 0.382  
    third_level = maximum_price - difference * 0.5     
    fourth_level = maximum_price - difference * 0.618 
    
    bank_nifty_fb = nifty_bank[nifty_bank['date']>=max_price_ts]
    
else:
    print("downtrend")
    trend = "downtrend"
    difference = maximum_price - minimum_price 
    first_level = minimum_price + difference * 0.236   
    second_level = minimum_price + difference * 0.382  
    third_level = minimum_price + difference * 0.5     
    fourth_level = minimum_price + difference * 0.618 
    
    bank_nifty_fb = nifty_bank[nifty_bank['date']>=min_price_ts]


def indentify_fibo_level(close):
    if(trend == "uptrend"):
        if(close == maximum_price):
            return 'Level 0'
        if((close < maximum_price) & (close >= first_level)):
            return 'Level 1'
        if((close < first_level) & (close >= second_level)):
            return 'Level 2'
        if((close < second_level) & (close >= third_level)):
            return 'Level 3'
        if((close < third_level) & (close >= fourth_level)):
            return 'Level 4'
        if((close < fourth_level) & (close > minimum_price)):
            return 'Level 5'
        if(close == minimum_price):
            return 'Level 6'
    
    else:    
        if(close == minimum_price):
            return ['Level 0',minimum_price]
        if((close > minimum_price) & (close <= first_level)):
            return ['Level 1',minimum_price]
        if((close > first_level) & (close <= second_level)):
            return ['Level 2',first_level]
        if((close > second_level) & (close <= third_level)):
            return ['Level 3',second_level]
        if((close > third_level) & (close <= fourth_level)):
            return ['Level 4',third_level]
        if((close > fourth_level) & (close < maximum_price)):
            return ['Level 5',fourth_level]
        if(close == maximum_price):
            return ['Level 6',maximum_price]
       
bank_nifty_fb['fibo_level'] = bank_nifty_fb['close'].apply(indentify_fibo_level)
bank_nifty_fb.loc[bank_nifty_fb['close'] > bank_nifty_fb['open'],'candle'] = 'green'
bank_nifty_fb.loc[bank_nifty_fb['close'] < bank_nifty_fb['open'],'candle'] = 'red'


#Print the price at each level
print("Level Percentage\t", "Price")
print("00.0%\t\t", maximum_price)
print("23.6%\t\t", first_level)
print("38.2%\t\t", second_level)
print("50.0%\t\t", third_level)
print("61.8%\t\t", fourth_level)
print("100.0%\t\t", minimum_price) 


#Plot the Fibonacci levels along with the close price
new_df = nifty_bank
plt.figure(figsize=(12.33,4.5))
plt.title('Fibonnacci Retracement Plot')
plt.plot(new_df.index, new_df['close'])
plt.axhline(maximum_price, linestyle='--', alpha=0.5, color = 'red')
plt.axhline(first_level, linestyle='--', alpha=0.5, color = 'orange')
plt.axhline(second_level, linestyle='--', alpha=0.5, color = 'yellow')
plt.axhline(third_level, linestyle='--', alpha=0.5, color = 'green')
plt.axhline(fourth_level, linestyle='--', alpha=0.5, color = 'blue')
plt.axhline(minimum_price, linestyle='--', alpha=0.5, color = 'purple')
plt.xlabel('Date',fontsize=18)
plt.ylabel('Nifty Bank Close Price',fontsize=18)
plt.show()
