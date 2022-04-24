#-------------Prep--------#
import warnings
import pandas as pd
import os
from dateutil.parser import parse
from pandas.tseries.offsets import BDay
import numpy as np
import datetime
import matplotlib.pyplot as plt
#import plotly.graph_objects as go
#import plotly.io as pio

os.chdir('C:/Users/naman/OneDrive - PangeaTech/Desktop/Algo Trading/Data')
warnings.filterwarnings("ignore")

#-------------Read Data------------#
nifty = pd.read_csv('NIFTY_2008_2020.csv')

#-------------Format Data------------#
nifty['Timestamp'] = nifty['Date'].astype(str) + ' ' + nifty['Time'].astype(str)
nifty['Timestamp'] = pd.to_datetime(nifty['Timestamp'],format = '%Y%m%d %H:%M')
nifty['Time'] = pd.to_datetime(nifty['Time'],format = '%H:%M',errors='coerce').dt.time
nifty['Date'] = nifty['Timestamp'].dt.date
nifty = nifty.sort_values(['Timestamp'],ascending=True)

market_end_time = pd.to_datetime('15:30:00',format = '%H:%M:%S').time()
market_start_time = pd.to_datetime('09:15:00',format = '%H:%M:%S').time()

nifty = nifty.loc[(nifty['Time'] <= market_end_time) & (nifty['Time'] >= market_start_time)]

nifty = nifty.groupby(['Date',pd.Grouper(key = "Timestamp",freq = '15T')]).agg({
                                        "Open":  "first",
                                        "High":  "max",
                                        "Low":   "min",
                                        "Close": "last"}).reset_index().dropna(axis=0)

nifty['hour'] = nifty['Timestamp'].dt.hour
nifty['time'] = nifty['Timestamp'].dt.time
nifty['minute'] = nifty['Timestamp'].dt.minute
nifty['Day'] = pd.to_datetime(nifty['Date']).dt.day_name()

nifty = nifty[~nifty['Day'].isin(['Saturday','Sunday'])]

"""fig = go.Figure(data=[go.Candlestick(x=nifty.loc[nifty['Date'] > pd.to_datetime('2020-11-26').date(),'Timestamp'],
                open=nifty['Open'],
                high=nifty['High'],
                low=nifty['Low'],
                close=nifty['Close'])])

fig.update_layout(xaxis_rangeslider_visible=False)
fig.show()"""


#-------------Returns Calc----------------#
nifty_fe = nifty.copy()
nifty_fe['previous_close'] = nifty_fe['Close'].shift(1)
nifty_fe['return'] = (nifty_fe['Close']/nifty_fe['previous_close'] - 1)
nifty_fe = nifty_fe[nifty_fe['return'].notna()]
#nifty_fe['return'].fillna(0, inplace = True)
nifty_fe['cum_return'] = (1 + nifty_fe['return']).cumprod() - 1

#-------------Can get idea of continuous increase or decrease in cum return
nifty_fe['yes_no'] = nifty_fe['cum_return'].diff()>0

"""initial_investment = 1000000
nifty_fe['investment_value'] = initial_investment * (1+nifty_fe['cum_return'])
nifty_fe['pnl'] = nifty_fe['investment_value']-initial_investment"""

#nifty_2008_1jan = nifty_fe[nifty_fe['Date'] == pd.to_datetime('2008-01-01')]
#plt.plot(nifty_2008_1jan['time'].astype(str), nifty_2008_1jan['cum_return'])

#-------------Maxima and Minima buy/sell opportunity
nifty_fe['max_return_day'] = nifty_fe.groupby(['Date'])[['cum_return']].transform(max)
nifty_fe['min_return_day'] = nifty_fe.groupby(['Date'])[['cum_return']].transform(min)
nifty_fe.loc[nifty_fe['cum_return'] == nifty_fe['max_return_day'],'buy/sell'] = 'Sell'
nifty_fe.loc[nifty_fe['cum_return'] == nifty_fe['min_return_day'],'buy/sell'] = 'Buy'

