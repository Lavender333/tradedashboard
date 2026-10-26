"""Publish delayed quote prices for static hosting without a broker backend."""
import json
from pathlib import Path
from quote_feed import market_quotes
from snapshot_io import atomic_write

if __name__ == '__main__':
    # Fail the build on an upstream error; do not publish an empty quote file.
    atomic_write(Path('data/market-quotes.json'), json.dumps(market_quotes(), indent=2) + '\n')
