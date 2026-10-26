"""Small, cached Yahoo quote feed; never promotes delayed quotes to live data."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import math
import threading
import time
import requests

_lock = threading.Lock()
_cache = None
_cache_time = 0


def fetch_quote(name):
    symbol = {'ES': 'ES=F', 'ZB': 'ZB=F'}[name]
    response = requests.get(
        f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}',
        params={'range': '1d', 'interval': '1m'},
        headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
    response.raise_for_status()
    chart = response.json().get('chart') or {}
    if chart.get('error') or not chart.get('result'):
        raise ValueError(f'{name}: quote unavailable')
    meta = chart['result'][0].get('meta') or {}
    price = float(meta['regularMarketPrice'])
    quote_time = datetime.fromtimestamp(meta['regularMarketTime'], timezone.utc)
    if not math.isfinite(price) or price <= 0:
        raise ValueError(f'{name}: invalid quote')
    return name, {
        'name': name, 'symbol': symbol, 'last': price,
        'quote_time': quote_time.isoformat(),
        'source': 'Yahoo Finance', 'delayed': True,
    }


def market_quotes():
    global _cache, _cache_time
    with _lock:
        if _cache is not None and time.monotonic() - _cache_time < 60:
            return _cache
        # Failure returns an error to the caller, not an old quote with a new timestamp.
        with ThreadPoolExecutor(max_workers=2) as pool:
            instruments = dict(pool.map(fetch_quote, ['ES', 'ZB']))
        _cache = {
            'provider': 'Yahoo Finance delayed quotes', 'status': 'delayed',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'instruments': instruments,
        }
        _cache_time = time.monotonic()
        return _cache
