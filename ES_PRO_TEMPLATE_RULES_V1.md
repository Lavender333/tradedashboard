# Professional ES Daily Template — Deterministic Rule Specification v1

## Purpose

This document translates the Professional ES Daily Trading Template into rules that a live dashboard and a historical backtest can evaluate identically. A field that cannot be reconstructed from historical data must be marked unavailable; it must never be silently counted as a pass.

## Two honest operating modes

1. **Full live mode (100 points):** Includes verified order-flow data. A trade may be labeled executable only when every hard gate passes and the score is at least 85/100.
2. **Historical core mode (90 points):** Excludes the 10-point order-flow section when historical order-flow data is unavailable. Display the result as `CORE RESEARCH`, normalize it as `core_points / 90 * 100`, and never label it a full-template validation.

## Data and time rules

- Instrument: front active ES contract selected by volume, then open interest; roll automatically.
- Historical series: continuous ES, open-interest mapped, back-adjusted for indicators. Entries and exits use the contemporaneous mapped contract price.
- Base data: one-minute trades aggregated into completed five-minute bars.
- Context data: completed five-minute bars aggregated into completed 20-minute bars.
- Time zone: America/New_York.
- CME trade date: begins at 6:00 PM ET on the prior calendar day.
- Overnight range: 6:00 PM–9:29:59 AM ET for the current CME trade date.
- Opening range: 9:30–9:59:59 AM ET.
- New-entry window: 10:00 AM–1:59:59 PM ET. No new entry before the opening range is complete or at/after 2:00 PM.
- Maximum: one ES trade per CME trade date.
- Only information timestamped at or before the decision bar may be used. No look-ahead values.
- Live-data gate: correct contract, correct trade date, completed bars, indicators ready, data age no more than seven minutes, and a non-delayed execution feed.

## ES-versus-ZB selector

Evaluate ES at 10:00 AM ET and ZB at 8:30 AM ET. Each receives one point for:

1. Clear higher-timeframe direction.
2. 20-minute EMA20/EMA50 aligned with that direction.
3. Price on the directional side of RTH VWAP.
4. Price within 0.25 ATR(14) of a defined reference level.
5. At least 0.50 ATR of unobstructed room to the next reference level.
6. One or two completed five-minute closes confirming the directional side of the level.

Selector decision:

- 5–6: eligible market.
- 4: watch only.
- 0–3: skip.
- Trade ES only when ES scores at least 5, exceeds ZB after tie-breaks, and all ES template gates below pass.
- Tie-break order: selector score, target room in ATR, VWAP separation in ATR, then confirmed reaction. An exact tie is `WAIT`.

## Direction definition

Determine a proposed direction before scoring. Every directional score is symmetric for longs and shorts.

- **Daily vote:** At least four of the 20/50/72/100/200 daily moving averages align with the proposed direction.
- **Weekly vote:** Price is in the directional half of the prior completed week's range; a break beyond the prior-week extreme is the strongest reading.
- **Monthly vote:** Same rule using the prior completed month's range.
- **Higher-timeframe direction:** At least two of daily, weekly, and monthly votes agree. Otherwise `NO TRADE`.

## Score — full live mode

### 1. Macro environment — 20 points

- Scheduled-news risk, 5 points: 5 with no relevant event; 4 with only a Fed speaker or Treasury auction; 3 with a high-impact release; 0 if event data is unavailable.
- Rates alignment, 5 points: 5 when at least two of 2Y/10Y/30Y yield directions support the trade; 3 when mixed; 1 when at least two oppose it; 0 if unavailable.
- Overnight/news context, 10 points: start at 10; subtract 4 for a high-impact release, 2 for a Fed/FOMC event, and 1 for a Treasury auction; floor at 0.
- Hard macro gate: at least two yield tenors must support the direction. Mixed or unavailable rates are watch-only.

### 2. Higher-timeframe trend — 35 points

- Daily alignment, 15 points: five aligned averages = 15; four = 12; three = 9; two = 6; fewer than two = 0.
- Weekly alignment, 10 points: beyond the prior-week extreme = 10; directional half of the range = 6; opposite half = 0.
- Monthly alignment, 10 points: beyond the prior-month extreme = 10; directional half of the range = 6; opposite half = 0.
- Hard HTF gate: at least two of the three votes must agree with the proposed trade.

### 3. Trend Pro confirmation — 15 points

