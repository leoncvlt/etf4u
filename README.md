# etf4u

A python tool which scrapes real-time information about ETF holdings from the web, and can blend multiple ETF together by proportionally distributing their assets allocation, optionally clamping the maximum amount of assets for the blended fund.

## Installation & Requirements

Make sure you're in your virtual environment of choice, then run
- `poetry install --no-dev` if you have [Poetry](https://python-poetry.org/) installed
- `pip install -r requirements.txt` otherwise

## Usage

```
etf4u [-h] [--funds FUNDS [FUNDS ...]] [--clamp CLAMP] [--out-file OUT_FILE] [--no-cache]

optional arguments:
  -h, --help            show this help message and exit
  --funds FUNDS [FUNDS ...]
                        Add the ETF with this symbol to the mix
  --clamp CLAMP         Clamp the number of maximum assets to this value, redistributing weights
  --out-file OUT_FILE   Exports the holdings list to this comma-separated (.csv) file
  --no-cache            Don't load from / save to cache files
   -v, --verbose         Increase output log verbosity
  ```

## Explanation

The tool exports the list of assets as a simple `{ [asset_symbol] : [weight] }` dictionary format. Use the `--out-file` option to export this to a .csv. 

When going through the ETF symbols provided with the `--funds` options, the script checks if there's a bespoke adapter defined to fetch information for that specific fund (some ETFs provides the full list of holdings on their website) - if not found, it uses a generic adapter that scrapes https://etfdb.com/ - the public version of the website only publishes the top 15 holdings for a fund but the script mixes and matches several requests with different sorting criterias to try and get the largest amount of data possible.

All data is cached on a daily basis, meaning that using the same fund in multiple commands will only scrape the real-time information once a day and then re-use the data from disk afterwards. Use the `--no-cache` flag to always query real-time data.

You can also use the tool to scrape a single ETF by passing only one symbole to the `--funds` parameter and not supplying the `--clamp` option.

## Creating an adapter

Simply create a new `.py` file in the `adapters` folder, implementing the following:

- A `FUNDS` variable in the module's scope containing a list of ETF symbols that should be processed with this adapter
- a `fetch()` method which takes a `fund` parameter being the ETF symbol, and returns a dictionary of assets and their weights in the  `{ [asset_symbol] : [weight] }` format

No need to add anything else, the script automatically checks all modules in the `adapters` folder when processing funds. For a practical examples, check the existing adapters.

## Example usage
`python etf4u --fund ARKK ARKW ARKQ ARKF ARKG --clamp 50 --out-file blend_ark.csv`
Adds together all holdings the 5 ARK’s Active ETFs, keeps only the top 50 holdings on the list, rebalances all weights proportionally and exports the assets list to the `blend_ark.csv` file 