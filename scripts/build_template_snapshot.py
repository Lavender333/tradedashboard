"""Build automated market context for the ES/ZB trading template."""

import json
import re
from html import unescape
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


OUTPUT = Path("data/template-snapshot.json")
OUTPUT_JS = Path("data/template-snapshot.js")
ECONOMIC_CALENDAR = Path("data/economic-calendar.json")
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
NASDAQ_ECONOMIC_CALENDAR_URL = "https://api.nasdaq.com/api/calendar/economicevents"
HEADERS = {"User-Agent": "Mozilla/5.0"}
NASDAQ_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/market-activity/economic-calendar",
}

SOURCE_CATALOG = {
    "futures_prices": {
        "label": "Yahoo Finance delayed futures candles",
        "role": "ES/ZB OHLC, overnight levels, moving averages, VWAP proxy",
        "status": "dynamic",
    },
    "rates": {
        "label": "Yahoo Finance Treasury yield indexes",
        "role": "2Y/10Y/30Y yield direction",
        "status": "dynamic",
    },
    "economic_calendar": {
        "label": "Nasdaq Economic Calendar with official-source tagging",
        "role": "scheduled reports, actual/consensus/previous when available",
        "status": "dynamic",
    },
    "official_macro_sources": {
        "label": "BLS / BEA / ISM / Conference Board / Treasury / Federal Reserve",
        "role": "primary source labels for macro events",
        "status": "mapped",
    },
}

OFFICIAL_EVENT_SOURCES = [
    (re.compile(r"\b(jolts|job openings|payroll|nonfarm|nfp|unemployment|cpi|ppi|claims)\b", re.I), "BLS", "https://www.bls.gov/"),
    (re.compile(r"\b(pce|personal income|personal spending|gdp|trade balance)\b", re.I), "BEA", "https://www.bea.gov/"),
    (re.compile(r"\b(ism|manufacturing pmi|services pmi|chicago pmi|business barometer)\b", re.I), "ISM / Chicago Business Barometer", "https://www.ismworld.org/"),
    (re.compile(r"\b(consumer confidence|leading economic index|lei)\b", re.I), "The Conference Board", "https://www.conference-board.org/"),
    (re.compile(r"\b(treasury auction|auction)\b", re.I), "U.S. Treasury", "https://home.treasury.gov/"),
    (re.compile(r"\b(fed|fomc|powell|beige book)\b", re.I), "Federal Reserve", "https://www.federalreserve.gov/"),
]


def get_json(url: str, params=None, headers=None, timeout: int = 30) -> Dict:
    query = f"?{urlencode(params)}" if params else ""
    request = Request(url + query, headers=headers or HEADERS)
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_chart(symbol: str, range_: str, interval: str) -> Dict:
    payload = get_json(
        YAHOO_URL.format(symbol=symbol),
        params={"range": range_, "interval": interval, "includePrePost": "true"},
        headers=HEADERS,
        timeout=30,
    )
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


def trade_decision(rate_result: str, htf_result: str, stale_data: bool = False) -> Dict:
    if stale_data:
        return {"todays_bias": "Neutral", "direction": "No Trade", "trade_plan_score": 0}
    if rate_result == "Bullish" and htf_result == "Bullish":
        return {"todays_bias": "Bull", "direction": "Long Only", "trade_plan_score": 3}
    if rate_result == "Bearish" and htf_result == "Bearish":
        return {"todays_bias": "Bear", "direction": "Short Only", "trade_plan_score": 3}
    return {"todays_bias": "Neutral", "direction": "No Trade", "trade_plan_score": 0}


def trade_levels(direction: str, last: float, previous_high: float, previous_low: float, atr_value) -> Dict:
    atr_points = atr_value or max(abs(previous_high - previous_low), 1)
    if direction == "Long Only":
        entry = max(last, previous_high)
        stop = entry - (atr_points * 0.35)
        target1 = entry + (entry - stop) * 2
        target2 = entry + (entry - stop) * 3
        return {
            "entry_type": "Breakout",
            "entry": round_price(entry),
            "stop": round_price(stop),
            "target1": round_price(target1),
            "target2": round_price(target2),
        }
    if direction == "Short Only":
        entry = min(last, previous_low)
        stop = entry + (atr_points * 0.35)
        target1 = entry - (stop - entry) * 2
        target2 = entry - (stop - entry) * 3
        return {
            "entry_type": "Breakdown",
            "entry": round_price(entry),
            "stop": round_price(stop),
            "target1": round_price(target1),
            "target2": round_price(target2),
        }
    return {
        "entry_type": "No Trade",
        "entry": None,
        "stop": None,
        "target1": None,
        "target2": None,
    }


