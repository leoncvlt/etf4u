import urllib.request, logging, json
from lxml import html
from utils import HEADERS

log = logging.getLogger(f"etf4u.{__name__}")

# The etfdb adapter is a fallback adapter used when no specific adapter exists for a fund
# It navigates to the etf fund's page on etfdb.com then queries a public api endpoint
# which returns the list of holdings. The endpoint is limited to 15 results for user
# which are not registered to their premium membership plan

FUNDS = []


def fetch(fund):
    result = {}
    fund_csv_url = f"https://etfdb.com/etf/{fund.upper()}/"
    req = urllib.request.Request(fund_csv_url, headers=HEADERS)
    res = urllib.request.urlopen(req)
    tree = html.parse(res)
    table = tree.xpath("//table[@data-hash='etf-holdings']")[0]

    # the api returns 15 results, but we can iterate different sorting
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

    return result
