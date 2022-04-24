import requests, json
from alice_blue import *
import dateutil.parser
from datetime import datetime, timedelta
import pandas as pd

login_credential = {'api_key': '', 'api_secret': '', 'user_id': '', 'password': '', 'two_fa': ''}
access_token = AliceBlue.login_and_get_access_token(username=login_credential["user_id"],
                                                    password=login_credential['password'],
                                                    twoFA=login_credential['two_fa'],
                                                    api_secret=login_credential["api_secret"],
                                                    app_id=login_credential["api_key"])
alice = AliceBlue(username=login_credential["user_id"], password=login_credential['password'], access_token=access_token)


def get_historical(instrument, from_datetime, to_datetime, interval, indices=False):
    params = {"token": instrument.token,
              "exchange": instrument.exchange if not indices else "NSE_INDICES",
              "starttime": str(int(from_datetime.timestamp())),
              "endtime": str(int(to_datetime.timestamp())),
              "candletype": 3 if interval.upper() == "DAY" else (2 if interval.upper().split("_")[1] == "HR" else 1),
              "data_duration": None if interval.upper() == "DAY" else interval.split("_")[0]}
    lst = requests.get(
        f" https://ant.aliceblueonline.com/api/v1/charts/tdv?", params=params).json()["data"]["candles"]
    records = []
    for i in lst:
        record = {"date": dateutil.parser.parse(i[0]), "open": i[1], "high": i[2], "low": i[3], "close": i[4], "volume": i[5]}
        records.append(record)
    return records


instrument = alice.get_instrument_by_symbol("NSE", "Nifty 50")
from_datetime = datetime.now() - timedelta(days=10)
to_datetime = datetime.now()
interval = "1_MIN"   # ["DAY", "1_HR", "3_HR", "1_MIN", "5_MIN", "15_MIN", "60_MIN"]
indices = True
df = pd.DataFrame(get_historical(instrument, from_datetime, to_datetime, interval, indices))

df.index = df["date"]
df = df.drop("date", axis=1)

df["MA_10"] = df["close"].rolling(window=10).mean()
print(df)