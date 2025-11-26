# tradedashboard

Tools to pull recent S&P 500 Futures (ES=F) data from Yahoo Finance, compute intraday reference levels, and show a trading bias summary. You can run it as a terminal helper or as a lightweight Flask dashboard ("Lavender mode").

## Setup
1. Use Python 3.10+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Terminal helper
Run the helper to fetch 15-minute ES candles, compute ATR-based levels, and output guidance:

```bash
python mes_live_levels.py
```

The script prints breakout/breakdown levels, dip-buy and supply zones, plus a directional bias suggestion. Levels are rounded to the nearest four points to keep the zones clean.

### Lavender dashboard (Flask)
Start the minimal dashboard and open it in your browser (defaults to http://localhost:8000):

```bash
python lavender_dashboard.py
```

The page auto-refreshes every 60 seconds and shows the same breakout/breakdown lines, dip and supply zones, ATR, and bias text. The JSON powering the page is available at `/api/snapshot`.

## Notes
- Yahoo Finance data is typically delayed by 10–15 minutes unless you have a paid feed.
- The script requires at least 20 candles to compute ATR. If fewer candles are returned, it will surface an error message.