#-------------Assume the first occurance of highest/lowest cum return as buy/sell
nifty_fe.loc[nifty_fe.groupby(['Date','cum_return']).cumcount() >= 1,'buy/sell'] = np.nan

#-------------Update values in buy/sell to hold and wait
nifty_fe.reset_index(inplace = True, drop=True)
nifty_fe.reset_index(inplace = True)
buy_sell_index = nifty_fe[nifty_fe['buy/sell'].isin(['Buy','Sell'])]
buy_sell_index['prev_index'] = buy_sell_index.groupby('Date')['index'].shift(1)
buy_sell_index = buy_sell_index[['Date','index','prev_index']].dropna()
buy_sell_index.columns = ['Date','index_1','index_2']
nifty_fe = nifty_fe.merge(buy_sell_index,how = 'left')
nifty_fe.loc[(nifty_fe['index']<nifty_fe['index_1']) & (nifty_fe['index']>nifty_fe['index_2']),'buy/sell'] = 'Hold'
nifty_fe = nifty_fe.drop(['index','index_1','index_2'],axis = 1)
nifty_fe['buy/sell'] = nifty_fe['buy/sell'].fillna('Wait')

#x = nifty_fe['yes_no'].factorize()[0]

#-------------Assuming buying 50 shares, calc buy and sell amt and qt. Also calc realised pnl
no_of_shares = 50
nifty_fe.loc[nifty_fe['buy/sell'] == 'Sell','buy_sell_amt'] = no_of_shares * nifty_fe['Close']
nifty_fe.loc[nifty_fe['buy/sell'] == 'Sell','buy_sell_qt'] = -1 * no_of_shares
nifty_fe.loc[nifty_fe['buy/sell'] == 'Buy','buy_sell_amt'] = -1 * no_of_shares * nifty_fe['Close']
nifty_fe.loc[nifty_fe['buy/sell'] == 'Buy','buy_sell_qt'] = no_of_shares

nifty_fe['buy_sell_amt'] = nifty_fe['buy_sell_amt'].fillna(0)
nifty_fe['buy_sell_qt'] = nifty_fe['buy_sell_qt'].fillna(0)
nifty_fe['realised_pnl'] = nifty_fe['buy_sell_amt'].cumsum()
nifty_fe['no_of_shares'] = nifty_fe['buy_sell_qt'].cumsum()
nifty_fe.loc[(nifty_fe['no_of_shares']!=0) & ((nifty_fe['buy/sell'] != 'Buy')|(nifty_fe['buy/sell'] != 'Sell')),'realised_pnl'] = 0
nifty_fe.loc[~(nifty_fe['buy/sell'].isin(['Buy','Sell'])),'realised_pnl'] = 0
nifty_fe['cum_realised_pnl'] = nifty_fe['realised_pnl'].cumsum()

#Create MACD signals

nifty_fe["MA_Fast"]=nifty_fe["Close"].ewm(span=10,min_periods=10).mean()
nifty_fe["MA_Slow"]=nifty_fe["Close"].ewm(span=21,min_periods=21).mean()
nifty_fe["MACD"]=nifty_fe["MA_Fast"]-nifty_fe["MA_Slow"]
nifty_fe["Signal"]=nifty_fe["MACD"].ewm(span=9,min_periods=9).mean()
nifty_fe = nifty_fe.drop(['MA_Fast','MA_Slow'],axis = 1)



