# tradedashboard

Tools to pull recent Micro E-mini S&P 500 (MES) data from Alpha Vantage, compute intraday reference levels, and show a trading bias summary. You can run it as a terminal helper or as a lightweight Flask dashboard ("Lavender mode").

## Setup
1. Use Python 3.10+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Export your Alpha Vantage API key so the script can authenticate (a default key is bundled for convenience, but you should re
place it with your own for reliability):
   ```bash
   export ALPHAVANTAGE_API_KEY="your_api_key"
   ```

## Usage

### Terminal helper
Run the helper to fetch the last 24 hours of 15-minute MES candles, compute ATR-based levels, and output guidance:

```bash
python mes_live_levels.py
```

The script prints breakout/breakdown levels, dip-buy and supply zones, plus a directional bias suggestion. Levels are rounded to the nearest five points to keep the zones clean.

### Lavender dashboard (Flask)
Start the minimal dashboard and open it in your browser (defaults to http://localhost:8000):

```bash
python lavender_dashboard.py
```

The page auto-refreshes every 60 seconds and shows the same breakout/breakdown lines, dip and supply zones, ATR, and bias text. The JSON powering the page is available at `/api/snapshot`.

## Notes
- The script requires at least 20 candles to compute ATR. If fewer candles are returned, it will raise an error.
- Alpha Vantage may rate-limit requests; re-run the script if you hit a transient failure.
