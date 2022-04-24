import copy
import pandas as pd
from kiteconnect import KiteConnect
from time import sleep
from datetime import time, datetime


class BankNiftyOptionSelling:

    def __init__(self, api_key, access_token, no_of_lots_to_trade,
                 spot_prev_day_high, spot_prev_day_low):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token=access_token)

        # "BANKNIFTY" option selling
        self.no_of_lots = no_of_lots_to_trade
        self.prev_day_high = spot_prev_day_high
        self.prev_day_low = spot_prev_day_low

        self.algo_start_time = time(9, 25)
        self.auto_square_off = time(15, 15)
        self.Exchange = None
        self.spot_ohlc = None
        self.lot_size = None
        self.opt_ce_symbol = None
        self.opt_pe_symbol = None
        self.opt_ce_ltp = None
        self.opt_pe_ltp = None
        self.entry = None
        self.exit = None

        if self.Exchange is None:
            while True:
                try:
                    self.Exchange = pd.DataFrame(self.kite.instruments("NFO"))
                    print("Exchange Downloaded..")
                    break
                except:
                    sleep(1)

    def instruments(self, strike):
        df = copy.deepcopy(self.Exchange)
        df = df[(df["segment"] == "NFO-OPT") &
                (df["name"] == "BANKNIFTY")]
        df = df[df["expiry"] == sorted(list(df["expiry"].unique()))[0]]

        def closest(lst, K):
            return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]
        df = df[df["strike"] == float(closest(list(df["strike"]),strike))]
        for i in df.index:
            if self.lot_size is None:
                self.lot_size = df["lot_size"][i]
                print(f"Lot size : {self.lot_size}")
            if df["instrument_type"][i] == "CE":
                self.opt_ce_symbol = df["tradingsymbol"][i]
                print(f'Opt Symbol added : {df["tradingsymbol"][i]}')
            elif df["instrument_type"][i] == "PE":
                self.opt_pe_symbol = df["tradingsymbol"][i]
                print(f'Opt Symbol added : {df["tradingsymbol"][i]}')

    def get_spot_ohlc(self):
        try:
            self.spot_ohlc = self.kite.quote("NSE:NIFTY BANK")["NSE:NIFTY BANK"]["ohlc"]
        except:
            pass

    def get_opt_premium(self):
        try:
            data = self.kite.ltp([f"NFO:{self.opt_ce_symbol}", f"NFO:{self.opt_pe_symbol}"])
            for symbol, values in data.items():
                if symbol[4:] == self.opt_ce_symbol:
                    self.opt_ce_ltp = values["last_price"]
                if symbol[4:] == self.opt_pe_symbol:
                    self.opt_pe_ltp = values["last_price"]
        except:
            pass

    def place_order(self, symbol, direction):
        if self.no_of_lots:
            try:
                order_id = self.kite.place_order(
                    variety=self.kite.VARIETY_REGULAR,
                    exchange=self.kite.EXCHANGE_NFO,
                    tradingsymbol=symbol,
                    transaction_type=self.kite.TRANSACTION_TYPE_SELL
                    if direction.upper() == "SELL" else self.kite.TRANSACTION_TYPE_BUY,
                    quantity=self.lot_size*self.no_of_lots,
                    product=self.kite.PRODUCT_MIS,
                    order_type=self.kite.ORDER_TYPE_MARKET,
                    validity=self.kite.VALIDITY_DAY)

                print(f" {symbol} : {direction.upper()} Order {order_id}")
            except Exception as e:
                print(f"{symbol} : {direction.upper()} Order {e}")

    def strategy(self):
        while datetime.now().time() <= self.algo_start_time:
            sleep(1)
        while self.spot_ohlc is None:
            self.get_spot_ohlc()
            sleep(1)
        # get opt symbol
        print(f"BANKNIFTY ohlc : {self.spot_ohlc}")
        if self.prev_day_high >= self.spot_ohlc['high'] and self.prev_day_low <= self.spot_ohlc['low']:
            self.instruments(strike=self.spot_ohlc["open"])
            # get ltp
            while self.opt_ce_ltp is None or self.opt_pe_ltp is None:
                self.get_opt_premium()
                sleep(1)

            stop_loss = None
            while True:
                sleep(2)
                self.get_opt_premium()

                # entry
                if self.entry is None:
                    self.entry = True
                    print(f"Symbol {self.opt_ce_symbol} SELL {self.opt_ce_ltp} at time {datetime.now().time()}")
                    print(f"Symbol {self.opt_pe_symbol} SELL {self.opt_pe_ltp} at time {datetime.now().time()}")
                    self.place_order(self.opt_ce_symbol, "SELL")
                    self.place_order(self.opt_pe_symbol, "SELL")

                # stop loss
                combined_premium = self.opt_ce_ltp + self.opt_pe_ltp
                if self.entry and stop_loss is None:
                    stop_loss = combined_premium + (combined_premium * 0.10)
                    print("Initial Stop loss at : ", round(stop_loss, 2))
                # trail stop loss
                if self.entry and stop_loss > combined_premium + (combined_premium * 0.10):
                    stop_loss = combined_premium + (combined_premium * 0.10)

                # exit
                if self.entry and self.exit is None and (stop_loss < combined_premium or
                                                         datetime.now().time() > self.auto_square_off):
                    self.exit = True
                    print(f"Symbol {self.opt_ce_symbol} BUY {self.opt_ce_ltp} at time {datetime.now().time()}")
                    print(f"Symbol {self.opt_pe_symbol} BUY {self.opt_pe_ltp} at time {datetime.now().time()}")
                    self.place_order(self.opt_ce_symbol, "BUY")
                    self.place_order(self.opt_pe_symbol, "BUY")
                    break
        print("Trading Done...")


def user_info():
    print("----BankNifty Option Selling Algo Started----")
    api_key = input("Enter Kite Api Key : ")
    access_token = input("Enter Kite Access Token : ")
    no_of_lots_to_trade = int(float(input("Enter no of lots to trade : ")))
    spot_prev_day_high = float(input("Enter BankNifty PrevDay High : "))
    spot_prev_day_low = float(input("Enter BankNifty PrevDay Low : "))
    return {"api_key": api_key,"access_token": access_token,"lotstotrade": no_of_lots_to_trade,
            "prev_day_high": spot_prev_day_high, "prev_day_low": spot_prev_day_low}


info = user_info()


bos = BankNiftyOptionSelling(api_key=info["api_key"],
                             access_token=info["access_token"],
                             no_of_lots_to_trade=info["lotstotrade"],
                             spot_prev_day_high=info["prev_day_high"],
                             spot_prev_day_low=info["prev_day_low"])
bos.strategy()