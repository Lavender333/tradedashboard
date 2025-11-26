# tradedashboard

Command-line helper to pull recent Micro E-mini S&P 500 (MES) data from Finnhub, compute intraday reference levels, and print a quick trading bias summary.

## Setup
1. Use Python 3.10+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Export your Finnhub API key so the script can authenticate:
   ```bash
   export FINNHUB_API_KEY="your_api_key"
   ```

## Usage
Run the helper to fetch the last 24 hours of 15-minute MES candles, compute ATR-based levels, and output guidance:

```bash
python mes_live_levels.py
```

The script prints breakout/breakdown levels, dip-buy and supply zones, plus a directional bias suggestion. Levels are rounded to the nearest five points to keep the zones clean.

## Notes
- The script requires at least 20 candles to compute ATR. If fewer candles are returned, it will raise an error.
- Finnhub may rate-limit requests; re-run the script if you hit a transient failure.
