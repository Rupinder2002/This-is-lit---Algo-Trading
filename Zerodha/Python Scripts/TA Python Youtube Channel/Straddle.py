from kiteconnect import KiteConnect
import pickle, sys
import datetime
import pandas as pd

api_key = ""
kite = KiteConnect(api_key=api_key)
access_token = ""
kite.set_access_token(access_token)


def straddle():
    df = pd.DataFrame(kite.instruments("NFO"))
    df = df[df["segment"] == "NFO-OPT"]
    instrument = input("Enter Instrument Name : ").upper()
    if instrument in list(df["name"].unique()):
        df = df[df["name"] == instrument]
    else:
        print("Select Valid Instrument, Listed in NFO!!!!!!")
        sys.exit()

    df = df[df["expiry"] == sorted(list(df["expiry"]))[0]]

    def closest(lst, K):
        return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

    instrument_for_ltp = "NSE:NIFTY 50" if instrument == "NIFTY" else ("NSE:NIFTY BANK" if instrument == "BANKNIFTY" else f"NSE:{instrument}")
    ltp = kite.ltp(instrument_for_ltp)[instrument_for_ltp]["last_price"]
    print(f"Ltp : {ltp}")

    df = df[df["strike"] == float(closest(list(df["strike"]), ltp))]

    print(list(df["tradingsymbol"]))
    for symbol in list(df["tradingsymbol"]):
        try:
            kite.place_order(variety=kite.VARIETY_REGULAR,
                             exchange=kite.EXCHANGE_NFO,
                             tradingsymbol=symbol,
                             transaction_type=kite.TRANSACTION_TYPE_SELL,
                             quantity=list(df["lot_size"])[0],
                             product=kite.PRODUCT_MIS,
                             order_type=kite.ORDER_TYPE_MARKET,
                             validity=kite.VALIDITY_DAY)
            print("Order Placed")
        except Exception as e:
            print(f"{e}")


straddle()
