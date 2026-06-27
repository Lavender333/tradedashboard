"""Build automated market context for the ES/ZB trading template."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests


OUTPUT = Path("data/template-snapshot.json")
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_chart(symbol: str, range_: str, interval: str) -> Dict:
    response = requests.get(
        YAHOO_URL.format(symbol=symbol),
        params={"range": range_, "interval": interval, "includePrePost": "true"},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"{symbol}: {chart['error']}")
    result = (chart.get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"{symbol}: no chart data returned")
    return result


def candles(symbol: str, range_: str, interval: str) -> List[Dict]:
    result = fetch_chart(symbol, range_, interval)
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    rows = []
    for index, timestamp in enumerate(timestamps):
        try:
            row = {
                "time": datetime.fromtimestamp(timestamp, timezone.utc),
                "open": quote["open"][index],
                "high": quote["high"][index],
                "low": quote["low"][index],
                "close": quote["close"][index],
                "volume": (quote.get("volume") or [0] * len(timestamps))[index] or 0,
            }
        except (IndexError, KeyError):
            continue
        if any(row[key] is None for key in ["open", "high", "low", "close"]):
            continue
        rows.append(row)
    if not rows:
        raise RuntimeError(f"{symbol}: no usable candles")
    return rows


def sma(values: List[float], period: int):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def atr(rows: List[Dict], period: int = 14):
    if len(rows) < period + 1:
        return None
    true_ranges = []
    for index in range(1, len(rows)):
        high = rows[index]["high"]
        low = rows[index]["low"]
        prev_close = rows[index - 1]["close"]
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    return sum(true_ranges[-period:]) / period


def vwap(rows: List[Dict]):
    weighted = 0.0
    total_volume = 0.0
    for row in rows:
        volume = row.get("volume") or 0
        typical = (row["high"] + row["low"] + row["close"]) / 3
        weighted += typical * volume
        total_volume += volume
    if total_volume == 0:
        return None
    return weighted / total_volume


def round_price(value):
    if value is None:
        return None
    return round(float(value), 2)


def trend_score(close: float, averages: Dict[str, float]) -> Dict:
    above_count = sum(1 for value in averages.values() if value is not None and close > value)
    if above_count == 5:
        score = 10
    elif above_count == 4:
        score = 8
    elif above_count == 3:
        score = 6
    else:
        score = 0
    if above_count >= 4:
        result = "Bullish"
    elif above_count <= 1:
        result = "Bearish"
    else:
        result = "Neutral"
    return {"above_count": above_count, "score": score, "result": result}


def period_range(rows: List[Dict], key_func, offset: int = 1) -> Dict:
    periods = []
    current_key = None
    bucket = []
    for row in rows:
        key = key_func(row["time"])
        if current_key is None:
            current_key = key
        if key != current_key:
            periods.append(bucket)
            bucket = []
            current_key = key
        bucket.append(row)
    if bucket:
        periods.append(bucket)
    if len(periods) <= offset:
        selected = periods[0]
    else:
        selected = periods[-1 - offset]
    return {
        "high": max(row["high"] for row in selected),
        "low": min(row["low"] for row in selected),
    }


def range_break_result(last: float, high: float, low: float) -> Dict:
    if last > high:
        result = "Bullish"
        score = 10
    elif last < low:
        result = "Bearish"
        score = 0
    else:
        midpoint = (high + low) / 2
        result = "Bullish" if last >= midpoint else "Bearish"
        score = 6 if result == "Bullish" else 3
    return {"result": result, "score": score}


def structure_score(last: float, previous_high: float, previous_low: float, on_high: float, on_low: float, vwap_value) -> Dict:
    score = 4
    if previous_low <= last <= previous_high:
        score += 2
    if on_low <= last <= on_high:
        score += 2
    if vwap_value is not None:
        score += 1
    score = min(10, score)
    if vwap_value is None:
        vwap_position = "Mixed"
    elif last > vwap_value:
        vwap_position = "Above"
    elif last < vwap_value:
        vwap_position = "Below"
    else:
        vwap_position = "Mixed"
    return {"score": score, "vwap": round_price(vwap_value), "vwap_position": vwap_position}


def volatility_score(name: str, vix, daily_atr_value) -> int:
    if name == "ES" and vix is not None:
        if vix < 16:
            return 5
        if vix < 22:
            return 4
        if vix < 30:
            return 3
        return 2
    if daily_atr_value is not None:
        return 3
    return 0


def trade_decision(rate_result: str, htf_result: str) -> Dict:
    if rate_result == "Bullish" and htf_result == "Bullish":
        return {"todays_bias": "Bull", "direction": "Long Only", "trade_plan_score": 3}
    if rate_result == "Bearish" and htf_result == "Bearish":
        return {"todays_bias": "Bear", "direction": "Short Only", "trade_plan_score": 3}
    return {"todays_bias": "Neutral", "direction": "No Trade", "trade_plan_score": 0}


def combined_htf_result(daily_result: str, weekly_result: str, monthly_result: str) -> str:
    votes = [daily_result, weekly_result, monthly_result]
    bullish = votes.count("Bullish")
    bearish = votes.count("Bearish")
    if bullish >= 2:
        return "Bullish"
    if bearish >= 2:
        return "Bearish"
    return "Neutral"


def instrument_snapshot(name: str, symbol: str, rate_result: str, vix=None) -> Dict:
    daily = candles(symbol, "1y", "1d")
    intraday = candles(symbol, "5d", "15m")
    closes = [row["close"] for row in daily]
    current = closes[-1]
    averages = {f"ma{period}": sma(closes, period) for period in [20, 50, 72, 100, 200]}
    trend = trend_score(current, averages)
    prev_day = daily[-2] if len(daily) > 1 else daily[-1]
    weekly_range = period_range(daily, lambda value: value.isocalendar()[:2])
    monthly_range = period_range(daily, lambda value: (value.year, value.month))
    weekly_trend = range_break_result(current, weekly_range["high"], weekly_range["low"])
    monthly_trend = range_break_result(current, monthly_range["high"], monthly_range["low"])
    htf_result = combined_htf_result(trend["result"], weekly_trend["result"], monthly_trend["result"])
    intraday_atr = atr(intraday)
    daily_atr = atr(daily)
    vwap_value = vwap(intraday[-26:])
    structure = structure_score(
        current,
        prev_day["high"],
        prev_day["low"],
        max(row["high"] for row in intraday[:-26] or intraday),
        min(row["low"] for row in intraday[:-26] or intraday),
        vwap_value,
    )
    decision = trade_decision(rate_result, htf_result)
    auto = {
        "direction": decision["direction"],
        "todays_bias": decision["todays_bias"],
        "trade_plan_score": decision["trade_plan_score"],
        "trend_pro_result": htf_result,
        "trend_pro_score": 15 if htf_result != "Neutral" else 7,
        "structure_score": structure["score"],
        "volatility_score": volatility_score(name, vix, daily_atr),
        "vwap": structure["vwap"],
        "vwap_position": structure["vwap_position"],
    }

    return {
        "automation": auto,
        "name": name,
        "symbol": symbol,
        "last": round_price(current),
        "last_time": intraday[-1]["time"].strftime("%Y-%m-%d %H:%M UTC"),
        "moving_averages": {key: round_price(value) for key, value in averages.items()},
        "trend": trend,
        "weekly_high": round_price(weekly_range["high"]),
        "weekly_low": round_price(weekly_range["low"]),
        "weekly_trend": weekly_trend,
        "monthly_high": round_price(monthly_range["high"]),
        "monthly_low": round_price(monthly_range["low"]),
        "monthly_trend": monthly_trend,
        "higher_timeframe_trend": htf_result,
        "previous_day_high": round_price(prev_day["high"]),
        "previous_day_low": round_price(prev_day["low"]),
        "opening_range_high": round_price(max(row["high"] for row in intraday[:2])),
        "opening_range_low": round_price(min(row["low"] for row in intraday[:2])),
        "overnight_high": round_price(max(row["high"] for row in intraday[:-26] or intraday)),
        "overnight_low": round_price(min(row["low"] for row in intraday[:-26] or intraday)),
        "atr_15m": round_price(intraday_atr),
        "atr_daily": round_price(daily_atr),
    }


def quote_last(symbol: str):
    result = fetch_chart(symbol, "5d", "1d")
    meta = result.get("meta") or {}
    price = meta.get("regularMarketPrice")
    return round_price(price)


def yield_direction(symbol: str) -> Dict:
    rows = candles(symbol, "5d", "1d")
    latest = rows[-1]["close"]
    previous = rows[-2]["close"] if len(rows) > 1 else latest
    direction = "Up" if latest > previous else "Down" if latest < previous else "Flat"
    return {
        "symbol": symbol,
        "latest": round_price(latest),
        "previous": round_price(previous),
        "direction": direction,
    }


def macro_rate_score(yields: Dict[str, Dict]) -> Dict:
    up_count = sum(1 for item in yields.values() if item["direction"] == "Up")
    down_count = sum(1 for item in yields.values() if item["direction"] == "Down")
    if down_count >= 2:
        result = "Bullish"
        score = 5
    elif up_count >= 2:
        result = "Bearish"
        score = 1
    else:
        result = "Neutral"
        score = 3
    return {"result": result, "score": score}


def safe_build() -> Dict:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        yields = {
            "2y": yield_direction("^IRX"),
            "10y": yield_direction("^TNX"),
            "30y": yield_direction("^TYX"),
        }
        rate_context = macro_rate_score(yields)
        volatility = {
            "vix": quote_last("^VIX"),
            "move": None,
        }
        instruments = {
            "ES": instrument_snapshot("ES", "ES=F", rate_context["result"], volatility["vix"]),
            "ZB": instrument_snapshot("ZB", "ZB=F", rate_context["result"], volatility["vix"]),
        }
        return {
            "generated_at": generated_at,
            "provider": "Yahoo Finance delayed",
            "yields": yields,
            "rate_context": rate_context,
            "instruments": instruments,
            "volatility": volatility,
            "suggested_scores": {
                "macro_rates": rate_context["score"],
                "es_daily_trend": instruments["ES"]["trend"]["score"],
                "zb_daily_trend": instruments["ZB"]["trend"]["score"],
            },
        }
    except Exception as exc:
        return {
            "generated_at": generated_at,
            "error": str(exc),
        }


def main() -> None:
    payload = safe_build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