- Actual Daily and 240-minute Trend Pro signals both agree = 15.
- One agrees and the other is neutral = 7.
- Any signal opposes, or both are unavailable = 0.
- Hard Trend Pro gate: both signals must be present and neither may oppose the trade in full live mode.
- A moving-average proxy must be labeled `PROXY`; it is not a full-template Trend Pro test.

### 4. Market structure — 10 points

- Entry is within 0.25 ATR of an approved reference level = 2.
- RTH VWAP agrees with direction = 2.
- Two-day anchored VWAP agrees = 1.
- A completed five-minute candle accepts beyond the level by at least two ES ticks = 2.
- A later bar retests the level without invalidation = 2.
- The newest completed five-minute candle confirms away from the level = 1.

The full professional worksheet may score overnight high/low, completed opening-range high/low, previous-day high/low, and previous-week high/low as context. The deployed ES Overnight-Only Research V1 execution candidate has a stricter setup whitelist: only an Overnight High breakout/retest long or Overnight Low breakdown/retest short can form a research entry. Opening Range, previous-day, and previous-week levels cannot trigger an ES research entry. A setup must identify exactly one primary level.

### 5. Order flow — 10 points

- Aggressor delta agrees = 3.
- Absorption or an iceberg supports the retest = 3.
- Liquidity shift agrees = 2.
- No dominant opposing liquidity immediately beyond entry = 2.
- Hard order-flow gate: at least 6/10 and no dominant opposing liquidity. If the feed is disconnected, full live mode is `NO TRADE`; historical core mode records `N/A` and excludes these 10 points.

### 6. Volatility — 5 points

- VIX below 16 = 5.
- VIX 16–21.99 = 4.
- VIX 22–29.99 = 3.
- VIX 30 or higher = 2.
- Missing VIX = 0.

### 7. Trade plan — 5 points

Award all 5 only when entry, structural stop, Target 1, Target 2, direction, timestamp, and cost-adjusted reward/risk are known and valid. Otherwise award 0.

## Setup sequence

An entry exists only after this ordered sequence:

1. The chosen market, direction, data-quality gate, and higher-timeframe gate pass.
2. A completed five-minute bar closes at least two ticks beyond the primary level.
3. A subsequent bar retests the level.
4. The retest does not violate the level by more than six ticks.
5. The newest completed five-minute candle closes in the trade direction beyond the level.
6. Confirmation-candle body is no more than 0.35 of 20-minute ATR(14).
7. Long BB position is 0.60–0.75. A short is rejected when BB position is below 0.15. These are frozen production rules until separately retested.
8. Structural risk is 0.45–1.00 ATR and at least six ES points. Never widen a stop merely to satisfy this rule; skip the setup.
9. Estimated transaction cost is no more than 0.10R.
10. Every applicable hard gate passes and the score is at least 85/100 in full live mode.

The confirmation close is the entry. A watch level is never an entry price.

## Stop, targets, costs, and outcome rules

- Stop: one tick beyond the most adverse price in the accepted break/retest/confirmation structure.
- Risk `R`: absolute distance from entry to structural stop.
- Target 1: 1R; exit 50%.
- Target 2: 2R; exit the remaining 50%.
- The 2:1 institutional gate evaluates **Target 2**, not Target 1.
- If Target 1 is reached, the existing tested model leaves the original structural stop in place unless a different rule is separately validated.
- Close any remainder at 3:55 PM ET.
- Backtests must use stop-first ordering when the same five-minute bar touches both stop and target.
- Costs: $5 round turn per contract plus at least one ES tick of slippage on entry and one on exit.

## Final decision

- `NO TRADE`: any hard gate fails, data is stale/unavailable, total is below 85, or the setup sequence is incomplete.
- `CORE RESEARCH`: historical core score is at least 85% and all automatable gates pass, but historical order flow or actual Trend Pro data is unavailable.
- `LIVE TRADE ELIGIBLE`: full score is at least 85/100 and every hard gate—including actual Trend Pro and order flow—passes.

The dashboard may display direction and watch levels before confirmation, but entry, stop, targets, position size, and an executable label must remain blank until the final decision is `LIVE TRADE ELIGIBLE`.

## Required backtest report

For every session, retain the selector scores, all seven section scores, every hard-gate result, rejection reason, setup type, entry/stop/targets, gross R, cost R, net R, and maximum adverse/favorable excursion. Report total trades, win rate, net R, expectancy, profit factor, maximum drawdown, setup-specific results, long/short results, time-of-day results, and rejection counts.

Minimum validation standard: at least 30 qualifying trades, positive cost-adjusted expectancy, profit factor at least 1.5, and an explicitly reported maximum drawdown. Parameters must remain locked during the validation window.
