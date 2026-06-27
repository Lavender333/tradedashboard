# tradedashboard

Tools to pull recent Micro E-mini S&P 500 (MES) futures data, compute intraday reference levels, and show a trading bias summary. You can run it as a terminal helper or as a lightweight Flask dashboard ("Lavender mode").

## Setup
1. Use Python 3.10+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. For accurate MES futures candles, export a Databento API key:
   ```bash
   export DATABENTO_API_KEY="your_databento_key"
   ```

   Optional futures feed settings:
   ```bash
   export MES_DATA_PROVIDER="databento"
   export MES_SYMBOL="MES.c.0"
   export DATABENTO_DATASET="GLBX.MDP3"
   export MES_RESOLUTION_MINUTES="15"
   ```

4. Alpha Vantage is still available as a legacy fallback, but it is not the recommended path for accurate MES futures data:
   ```bash
   export MES_DATA_PROVIDER="alphavantage"
   export ALPHAVANTAGE_API_KEY="your_api_key"
   export ALPHAVANTAGE_SYMBOL="MES=F"
   ```

## Usage

### Terminal helper
Run the helper to fetch recent 15-minute MES candles, compute ATR-based levels, and output guidance:

```bash
python mes_live_levels.py
```

The script prints breakout/breakdown levels, dip-buy and supply zones, plus a directional bias suggestion. Levels are rounded to the nearest five points to keep the zones clean.

### Lavender dashboard (Flask)
Start the minimal dashboard and open it in your browser (defaults to http://localhost:8000):

```bash
python lavender_dashboard.py
```

The page auto-refreshes every 60 seconds and shows the same breakout/breakdown lines, dip and supply zones, ATR, bias text, provider/symbol, data freshness, ETH session window, overnight high/low, and prior RTH high/low. The JSON powering the page is available at `/api/snapshot`.

### GitHub Pages
The public static dashboard is available at:

```text
https://lavender333.github.io/tradedashboard/
```

GitHub Pages cannot run Flask, so the Pages version reads `data/snapshot.json`. The included GitHub Actions workflow refreshes that file every 15 minutes and deploys the static site.

To make the Pages dashboard live:

1. In GitHub, add a repository secret named `DATABENTO_API_KEY`.
2. Go to the repository's **Actions** tab.
3. Run **Deploy GitHub Pages** once, or push a change to `main`.
4. In repository settings, set Pages to use **GitHub Actions** if GitHub asks for a source.

## Notes
- The script requires at least 20 candles to compute ATR. If fewer candles are returned, it will raise an error.
- By default, levels are based on the current or most recent CME equity futures ETH session, with RTH and overnight reference levels included in the snapshot.
- The dashboard marks data as stale when the latest candle is older than `MES_STALE_AFTER_MINUTES`.
- Alpha Vantage may rate-limit requests and may not return valid MES futures candles. Use Databento or another futures-capable provider for trading-grade accuracy.
