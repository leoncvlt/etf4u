import urllib.request, logging, json
from lxml import html
from utils import HEADERS

log = logging.getLogger(__name__)

FUNDS = []


def fetch(fund):
    result = {}
    fund_csv_url = f"https://etfdb.com/etf/{fund.upper()}/"
    req = urllib.request.Request(fund_csv_url, headers=HEADERS)
    res = urllib.request.urlopen(req)
    tree = html.parse(res)
    table = tree.xpath("//table[@data-hash='etf-holdings']")[0]
    print(table.get("data-url"))

    # etfdb only returns 15 results, but we can iterated different sorting
    # criterias in the request to maximize the number of different holdings
    for query in [
        "&sort=weight&order=asc",
        "&sort=weight&order=desc",
        "&sort=symbol&order=asc",
        "&sort=symbol&order=desc",
    ]:
        holdings_url = f"https://etfdb.com/{table.get('data-url')}{query}"
        holdings_req = urllib.request.Request(holdings_url, headers=HEADERS)
        holdings_res = urllib.request.urlopen(holdings_req)
        holdings = json.loads(holdings_res.read().decode("utf-8"))
        for row in holdings["rows"]:
            symbol = html.fromstring(row["symbol"]).text_content()
            weight = float(row["weight"].strip("%"))
            if symbol != "N/A":
                result[symbol] = weight

    # reorder the holdings, from largest to smallest weight
    result = {k: result[k] for k in sorted(result, key=result.get, reverse=True)}
    return result
