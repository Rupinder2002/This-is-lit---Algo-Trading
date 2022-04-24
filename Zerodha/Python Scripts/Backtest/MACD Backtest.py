# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 22:37:10 2022

@author: naman
"""

import pandas as pd
import numpy as np
import os 

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

#historical_df = pd.read_csv('Data/Tickers Historical Data.csv')
historical_df = pd.read_csv('Data/NIFTY_2008_2020.csv')
ticker_df = historical_df.copy()

ticker_df = ticker_df.reset_index(drop = True)
ticker_df['date'] = pd.to_datetime(ticker_df['date'],format = '%Y%m%d').dt.date
ticker_df['timestamp'] = pd.to_datetime(ticker_df['date'].astype(str) +' ' + ticker_df['time'])
ticker_df.set_index('timestamp',inplace = True)

def MACD(DF,a,b,c):
    """function to calculate MACD
       typical values a(fast moving average) = 12; 
                      b(slow moving average) =26; 
                      c(signal line ma window) =9"""
    df = DF.copy()
    df["MA_Fast"]=df["close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return df

ticker_df_1 = ticker_df.resample('120min').agg({'ticker':['first'],'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last']})  #check if M is minutes or months
ticker_df_1.dropna(how = 'all',inplace = True)
ticker_df_1.columns = ['ticker','open','high','low','close']
ticker_df_1['date'] = pd.to_datetime(ticker_df_1.index).date
ticker_df_1['days'] = ticker_df_1.groupby(['ticker']).cumcount()+1
ticker_df_1['days'] = np.ceil(ticker_df_1['days']/26)

macd = MACD(ticker_df_1,12,26,9)

macd['lag_macd'] = macd['MACD'].shift(1)
macd['lag_signal'] = macd['Signal'].shift(1)
macd.loc[(macd['lag_macd'] < macd['lag_signal']) & (macd['MACD'] > macd['Signal']),'trend'] = 'bull'
macd.loc[(macd['lag_macd'] > macd['lag_signal']) & (macd['MACD'] < macd['Signal']),'trend'] = 'bear'

macd['support'] = macd.groupby(['days'])['close'].transform(min)
macd['target'] = macd['trade_price'] * 1.05

import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

start_date = '2018-01-03'
end_date = '2018-01-15'

new_df = macd[(macd['date']>=pd.to_datetime(start_date)) & (macd['date']<=pd.to_datetime(end_date))]
plt.figure(figsize=(12.33,4.5))
plt.title('MACD')
plt.plot(new_df.index, new_df['MACD'])
plt.plot(new_df['Signal'], color = 'red')
plt.xlabel('Date',fontsize=18)
#plt.ylabel('Nifty Bank Close Price',fontsize=18)
plt.show()



def macd_backtest(data,start_date,end_date,short_term_look_back_period,long_term_look_back_period,per_stock_initial_investment):
    
    data = data[(data['date']>=pd.to_datetime(start_date)) & (data['date']<=pd.to_datetime(end_date))]
    
    order_df = pd.DataFrame(columns = ['ticker','timestamp','order_type','order_reason','trade_price','quantity','balance','target','stop_loss','stt_value', 'transcation_charges_value', 'gst_value', 'sebi_value', 'stamp_value'])
    return_df = pd.DataFrame(columns = ['ticker','initial_investment','ending_investment_value','return_pct'])
    
    for ticker in data.ticker.drop_duplicates().values:
        balance = per_stock_initial_investment
        total_charges = 0
        order_type = 'No Open Orders'

        #print('Algo running for: ', ticker)

        data = MACD(data,short_term_look_back_period,long_term_look_back_period,9)

        ticker_df_filtered = data[data['ticker'] == ticker]

        for j in range(1,len(ticker_df_filtered)):
        
            if order_type == 'No Open Orders':
            
                if (ticker_df_filtered['MACD'][j-1] < ticker_df_filtered['Signal'][j-1]) and (ticker_df_filtered['MACD'][j] > ticker_df_filtered['Signal'][j]):
            
                    timestamp = ticker_df_filtered.index[j]
                    order_type = 'BUY'
                    order_reason = 'MACD Crossover'
                    trade_price = ticker_df_filtered['close'][j]
                    stop_loss = ticker_df_filtered['support'][j]
                    target = ticker_df_filtered['target'][j]
                    quantity = np.floor(balance/trade_price)
                    transcation_value = None
                    stt_value = None
                    transcation_charges_value = None
                    gst_value = None
                    sebi_value = None
                    stamp_value = None
                    total_charges = None
        
                    balance = balance - (trade_price * quantity)
            
                    trade = pd.DataFrame([[ticker,timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,
                                           stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
        
                    order_df = order_df.append(trade)
                    
                else:
                    order_type = 'No Open Orders'
                
            elif order_type == 'BUY' or order_type == 'HOLD':
                current_price = ticker_df_filtered['close'].iloc[j]
                
                if j == len(ticker_df_filtered)-1:
                    timestamp = ticker_df_filtered.index[j]
                    order_type = 'SELL'
                    order_reason = 'Closed Open Position'
                    trade_price = current_price
                    target = None
                    stop_loss = None
                    transcation_value = (trade_price + trade['trade_price'][0]) * quantity
                    stt_value = stt * transcation_value
                    transcation_charges_value = transcation_charges * transcation_value
                    gst_value = gst * transcation_charges_value
                    sebi_value = sebi_charges * transcation_value 
                    stamp_value = trade['trade_price'][0] * stamp_charges * quantity
                    total_charges = stt_value + transcation_charges_value + gst_value + sebi_value + stamp_value
        
                    balance = balance + (trade_price * quantity) - total_charges
            
                    trade = pd.DataFrame([[ticker,timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,
                                           stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
                    
                    order_df = order_df.append(trade)
                    total_charges = 0
                    order_type = 'No Open Orders'
                                 
                elif current_price < stop_loss:
                    timestamp = ticker_df_filtered.index[j]
                    order_type = 'SELL'
                    order_reason = 'Stop Loss Hit'
                    trade_price = stop_loss
                    target = None
                    stop_loss = None
                    transcation_value = (trade_price + trade['trade_price'][0]) * quantity
                    stt_value = stt * transcation_value
                    transcation_charges_value = transcation_charges * transcation_value
                    gst_value = gst * transcation_charges_value
                    sebi_value = sebi_charges * transcation_value 
                    stamp_value = trade['trade_price'][0] * stamp_charges * quantity
                    total_charges = stt_value + transcation_charges_value + gst_value + sebi_value + stamp_value
        
                    balance = balance + (trade_price * quantity) - total_charges
            
                    trade = pd.DataFrame([[ticker,timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,
                                           stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
                    
                    order_df = order_df.append(trade)
                    
                    total_charges = 0
                    order_type = 'No Open Orders'
                    
                elif current_price > target:
                    timestamp = ticker_df_filtered.index[j]
                    order_type = 'HOLD'
                    # stop_loss = ticker_df_filtered['support'][j]
                    # target = ticker_df_filtered['target'][j]
                     
                    trade = pd.DataFrame([[ticker,timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,
                                           stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
                    
                    order_df = order_df.append(trade)
                    
                else :
                    order_type = 'HOLD'
            
        #print(ticker,': Return %', 100 * round((balance/per_stock_initial_investment) - 1,2))
        
        ticker_return = pd.DataFrame([[ticker,per_stock_initial_investment,balance,100 * round((balance/per_stock_initial_investment) - 1,2)]],columns = return_df.columns)
        return_df = return_df.append(ticker_return)

    return [order_df,return_df]

function_res = macd_backtest(data = ticker_df_1,
                   start_date = '2016-01-01',
                   end_date = '2018-01-01',
                   short_term_look_back_period = 12,
                   long_term_look_back_period = 26,
                   per_stock_initial_investment = 100000)

order_df = function_res[0]
return_df = function_res[1]

print('Total Investment Return = ', round(100*(return_df['ending_investment_value'].sum()/return_df['initial_investment'].sum() - 1),2),'%')
