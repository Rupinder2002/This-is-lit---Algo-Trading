from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta, gamma, rho, theta, vega
from datetime import datetime, timedelta, date


"""
price (float) – the Black-Scholes option price
S (float) – underlying asset price
sigma (float) – annualized standard deviation, or volatility
K (float) – strike price
t (float) – time to expiration in years
r (float) – risk-free interest rate
flag (str) – ‘c’ or ‘p’ for call or put.
"""


# subscribe "TA Python"
def greeks(premium, expiry, asset_price, strike_price, intrest_rate, instrument_type):
    # t = ((datetime(expiry.year, expiry.month, expiry.day, 15, 30) - datetime(2021, 7, 8, 10, 15, 19))/timedelta(days=1))/365
    t = ((datetime(expiry.year, expiry.month, expiry.day, 15, 30) - datetime.now())/timedelta(days=1))/365
    S = asset_price
    K = strike_price
    r = intrest_rate
    flag = instrument_type[0].lower()
    imp_v = implied_volatility(premium, S, K, t, r, flag)
    return {"IV": imp_v,
            "Delta": delta(flag, S, K, t, r, imp_v),
            "Gamma": gamma(flag, S, K, t, r, imp_v),
            "Rho": rho(flag, S, K, t, r, imp_v),
            "Theta": theta(flag, S, K, t, r, imp_v),
            "Vega": vega(flag, S, K, t, r, imp_v)}


premium = 73.3
expiry = date(2021, 7, 8)
asset_price = 15839.3
strike_price = 15900
intrest_rate = 0.1
instrument_type = "p"

print(greeks(premium,expiry,asset_price,strike_price,intrest_rate,instrument_type))

