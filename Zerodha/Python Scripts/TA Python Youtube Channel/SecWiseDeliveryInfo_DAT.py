import requests
import pandas as pd
from datetime import date
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


# Subscribe "TA Python" on YouTube and Telegram
def SecWiseDeliveryInfo(date,to_excel=False):
    try:
        day = str(date.day) if len(str(date.day)) == 2 else "0"+str(date.day)
        month = str(date.month) if len(str(date.month)) == 2 else "0"+str(date.month)
        year = str(date.year)
        data = requests.get(f"https://www1.nseindia.com/archives/equities/mto/MTO_{day+month+year}.DAT").text.split("<N>")[1]
        lst = []
        for i in data.split("\n")[1:-1]:
            lst.append(i.split(","))
        lst[0].insert(3, "Type")
        df = pd.DataFrame(lst[1:],columns=lst[0])
        for i in df.columns:
            try:
                df[i] = df[i].apply(lambda x: int(x))
            except:
                try:
                    df[i] = df[i].apply(lambda x: float(x))
                except:
                    pass
        if to_excel:
            df.to_excel(f"{day}-{month}-{year}.xlsx")
        return df
    except:
        pass


print(SecWiseDeliveryInfo(date=date(2021,6,14),to_excel=True))

