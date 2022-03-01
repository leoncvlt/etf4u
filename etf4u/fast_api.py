import os, sys, argparse, pkgutil

#Paths
cwdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, cwdir)
import adapters

from fastapi import FastAPI
app_version = '0.01'
app = FastAPI(
	title = 'ETF4U',
	description = "an API to tell you a given ETF's constituents",
	version = app_version
)

# For Caching
from functools import lru_cache, wraps
from datetime import datetime, timedelta

def timed_lru_cache(seconds: int, maxsize: int = 128):
	''' add an expiry to the lru_cache
	ref: https://realpython.com/lru-cache-python/
	'''
	def wrapper_cache(func):
		func = lru_cache(maxsize=maxsize)(func)
		func.lifetime = timedelta(seconds=seconds)
		func.expiration = datetime.utcnow() + func.lifetime

		@wraps(func)
		def wrapped_func(*args, **kwargs):
			if datetime.utcnow() >= func.expiration:
				func.cache_clear()
				func.expiration = datetime.utcnow() + func.lifetime
			return func(*args, **kwargs)

		return wrapped_func

	return wrapper_cache

@timed_lru_cache(seconds = 8*60**2) #cache data for 8 hours
def decompose(etf_ticker):
    sanitized_fund = etf_ticker.lower()
    result = None
    for loader, name, _ in pkgutil.iter_modules(adapters.__path__):
        adapter = loader.find_module(name).load_module(name)
        if sanitized_fund in [f.lower() for f in adapter.FUNDS]:
            # log.info(f"Fetching ETF {sanitized_fund.upper()} using {name} adapter")
            result = adapter.fetch(sanitized_fund)
            break
    if not result:
        # log.warning(f"No adapter found for ETF {fund}, using default etfdbd adapter")
        from adapters import etfdb
        result = etfdb.fetch(sanitized_fund)
    return {k: result[k] for k in sorted(result, key = result.get, reverse= True)}

@app.get("/query", response_model = dict, response_model_exclude_unset = True)
async def query(etf_ticker: str):
    ''' get ETF constituents
    * `etf_ticker`: a single etf symbol/ ticker
    '''
    return decompose(etf_ticker)

@app.get('/')
def read_root():
	return {"ETF4U API": app_version,
			'status': 'Healthy',
			'message': f'see docs/ endpoint for help',
			}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description= f'get ETF constituents')
    parser.add_argument('--etf', required = True, type = str,
                            help = 'etf symbol/ticker')
    parser.add_argument('--cache', required = False, default = False,
                            action = 'store_true',
                            help = 'save result to cache')
    args = parser.parse_args()
    result = decompose(etf_ticker = args.etf, do_cache = args.cache)

    if result:
        print(f'--- {args.etf} constituents:\n{result}')
    else:
        print(f'no result for {args.etf}')