def ny_time(row: Dict):
    return row["time"].astimezone(ZoneInfo("America/New_York"))


def latest_session_date(rows: List[Dict]):
    return ny_time(rows[-1]).date()


def session_rows(rows: List[Dict], session_date) -> Dict[str, List[Dict]]:
    overnight = []
    europe = []
    regular = []
    for row in rows:
        local = ny_time(row)
        minutes = local.hour * 60 + local.minute
        if local.date() == session_date and minutes < 9 * 60 + 30:
            overnight.append(row)
            if minutes >= 3 * 60:
                europe.append(row)
        elif local.date() == session_date and minutes >= 9 * 60 + 30:
            regular.append(row)
        elif local.date() < session_date and minutes >= 18 * 60:
            overnight.append(row)
    return {"overnight": overnight, "europe": europe, "regular": regular}


def session_market_context(rows: List[Dict]) -> Dict:
    session_date = latest_session_date(rows)
    buckets = session_rows(rows, session_date)
    overnight = buckets["overnight"] or rows[:-26] or rows
    regular = buckets["regular"]
    opening_source = regular if regular else rows[-min(len(rows), 26):]
    opening_range = opening_source[:2] if len(opening_source) >= 2 else opening_source
    vwap_source = regular if regular else rows[-min(len(rows), 26):]
    return {
        "session_date": session_date,
        "overnight": overnight,
        "europe": buckets["europe"],
        "regular": regular,
        "opening_range_high": max(row["high"] for row in opening_range),
        "opening_range_low": min(row["low"] for row in opening_range),
        "overnight_high": max(row["high"] for row in overnight),
        "overnight_low": min(row["low"] for row in overnight),
        "vwap": vwap(vwap_source),
    }


def overnight_context(rows: List[Dict], market_context: Dict) -> Dict:
    session_date = market_context["session_date"]
    overnight = market_context["overnight"]
    europe = market_context["europe"]
    regular = market_context["regular"]
    current = rows[-1]["close"]
    on_high = max(row["high"] for row in overnight)
    on_low = min(row["low"] for row in overnight)
    on_start = overnight[0]["open"]
    on_last = overnight[-1]["close"]
    on_range = max(on_high - on_low, 0.01)
    recovery_ratio = (on_last - on_low) / on_range
    direction = "Recovered / Bullish" if recovery_ratio >= 0.7 else "Weak / Bearish" if recovery_ratio <= 0.3 else "Balanced"

    if europe:
        europe_direction = "Buying into NY open" if europe[-1]["close"] > europe[0]["open"] else "Selling into NY open" if europe[-1]["close"] < europe[0]["open"] else "Balanced"
    else:
        europe_direction = "Not enough Europe-session data"

    if regular:
        opening_slice = regular[:2]
        open_close = opening_slice[-1]["close"]
        open_high = max(row["high"] for row in opening_slice)
        open_low = min(row["low"] for row in opening_slice)
        if open_close > on_high:
            open_confirmation = "Continuation above overnight high"
            bias = "Bullish continuation favored"
        elif open_close < on_low:
            open_confirmation = "Breakdown below overnight low"
            bias = "Bearish continuation favored"
        elif open_high >= on_high and open_close < on_high:
            open_confirmation = "Rejected overnight high"
            bias = "Watch for inventory correction"
        elif open_low <= on_low and open_close > on_low:
            open_confirmation = "Rejected overnight low"
            bias = "Buyers defended overnight low"
        else:
            open_confirmation = "Opening range inside overnight range"
            bias = "Wait for confirmation"
    else:
        open_confirmation = "Waiting for RTH open confirmation"
        bias = "Pre-open context only"

    if current > on_high:
        position = "Above overnight high"
    elif current < on_low:
        position = "Below overnight low"
    else:
        position = "Inside overnight range"

    inventory = "Long overnight inventory" if on_last > on_start else "Short overnight inventory" if on_last < on_start else "Balanced overnight inventory"
    return {
        "date": session_date.isoformat(),
        "overnight_direction": direction,
        "overnight_high": round_price(on_high),
        "overnight_low": round_price(on_low),
        "overnight_last": round_price(on_last),
        "position": position,
        "europe_direction": europe_direction,
        "inventory": inventory,
        "open_confirmation": open_confirmation,
        "bias": bias,
        "summary": (
            f"{direction}; {europe_direction}; {position}; "
            f"{open_confirmation}. {bias}."
        ),
    }


