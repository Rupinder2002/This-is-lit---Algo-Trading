import yfinance as yf
import talib
import pandas as pd
import copy
import numpy as np
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

#["TATAMOTORS", "Reliance", "Upl"]
tickers = ["ZEEL","WIPRO","VEDL","ULTRACEMCO","UPL","TITAN","TECHM","TATASTEEL",
           "TATAMOTORS","TCS","SUNPHARMA","SBIN","SHREECEM","RELIANCE","POWERGRID",
           "ONGC","NESTLEIND","NTPC","MARUTI","M&M","LT","KOTAKBANK","JSWSTEEL","INFY",
           "INDUSINDBK","IOC","ITC","ICICIBANK","HDFC","HINDUNILVR","HINDALCO",
           "HEROMOTOCO","HDFCBANK","HCLTECH","GRASIM","GAIL","EICHERMOT","DRREDDY",
           "COALINDIA","CIPLA","BRITANNIA","BHARTIARTL","BPCL","BAJAJFINSV",
           "BAJFINANCE","BAJAJ-AUTO","AXISBANK","ASIANPAINT","ADANIPORTS"]

df = pd.DataFrame()

for ticker in tickers:
    data = yf.Ticker(f"{ticker}.NS").history(interval="5m",start = '2021-01-01', end = '2021-01-30')
    data['ticker'] = ticker
    df = df.append(data)


def symbols_backtesting(symbol_list):
    all_trades = []
    for symbol in symbol_list:
        df = yf.Ticker(f"{symbol}.NS").history(period="2y", interval="1h")
        df["MA_10"] = talib.MA(df["Close"], timeperiod=5)
        df["MA_50"] = talib.MA(df["Close"], timeperiod=20)
        df["RSI_14"] = talib.RSI(df["Close"], timeperiod=14)
        # df["ATR_14"] = talib.ATR(df["High"], df["Low"], df["Close"], timeperiod=14)
        # df["Upper_Band"], df["Middle_Band"], df["Lower_Band"] = talib.BBANDS(df["Close"], timeperiod=20,
        #                                                                      nbdevup=2,nbdevdn=2)

        trade = {"Symbol": None, "Buy/Sell": None, "Entry": None, "Entry Date": None, "Exit": None, "Exit Date": None}
        # print(df)
        position = None
        for i in df.index[49:]:
            if df["MA_10"][i] > df["MA_50"][i] and df["RSI_14"][i] > 70 and position != "Buy":
                if trade["Symbol"] is not None:
                    trade["Exit"] = df["Close"][i]
                    trade["Exit Date"] = i
                    all_trades.append(copy.deepcopy(trade))
                if position is not None:
                    trade["Symbol"] = symbol
                    trade["Buy/Sell"] = "Buy"
                    trade["Entry"] = df["Close"][i]
                    trade["Entry Date"] = i
                position = "Buy"
            if df["MA_10"][i] < df["MA_50"][i] and df["RSI_14"][i] < 30 and position != "Sell":
                if trade["Symbol"] is not None:
                    trade["Exit"] = df["Close"][i]
                    trade["Exit Date"] = i
                    all_trades.append(copy.deepcopy(trade))
                if position is not None:
                    trade["Symbol"] = symbol
                    trade["Buy/Sell"] = "Sell"
                    trade["Entry"] = df["Close"][i]
                    trade["Entry Date"] = i
                position = "Sell"
    return all_trades


symbol_list = ["TATAMOTORS", "Reliance", "Upl"]

data = symbols_backtesting(symbol_list)
if data:
    risk_percent = 5/100
    df = pd.DataFrame(data)
    df["P/L"] = np.where(df["Buy/Sell"] == "Buy", (100*(df["Exit"] - df["Entry"])/df["Entry"])*risk_percent,
                         (100*(df["Entry"] - df["Exit"])/df["Entry"])*risk_percent)
    df = df[df["Buy/Sell"] == "Buy"].reset_index(drop=True)

    df["Probability"] = 100*(np.where(df["P/L"] > 0, 1, 0).cumsum())/(np.where(df["P/L"] != np.NaN, 1, 0).cumsum())
    df["Return"] = df["P/L"].cumsum()
    df["Drawdown"] = df["Return"] - (df["Return"].cummax().apply(lambda x: x if x > 0 else 0))

    print(df)
else:
    print("No Trades")









