# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 15:04:01 2022

@author: naman
"""

from alice_blue import AliceBlue,TransactionType,OrderType,ProductType
import os

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')

username = open('Aliceblue/alice_username.txt','r').read()
password = open('Aliceblue/alice_pwd.txt','r').read()
twoFA = open('Aliceblue/alice_twoFA.txt','r').read()
api_key = open('Aliceblue/api_key_alice.txt','r').read()
api_secret = open('Aliceblue/api_secret_alice.txt','r').read()

access_token = AliceBlue.login_and_get_access_token(username = username, password = password, twoFA = twoFA, api_secret = api_secret, app_id = api_key)
   
alice = AliceBlue(username=username, password=password,access_token=access_token, master_contracts_to_download=['MCX', 'NSE', 'CDS','NFO'])

print(alice.get_balance()) # get balance / margin limits
print(alice.get_profile()) # get profile
print(alice.get_daywise_positions()) # get daywise positions
print(alice.get_netwise_positions()) # get netwise positions
print(alice.get_holding_positions()) # get holding positions

multiple_underlying = ['BANKNIFTY','NIFTY']
all_scripts = alice.search_instruments('NFO', multiple_underlying)

print (alice.get_profile())

# TransactionType.Buy, OrderType.Market, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%1%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.Delivery,
                     price = 0.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
   )

# TransactionType.Buy, OrderType.Market, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%2%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.Intraday,
                     price = 0.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)

# TransactionType.Buy, OrderType.Market, ProductType.CoverOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%3%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.CoverOrder,
                     price = 0.0,
                     trigger_price = 7.5, # trigger_price Here the trigger_price is taken as stop loss (provide stop loss in actual amount)
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)


# TransactionType.Buy, OrderType.Limit, ProductType.BracketOrder
# OCO Order can't be of type market

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%4%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.BracketOrder,
                     price = 8.0,
                     trigger_price = None,
                     stop_loss = 6.0,
                     square_off = 10.0,
                     trailing_sl = None,
                     is_amo = False)
)

# TransactionType.Buy, OrderType.Limit, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%5%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.Intraday,
                     price = 8.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)


# TransactionType.Buy, OrderType.Limit, ProductType.CoverOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%6%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.CoverOrder,
                     price = 7.0,
                     trigger_price = 6.5, # trigger_price Here the trigger_price is taken as stop loss (provide stop loss in actual amount)
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)

###############################

# TransactionType.Buy, OrderType.StopLossMarket, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%7%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Delivery,
                     price = 0.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)


# TransactionType.Buy, OrderType.StopLossMarket, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Intraday,
                     price = 0.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)



# TransactionType.Buy, OrderType.StopLossMarket, ProductType.CoverOrder
# CO order is of type Limit and And Market Only

# TransactionType.Buy, OrderType.StopLossMarket, ProductType.BO
# BO order is of type Limit and And Market Only

###################################

# TransactionType.Buy, OrderType.StopLossLimit, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%9%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Delivery,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)


# TransactionType.Buy, OrderType.StopLossLimit, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%10%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.Intraday,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)



# TransactionType.Buy, OrderType.StopLossLimit, ProductType.CoverOrder
# CO order is of type Limit and And Market Only


# TransactionType.Buy, OrderType.StopLossLimit, ProductType.BracketOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%11%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.BracketOrder,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = 1.0,
                     square_off = 1.0,
                     trailing_sl = 20,
                     is_amo = False)
)


# =============================================================================
# Place basket order
# Basket order is used to buy or sell group of securities simultaneously.
# =============================================================================

order1 = {  "instrument"        : alice.get_instrument_by_symbol('NSE', 'INFY'),
            "order_type"        : OrderType.Market,
            "quantity"          : 1,
            "transaction_type"  : TransactionType.Buy,
            "product_type"      : ProductType.Delivery}
order2 = {  "instrument"        : alice.get_instrument_by_symbol('NSE', 'SBIN'),
            "order_type"        : OrderType.Limit,
            "quantity"          : 2,
            "price"             : 280.0,
            "transaction_type"  : TransactionType.Sell,
            "product_type"      : ProductType.Intraday}

orders = [order1, order2]
print(alice.place_basket_order(orders))


print(alice.get_trade_book())
