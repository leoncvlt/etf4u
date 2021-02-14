import csv, urllib.request, logging
from utils import HEADERS

log = logging.getLogger(f"etf4u.{__name__}")

# The iShares adapter fetches the .csv file of the funds' holdings published on their site
# AFAIK there's no way to do this programmatically for any fund so we need to manually
# add the unique URL for each fund's file (see get_fund_file() function below)

FUNDS = ["icln"]


def get_fund_file(symbol):
    funds_basepaths = {
        "icln": "/239738/ishares-global-clean-energy-etf/1467271812596.ajax",
    }
    return (
        "https://www.ishares.com/us/products"
        + funds_basepaths[symbol]
        + f"?fileType=csv&fileName={symbol.upper()}_holdings&dataType=fund"
    )


def fetch(fund):
    result = {}
    fund_csv_url = get_fund_file(fund)
    req = urllib.request.Request(fund_csv_url, headers=HEADERS)
    res = urllib.request.urlopen(req)
    data = csv.reader([l.decode("utf-8").strip() for l in res.readlines()])
    for i in range(0, 10):
        next(data)
    for holding in data:
        try:
            ticker = holding[0]
            weight = holding[5]
            asset_class = holding[3]
            if not ticker or not weight or not (asset_class == "Equity"):
                continue
            result[ticker] = result.get(ticker, 0) + float(weight)
        except IndexError:
            break
    return result