from kiteconnect import KiteConnect
import os
import datetime as dt
import pandas as pd

cwd = os.chdir("F:\\Zerodha KiteConnect API")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)
#instrument_df.to_csv("NSE_Instruments_31122019.csv",index=False)

#get dumo of all NFO instruments
nfo_instrument_dump = kite.instruments("NFO")
nfo_instrument_df = pd.DataFrame(nfo_instrument_dump)
fut_df = nfo_instrument_df[nfo_instrument_df["segment"]=="NFO-FUT"]

def instrumentLookup(dataframe,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return dataframe[dataframe.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1

def duration(interval):
    if interval == 'minute':
        return(60)
    if interval in ['3minute','5minute','10minute']:
        return(100)
    if interval in ['15minute','30minute']:
        return(200)
    if interval == '60minute':
        return(400)
    if interval == 'day':
        return(2000)
    else:
        return -1

def fetchOHLC(dataframe,ticker,inception_date, interval,date_format = '%d-%m-%Y'):
    """extracts historical data and outputs in the form of dataframe
       inception date string format - dd-mm-yyyy"""
       
    instrument = instrumentLookup(dataframe,ticker)
    from_date = dt.datetime.strptime(inception_date, date_format )
    to_date = dt.date.today()
    data = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume','date','time'])
    while True:
        if from_date.date() >= (dt.date.today() - dt.timedelta(duration(interval))):
            data = data.append(pd.DataFrame(kite.historical_data(instrument,from_date,dt.date.today(),interval)),ignore_index=True)
            break
        else:
            to_date = from_date + dt.timedelta(100)
            data = data.append(pd.DataFrame(kite.historical_data(instrument,from_date,to_date,interval)),ignore_index=True)
            from_date = to_date
    
    data['date'] = pd.to_datetime(data['timestamp']).dt.date
    data['time'] = pd.to_datetime(data['timestamp']).dt.time
    
    data.set_index("date",inplace=True)
    return data

infy_eq_ohlc = fetchOHLC(instrument_df,"INFY","20-08-2019","5minute")
nifty_fut_ohlc = fetchOHLC(nfo_instrument_df,"NIFTY20OCTFUT","20-09-2021","5minute")
