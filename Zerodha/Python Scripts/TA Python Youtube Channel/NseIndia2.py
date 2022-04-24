import requests
import pandas as pd


class NseIndia2:

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'}
        self.session = requests.Session()
        self.session.get("http://nseindia.com", headers=self.headers)

    def get_stock_info(self, symbol, trade_info=False):
        if trade_info:
            url = 'https://www.nseindia.com/api/quote-equity?symbol=' + symbol +"&section=trade_info"
        else:
            url = 'https://www.nseindia.com/api/quote-equity?symbol=' + symbol
        data = self.session.get(url, headers=self.headers).json()
        return data

    def get_option_chain(self, symbol, indices=False):
        if not indices:
            url = 'https://www.nseindia.com/api/option-chain-equities?symbol=' + symbol
        else:
            url = 'https://www.nseindia.com/api/option-chain-indices?symbol=' + symbol
        data = self.session.get(url,headers=self.headers).json()["records"]["data"]
        my_df = []
        for i in data:
            for k, v in i.items():
                if k == "CE" or k == "PE":
                    info = v
                    info["instrumentType"] = k
                    my_df.append(info)
        return pd.DataFrame(my_df)


nse = NseIndia2()


print(nse.get_stock_info("RELIANCE"))
# print(nse.get_stock_info("RELIANCE", trade_info=True))

# # print(nse.get_option_chain("ZEEL"))
# print(nse.get_option_chain("NIFTY",indices=True).columns)



