import os
import copy
import xlwings as xw
import pandas as pd
from kiteconnect import KiteConnect
import time


class OptionChain:

    def __init__(self, api_key, access_token):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token=access_token)
        self.Exchange = None
        self.prev_info = {"Symbol": None, "Expiry": None}
        self.instruments_dict = {}
        self.option_data = {}

    def instruments(self, symbol, expiry):
        self.instruments_dict = {}
        self.option_data = {}
        if self.Exchange is None:
            while True:
                try:
                    self.Exchange = pd.DataFrame(self.kite.instruments("NFO"))
                    break
                except:
                    pass
        if symbol and not expiry is None:
            try:
                df = copy.deepcopy(self.Exchange)
                df = df[(df["segment"] == "NFO-OPT") &
                        (df["name"] == symbol.upper())]
                df = df[df["expiry"] == sorted(list(df["expiry"].unique()))[expiry]]
                for i in df.index:
                    self.instruments_dict[f'NFO:{df["tradingsymbol"][i]}'] = {"Strike": float(df["strike"][i]),
                                                                              "Segment": df["segment"][i],
                                                                 "Instrument Type": df["instrument_type"][i],
                                                                 "Expiry": df["expiry"][i],
                                                                 "Lot": df["lot_size"][i]}
            except:
                pass
        self.prev_info = {"Symbol": symbol, "Expiry": expiry}
        return self.instruments_dict

    def quote(self, instruments):
        if instruments:
            try:
                data = self.kite.quote(instruments)
                for symbol, values in data.items():
                    try:
                        self.option_data[symbol[4:]]
                    except:
                        self.option_data[symbol[4:]] = {}
                    self.option_data[symbol[4:]]["Strike"] = self.instruments_dict[symbol]["Strike"]
                    self.option_data[symbol[4:]]["Lot"] = self.instruments_dict[symbol]["Lot"]
                    self.option_data[symbol[4:]]["Expiry"] = self.instruments_dict[symbol]["Expiry"]
                    self.option_data[symbol[4:]]["Instument Type"] = self.instruments_dict[symbol]["Instrument Type"]
                    self.option_data[symbol[4:]]["Open"] = values["ohlc"]["open"]
                    self.option_data[symbol[4:]]["High"] = values["ohlc"]["high"]
                    self.option_data[symbol[4:]]["Low"] = values["ohlc"]["low"]
                    self.option_data[symbol[4:]]["Ltp"] = values["last_price"]
                    self.option_data[symbol[4:]]["Close"] = values["ohlc"]["close"]
                    self.option_data[symbol[4:]]["Volume"] = values["volume"]
                    self.option_data[symbol[4:]]["Vwap"] = values["average_price"]
                    self.option_data[symbol[4:]]["OI"] = values["oi"]
                    self.option_data[symbol[4:]]["OI High"] = values["oi_day_high"]
                    self.option_data[symbol[4:]]["OI Low"] = values["oi_day_low"]
                    self.option_data[symbol[4:]]["Buy Qty"] = values["buy_quantity"]
                    self.option_data[symbol[4:]]["Sell Qty"] = values["sell_quantity"]
                    self.option_data[symbol[4:]]["Ltq"] = values["last_quantity"]
                    self.option_data[symbol[4:]]["Change"] = values["net_change"]
                    self.option_data[symbol[4:]]["Bid Price"] = values["depth"]["buy"][0]["price"]
                    self.option_data[symbol[4:]]["Bid Qty"] = values["depth"]["buy"][0]["quantity"]
                    self.option_data[symbol[4:]]["Ask Price"] = values["depth"]["sell"][0]["price"]
                    self.option_data[symbol[4:]]["Ask Qty"] = values["depth"]["sell"][0]["quantity"]
            except:
                pass
        return self.option_data

    def to_excel(self):
        if not os.path.exists("Trading.xlsx"):
            wb = xw.Book()
            wb.sheets.add("OptionChain")
            wb.save('Trading.xlsx')
            wb.close()

        wb = xw.Book('Trading.xlsx')

        oc = wb.sheets("OptionChain")
        oc.range("a1").value = "Symbol"
        oc.range("a2").value = "Expiry"
        while True:
            try:
                try:
                    symbol = oc.range("b1").value.upper()
                    expiry = int(oc.range("b2").value)
                except:
                    symbol, expiry = None, None
                if self.prev_info["Symbol"] != symbol or self.prev_info["Expiry"] != expiry:
                    oc.range("d:z").value = None
                    self.instruments(symbol, expiry=expiry)
                oc.range("d1").value = pd.DataFrame(self.quote(list(self.instruments_dict.keys()))).transpose()
                time.sleep(1)
            except:
                break


def user_info():
    print("----Option Chain----")
    api_key = input("Enter Kite Api Key : ")
    access_token = input("Enter Kite Access Token : ")
    return {"api_key": api_key, "access_token": access_token}


info = user_info()

a = OptionChain(api_key=info["api_key"],access_token=info["access_token"])
a.to_excel()

