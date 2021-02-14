import json, logging
from pathlib import Path
from utils import HEADERS

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

log = logging.getLogger(f"etf4u.{__name__}")

# The Vanguard adapter navigates to the Vanguard's website page for the ETF and uses
# selenium-wire waits up on a request call to their API which returns the fund list


def get_chromedriver(headless=False):
    chromedriver_path = chromedriver_autoinstaller.install()
    logs_path = Path.cwd() / ".logs" / "webdrive.log"
    logs_path.parent.mkdir(parents=True, exist_ok=True)

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=4")
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    return webdriver.Chrome(
        executable_path=str(chromedriver_path),
        service_log_path=str(logs_path),
        options=chrome_options,
    )


def get_fund_file(symbol):
    return f"https://investor.vanguard.com/etf/profile/portfolio/{symbol.upper()}/portfolio-holdings"


def fetch(fund):
    result = {}
    fund_url = get_fund_file(fund)
    driver = get_chromedriver(headless=True)
    driver.get(fund_url)
    request = driver.wait_for_request(r"(?=.*stock\.jsonp)^https://api.vanguard.com")
    body = request.response.body.decode("utf-8")

    # the json data text is wrapped inside a `angular.callbacks._6()` function call
    # extract it so we can load it properly
    data = body[body.find("(") + 1 : body.rfind(")")]
    json_data = json.loads(data)
    holdings = json_data["fund"]["entity"]
    for holding in holdings:
        result[holding["ticker"]] = float(holding["percentWeight"])
    return result


# To get a full list of all Vanguard ETFs, navigate to https://investor.vanguard.com/etf/list#/etf/
# and run the following lines of javascript code:
"""
tickers = document.querySelectorAll(`td[data-ng-bind="investmentProduct.profile.ticker || '—'"]`)
console.log("[" + Array.from(tickers).map(t => '"' + t.textContent + '"').join(",") + "]")
"""

FUNDS = [
    "EDV",
    "BIV",
    "VGIT",
    "BLV",
    "VGLT",
    "VMBS",
    "BSV",
    "VTIP",
    "VGSH",
    "BND",
    "VCEB",
    "VCIT",
    "VCLT",
    "VCSH",
    "VTC",
    "VTEB",
    "VIG",
    "ESGV",
    "VUG",
    "VYM",
    "VV",
    "MGC",
    "MGK",
    "MGV",
    "VONE",
    "VONG",
    "VONV",
    "VTHR",
    "VOO",
    "VOOG",
    "VOOV",
    "VTI",
    "VTV",
    "VXF",
    "VO",
    "VOT",
    "VOE",
    "IVOO",
    "IVOG",
    "IVOV",
    "VTWO",
    "VTWG",
    "VTWV",
    "VIOO",
    "VIOG",
    "VIOV",
    "VB",
    "VBK",
    "VBR",
    "BNDW",
    "BNDX",
    "VWOB",
    "VT",
    "VSGX",
    "VEU",
    "VSS",
    "VEA",
    "VGK",
    "VPL",
    "VNQI",
    "VIGI",
    "VYMI",
    "VXUS",
    "VWO",
    "VOX",
    "VCR",
    "VDC",
    "VDE",
    "VFH",
    "VHT",
    "VIS",
    "VGT",
    "VAW",
    "VNQ",
    "VPU",
    "EDV",
    "BIV",
    "VGIT",
    "BLV",
    "VGLT",
    "VMBS",
    "BSV",
    "VTIP",
    "VGSH",
    "BND",
    "VCEB",
    "VCIT",
    "VCLT",
    "VCSH",
    "VTC",
    "VTEB",
    "VIG",
    "ESGV",
    "VUG",
    "VYM",
    "VV",
    "MGC",
    "MGK",
    "MGV",
    "VONE",
    "VONG",
    "VONV",
    "VTHR",
    "VOO",
    "VOOG",
    "VOOV",
    "VTI",
    "VTV",
    "VXF",
    "VO",
    "VOT",
    "VOE",
    "IVOO",
    "IVOG",
    "IVOV",
    "VTWO",
    "VTWG",
    "VTWV",
    "VIOO",
    "VIOG",
    "VIOV",
    "VB",
    "VBK",
    "VBR",
    "BNDW",
    "BNDX",
    "VWOB",
    "VT",
    "VSGX",
    "VEU",
    "VSS",
    "VEA",
    "VGK",
    "VPL",
    "VNQI",
    "VIGI",
    "VYMI",
    "VXUS",
    "VWO",
    "VOX",
    "VCR",
    "VDC",
    "VDE",
    "VFH",
    "VHT",
    "VIS",
    "VGT",
    "VAW",
    "VNQ",
    "VPU",
]