#Create Bollinger Bands
n = 23
nifty_fe["MA"] = nifty_fe['Close'].rolling(n).mean()
nifty_fe["BB_up"] = nifty_fe["MA"] + 2*nifty_fe['Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
nifty_fe["BB_dn"] = nifty_fe["MA"] - 2*nifty_fe['Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
nifty_fe["BB_width"] = nifty_fe["BB_up"] - nifty_fe["BB_dn"]
#nifty_fe['outside_BB'] = (nifty_fe['Close'] >= nifty_fe['BB_up']) | (nifty_fe['Close'] <= nifty_fe['BB_dn'])
#nifty_fe = nifty_fe.drop(['MA','BB_up','BB_dn'],axis = 1)

model_data = nifty_fe.dropna()

model_data = model_data[['Date','hour','minute','Day',
                       'Open','High','Low','Close',
                       'return','cum_return','yes_no',
                       #'MA_Fast','MA_Slow','MACD','Signal',
                       'MA','BB_up','BB_dn','BB_width',
                       'buy/sell']]

model_data.loc[model_data['Date'] <= pd.to_datetime('2020-11-01'),'Class'] = 'train'
model_data.loc[model_data['Date'] > pd.to_datetime('2020-11-01'),'Class'] = 'test'

model_data['year'] = pd.DatetimeIndex(model_data['Date']).year
model_data['month'] = pd.DatetimeIndex(model_data['Date']).month
model_data['day'] = pd.DatetimeIndex(model_data['Date']).day
model_data['dayofyear'] = pd.DatetimeIndex(model_data['Date']).dayofyear
model_data['weekofyear'] = pd.DatetimeIndex(model_data['Date']).weekofyear
model_data['weekday'] = pd.DatetimeIndex(model_data['Date']).weekday
model_data['quarter'] = pd.DatetimeIndex(model_data['Date']).quarter
model_data['is_month_start'] = pd.DatetimeIndex(model_data['Date']).is_month_start
model_data['is_month_end'] = pd.DatetimeIndex(model_data['Date']).is_month_end
model_data = model_data.drop(['Date','Day'], axis = 1) 

#model_data = pd.get_dummies(model_data, columns=['year'], drop_first=True, prefix='year')
#model_data = pd.get_dummies(model_data, columns=['month'], drop_first=True, prefix='month')
#model_data = pd.get_dummies(model_data, columns=['hour'], drop_first=True, prefix='hour')
#model_data = pd.get_dummies(model_data, columns=['minute'], drop_first=True, prefix='minute')
#model_data = pd.get_dummies(model_data, columns=['weekday'], drop_first=True, prefix='wday')
#model_data = pd.get_dummies(model_data, columns=['quarter'], drop_first=True, prefix='qrtr')
#model_data = pd.get_dummies(model_data, columns=['is_month_start'], drop_first=True, prefix='m_start')
#model_data = pd.get_dummies(model_data, columns=['yes_no'], drop_first=True, prefix='yes_no')
#model_data = pd.get_dummies(model_data, columns=['is_month_end'], drop_first=True, prefix='m_end')

train = model_data[model_data["Class"] == "train"] 
test = model_data[model_data["Class"] == "test"] 
train = train.drop(['Class'], axis = 1)
test = test.drop(['Class'], axis = 1)

target_column_train = ['buy/sell'] 
predictors_train = list(set(list(train.columns))-set(target_column_train))

X_train = train[predictors_train].values
y_train = train[target_column_train].values

print(X_train.shape)
print(y_train.shape)

target_column_test = ['buy/sell'] 
predictors_test = list(set(list(test.columns))-set(target_column_test))

X_test = test[predictors_test].values
y_test = test[target_column_test].values

print(X_test.shape)
print(y_test.shape)

from sklearn import model_selection
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
from math import sqrt
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

# fit model no training data
model = XGBClassifier()
model.fit(X_train, y_train)

# make predictions for test data
y_pred = model.predict(X_test)
predictions = y_pred

# evaluate predictions
accuracy = accuracy_score(y_test, predictions)
print("Accuracy: %.2f%%" % (accuracy * 100.0))

pd.concat([test,pd.DataFrame(y_pred)])
test.join(pd.DataFrame(y_pred))

x = pd.merge(test.reset_index(drop = True), pd.DataFrame(y_pred), left_index=True, right_index=True)
