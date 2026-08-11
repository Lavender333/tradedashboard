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

The homepage is the interactive Market Conditions Calendar supplied in React/TSX and bundled as a static asset for GitHub Pages. The live ES/ZB execution view remains available at `trade-board.html`, with the full worksheets at `trading-template-es.html` and `trading-template-zb.html`.
The public static dashboard is available at:

```text
https://lavender333.github.io/tradedashboard/
```

The professional ES and ZB daily trading templates are available at:

```text
https://lavender333.github.io/tradedashboard/trading-template-es.html
https://lavender333.github.io/tradedashboard/trading-template-zb.html
```

The ES/ZB template prefers Webull OpenAPI futures data. It automatically selects the active ES and ZB contracts, builds 20-minute candles, and calculates all technicals locally from that single synchronized feed. If Webull is unavailable, Yahoo is an explicitly labeled delayed planning fallback and execution remains blocked.

Webull setup:

1. Enable Webull OpenAPI and purchase the separate OpenAPI futures market-data subscription.
2. Add repository secrets `WEBULL_APP_KEY` and `WEBULL_APP_SECRET`.
3. The dashboard automatically queries Webull's listed contracts and selects the most liquid of the nearest two unexpired contracts using volume, then open interest as a tie-breaker.
4. Optional repository variables `WEBULL_ES_SYMBOL` and `WEBULL_ZB_SYMBOL` may be set as emergency fallbacks if Webull's contract directory is temporarily unavailable. They are not the normal rollover mechanism.

The displayed current price always includes its provider symbol, Eastern timestamp, source, delay status, and age. Five-minute feed bars drive the displayed price and confirmation checks; 20-minute bars drive ATR and Bollinger calculations. RTH VWAP begins at 9:30 a.m. ET, the opening range completes at 10:00 a.m. ET, and overnight levels use only the current CME trade date.

The complete Professional ES template is defined in [ES_PRO_TEMPLATE_RULES_V1.md](ES_PRO_TEMPLATE_RULES_V1.md). That specification separates the full 100-point live model from the 90-point historical core so unavailable Trend Pro or order-flow data cannot be silently counted as a passing backtest input.

When live Webull data passes the quality gate, the ES research engine waits until 10:00 a.m. ET for a completed five-minute breakout, subsequent retest, and confirming candle. The confirmation close, structural stop, Target 1 at 1R, and Target 2 at 2R remain research fields until the ES selector, 85/100 score, actual Trend Pro, verified order flow, and every institutional gate pass. ES stops below 0.45 ATR, above 1.0 ATR, below six points, above 0.10R modeled cost, or outside Bollinger chase rules are rejected. Delayed fallback data can never publish an executable trade.

ES entries are limited to Monday–Friday, 10:00 a.m.–2:00 p.m. ET; ZB retains its instrument-specific schedule. GitHub requests a new Webull snapshot every five minutes and an open dashboard checks for a newly deployed snapshot every minute. GitHub-hosted schedules and deployments can run late, so the displayed source timestamp and age remain authoritative; snapshots older than seven minutes cannot confirm a trade.

- Daily ES-vs-ZB six-point selection at the 8:10 ET (ZB) and 9:20 ET (ES) checkpoints, using HTF direction, true EMA 20/50 alignment, VWAP, key-level proximity, ATR-normalized target room, and one-to-two completed five-minute closes
- A `TRADE`, `WATCH`, `WAIT`, or `SKIP BOTH` recommendation before the detailed 100-point worksheet and institutional gate
- ES and ZB current price context
- 20/50/72/100/200 daily moving-average checks
- Daily trend score suggestion
- Weekly and monthly high/low
- Previous day high/low
- Opening range and overnight high/low
- Session VWAP for ES/ZB, ES-only two-session anchored VWAP, ATR(14) on 20-minute candles, Bollinger Bands (20,2), delayed VIX context, and Treasury-yield direction
- Economic calendar highlights from the live Nasdaq Economic Calendar feed, with `data/economic-calendar.json` as a fallback
- Overnight / Europe context using overnight range, pre-open direction, inventory, and open confirmation signals
- Instrument-specific ES/ZB master pattern analysis for market state, highest-probability setup, liquidity pattern, news behavior, time window, and intermarket read
- Macro result, Trend Pro proxy, VWAP state, today’s bias, direction, structure score, volatility score, trade-plan score, and the objective gate checks

Manual confirmation is still required for custom Trend Pro levels, Bookmap/order-flow reads, trade entries, stops, targets, and the order-flow portion of the Institutional Alignment Gate.

GitHub Pages cannot run Flask, so the Pages version reads generated snapshots. The included workflow requests a fresh snapshot every five minutes, preferring configured Webull OpenAPI futures data and falling back to explicitly labeled delayed Yahoo planning data. A paid Databento feed can still be selected locally with `TEMPLATE_DATA_PROVIDER=databento`, but it is not required by the public deployment.

For trading-grade data:

1. In GitHub, add a repository secret named `DATABENTO_API_KEY`.
2. Go to the repository's **Actions** tab.
3. Run **Deploy GitHub Pages** once, or push a change to `main`.
4. In repository settings, set Pages to use **GitHub Actions** if GitHub asks for a source.

## Notes
- The script requires at least 20 candles to compute ATR. If fewer candles are returned, it will raise an error.
- By default, levels are based on the current or most recent CME equity futures ETH session, with RTH and overnight reference levels included in the snapshot.
- The dashboard marks data as stale when the latest candle is older than `MES_STALE_AFTER_MINUTES`.
- Alpha Vantage may rate-limit requests and may not return valid MES futures candles. Use Databento or another futures-capable provider for trading-grade accuracy.
