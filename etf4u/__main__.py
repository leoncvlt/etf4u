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
        description="Creates a stock portfolio by mix and matching ETFs on the web"
    )
    argparser.add_argument(
        "--fund",
        action="append",
        help="Add the ETF with this symbol to the mix",
    )
    argparser.add_argument(
        "--clamp",
        type=int,
        default=0,
        help="Clamp the number of maximum holdings to this value, and redistribute weights",
    )
    argparser.add_argument(
        "--out-file",
        help="Exports the holdings list to this comma-separated (.csv) file",
    )
    argparser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't load from / save to cache files",
    )
    args = argparser.parse_args()

    # configure logging for the application
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    rich_handler = RichHandler()
    rich_handler.setFormatter(logging.Formatter(fmt="%(message)s", datefmt="[%X]"))
    log.addHandler(rich_handler)
    log.propagate = False

    if not args.fund:
        log.warning("Please add at least one ETF fund with using --fund [symbol]")
        sys.exit(0)

    # start the application
    portfolio = {}
    for fund in args.fund:
        sanitized_fund = fund.lower()
        for loader, name, _ in pkgutil.iter_modules(adapters.__path__):
            adapter = loader.find_module(name).load_module(name)
            if sanitized_fund in adapter.FUNDS:
                log.info(f"Fetching ETF {sanitized_fund.upper()} using {name} adapter")
                if (args.no_cache):
                    result = adapter.fetch(sanitized_fund)
                else:
                    result = query(sanitized_fund, adapter.fetch)
                portfolio = combine_dicts(portfolio, result)
                break
        else:
            log.warning(f"No adapter found for ETF {fund}, using default etfdbd adapter")
            from adapters import etfdb
            if (args.no_cache):
                result = etfdb.fetch(sanitized_fund)
            else:
                result = query(sanitized_fund, etfdb.fetch)
           
            portfolio = combine_dicts(portfolio, result)

    if args.clamp:
        portfolio = dict(
            sorted(portfolio.items(), key=operator.itemgetter(1), reverse=True)[
                : args.clamp
            ]
        )

    total_fund_weight = sum([float(value) for value in portfolio.values()])
    for holding, weight in portfolio.items():
        portfolio[holding] = round((weight * 100) / total_fund_weight, 2)

    print(portfolio)

    if args.out_file:
        with open(args.out_file, "w") as csv_file:
            print(f"Exporting to {args.out_file}...")
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
