# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 18:29:05 2022

@author: naman
"""
import pandas as pd
import requests
import os
import datetime as dt

#os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading')
cwd = os.getcwd()
strategy_name = 'BANKNIFTY ADX ST StochRSI'
filename = os.path.join(cwd,strategy_name + ' Order Book ' + str(dt.datetime.now().date()) + '.csv')

def telegram_bot_sendmessage(message):
    bot_token = '5173424624:AAGWIHX1xrGfX8doCYtskOHnxhtxVr1PMCI'
    bot_ChatID = 'algo_trading_bot_trades'
    send_message = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=@' + bot_ChatID + \
                   '&parse_mode = MarkdownV2&text=' + message
    
    requests.get(send_message)

ord_df = pd.read_csv(filename)
tickers = ord_df['tradingsymbol'].drop_duplicates().tolist()

if len(ord_df) > 0:
    ord_df = ord_df.reset_index(drop = True)
    
    ord_df.loc[ord_df['Order'] == 'sell','new_price'] = 1 * ord_df['price']
    ord_df.loc[ord_df['Order'] == 'buy','new_price'] = -1 * ord_df['price']
    ord_df['lot_size'] = 25
    
    for ticker in tickers:
        trade_df = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].reset_index(drop = True)
        trade_df['ltp'] = trade_df['new_price'].shift(1)
        trade_df['pnl'] = trade_df['ltp'] + trade_df['new_price']
        trade_df = trade_df[~trade_df['Reason'].str.contains('show')]
        telegram_bot_sendmessage('Profit for ' + ticker + ':' + str(round(sum(trade_df['pnl'] * trade_df['lot_size']))))
else:
    telegram_bot_sendmessage('----No Trades Today----')