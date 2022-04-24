# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 18:29:05 2022

@author: naman
"""
import pandas as pd
import requests
import os
import datetime as dt
import locale

locale.setlocale(locale.LC_MONETARY, 'en_IN')

os.chdir('C:/Users/naman/Downloads')
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
lot_size = 25

if len(ord_df) > 0:
    profits = []
    ord_df = ord_df.reset_index(drop = True)
    
    ord_df.loc[ord_df['Order'] == 'sell','new_price'] = 1 * ord_df['price']
    ord_df.loc[ord_df['Order'] == 'buy','new_price'] = -1 * ord_df['price']
    ord_df['no_of_tickers'] = ((100000/ord_df['price'])/lot_size).astype(int) * lot_size
    
    for ticker in tickers:
        trade_df = ord_df[(ord_df["tradingsymbol"]==ticker) & (ord_df['Order']!='Modify')].reset_index(drop = True)
        trade_df['ltp'] = trade_df['new_price'].shift(1)
        trade_df['pnl'] = trade_df['ltp'] + trade_df['new_price']
        trade_df = trade_df[~trade_df['Reason'].str.contains('show')]
        pnl = round(sum(trade_df['pnl'] * trade_df['no_of_tickers']),2)
        profits.append(pnl)
        print('Profit for ' + ticker + ' : ' + str(locale.currency(pnl,grouping=True)))
    
    print('Overall Profit for today : ' + str(locale.currency(sum(profits),grouping=True)))

else:
    print('----No Trades Today----')