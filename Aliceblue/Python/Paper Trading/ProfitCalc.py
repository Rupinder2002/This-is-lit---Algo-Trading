# -*- coding: utf-8 -*-
"""
Created on Fri Apr 29 17:34:03 2022

@author: naman
"""
import pandas as pd
from alice_blue import AliceBlue
import os
import requests
import datetime as dt

#os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading/Aliceblue/Credentials')

strategy_name = 'Mean Reversion Long Option Trading'

def telegram_bot_sendmessage(message):
    bot_token = '5173424624:AAGWIHX1xrGfX8doCYtskOHnxhtxVr1PMCI'
    bot_ChatID = 'algo_trading_bot_trades'
    send_message = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=@' + bot_ChatID + \
                   '&parse_mode = MarkdownV2&text=' + message
    
    requests.get(send_message)

cwd = os.getcwd()

username = open('alice_username.txt','r').read()
password = open('alice_pwd.txt','r').read()
twoFA = open('alice_twoFA.txt','r').read()
api_key = open('api_key_alice.txt','r').read()
api_secret = open('api_secret_alice.txt','r').read()
socket_opened = False

def login():
    
    access_token = AliceBlue.login_and_get_access_token(username = username, password = password, twoFA = twoFA, api_secret = api_secret, app_id = api_key)   
    alice = AliceBlue(username=username, password=password,access_token=access_token, master_contracts_to_download=['NFO'])
   
    return alice

alice = login()

filename = os.path.join(cwd,strategy_name + ' Order Book ' + str(dt.datetime.now().date()) + '.csv')
ord_df = pd.read_csv(filename)

tickers = ord_df.tradingsymbol.unique().tolist()
ticker_lot_size = pd.DataFrame(columns = ['tradingsymbol','lot_size'])
for ticker in tickers:
    instrument = alice.get_instrument_by_symbol('NFO',ticker)
    df = pd.DataFrame([[ticker,int(instrument.lot_size)]],columns = ticker_lot_size.columns)
    ticker_lot_size = ticker_lot_size.append(df)

lot_df = ticker_lot_size.reset_index(drop = True)

ord_df1 = ord_df.reset_index(drop = True)
ord_df1 = ord_df1.merge(lot_df, on = 'tradingsymbol')

trade_df = ord_df1[(ord_df1['Order']!='Modify')].reset_index(drop = True)
trade_df.loc[trade_df['Order'] == 'buy','new_price'] = -1 * trade_df['price']
trade_df.loc[trade_df['Order'] == 'sell','new_price'] = 1 * trade_df['price']
trade_df['ltp'] = trade_df.groupby('tradingsymbol')['new_price'].shift(1)
trade_df['pnl'] = (trade_df['ltp'] + trade_df['new_price'])
trade_df = trade_df[~trade_df['Reason'].str.contains('reverse')]

trade_df['Date'] = pd.to_datetime(trade_df['timestamp']).dt.date

trade_df.loc[trade_df['pnl'] > 0,'streak'] = 1
trade_df.loc[trade_df['pnl'] < 0,'streak'] = -1
trade_df.loc[trade_df['pnl'] == 0,'streak'] = 0

no_of_signals = len(trade_df)
no_of_wins = len(trade_df[trade_df['pnl']>0])
no_of_losses = len(trade_df[trade_df['pnl']<0])
max_gain = round(max(trade_df['pnl'] * trade_df['lot_size']),2)
max_loss = round(min(trade_df['pnl'] * trade_df['lot_size']),2)
avg_gain_per_win = round((trade_df[trade_df['pnl'] > 0]['pnl'] * trade_df[trade_df['pnl'] > 0]['lot_size']).mean(),2)
avg_loss_per_loss = round((trade_df[trade_df['pnl'] < 0]['pnl'] * trade_df[trade_df['pnl'] < 0]['lot_size']).mean(),2)


