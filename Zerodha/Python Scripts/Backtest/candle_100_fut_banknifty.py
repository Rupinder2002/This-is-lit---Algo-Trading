

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

############

name = 'BANKNIFTY'
name0= 'NIFTY BANK'

# NOTE  
wseries = '22FEB' # <--------------------CHANGE WEEKLY EXPIRY SERIES EVERY FRIDAY----------->
# NOTE

ltpc  = kite.ltp('NSE:' + name0 )['NSE:' + name0 ]['last_price']

df_nse = fetchOHLC('NIFTY BANK' , 'minute' , 30)  

name1 = 'BANKNIFTY22FEBFUT'

df_nfo = fetchOHLC( name1  , 'minute' , 30)

df_nse['timestamp'] = df_nse.index
# df_nse.rename(index={'date':'timestamp'})
df_nse['date'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.date
df_nse['month'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.month
df_nse['time'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.time
df_nse['hour'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.hour
df_nse['weekday'] = pd.to_datetime(df_nse['timestamp'],dayfirst=True).dt.weekday

 
df_nse['nfo_price'] = df_nfo['close']



#########

df_nse['EMA'] = talib.EMA( df_nse['close'] , 75 )

df_nse['previous_day_open'] = None
df_nse['previous_day_high'] = None
df_nse['previous_day_low'] = None
df_nse['previous_day_close'] = None


for j,i in enumerate( df_nse['date'].unique() ):
    
    try :        
        df_nse.loc[ df_nse['date'] == df_nse['date'].unique()[j + 1] , 'previous_day_open'  ] =  df_nse.loc[ df_nse['date'] ==  i , 'open'  ].iloc[0]
        df_nse.loc[ df_nse['date'] == df_nse['date'].unique()[j + 1] , 'previous_day_high'  ] =  df_nse.loc[ df_nse['date'] ==  i , 'high'  ].max()
        df_nse.loc[ df_nse['date'] == df_nse['date'].unique()[j + 1] , 'previous_day_low'  ] =  df_nse.loc[ df_nse['date'] ==  i , 'low'  ].min()
        df_nse.loc[ df_nse['date'] == df_nse['date'].unique()[j + 1] , 'previous_day_close'  ] =  df_nse.loc[ df_nse['date'] ==  i , 'close'  ].iloc[-1]
                        
    except :        
        pass
    
df_nse['PP'] = ( df_nse['previous_day_high'] + df_nse['previous_day_low'] + df_nse['previous_day_close'] )/3


df_nse['res_1'] = 2*df_nse['PP'] - df_nse['previous_day_low']
df_nse['sup_1'] = 2*df_nse['PP'] - df_nse['previous_day_high']

df_nse = df_nse[df_nse['date'] >= df_nfo.index[0].date()]

df_nse.dropna(how = 'any' , inplace=True)
#######################

df_nse['move'] = None
in_trade = 'OFF'     # OFF , CALL_BUY , CALL_BUY_ON , CALL_SELL,  PUT_BUY , PUT_BUY_ON , PUT_SELL
df_nse['buying_price'] = None
df_nse['stoploss'] = None
df_nse['target'] = None
df_nse['exit_reason'] = None




for j in range (len(df_nse)) :

    previous_day_high = df_nse['previous_day_high'].iloc[j]
    previous_day_low = df_nse['previous_day_low'].iloc[j]
    res_1 = df_nse['res_1'].iloc[j]
    sup_1 = df_nse['sup_1'].iloc[j]
    
    candle = df_nse.resample('5min').agg({ 'open' : ['first'] , 'high' : ['max'] ,'low' : ['min'] ,'close' : ['last'] ,  'EMA' : ['last']})  #check if M is minutes or months
    candle.columns = ['O','H','L','C','EMA']
    candle.dropna(how = 'all',inplace = True)
    candle['diff'] = candle['C'] - candle['O']  
    
    
    if (in_trade == 'OFF' or in_trade == 'SELL_CALL' or in_trade == 'SELL_PUT')   :
        
        if (df_nse['timestamp'].iloc[j] in candle.index) and (df_nse.index[j].time() < datetime.time(15,0)) and j >=5 :
        
            # if (candle[candle.index == df_nse.index[j-5]]['C'][0] - candle[candle.index == df_nse.index[j-5]]['O'][0] > 100)  :
            if (candle[candle.index == df_nse.index[j-5]]['diff'][0]) > 100  :
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
                                    
            # elif (candle[candle.index == df_nse.index[j-5]]['C'][0] - candle[candle.index == df_nse.index[j-5]]['O'][0] < -100) : 
            elif (candle[candle.index == df_nse.index[j-5]]['diff'][0]) < -100 :
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
            stoploss = round(target - 20,2)
            target = round(target + 20)
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
            stoploss = round(target + 20,2)
            target = round(target - 20)
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

# summary = summary[summary['date'] > datetime.date(2022,1,15)]

summary['diff'].sum()

# summary['diff'] = None
########

# Change close to high in selling


























########

# par = ['hour', 'weekday', 'buy_or_sell', 'no_of_trades' , 'previous_day_range', 'previous_trade','successive_candle']

# output = sum([list(map(list, combinations(par, i))) for i in range(len(par) + 1)], [])


# x = summary.pivot_table(index = 'date' , values = 'diff' , aggfunc = np.size ).apply(lambda x : x/2)

######## ROUGH WORK ##########

# summary.set_index('timestamp',inplace=True)

# summary['day_trades'] = None

# summary.loc[ (summary['move'] == 'SELL_CALL') | (summary['move'] == 'SELL_PUT') , 'day_trades'] = x.values