def combined_htf_result(daily_result: str, weekly_result: str, monthly_result: str) -> str:
    votes = [daily_result, weekly_result, monthly_result]
    bullish = votes.count("Bullish")
    bearish = votes.count("Bearish")
    if bullish >= 2:
        return "Bullish"
    if bearish >= 2:
        return "Bearish"
    return "Neutral"


def instrument_snapshot(name: str, symbol: str, rate_result: str, generated_at: datetime, vix=None) -> Dict:
    daily = candles(symbol, "1y", "1d")
    intraday = candles(symbol, "5d", "15m")
    closes = [row["close"] for row in daily]
    current = intraday[-1]["close"]
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
    last_time = intraday[-1]["time"]
    age_minutes = max(0, int((generated_at - last_time).total_seconds() // 60))
    data_status = "fresh" if age_minutes <= 90 else "stale"
    market_context = session_market_context(intraday)
    overnight = overnight_context(intraday, market_context)
    vwap_value = market_context["vwap"]
    structure = structure_score(
        current,
        prev_day["high"],
        prev_day["low"],
        market_context["overnight_high"],
        market_context["overnight_low"],
        vwap_value,
    )
    decision = trade_decision(rate_result, htf_result, data_status == "stale")
    plan_levels = trade_levels(decision["direction"], current, prev_day["high"], prev_day["low"], daily_atr)
    auto = {
        "direction": decision["direction"],
        "delta_result": "Mixed",
        "entry_type": plan_levels["entry_type"],
        "entry": plan_levels["entry"],
        "stop": plan_levels["stop"],
        "target1": plan_levels["target1"],
        "target2": plan_levels["target2"],
        "liquidity_shift": "Live order-flow feed not connected",
        "order_flow_result": "Neutral",
        "order_flow_score": 0,
        "todays_bias": decision["todays_bias"],
        "trade_plan_score": decision["trade_plan_score"],
        "trend_pro_daily_bullish_level": round_price(max(current, prev_day["high"])),
        "trend_pro_daily_bearish_level": round_price(min(current, prev_day["low"])),
        "trend_pro_240_bullish_level": structure["vwap"] or round_price(max(row["high"] for row in intraday[-16:])),
        "trend_pro_240_bearish_level": round_price(min(row["low"] for row in intraday[-16:])),
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
        "last_time": last_time.strftime("%Y-%m-%d %H:%M UTC"),
        "last_candle_age_minutes": age_minutes,
        "data_status": data_status,
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
        "opening_range_high": round_price(market_context["opening_range_high"]),
        "opening_range_low": round_price(market_context["opening_range_low"]),
        "overnight_high": round_price(market_context["overnight_high"]),
        "overnight_low": round_price(market_context["overnight_low"]),
        "overnight_context": overnight,
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


def source_status(events: List[Dict]) -> Dict:
    calendar_primary_sources = sorted({
        event.get("primary_source")
        for event in events
        if event.get("primary_source") and event.get("primary_source") != "Economic calendar provider"
    })
    catalog = {key: value.copy() for key, value in SOURCE_CATALOG.items()}
    catalog["economic_calendar"]["events"] = len(events)
    catalog["economic_calendar"]["primary_sources"] = calendar_primary_sources
    return {
        "active": [
            catalog["futures_prices"]["label"],
            catalog["rates"]["label"],
            catalog["economic_calendar"]["label"],
        ],
        "catalog": catalog,
        "summary": (
            "Dynamic sources: futures/rates from Yahoo delayed feeds; macro calendar from Nasdaq; "
            "events tagged to official primary sources when recognized."
        ),
    }


def clean_calendar_text(value) -> str:
    text = unescape(str(value or "")).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def classify_calendar_event(title: str) -> str:
    text = title.lower()
    if "treasury" in text and "auction" in text:
        return "treasury"
    if "fed" in text or "fomc" in text or "powell" in text or "speaks" in text:
        return "fed"
    if "holiday" in text or "options expiration" in text or "opex" in text:
        return "holiday"
    if re.search(r"\b(cpi|ppi|pce|nfp|nonfarm|payroll|gdp)\b", text) or "retail sales" in text:
        return "high-impact"
    return "other"


def official_source_for_event(title: str) -> Dict[str, str]:
    for pattern, name, url in OFFICIAL_EVENT_SOURCES:
        if pattern.search(title):
            return {"name": name, "url": url}
    return {"name": "Economic calendar provider", "url": ""}


def calendar_time_et(calendar_date: datetime, gmt_time: str) -> str:
    time_text = clean_calendar_text(gmt_time)
    if not re.match(r"^\d{1,2}:\d{2}$", time_text):
        return time_text or "Time TBD"
    hour, minute = [int(part) for part in time_text.split(":", 1)]
    event_utc = calendar_date.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc)
    return event_utc.astimezone(ZoneInfo("America/New_York")).strftime("%-I:%M %p")


def fetch_live_economic_calendar() -> List[Dict]:
    calendar_date = datetime.now(ZoneInfo("America/New_York"))
    payload = get_json(
        NASDAQ_ECONOMIC_CALENDAR_URL,
        params={"date": calendar_date.strftime("%Y-%m-%d")},
        headers=NASDAQ_HEADERS,
        timeout=30,
    )
    rows = ((payload.get("data") or {}).get("rows") or [])
    events = []
    for row in rows:
        country = clean_calendar_text(row.get("country"))
        if country not in {"United States", "USA", "US"}:
            continue
        title = clean_calendar_text(row.get("eventName"))
        if not title:
            continue
        kind = classify_calendar_event(title)
        if kind == "other":
            continue
        actual = clean_calendar_text(row.get("actual"))
        consensus = clean_calendar_text(row.get("consensus"))
        previous = clean_calendar_text(row.get("previous"))
        meta_parts = []
        if consensus:
            meta_parts.append(f"Consensus {consensus}")
        if previous:
            meta_parts.append(f"Previous {previous}")
        if actual:
            meta_parts.append(f"Actual {actual}")
        official_source = official_source_for_event(title)
        events.append({
            "date": calendar_date.strftime("%Y-%m-%d"),
            "time_et": calendar_time_et(calendar_date, row.get("gmt")),
            "title": title,
            "country": "United States",
            "category": kind,
            "impact": "high" if kind == "high-impact" else "medium",
            "source": "Nasdaq Economic Calendar",
            "primary_source": official_source["name"],
            "source_url": official_source["url"],
            "note": " · ".join(meta_parts),
        })
    return events


def load_economic_calendar() -> List[Dict]:
    try:
        live_events = fetch_live_economic_calendar()
        if live_events:
            return live_events
    except Exception:
        pass
    if not ECONOMIC_CALENDAR.exists():
        return []
    payload = json.loads(ECONOMIC_CALENDAR.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        events = payload
    else:
        events = payload.get("events", [])
    for event in events:
        if not event.get("primary_source"):
            official_source = official_source_for_event(event.get("title") or event.get("name") or "")
            event["primary_source"] = official_source["name"]
            event["source_url"] = official_source["url"]
    return events


def safe_build() -> Dict:
    generated_at_dt = datetime.now(timezone.utc)
    generated_at = generated_at_dt.strftime("%Y-%m-%d %H:%M UTC")
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
        economic_calendar = load_economic_calendar()
        instruments = {
            "ES": instrument_snapshot("ES", "ES=F", rate_context["result"], generated_at_dt, volatility["vix"]),
            "ZB": instrument_snapshot("ZB", "ZB=F", rate_context["result"], generated_at_dt, volatility["vix"]),
        }
        return {
            "generated_at": generated_at,
            "provider": "Dynamic delayed market data",
            "data_sources": source_status(economic_calendar),
            "yields": yields,
            "rate_context": rate_context,
            "economic_calendar": economic_calendar,
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
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    OUTPUT.write_text(serialized + "\n", encoding="utf-8")
    OUTPUT_JS.write_text("window.templateSnapshotFallback = " + serialized + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
