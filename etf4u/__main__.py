import os
import sys
import logging
import argparse
import csv
import operator
import pkgutil

from rich import print
from rich.logging import RichHandler
from rich.traceback import install as install_rich_tracebacks

log = logging.getLogger(__name__)
install_rich_tracebacks()

import adapters


def combine_dicts(a, b, op=operator.add):
    return {**a, **b, **{k: op(float(a[k]), float(b[k])) for k in a.keys() & b}}


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
        for loader, name, _ in pkgutil.iter_modules(adapters.__path__):
            sanitized_fund = fund.lower()
            adapter = loader.find_module(name).load_module(name)
            if sanitized_fund in adapter.FUNDS:
                log.info(f"Fetching ETF {sanitized_fund.upper()} using {name} adapter")
                result = adapter.query(sanitized_fund)
                portfolio = combine_dicts(portfolio, result)
                break
        else:
            log.warning(f"No adapter found for ETF {fund}")

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
