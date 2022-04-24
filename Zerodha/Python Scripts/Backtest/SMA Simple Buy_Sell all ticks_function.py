from IPython import get_ipython
get_ipython().magic('reset -sf') 

import pandas as pd
import numpy as np
import talib
import os 

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

historical_df = pd.read_csv('Data/Tickers Historical Data.csv')
ticker_df = historical_df.copy()

ticker_df = ticker_df.reset_index(drop = True)
ticker_df['date'] = pd.to_datetime(ticker_df['date'])
ticker_df['date'] = ticker_df['date'].dt.tz_localize(None)
ticker_df['timestamp'] = ticker_df['date']
ticker_df['date'] = ticker_df['timestamp'].dt.date
ticker_df.set_index('timestamp',inplace = True)

#Zerodha Charges
stt = 0.001                      #-------------on buy and sell
transcation_charges = 0.0000345  #-------------on buy and sell
gst = 0.18                       #-------------on brokerage + transaction charges
sebi_charges = 10/10000000       #-------------on buy and sell
stamp_charges = 0.00015          #-------------only on buy side

def sma_backtest(data,start_date,end_date,short_term_look_back_period,long_term_look_back_period,per_stock_initial_investment,target_pct,stoploss_pct):
    
    data = data[(data['date']>=pd.to_datetime(start_date)) & (data['date']<=pd.to_datetime(end_date))]
    
    order_df = pd.DataFrame(columns = ['ticker','timestamp','order_type','order_reason','trade_price','quantity','balance','target','stop_loss','stt_value', 'transcation_charges_value', 'gst_value', 'sebi_value', 'stamp_value'])
    return_df = pd.DataFrame(columns = ['ticker','initial_investment','ending_investment_value','return_pct'])
    
    for ticker in data.ticker.drop_duplicates().values:
        balance = per_stock_initial_investment
        total_charges = 0
        order_type = 'No Open Orders'

        #print('Algo running for: ', ticker)

        data['sma_st'] = talib.SMA(data.close,short_term_look_back_period)
        data['sma_lt'] = talib.SMA(data.close,long_term_look_back_period)
        data.dropna(inplace = True)

        ticker_df_filtered = data[data['ticker'] == ticker]

        for j in range(1,len(ticker_df_filtered)):
        
            if order_type == 'No Open Orders':
            
                if (ticker_df_filtered['sma_st'][j-1] < ticker_df_filtered['sma_lt'][j-1]) and (ticker_df_filtered['sma_st'][j] > ticker_df_filtered['sma_lt'][j]):
            
                    timestamp = ticker_df_filtered.index[j]
                    order_type = 'BUY'
                    order_reason = 'SMA Crossover'
                    trade_price = ticker_df_filtered['close'][j]
                    target = ticker_df_filtered['close'][j] * (1 + target_pct)
                    stop_loss = ticker_df_filtered['close'][j] * (1 - stoploss_pct)
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
                    stop_loss = round(current_price * (1 - stoploss_pct), 2)
                    target = round(current_price * (1 + stoploss_pct), 2)
                     
                    trade = pd.DataFrame([[ticker,timestamp,order_type,order_reason,trade_price,quantity,balance,target,stop_loss,
                                           stt_value, transcation_charges_value, gst_value, sebi_value, stamp_value]],columns = order_df.columns)
                    
                    order_df = order_df.append(trade)
                    
                else :
                    order_type = 'HOLD'
            
        #print(ticker,': Return %', 100 * round((balance/per_stock_initial_investment) - 1,2))
        
        ticker_return = pd.DataFrame([[ticker,per_stock_initial_investment,balance,100 * round((balance/per_stock_initial_investment) - 1,2)]],columns = return_df.columns)
        return_df = return_df.append(ticker_return)

    return [order_df,return_df]


function_res = sma_backtest(data = ticker_df,
                   start_date = '2016-01-01',
                   end_date = '2017-12-31',
                   short_term_look_back_period = 5,
                   long_term_look_back_period = 10,
                   per_stock_initial_investment = 30000,
                   target_pct = 0.1,
                   stoploss_pct = 0.07)

order_df = function_res[0]
return_df = function_res[1]

print('Total Investment Return = ', round(100*(return_df['ending_investment_value'].sum()/return_df['initial_investment'].sum() - 1),2),'%')