trade_df['Total_Profit_Per_Lot'] = trade_df['pnl'] * trade_df['lot_size']
trade_df['Total_Cost_Per_Lot'] = abs(trade_df['ltp'] * trade_df['lot_size'])

#Brokerage Charges
brokerage = 20
stt = 0.05/100
transcation_charges = 0.053/100
gst = 18/100
sebi_charges = 10/10000000
stamp_charges = 0.003/100

trade_df['brokerage'] = 40
trade_df['stt'] = trade_df['lot_size'] * trade_df['price'] * stt
trade_df['transcation_charges'] = (trade_df['Total_Cost_Per_Lot'] + trade_df['lot_size'] * trade_df['price']) * transcation_charges
trade_df['gst'] = (trade_df['brokerage'] + trade_df['transcation_charges']) * gst
trade_df['sebi'] =  0.1
trade_df['stamp_charges'] = trade_df['Total_Cost_Per_Lot'] * stamp_charges

trade_df['total_tax_and_charges'] = trade_df['brokerage'] + trade_df['stt'] + \
        trade_df['transcation_charges'] + trade_df['gst'] + trade_df['sebi'] + \
        trade_df['stamp_charges']

trade_df['Total_Profit_After_Tax'] = trade_df['Total_Profit_Per_Lot'] - trade_df['total_tax_and_charges']

telegram_bot_sendmessage('Summary as of: ' + str(trade_df['Date'].iloc[0].strftime('%d %b')) + 
                         '\nTotal Invested: Rs. ' + str(round(trade_df['Total_Cost_Per_Lot'].sum())) + 
                         '\nTotal Profit: Rs. ' + str(round(trade_df['Total_Profit_Per_Lot'].sum())) + 
                         '\nTotal Tax and Charges: Rs. ' + str(round(trade_df['total_tax_and_charges'].sum())) + 
                         '\nTotal Profit After Tax: Rs. ' + str(round(trade_df['Total_Profit_After_Tax'].sum())) + 
                         '\nTotal Profit %: ' + str(100 * round(trade_df['Total_Profit_Per_Lot'].sum()/trade_df['Total_Cost_Per_Lot'].sum(),4)) + '%' + 
                         '\nTotal After Tax Profit %: ' + str(100 * round(trade_df['Total_Profit_After_Tax'].sum()/trade_df['Total_Cost_Per_Lot'].sum(),4)) + '%' + 
                         '\nTotal Signals: ' + str(no_of_signals) + 
                         '\nTotal Wins: ' + str(no_of_wins) + 
                         '\nTotal Losses: ' + str(no_of_losses) + 
                         '\nWin Rate: ' + str(round(100 * no_of_wins/no_of_signals,1)) + '%' + 
                         '\nLoss Rate: ' + str(round(100 * no_of_losses/no_of_signals,1)) + '%' + 
                         '\nMax Gain: Rs. ' + str(round(max_gain)) + 
                         '\nMax Loss: Rs. ' + str(round(max_loss)) +
                         '\nAvg Gain per win: Rs. ' + str(round(avg_gain_per_win)) +
                         '\nAvg Loss per Loss: Rs. ' + str(round(avg_loss_per_loss)))

# summary = pd.DataFrame(columns = ['ticker','Total Profit','PnL%'])

# for ticker in tickers:

#     ticker_trade_df = trade_df[trade_df['tradingsymbol'] == ticker]
#     if len(ticker_trade_df)!=0:
        
#         average_price = abs(ticker_trade_df['ltp'].mean())
        
#         total_profit = round(sum(ticker_trade_df['pnl'] * ticker_trade_df['lot_size']),2)
#         pnl_pct = round(sum(ticker_trade_df['pnl'])/average_price * 100,2)
        
#         ticker_summary = pd.DataFrame([[ticker,total_profit,pnl_pct]],
#                                       columns = summary.columns.tolist())
        
#         summary = summary.append(ticker_summary)

