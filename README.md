# etf4u

A python tool which scrapes real-time information about ETF holdings from the web, and can blend multiple ETF together by proportionally distributing their assets allocation, optionally clamping the maximum amount of assets for the blended fund.

## Installation & Requirements

Make sure you're in your virtual environment of choice, then run
- `poetry install --no-dev` if you have [Poetry](https://python-poetry.org/) installed
- `pip install -r requirements.txt` otherwise

## Usage

```
etf4u [-h] [--clamp CLAMP] [--minimum MINIMUM] [--exclude EXCLUDE [EXCLUDE ...]] [--include INCLUDE [INCLUDE ...]] [--out-file OUT_FILE] [--no-cache] [-v] funds [funds ...]

positional arguments:
  funds                 A list of ETF symbols (or a single one) to scrape

optional arguments:
  -h, --help            show this help message and exit
  --clamp CLAMP         Clamp the number of maximum assets to this value, redistributing weights
  --minimum MINIMUM     Remove all assets with allocation smaller than this number after redistribution
  --exclude EXCLUDE [EXCLUDE ...]
                        A list of tickers to exclude from the scraped portfolio. Pass the tickers directly to the argument (e.g. --exclude AAA BBB CCC) Or pass the path to a text file containing the tickers
  --include INCLUDE [INCLUDE ...]
                        Only include assets whose ticker appear in this list. Pass the tickers directly to the argument (e.g. --include AAA BBB CCC) Or pass the path to a text file containing the tickers
  --out-file OUT_FILE   Exports the holdings list to this comma-separated (.csv) file
  --no-cache            Don't use cache files to load or store data
  -v, --verbose         Increase output log verbosity
  ```

## Explanation

The tool exports the list of assets as a simple `{ [asset_symbol] : [weight] }` dictionary format. Use the `--out-file` option to export this to a .csv. 

When going through the provided ETF symbols, the script checks if there's a bespoke adapter defined to fetch information for that specific fund (some ETFs provides the full list of holdings on their website) - if not found, it uses a generic adapter that scrapes https://etfdb.com/ - the public version of the website only publishes the top 15 holdings for a fund but the script mixes and matches several requests with different sorting criterias to try and get the largest amount of data possible.

All data is cached on a daily basis, meaning that using the same fund in multiple commands will only scrape the real-time information once a day and then re-use the data from disk afterwards. Use the `--no-cache` flag to always query real-time data.

You can also use the tool to scrape a single ETF by passing only one symbole to the `--funds` parameter and not supplying the `--clamp` option.

## Creating an adapter

Simply create a new `.py` file in the `adapters` folder, implementing the following:

- A `FUNDS` variable in the module's scope containing a list of ETF symbols that should be processed with this adapter
- a `fetch()` method which takes a `fund` parameter being the ETF symbol, and returns a dictionary of assets and their weights in the  `{ [asset_symbol] : [weight] }` format

No need to add anything else, the script automatically checks all modules in the `adapters` folder when processing funds. For a practical examples, check the existing adapters.

## Example usage
`python etf4u ARKK ARKW ARKQ ARKF ARKG --clamp 50 --out-file blend_ark.csv`
Adds together all holdings the 5 ARK’s Active ETFs, keeps only the top 50 holdings on the list, rebalances all weights proportionally and exports the assets list to the `blend_ark.csv` file 

## Support [![Buy me a coffee](https://img.shields.io/badge/-buy%20me%20a%20coffee-lightgrey?style=flat&logo=buy-me-a-coffee&color=FF813F&logoColor=white "Buy me a coffee")](https://www.buymeacoffee.com/leoncvlt)
If this tool has proven useful to you, consider [buying me a coffee](https://www.buymeacoffee.com/leoncvlt) to support development of this and [many other projects](https://github.com/leoncvlt?tab=repositories).