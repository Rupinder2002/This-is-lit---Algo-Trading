def fetchOHLC_LastCandle(ticker,interval,minutes):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    current = dt.datetime.today()
    current = current.replace(second = 0, microsecond=0)
    start = current - dt.timedelta(minutes = minutes)
    end = current
    data = pd.DataFrame(kite.historical_data(instrument,start, end, interval))
    data.set_index("date",inplace=True)
    return data
