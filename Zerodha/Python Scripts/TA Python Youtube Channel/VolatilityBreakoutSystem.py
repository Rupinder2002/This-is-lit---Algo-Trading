from alice_blue import *
from time import sleep
import datetime

username = "user_id"
password = 'password'
twoFA = 'two_fa'
api_secret = "api_secret"
app_id = "api_key"

access_token = AliceBlue.login_and_get_access_token(username=username, password=password, twoFA=twoFA,
                                                    api_secret=api_secret, app_id=app_id)
alice = AliceBlue(username=username, password=password, access_token=access_token)


instrument_list = ['AARTIIND', 'ACC', 'ADANIENT', 'ADANIPORTS', 'ALKEM', 'AMARAJABAT', 'AMBUJACEM', 'APLLTD',
                   'APOLLOHOSP']
capital = 100000
risk_percent = 1/100
live_data = {}

socket_opened = False


def event_handler_quote_update(message):
    live_data[message["instrument"].symbol] = {"High": message["high"],
                                               "Low": message["low"],
                                               "Open": message["open"]}


def open_callback():
    global socket_opened
    socket_opened = True


alice.start_websocket(subscribe_callback=event_handler_quote_update,
                      socket_open_callback=open_callback,
                      run_in_background=True)
while not socket_opened:
    sleep(1)

alice.subscribe([alice.get_instrument_by_symbol('NSE', i.upper()) for i in instrument_list], LiveFeedType.MARKET_DATA)

while len(instrument_list) != len(list(live_data.keys())):
    sleep(1)
print("Connected to web socket..")

while datetime.time(9, 15) > datetime.datetime.now().time():
    sleep(1)


def place_trade(symbol, quantity, direction):
    alice.place_order(transaction_type=TransactionType.Buy if direction == "Buy" else TransactionType.Sell,
                      instrument=alice.get_instrument_by_symbol('NSE', symbol),
                      quantity=quantity,
                      order_type=OrderType.Market,
                      product_type=ProductType.Intraday,
                      price=0.0,
                      trigger_price=None,
                      stop_loss=None,
                      square_off=None,
                      trailing_sl=None,
                      is_amo=False)


print("---TA Python - Algo Started---")
history = {}
while datetime.time(15, 15) > datetime.datetime.now().time():
    for symbol, values in live_data.items():
        try:
            history[symbol]
        except:
            history[symbol] = {"High": values["High"], "Low": values["Low"],
                               "Qty": None, "Direction": None, "Entry": False,
                               "Stoploss": None, "Target": None, "Exit": False}

        volatility = round((values["High"]-values["Low"])*100/values["Open"],2)
        if volatility > 1 and history[symbol]["High"] < values["High"] and not history[symbol]["Entry"]:
            direction = "Buy"
            quantity = int(capital*risk_percent/(values["High"]-values["Low"]))
            place_trade(symbol, quantity, direction)
            history[symbol]["Entry"] = True
            history[symbol]["Qty"] = quantity
            history[symbol]["Direction"] = direction
            history[symbol]["Stoploss"] = values["Low"]
            history[symbol]["Target"] = round(values["High"] + 2*(values["High"]-values["Low"]), 2)
            print(f"{direction} : {symbol}, Entry {values['High']}, Qty {quantity}, Stoploss {history[symbol]['Stoploss']}, "
                  f"Target {history[symbol]['Target']}, Time {datetime.datetime.now().time()}")

        if volatility > 1 and history[symbol]["Low"] > values["Low"] and not history[symbol]["Entry"]:
            direction = "Sell"
            quantity = int(capital*risk_percent/(values["High"]-values["Low"]))
            place_trade(symbol, quantity, direction)
            history[symbol]["Entry"] = True
            history[symbol]["Qty"] = quantity
            history[symbol]["Direction"] = direction
            history[symbol]["Stoploss"] = values["High"]
            history[symbol]["Target"] = round(values["Low"] - 2 * (values["High"] - values["Low"]),2)
            print(f"{direction} : {symbol}, Entry {values['Low']}, Qty {quantity}, Stoploss {history[symbol]['Stoploss']}, "
                  f"Target {history[symbol]['Target']}, Time {datetime.datetime.now().time()}")

        if history[symbol]["Entry"] and not history[symbol]["Exit"]:
            if history[symbol]["Direction"] == "Buy" and (history[symbol]["Stoploss"] > values["Low"] or
                                                          history[symbol]["Target"] < values["High"] or
                                                          datetime.time(15, 14) < datetime.datetime.now().time()):
                place_trade(symbol, history[symbol]["Qty"], "Sell")
                history[symbol]["Exit"] = True
                print(f"Exit : {symbol}, Qty {history[symbol]['Qty']}, Time {datetime.datetime.now().time()}")
            if history[symbol]["Direction"] == "Sell" and (history[symbol]["Stoploss"] < values["High"] or
                                                          history[symbol]["Target"] > values["Low"] or
                                                          datetime.time(15, 14) < datetime.datetime.now().time()):
                place_trade(symbol, history[symbol]["Qty"], "Buy")
                history[symbol]["Exit"] = True
                print(f"Exit : {symbol}, Qty {history[symbol]['Qty']}, Time {datetime.datetime.now().time()}")
        history[symbol]["High"] = values["High"]
        history[symbol]["Low"] = values["Low"]
    sleep(1)

print("Session end..\nSubscribe on YouTube 'TA Python'....")