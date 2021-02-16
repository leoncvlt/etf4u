import os
import sys
import logging
import argparse
import csv
import operator
import pkgutil

from datetime import datetime
from pathlib import Path
from rich import print
from rich.logging import RichHandler
from rich.traceback import install as install_rich_tracebacks

log = logging.getLogger(__name__)
install_rich_tracebacks()

import adapters


def combine_dicts(a, b, op=operator.add):
    return {**a, **b, **{k: op(float(a[k]), float(b[k])) for k in a.keys() & b}}


def query(fund, fetch_method):
    now = datetime.now()
    cached_file = Path(".cache") / f"{fund.upper()}_{now.strftime('%Y%m%d')}.csv"
    if cached_file.is_file():
        log.debug(f"Using data from cached file: {cached_file}")
        with open(cached_file, "r") as csv_file:
            reader = csv.reader(csv_file)
            return {rows[0]: float(rows[1]) for rows in reader}
    else:
        data = fetch_method(fund)
        if data:
            cached_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cached_file, "w") as csv_file:
                log.debug(f"Caching data to file: {cached_file}")
                writer = csv.writer(csv_file, delimiter=",", lineterminator="\n")
                for holding, weight in data.items():
                    writer.writerow([holding, weight])
        return data


def main():
    # parse command line arguments
    argparser = argparse.ArgumentParser(
        description="Scrapes ETF holdings data and creates blended assets lists"
    )
    argparser.add_argument(
        "funds",
        nargs="+",
        default=[],
        help="A list of ETF symbols (or a single one) to scrape",
    )
    argparser.add_argument(
        "--clamp",
        type=int,
        default=0,
        help="Clamp the number of maximum assets to this value, redistributing weights",
    )
    argparser.add_argument(
        "--minimum",
        type=float,
        default=0.0,
        help="Remove all assets with allocation smaller than this number after redistribution",
    )
    argparser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="A list of tickers to exclude from the scraped portfolio. "
        "Pass the tickers directly to the argument (e.g. --exclude AAA BBB CCC) "
        "Or pass the path to a text file containing the tickers",
    )
    argparser.add_argument(
        "--include",
        nargs="+",
        default=[],
        help="Only include assets whose ticker appear in this list. "
        "Pass the tickers directly to the argument (e.g. --include AAA BBB CCC) "
        "Or pass the path to a text file containing the tickers",
    )
    argparser.add_argument(
        "--out-file",
        help="Exports the holdings list to this comma-separated (.csv) file",
    )
    argparser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cache files to load or store data",
    )
    argparser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output log verbosity"
    )
    args = argparser.parse_args()

    # configure logging for the application
    log = logging.getLogger("etf4u")
    log.setLevel(logging.INFO if not args.verbose else logging.DEBUG)
    rich_handler = RichHandler()
    rich_handler.setFormatter(logging.Formatter(fmt="%(message)s", datefmt="[%X]"))
    log.addHandler(rich_handler)
    log.propagate = False

    # start the application
    portfolio = {}
    for fund in args.funds:
        sanitized_fund = fund.lower()
        for loader, name, _ in pkgutil.iter_modules(adapters.__path__):
            adapter = loader.find_module(name).load_module(name)
            if sanitized_fund in [f.lower() for f in adapter.FUNDS]:
                log.info(f"Fetching ETF {sanitized_fund.upper()} using {name} adapter")
                if args.no_cache:
                    result = adapter.fetch(sanitized_fund)
                else:
                    result = query(sanitized_fund, adapter.fetch)
                portfolio = combine_dicts(portfolio, result)
                break
        else:
            log.warning(f"No adapter found for ETF {fund}, using default etfdbd adapter")
            from adapters import etfdb

            if args.no_cache:
                result = etfdb.fetch(sanitized_fund)
            else:
                result = query(sanitized_fund, etfdb.fetch)

            portfolio = combine_dicts(portfolio, result)

    # process inclusion list / file
    if len(args.include):
        inclusion_list = args.include
        if Path(inclusion_list[0]).is_file():
            with open(inclusion_list[0]) as f:
                inclusion_list = f.read().split()
        portfolio = {
            asset: weight
            for (asset, weight) in portfolio.items()
            if asset in inclusion_list
        }

    # process exclusion list / file
    if len(args.exclude):
        exclusion_list = args.include
        if Path(exclusion_list[0]).is_file():
            with open(exclusion_list[0]) as f:
                exclusion_list = f.read().split()
        portfolio = {
            asset: weight
            for (asset, weight) in portfolio.items()
            if not asset in exclusion_list
        }

    # clamp assets amount if necessary
    if args.clamp:
        portfolio = dict(
            sorted(portfolio.items(), key=operator.itemgetter(1), reverse=True)[
                : args.clamp
            ]
        )

    # go through the portfolio, redistributing all weights to a 100% allocation value,
    # and if any asset doesn't meet the minimum allocation value once redistributed,
    # remove those from the portfolio and redistribute again afterwards
    redistributed = False
    while not redistributed:
        total_fund_weight = sum([float(value) for value in portfolio.values()])
        holdings_to_remove = []
        redistribution_successful = True
        for holding, weight in portfolio.items():
            new_weight = round((weight * 100) / total_fund_weight, 2)
            if new_weight >= args.minimum and not holding in args.exclude:
                portfolio[holding] = new_weight
            else:
                log.debug(f"{holding} doesn't meet minimum allocation value")
                holdings_to_remove.append(holding)
                if redistribution_successful:
                    redistribution_successful = False
        for holding in holdings_to_remove:
            del portfolio[holding]
        redistributed = redistribution_successful

    # reorder the holdings, from largest to smallest weight
    portfolio = {
        k: portfolio[k] for k in sorted(portfolio, key=portfolio.get, reverse=True)
    }

    print(portfolio)

    # export to file
    if args.out_file:
        with open(args.out_file, "w") as csv_file:
            log.info(f"Exporting to {args.out_file}...")
            writer = csv.writer(csv_file, delimiter=",", lineterminator="\n")
            for key, value in portfolio.items():
                writer.writerow([key, value])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.critical("Interrupted by user")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
