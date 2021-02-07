import csv, urllib.request, logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

FUNDS = ["pbw", "tan", "pbd", "ptf", "psj", "pth", "psi"]

FUNDS_BASE_PATH = "https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0?audienceType=Investor&action=download&ticker="
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
}

def query(fund):
    now = datetime.now()
    cached_file = Path(".cache") / f"{fund.upper()}_{now.strftime('%Y%m%d')}.csv"
    if cached_file.is_file():
        log.debug(f"Using data from cached file: {cached_file}")
        with open(cached_file, "r") as csv_file:
            reader = csv.reader(csv_file)
            return {rows[0]: float(rows[1]) for rows in reader}
    else:
        data = fetch(fund)
        cached_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cached_file, "w") as csv_file:
            log.debug(f"Caching data to file: {cached_file}")
            writer = csv.writer(csv_file, delimiter=",", lineterminator="\n")
            for holding, weight in data.items():
                writer.writerow([holding, weight])
        return data
        

def fetch(fund):
    result = {}
    fund_csv_url = FUNDS_BASE_PATH + fund.upper()
    req = urllib.request.Request(fund_csv_url, headers=HEADERS)
    res = urllib.request.urlopen(req)
    data = csv.reader([l.decode("utf-8") for l in res.readlines()])
    next(data)
    for holding in data:
        ticker = holding[2].strip()
        weight = holding[5]
        if ticker.startswith("-") or not ticker or not weight:
            break
        result[ticker] = result.get(ticker, 0) + float(weight)
    return result