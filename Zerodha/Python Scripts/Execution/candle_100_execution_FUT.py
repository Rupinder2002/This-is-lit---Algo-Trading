# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 23:29:52 2022

@author: ANMOL
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 20:55:56 2022

@author: ANMOL
"""

from kiteconnect import KiteTicker, KiteConnect
import datetime
import datetime as dt
import sys
import pandas as pd
import os
import pymongo
import talib

cwd = os.chdir("C:/Users/ANMOL/Desktop/zerodha")
client=pymongo.MongoClient('mongodb://localhost:27017/')
collect=client['Ticks']
#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

db=collect['260105']
df = pd.DataFrame(db.find())

instrument_dump = kite.instruments("NSE")
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

instrumentLookup(instrument_df,'NIFTY BANK')
ohlc_day = fetchOHLC('NIFTY BANK', 'day',5)

trade_dict = {}
traded_stock = []

call_lock={}
put_lock={}
quant = 25

name = 'BANKNIFTY'
name0= 'NIFTY BANK'

# NOTE  
wseries = '22FEB' # <--------------------CHANGE WEEKLY EXPIRY SERIES EVERY FRIDAY----------->
# NOTE

name1 = name + wseries + 'FUT'

ltpc  = kite.ltp('NSE:' + name0 )['NSE:' + name0 ]['last_price']
print("Current BankNifty Spot price :", ltpc)
CE_exit_time = "NA"
PE_exit_time = "NA"

df = pd.DataFrame(db.find())    
df.set_index('exchange_timestamp' , inplace = True)
df = df[['last_price']]

##########

in_trade = False
last_candle = None

while True:
    now = datetime.datetime.now()
    if (now.hour >= 9 and now.minute >= 15 ):

        # define variables

        df = pd.DataFrame(db.find())    
        df.set_index('exchange_timestamp' , inplace = True)
        df = df[['last_price']]

        candle = df.resample('5min').agg({ 'last_price' : ['first','last'] })  #check if M is minutes or months
        candle.columns = ['O','C']    
        candle = candle.iloc[:-1,:]
        candle['diff'] = candle['C'] - candle['O']

        
        if in_trade :
            
            time_now = datetime.datetime.now().time()
            ltpc  = kite.ltp('NSE:' + name0 )['NSE:' + name0 ]['last_price']
            ltp1  = kite.ltp('NFO:' + name1)['NFO:' + name1]['last_price']

            check1 = (ltp1 >= target1 and entry_order_id_1 == 1) or (ltp1 <= target1 and entry_order_id_1 == -1) 
            check2 = (ltp1 <= stop_loss1 and entry_order_id_1 == 1) or (ltp1 >= stop_loss1 and entry_order_id_1 == -1) 
            # check2 = ltp1 <= stop_loss1
            check3 = time_now >= datetime.time(15, 0)
            
            if check1 :
                stoploss1 = round(target1 - 10*entry_order_id_1,2)
                target1 = round(target1 + 10*entry_order_id_1,2)
        
            elif check2 or check3 :
                exit_time = datetime.datetime.now().replace(microsecond=0)
                call_lock={"ltp1":ltp1, 'name':name, 'status':check1, 'ex_time':exit_time}
                
                current_traded_price = round((ltp1),2)
                cepoints = round((current_traded_price - trade_dict['traded_price'] )*entry_order_id_1,2)
                PNL = round((cepoints*25),2)
                
                trade_dict.update({'CE_exit_price':ltp1, 'CE_stop_loss_time':CE_exit_time, "exit_traded_price":current_traded_price,'exit_time': exit_time, 'PNL': PNL})
                traded_stock.append(trade_dict)
                print(trade_dict)
                res = pd.DataFrame(traded_stock)
                print(res)

                in_trade = False

                 
        
        else :
            
            # if candle['C'].iloc[-1] - candle['O'].iloc[-1] > 100 :
            if candle['diff'].iloc[-1]  > 100 and last_candle != candle.index[-1]:
                
                ltpc  = kite.ltp('NSE:' + name0 )['NSE:' + name0 ]['last_price']
                print("Current BankNifty Spot price :", ltpc)            

                

                
                ltp1  = kite.ltp('NFO:' + name1)['NFO:' + name1]['last_price']
                
                ATM_dict={"ATM_Spot": ltpc}
                
                ### trade execution ###
                
                print("we will BUY a CALL NOW")
                entry_order_id_1 = 1

                traded_time = datetime.datetime.now().replace(microsecond=0)
                traded_price = round((ltp1),2)
                
                stop_loss1 = round((ltp1 - 20),2)
                target1 = round((ltp1 + 50 ),2)
                
                trade_dict = {"name":name, "status":"CALL",  "strike_price":ltp1, "quantity":quant, "call_entry_price":ltp1, "traded_time":traded_time, "traded_price":traded_price, "stop_loss_CE":stop_loss1}
                
                print(trade_dict)
                
                in_trade = True
        
            # elif candle['C'].iloc[-1] - candle['O'].iloc[-1] < -100 :
            elif candle['diff'].iloc[-1]  < -100 and last_candle != candle.index[-1] :
                
                ltpc  = kite.ltp('NSE:' + name0 )['NSE:' + name0 ]['last_price']
                print("Current BankNifty Spot price :", ltpc)        
                                
                
                ltp1  = kite.ltp('NFO:' + name1)['NFO:' + name1]['last_price']
                
                ### trade execution ###
                
                print("we will BUY a PUT NOW")
                entry_order_id_1 = -1

                traded_time = datetime.datetime.now().replace(microsecond=0)
                traded_price = round((ltp1),2)
                
                stop_loss1 = round((ltp1 + 20),2)
                target1 = round((ltp1 - 50),2)
                
                trade_dict = {"name":name, "status":"PUT",  "strike_price":ltp1, "quantity":quant, "put_entry_price":ltp1, "traded_time":traded_time, "traded_price":traded_price, "stop_loss_PEE":stop_loss1}
                
                print(trade_dict)
            
                in_trade = True

        last_candle = candle.index[-1]

    if (now.hour >= 15 and now.minute >= 30):
        break          
                
                
             
                
                
                
                
                
                