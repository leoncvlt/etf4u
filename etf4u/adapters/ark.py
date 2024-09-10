import csv, urllib.request, logging
from utils import HEADERS

log = logging.getLogger(f"etf4u.{__name__}")

# The ARK adapter fetches the .csv file of the funds' holdings published on their site

FUNDS = ["arkk", "arkw", "arkq", "arkf", "arkg", "arkx", "prnt", "izrl"]


def get_fund_file(fund):
    funds_filenames = {
        "arkk": "ARK_INNOVATION_ETF_ARKK_HOLDINGS",
        "arkw": "ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS",
        "arkq": "ARK_AUTONOMOUS_TECH._&_ROBOTICS_ETF_ARKQ_HOLDINGS",
        "arkf": "ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS",
        "arkg": "ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS",
        "arkx": "ARK_SPACE_EXPLORATION_&_INNOVATION_ETF_ARKX_HOLDINGS",
        "prnt": "THE_3D_PRINTING_ETF_PRNT_HOLDINGS",
        "izrl": "ARK_ISRAEL_INNOVATIVE_TECHNOLOGY_ETF_IZRL_HOLDINGS",
    }
    return (
        "https://assets.ark-funds.com/fund-documents/funds-etf-csv/"
        + funds_filenames[fund]
        + ".csv"
    )


def fetch(fund):
    result = {}
    fund_csv_url = get_fund_file(fund)
    req = urllib.request.Request(fund_csv_url, headers=HEADERS)
    res = urllib.request.urlopen(req)
    data = csv.reader([l.decode("utf-8") for l in res.readlines()])
    next(data)
    for holding in data:
        try:
            ticker = holding[3]
            weight = holding[7]
            if not ticker or not weight:
                continue
            result[ticker] = result.get(ticker, 0) + float(weight.strip("%"))  # /100
        except IndexError:
            continue
    return result
