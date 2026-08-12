"""Build automated market context for the ES/ZB trading template."""

import json
import os
import re
import calendar
from html import unescape
from datetime import datetime, timedelta, timezone
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
        "label": "Webull OpenAPI CME futures data",
        "role": "Single-source ES/ZB OHLCV for day-trading calculations",
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

DATABENTO_DATASET = os.environ.get("DATABENTO_DATASET", "GLBX.MDP3")
FUTURES_PROVIDER = os.environ.get("TEMPLATE_DATA_PROVIDER", "yahoo").lower()
FUTURES_SYMBOLS = {
    "ES": os.environ.get("ES_SYMBOL", "ES.c.0"),
    "ZB": os.environ.get("ZB_SYMBOL", "ZB.c.0"),
}
YAHOO_FALLBACK_SYMBOLS = {"ES": "ES=F", "ZB": "ZB=F"}
WEBULL_SYMBOLS = {
    "ES": os.environ.get("WEBULL_ES_SYMBOL", ""),
    "ZB": os.environ.get("WEBULL_ZB_SYMBOL", ""),
}
ACTIVE_FUTURES_SOURCE = ""
WEBULL_DATA_CLIENT = None
CONTRACT_SELECTION = {}

ES_RESEARCH_ENGINE = "ES OVERNIGHT-ONLY RESEARCH V1"
ES_APPROVED_SETUPS = frozenset({
    "Overnight High Breakout Retest",
    "Overnight Low Breakdown Retest",
})

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


def databento_candles(symbol: str, start: datetime, schema: str = "ohlcv-1m") -> List[Dict]:
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        raise RuntimeError("DATABENTO_API_KEY is not configured")
    try:
        import databento as db
    except ImportError as exc:
        raise RuntimeError("Install the databento package") from exc

    data = db.Historical(api_key).timeseries.get_range(
        dataset=DATABENTO_DATASET,
        symbols=[symbol],
        schema=schema,
        start=start.isoformat(),
        end=datetime.now(timezone.utc).isoformat(),
    ).to_df().reset_index()
    time_column = "ts_event" if "ts_event" in data.columns else "index"
    rows = []
    for record in data.to_dict("records"):
        values = {key: record.get(key) for key in ("open", "high", "low", "close")}
        if any(value is None for value in values.values()):
            continue
        scale = 1_000_000_000 if max(abs(float(value)) for value in values.values()) > 1_000_000 else 1
        rows.append({
            "time": record[time_column].to_pydatetime().astimezone(timezone.utc),
            "open": float(values["open"]) / scale,
            "high": float(values["high"]) / scale,
            "low": float(values["low"]) / scale,
            "close": float(values["close"]) / scale,
            "volume": float(record.get("volume") or 0),
        })
    if not rows:
        raise RuntimeError(f"{symbol}: Databento returned no usable candles")
    return rows


def webull_client():
    global WEBULL_DATA_CLIENT
    if WEBULL_DATA_CLIENT is not None:
        return WEBULL_DATA_CLIENT
    app_key = os.environ.get("WEBULL_APP_KEY")
    app_secret = os.environ.get("WEBULL_APP_SECRET")
    if not app_key or not app_secret:
        raise RuntimeError("WEBULL_APP_KEY and WEBULL_APP_SECRET are required")
    try:
        from webull.core.client import ApiClient
        from webull.data.data_client import DataClient
    except ImportError as exc:
        raise RuntimeError("Install webull-openapi-python-sdk") from exc
    region = os.environ.get("WEBULL_REGION", "us")
    client = ApiClient(app_key, app_secret, region)
    client.add_endpoint(region, os.environ.get("WEBULL_API_ENDPOINT", "https://api.webull.com"))
    token_dir = os.environ.get("WEBULL_OPENAPI_TOKEN_DIR")
    if token_dir:
        client.set_token_dir(token_dir)
    WEBULL_DATA_CLIENT = DataClient(client)
    return WEBULL_DATA_CLIENT


def parse_webull_time(value: str) -> datetime:
    normalized = str(value).strip().replace("Z", "+00:00")
    if re.search(r"[+-]\d{4}$", normalized):
        normalized = normalized[:-5] + normalized[-5:-2] + ":" + normalized[-2:]
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def webull_candles(symbol: str, timespan: str, count: int) -> List[Dict]:
    if not symbol:
        raise RuntimeError("Set the exact WEBULL_ES_SYMBOL and WEBULL_ZB_SYMBOL contract codes")
    try:
        from webull.data.common.category import Category
    except ImportError as exc:
        raise RuntimeError("Install webull-openapi-python-sdk") from exc
    response = webull_client().futures_market_data.get_futures_history_bars(
        symbol,
        Category.US_FUTURES.name,
        timespan,
        count=str(count),
        real_time_required="Y",
    )
    if response.status_code != 200:
        raise RuntimeError(f"Webull futures bars failed ({response.status_code}): {response.text[:300]}")
    payload = response.json()
    instruments = payload.get("result") or []
    bar_rows = instruments[0].get("result") if instruments else []
    rows = [{
        "time": parse_webull_time(bar["time"]),
        "open": float(bar["open"]),
        "high": float(bar["high"]),
        "low": float(bar["low"]),
        "close": float(bar["close"]),
        "volume": float(bar.get("volume") or 0),
    } for bar in bar_rows if all(bar.get(key) is not None for key in ("time", "open", "high", "low", "close"))]
    if not rows:
        raise RuntimeError(f"{symbol}: Webull returned no usable futures bars")
    return sorted(rows, key=lambda row: row["time"])


def webull_result_items(payload) -> List[Dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    result = payload.get("result", payload.get("data", []))
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        nested = result.get("result", result.get("data", []))
        return [item for item in nested if isinstance(item, dict)] if isinstance(nested, list) else [result]
    return []


def contract_expiration(item: Dict):
    raw = next((item.get(key) for key in ("expiration_date", "expire_date", "last_trade_date", "last_trading_date") if item.get(key)), None)
    if not raw:
        symbol = str(item.get("symbol") or item.get("ticker") or "")
        match = re.search(r"([FGHJKMNQUVXZ])(\d)$", symbol)
        if not match:
            return None
        month = {code: index for index, code in enumerate("FGHJKMNQUVXZ", start=1)}[match.group(1)]
        now_year = datetime.now(ZoneInfo("America/New_York")).year
        decade = (now_year // 10) * 10
        year = decade + int(match.group(2))
        if year < now_year - 2:
            year += 10
        return datetime(year, month, calendar.monthrange(year, month)[1]).date()
    try:
        return datetime.fromisoformat(str(raw)[:10]).date()
    except ValueError:
        return None


def select_liquid_contract(candidates: List[Dict], snapshots: List[Dict], today) -> Dict:
    eligible = []
    for item in candidates:
        symbol = item.get("symbol") or item.get("ticker")
        expiration = contract_expiration(item)
        if symbol and expiration and expiration >= today:
            eligible.append({"symbol": symbol, "expiration": expiration})
    eligible.sort(key=lambda item: item["expiration"])
    nearest = eligible[:2]
    snapshot_map = {item.get("symbol"): item for item in snapshots if item.get("symbol")}
    for item in nearest:
        snapshot = snapshot_map.get(item["symbol"], {})
        item["volume"] = float(snapshot.get("volume") or 0)
        item["open_interest"] = float(snapshot.get("open_interest") or 0)
    if not nearest:
        raise RuntimeError("Webull returned no unexpired futures contracts")
    return max(nearest, key=lambda item: (item["volume"], item["open_interest"], -item["expiration"].toordinal()))


def webull_active_contract(name: str) -> str:
    global CONTRACT_SELECTION
    fallback_symbol = WEBULL_SYMBOLS[name]
    try:
        from webull.data.common.category import Category
    except ImportError as exc:
        raise RuntimeError("Install webull-openapi-python-sdk") from exc
    response = webull_client().instrument.get_futures_instrument(
        category=Category.US_FUTURES.name,
        code=name,
        status="LISTING",
    )
    if response.status_code != 200:
        if fallback_symbol:
            CONTRACT_SELECTION[name] = {"mode": "configured fallback", "symbol": fallback_symbol, "reason": f"contract directory HTTP {response.status_code}"}
            return fallback_symbol
        raise RuntimeError(f"Webull contract directory failed ({response.status_code})")
    candidates = webull_result_items(response.json())
    symbols = [item.get("symbol") or item.get("ticker") for item in candidates]
    symbols = [symbol for symbol in symbols if symbol and symbol.startswith(name)][:4]
    snapshot_rows = []
    if symbols:
        snapshot = webull_client().futures_market_data.get_futures_snapshot(
            ",".join(symbols), Category.US_FUTURES.name
        )
        if snapshot.status_code == 200:
            snapshot_rows = webull_result_items(snapshot.json())
    try:
        selected = select_liquid_contract(candidates, snapshot_rows, datetime.now(ZoneInfo("America/New_York")).date())
    except RuntimeError:
        if not fallback_symbol:
            raise
        CONTRACT_SELECTION[name] = {"mode": "configured fallback", "symbol": fallback_symbol, "reason": "no usable Webull contract metadata"}
        return fallback_symbol
    CONTRACT_SELECTION[name] = {
        "mode": "automatic liquidity rollover",
        "symbol": selected["symbol"],
        "expiration": selected["expiration"].isoformat(),
        "volume": selected["volume"],
        "open_interest": selected["open_interest"],
        "reason": "highest volume/open interest among the nearest two unexpired contracts",
    }
    return selected["symbol"]


def aggregate_candles(rows: List[Dict], minutes: int = 20) -> List[Dict]:
    buckets = {}
    for row in rows:
        stamp = row["time"].astimezone(timezone.utc)
        bucket_minute = (stamp.minute // minutes) * minutes
        key = stamp.replace(minute=bucket_minute, second=0, microsecond=0)
        bucket = buckets.setdefault(key, {"time": key, "open": row["open"], "high": row["high"], "low": row["low"], "close": row["close"], "volume": 0})
        bucket["high"] = max(bucket["high"], row["high"])
        bucket["low"] = min(bucket["low"], row["low"])
        bucket["close"] = row["close"]
        bucket["volume"] += row.get("volume") or 0
    return [buckets[key] for key in sorted(buckets)]


def futures_history(name: str) -> tuple[List[Dict], List[Dict], List[Dict], str]:
    global ACTIVE_FUTURES_SOURCE
    if FUTURES_PROVIDER == "webull":
        try:
            symbol = webull_active_contract(name)
            five_minute = webull_candles(symbol, "M5", 1200)
            daily = webull_candles(symbol, "D", 370)
            ACTIVE_FUTURES_SOURCE = "Webull OpenAPI real-time CME futures"
            return daily, aggregate_candles(five_minute, 20), five_minute, symbol
        except Exception:
            if os.environ.get("ALLOW_YAHOO_FALLBACK", "true").lower() != "true":
                raise
    if FUTURES_PROVIDER == "databento":
        try:
            symbol = FUTURES_SYMBOLS[name]
            minute_rows = databento_candles(symbol, datetime.now(timezone.utc) - timedelta(days=10))
            daily = databento_candles(symbol, datetime.now(timezone.utc) - timedelta(days=370), "ohlcv-1d")
            ACTIVE_FUTURES_SOURCE = "Databento CME futures data"
            return daily, aggregate_candles(minute_rows, 20), aggregate_candles(minute_rows, 5), symbol
        except Exception:
            if os.environ.get("ALLOW_YAHOO_FALLBACK", "true").lower() != "true":
                raise
    symbol = YAHOO_FALLBACK_SYMBOLS[name]
    ACTIVE_FUTURES_SOURCE = "Yahoo Finance delayed backup"
    CONTRACT_SELECTION[name] = {"mode": "Yahoo continuous fallback", "symbol": symbol, "reason": "Webull unavailable or not configured"}
    five_minute = candles(symbol, "5d", "5m")
    return candles(symbol, "1y", "1d"), aggregate_candles(five_minute, 20), five_minute, symbol


def sma(values: List[float], period: int):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema(values: List[float], period: int):
    """Return a standard exponentially weighted moving average."""
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    result = sum(values[:period]) / period
    for value in values[period:]:
        result = (value - result) * multiplier + result
    return result


def atr(rows: List[Dict], period: int = 14):
    if len(rows) < period + 1:
        return None
    true_ranges = []
    for index in range(1, len(rows)):
        high = rows[index]["high"]
        low = rows[index]["low"]
        prev_close = rows[index - 1]["close"]
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    value = sum(true_ranges[:period]) / period
    for true_range in true_ranges[period:]:
        value = ((period - 1) * value + true_range) / period
    return value


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


def two_session_anchored_vwap(rows: List[Dict]):
    """Return VWAP spanning the latest two CME trading sessions.

    CME equity-index sessions begin at 18:00 ET. Bars after 18:00 belong to
    the following trade date, keeping the anchor aligned across midnight.
    """
    if not rows:
        return None
    labeled = []
    for row in rows:
        local = ny_time(row)
        trade_date = local.date() + timedelta(days=1) if local.hour >= 18 else local.date()
        labeled.append((trade_date, row))
    sessions = sorted({trade_date for trade_date, _ in labeled})
    selected = set(sessions[-2:])
    return vwap([row for trade_date, row in labeled if trade_date in selected])


def bollinger(rows: List[Dict], period: int = 20, deviations: float = 2.0) -> Dict:
    closes = [row["close"] for row in rows]
    if len(closes) < period:
        return {"middle": None, "upper": None, "lower": None}
    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((value - middle) ** 2 for value in window) / period
    width = deviations * variance ** 0.5
    return {"middle": round_price(middle), "upper": round_price(middle + width), "lower": round_price(middle - width)}


def round_price(value):
    if value is None:
        return None
    # Five decimals preserve Treasury-futures 1/32 ticks while remaining exact for ES quarter points.
    return round(float(value), 5)


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
    if on_low is not None and on_high is not None and on_low <= last <= on_high:
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


def trade_decision(rate_result: str, htf_result: str, data_quality_pass: bool = False) -> Dict:
    if not data_quality_pass:
        bias = "Bull" if htf_result == "Bullish" else "Bear" if htf_result == "Bearish" else "Neutral"
        return {"todays_bias": bias, "direction": "No Trade", "trade_plan_score": 0}
    if rate_result == "Bullish" and htf_result == "Bullish":
        return {"todays_bias": "Bull", "direction": "Long Only", "trade_plan_score": 3}
    if rate_result == "Bearish" and htf_result == "Bearish":
        return {"todays_bias": "Bear", "direction": "Short Only", "trade_plan_score": 3}
    return {"todays_bias": "Neutral", "direction": "No Trade", "trade_plan_score": 0}


def ranked_watch_levels(name: str, htf_result: str, market_context: Dict, previous_high: float, previous_low: float) -> List[Dict]:
    if name == "ES" and htf_result == "Bullish":
        candidates = [
            ("Overnight High Breakout Retest", market_context["overnight_high"], "5m acceptance above, later retest, then reclaim"),
        ]
    elif name == "ES" and htf_result == "Bearish":
        candidates = [
            ("Overnight Low Breakdown Retest", market_context["overnight_low"], "5m acceptance below, later retest, then rejection"),
        ]
    elif name == "ES":
        candidates = [
            ("Overnight High", market_context["overnight_high"], "wait for bullish HTF direction and confirmed break/retest"),
            ("Overnight Low", market_context["overnight_low"], "wait for bearish HTF direction and confirmed break/retest"),
        ]
    elif htf_result == "Bullish":
        candidates = [
            ("Opening Range Breakout Retest", market_context["opening_range_high"], "5m close above, retest, then reclaim"),
            ("Overnight High Breakout Retest", market_context["overnight_high"], "5m acceptance above, retest, then reclaim"),
            ("Previous Day Low Rejection", previous_low, "sweep and completed 5m reclaim"),
        ]
    elif htf_result == "Bearish":
        candidates = [
            ("Opening Range Breakdown Retest", market_context["opening_range_low"], "5m close below, retest, then rejection"),
            ("Overnight Low Breakdown Retest", market_context["overnight_low"], "5m acceptance below, retest, then rejection"),
            ("Previous Day High Rejection", previous_high, "sweep and completed 5m rejection"),
        ]
    else:
        candidates = [
            ("Opening Range High", market_context["opening_range_high"], "wait for confirmed break/retest"),
            ("Opening Range Low", market_context["opening_range_low"], "wait for confirmed break/retest"),
        ]
    usable = [(setup, level, trigger) for setup, level, trigger in candidates if level is not None]
    return [{"rank": index + 1, "setup": setup, "watch_level": round_price(level), "trigger": trigger, "status": "WAITING FOR CONFIRMATION"} for index, (setup, level, trigger) in enumerate(usable)]


def confirmed_trade_setup(name: str, htf_result: str, watch_levels: List[Dict], rows: List[Dict], atr_value, bb_position, generated_at: datetime, data_quality_pass: bool) -> Dict:
    pending = {
        "confirmed": False,
        "engine_version": ES_RESEARCH_ENGINE if name == "ES" else "ZB V2",
        "direction": "No Trade",
        "status": "WAITING FOR BREAKOUT / RETEST / 5m CONFIRMATION",
        "entry": None,
        "stop": None,
        "target1": None,
        "target2": None,
        "risk_points": None,
        "rr1": None,
        "rr2": None,
        "exit_plan": "No position. Wait for confirmation.",
    }
    if not data_quality_pass:
        pending["status"] = "NO TRADE — LIVE DATA QUALITY GATE FAILED"
        return pending
    if htf_result not in {"Bullish", "Bearish"} or not watch_levels or not atr_value:
        pending["status"] = "NO TRADE — DIRECTION OR INDICATORS NOT READY"
        return pending

    if name == "ES":
        watch_levels = [watch for watch in watch_levels if watch.get("setup") in ES_APPROVED_SETUPS]
        if not watch_levels:
            pending["status"] = "ES OVERNIGHT-ONLY SKIP — SETUP NOT APPROVED"
            return pending

    completed = [row for row in rows if row["time"] + timedelta(minutes=5) <= generated_at][-24:]
    if len(completed) < 3:
        return pending
    long_side = htf_result == "Bullish"
    tick = 0.25 if name == "ES" else 1 / 32
    acceptance = 2 * tick
    retest_above = 4 * tick
    retest_below = 6 * tick
    confirmation_bar = completed[-1]
    confirmation_index = len(completed) - 1

    if name == "ES":
        confirmation_et = confirmation_bar["time"].astimezone(ZoneInfo("America/New_York"))
        confirmation_minutes = confirmation_et.hour * 60 + confirmation_et.minute
        if confirmation_minutes < 10 * 60 or confirmation_minutes >= 14 * 60:
            pending["status"] = "ES PRO SKIP — OUTSIDE 10:00 AM–2:00 PM ET"
            return pending
        confirmation_body_atr = abs(confirmation_bar["close"] - confirmation_bar["open"]) / float(atr_value)
        if confirmation_body_atr > 0.35:
            pending["status"] = "ES PRO SKIP — CONFIRMATION CANDLE CHASE (>0.35 ATR)"
            return pending
        if long_side and (bb_position is None or bb_position < 0.60 or bb_position > 0.75):
            pending["status"] = "ES PRO SKIP — LONG BB LOCATION MUST BE 0.60–0.75"
            return pending

    for watch in watch_levels:
        level = float(watch["watch_level"])
        if long_side:
            candle_confirmed = confirmation_bar["close"] > level and confirmation_bar["close"] > confirmation_bar["open"]
        else:
            candle_confirmed = confirmation_bar["close"] < level and confirmation_bar["close"] < confirmation_bar["open"]
        if not candle_confirmed:
            continue

        # The confirmation must be the newest completed five-minute candle.
        # Search backward for the most recent accepted break, then prove a later retest occurred.
        for break_index in range(confirmation_index - 1, -1, -1):
            breakout_bar = completed[break_index]
            broke = breakout_bar["close"] >= level + acceptance if long_side else breakout_bar["close"] <= level - acceptance
            if not broke:
                continue

            sequence = completed[break_index + 1 : confirmation_index + 1]
            if long_side:
                failed = any(item["low"] < level - retest_below for item in sequence)
                retest_indices = [
                    break_index + 1 + index for index, item in enumerate(sequence)
                    if level - retest_below <= item["low"] <= level + retest_above
                ]
            else:
                failed = any(item["high"] > level + retest_below for item in sequence)
                retest_indices = [
                    break_index + 1 + index for index, item in enumerate(sequence)
                    if level - retest_above <= item["high"] <= level + retest_below
                ]
            if failed or not retest_indices:
                continue

            retest_index = retest_indices[-1]
            entry = float(confirmation_bar["close"])
            structure_rows = completed[max(retest_index - 1, break_index):confirmation_index + 1]
            stop = min(item["low"] for item in structure_rows) - tick if long_side else max(item["high"] for item in structure_rows) + tick
            risk = entry - stop if long_side else stop - entry
            atr_ratio = risk / float(atr_value)
            chase_failed = (long_side and bb_position is not None and bb_position > 0.85) or (not long_side and bb_position is not None and bb_position < 0.15)
            minimum_atr_risk = 0.45 if name == "ES" else 0.25
            if risk <= 0 or atr_ratio < minimum_atr_risk or atr_ratio > 1.0 or chase_failed:
                if name == "ES" and risk > 0 and atr_ratio < minimum_atr_risk:
                    pending["status"] = "ES PRO SKIP — STRUCTURAL STOP TOO TIGHT (<0.45 ATR)"
                continue
            if name == "ES":
                # $5 round turn plus one ES tick each way is $30/contract.
                # Six points keeps that modeled cost at or below 0.10R.
                transaction_cost_r = 0.60 / risk
                if risk < 6.0 or transaction_cost_r > 0.10:
                    pending["status"] = "ES PRO SKIP — COST TOO LARGE RELATIVE TO STOP"
                    continue
            target1 = entry + risk if long_side else entry - risk
            target2 = entry + 2 * risk if long_side else entry - 2 * risk
            direction = "Long Only" if long_side else "Short Only"
            return {
                "confirmed": True,
                "direction": direction,
                "status": f"CONFIRMED {direction.upper()} — {watch['setup']}",
                "setup": watch["setup"],
                "watch_level": round_price(level),
                "entry": round_price(entry),
                "stop": round_price(stop),
                "target1": round_price(target1),
                "target2": round_price(target2),
                "risk_points": round_price(risk),
                "atr_risk_ratio": round(atr_ratio, 3),
                "transaction_cost_r": round(0.60 / risk, 3) if name == "ES" else None,
                "engine_version": ES_RESEARCH_ENGINE if name == "ES" else "ZB V2",
                "rr1": 1.0,
                "rr2": 2.0,
                "confirmation_time": confirmation_bar["time"].astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %-I:%M %p ET"),
                "exit_plan": f"Exit if stop {round_price(stop)} trades. Scale at {round_price(target1)} (1R); exit remainder at {round_price(target2)} (2R) or move stop per plan.",
            }
    return pending


def ny_time(row: Dict):
    return row["time"].astimezone(ZoneInfo("America/New_York"))


def trade_date_for_row(row: Dict):
    local = ny_time(row)
    return local.date() + timedelta(days=1) if local.hour >= 18 else local.date()


def trade_date_for_datetime(value: datetime):
    local = value.astimezone(ZoneInfo("America/New_York"))
    return local.date() + timedelta(days=1) if local.hour >= 18 else local.date()


def latest_session_date(rows: List[Dict]):
    return trade_date_for_row(rows[-1])


def session_rows(rows: List[Dict], session_date) -> Dict[str, List[Dict]]:
    overnight = []
    europe = []
    regular = []
    for row in rows:
        local = ny_time(row)
        minutes = local.hour * 60 + local.minute
        if trade_date_for_row(row) != session_date:
            continue
        if minutes >= 18 * 60 or minutes < 9 * 60 + 30:
            overnight.append(row)
            if 3 * 60 <= minutes < 9 * 60 + 30:
                europe.append(row)
        elif 9 * 60 + 30 <= minutes < 16 * 60:
            regular.append(row)
    return {"overnight": overnight, "europe": europe, "regular": regular}


def session_market_context(rows: List[Dict]) -> Dict:
    session_date = latest_session_date(rows)
    buckets = session_rows(rows, session_date)
    overnight = buckets["overnight"]
    regular = buckets["regular"]
    opening_range = regular[:6] if len(regular) >= 6 else []
    return {
        "session_date": session_date,
        "overnight": overnight,
        "europe": buckets["europe"],
        "regular": regular,
        "opening_range_high": max((row["high"] for row in opening_range), default=None),
        "opening_range_low": min((row["low"] for row in opening_range), default=None),
        "overnight_high": max((row["high"] for row in overnight), default=None),
        "overnight_low": min((row["low"] for row in overnight), default=None),
        "vwap": vwap(regular),
    }


def overnight_context(rows: List[Dict], market_context: Dict) -> Dict:
    session_date = market_context["session_date"]
    overnight = market_context["overnight"]
    europe = market_context["europe"]
    regular = market_context["regular"]
    if not overnight:
        return {
            "date": session_date.isoformat(),
            "overnight_direction": "Not available",
            "overnight_high": None,
            "overnight_low": None,
            "overnight_last": None,
            "position": "Not available",
            "europe_direction": "Not available",
            "inventory": "Not available",
            "open_confirmation": "Waiting for valid session data",
            "bias": "No Trade",
            "summary": "Overnight session data is unavailable.",
        }
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


def selector_rating(score: int, ready: bool, data_fresh: bool = True) -> str:
    if not data_fresh:
        return "STALE"
    if not ready:
        return "NOT READY"
    if score >= 5:
        return "A+"
    if score == 4:
        return "WAIT"
    return "SKIP"


def market_selector(
    name: str,
    generated_at: datetime,
    current: float,
    htf_result: str,
    ema20_value,
    ema50_value,
    vwap_value,
    key_levels: Dict[str, float],
    atr_value,
    five_minute_rows: List[Dict],
    data_fresh: bool,
) -> Dict:
    """Score the six objective checks used to choose between ES and ZB."""
    decision_minutes = 8 * 60 + 30 if name == "ZB" else 10 * 60
    decision_time = "08:30 ET" if name == "ZB" else "10:00 ET"
    now_et = generated_at.astimezone(ZoneInfo("America/New_York"))
    ready = now_et.hour * 60 + now_et.minute >= decision_minutes
    direction = "LONG" if htf_result == "Bullish" else "SHORT" if htf_result == "Bearish" else "NONE"
    tolerance = max(float(atr_value or 0) * 0.25, 0.01)
    usable_levels = {key: float(value) for key, value in key_levels.items() if value is not None}
    nearest_name, nearest_level = (None, None)
    if usable_levels:
        nearest_name, nearest_level = min(usable_levels.items(), key=lambda item: abs(current - item[1]))

    htf_clear = direction != "NONE"
    ema_aligned = bool(
        ema20_value is not None
        and ema50_value is not None
        and ((direction == "LONG" and ema20_value > ema50_value) or (direction == "SHORT" and ema20_value < ema50_value))
    )
    vwap_aligned = bool(
        vwap_value is not None
        and ((direction == "LONG" and current > vwap_value) or (direction == "SHORT" and current < vwap_value))
    )
    at_level = nearest_level is not None and abs(current - nearest_level) <= tolerance

    targets = []
    if direction == "LONG":
        targets = [(key, value) for key, value in usable_levels.items() if value > current + tolerance]
    elif direction == "SHORT":
        targets = [(key, value) for key, value in usable_levels.items() if value < current - tolerance]
    if targets:
        target_name, target_level = min(targets, key=lambda item: abs(current - item[1]))
        room = abs(target_level - current)
    else:
        target_name, target_level, room = None, None, 0
    enough_room = bool(atr_value and room >= float(atr_value) * 0.5)

    confirmation_level = nearest_level if at_level else vwap_value
    completed_rows = [row for row in five_minute_rows if row["time"] + timedelta(minutes=5) <= generated_at]
    completed_closes = [row["close"] for row in completed_rows[-2:]]
    if direction == "LONG" and confirmation_level is not None:
        confirmed = bool(completed_closes and all(close > confirmation_level for close in completed_closes))
    elif direction == "SHORT" and confirmation_level is not None:
        confirmed = bool(completed_closes and all(close < confirmation_level for close in completed_closes))
    else:
        confirmed = False

    checks = {
        "htf_direction": {
            "pass": htf_clear,
            "evidence": f"HTF {htf_result}; directional plan {direction}",
        },
        "ema_alignment": {
            "pass": ema_aligned,
            "evidence": f"EMA20 {round_price(ema20_value)} vs EMA50 {round_price(ema50_value)}",
        },
        "vwap_alignment": {
            "pass": vwap_aligned,
            "evidence": f"Price {round_price(current)} vs VWAP {round_price(vwap_value)}",
        },
        "meaningful_level": {
            "pass": at_level,
            "evidence": f"Nearest: {nearest_name or '-'} {round_price(nearest_level)}; distance {round_price(abs(current - nearest_level)) if nearest_level is not None else '-'}",
        },
        "room_to_target": {
            "pass": enough_room,
            "evidence": f"Next: {target_name or '-'} {round_price(target_level)}; room {round_price(room)}",
        },
        "confirmed_reaction": {
            "pass": confirmed,
            "evidence": f"{len(completed_closes)} five-minute close(s) vs {round_price(confirmation_level)}",
        },
    }
    score = sum(1 for check in checks.values() if check["pass"])
    return {
        "name": name,
        "decision_time": decision_time,
        "ready": ready,
        "data_fresh": data_fresh,
        "direction": direction,
        "checks": checks,
        "score": score,
        "rating": selector_rating(score, ready, data_fresh),
        "target_room": round_price(room),
        "target_room_atr": round(room / float(atr_value), 3) if atr_value else 0,
        "vwap_distance": round_price(abs(current - vwap_value)) if vwap_value is not None else None,
        "vwap_distance_atr": round(abs(current - vwap_value) / float(atr_value), 3) if vwap_value is not None and atr_value else 0,
        "confirmed": confirmed,
        "fib_50": round_price(key_levels["fib_50"]),
        "pivot": round_price(key_levels["pivot"]),
    }


def choose_market(instruments: Dict[str, Dict]) -> Dict:
    """Choose one market using score, target room, VWAP separation, and confirmation."""
    candidates = [
        instrument["selector"]
        for instrument in instruments.values()
        if instrument["selector"]["ready"] and instrument["selector"]["data_fresh"]
    ]
    if not candidates:
        return {"market": None, "decision": "NOT READY", "reason": "Wait for decision time and fresh market data."}

    ranked = sorted(
        candidates,
        key=lambda item: (
            item["score"],
            item["target_room_atr"] or 0,
            item["vwap_distance_atr"] or 0,
            1 if item["confirmed"] else 0,
        ),
        reverse=True,
    )
    winner = ranked[0]
    if winner["score"] < 4:
        return {"market": None, "decision": "SKIP BOTH", "reason": "Neither market reached the four-point watch threshold."}
    if len(ranked) > 1:
        first_key = (winner["score"], winner["target_room_atr"], winner["vwap_distance_atr"], winner["confirmed"])
        second = ranked[1]
        second_key = (second["score"], second["target_room_atr"], second["vwap_distance_atr"], second["confirmed"])
        if first_key == second_key:
            return {"market": None, "decision": "WAIT", "reason": "The markets are tied with no clear quality advantage."}
    action = "TRADE" if winner["score"] >= 5 else "WATCH"
    return {
        "market": winner["name"],
        "decision": f"{action} {winner['name']}",
        "reason": f"{winner['name']} leads with {winner['score']}/6 checks and the cleaner tie-break profile.",
    }


def professional_trend_scores(price: float, averages: Dict[str, float], weekly_range: Dict, monthly_range: Dict, direction: str) -> Dict:
    """Symmetric long/short scores for the Professional ES 35-point trend section."""
    long_side = direction == "Long Only"
    short_side = direction == "Short Only"
    aligned = sum(
        1 for value in averages.values()
        if value is not None and ((long_side and price > value) or (short_side and price < value))
    ) if long_side or short_side else 0
    daily_points = {5: 15, 4: 12, 3: 9, 2: 6}.get(aligned, 0)

    def range_points(bounds: Dict) -> int:
        high, low = float(bounds["high"]), float(bounds["low"])
        midpoint = (high + low) / 2
        if long_side:
            return 10 if price > high else 6 if price >= midpoint else 0
        if short_side:
            return 10 if price < low else 6 if price <= midpoint else 0
        return 0

    return {
        "daily": daily_points,
        "weekly": range_points(weekly_range),
        "monthly": range_points(monthly_range),
        "aligned_daily_averages": aligned,
    }


def instrument_snapshot(name: str, rate_result: str, generated_at: datetime, vix=None) -> Dict:
    daily, intraday, five_minute, symbol = futures_history(name)
    closes = [row["close"] for row in daily]
    current = five_minute[-1]["close"]
    averages = {f"ma{period}": sma(closes, period) for period in [20, 50, 72, 100, 200]}
    exponential_averages = {f"ema{period}": ema(closes, period) for period in [20, 50]}
    trend = trend_score(current, averages)
    prev_day = daily[-2] if len(daily) > 1 else daily[-1]
    weekly_range = period_range(daily, lambda value: value.isocalendar()[:2])
    monthly_range = period_range(daily, lambda value: (value.year, value.month))
    weekly_trend = range_break_result(current, weekly_range["high"], weekly_range["low"])
    monthly_trend = range_break_result(current, monthly_range["high"], monthly_range["low"])
    htf_result = combined_htf_result(trend["result"], weekly_trend["result"], monthly_trend["result"])
    intraday_atr = atr(intraday)
    daily_atr = atr(daily)
    last_time = five_minute[-1]["time"]
    age_minutes = max(0, int((generated_at - last_time).total_seconds() // 60))
    source_live = ACTIVE_FUTURES_SOURCE.startswith(("Webull", "Databento"))
    data_status = "live" if source_live and age_minutes <= 7 else "delayed" if age_minutes <= 30 else "stale"
    market_context = session_market_context(five_minute)
    overnight = overnight_context(five_minute, market_context)
    vwap_value = market_context["vwap"]
    anchored_vwap = two_session_anchored_vwap(five_minute) if name == "ES" else None
    bands = bollinger(intraday)
    band_width = (bands["upper"] - bands["lower"]) if bands["upper"] is not None else None
    bb_position = ((current - bands["lower"]) / band_width) if band_width else None
    chase_status = "N/A"
    if bb_position is not None:
        chase_status = "LONG CHASE — wait for pullback/retest" if bb_position > 0.85 else "SHORT CHASE — wait for pullback/retest" if bb_position < 0.15 else "PASS — normal band position"
    structure = structure_score(
        current,
        prev_day["high"],
        prev_day["low"],
        market_context["overnight_high"],
        market_context["overnight_low"],
        vwap_value,
    )
    key_levels = {
        "overnight_high": market_context["overnight_high"],
        "overnight_low": market_context["overnight_low"],
        "previous_day_high": prev_day["high"],
        "previous_day_low": prev_day["low"],
        "previous_week_high": weekly_range["high"],
        "previous_week_low": weekly_range["low"],
        "fib_50": (prev_day["high"] + prev_day["low"]) / 2,
        "pivot": (prev_day["high"] + prev_day["low"] + prev_day["close"]) / 3,
    }
    correct_date = trade_date_for_row(five_minute[-1]) == trade_date_for_datetime(generated_at)
    indicators_ready = vwap_value is not None and intraday_atr is not None and bands["middle"] is not None
    now_et = generated_at.astimezone(ZoneInfo("America/New_York"))
    now_minutes = now_et.hour * 60 + now_et.minute
    market_hours_pass = now_et.weekday() < 5 and 9 * 60 + 30 <= now_minutes < 16 * 60
    data_quality_pass = source_live and age_minutes <= 7 and correct_date and indicators_ready and market_hours_pass
    watch_levels = ranked_watch_levels(name, htf_result, market_context, prev_day["high"], prev_day["low"])
    trade_setup = confirmed_trade_setup(
        name, htf_result, watch_levels, five_minute, intraday_atr, bb_position, generated_at, data_quality_pass
    )
    decision = trade_decision(rate_result, htf_result, data_quality_pass)
    if trade_setup["confirmed"]:
        decision["direction"] = trade_setup["direction"]
        decision["trade_plan_score"] = 5
    else:
        decision["direction"] = "No Trade"
        decision["trade_plan_score"] = 0
    selector = market_selector(
        name,
        generated_at,
        current,
        htf_result,
        exponential_averages["ema20"],
        exponential_averages["ema50"],
        vwap_value,
        key_levels,
        intraday_atr,
        five_minute,
        data_quality_pass,
    )
    proposed_direction = trade_setup["direction"] if trade_setup["confirmed"] else decision["direction"]
    trend_points = professional_trend_scores(
        current, averages, weekly_range, monthly_range, proposed_direction
    )
    long_proposal = proposed_direction == "Long Only"
    short_proposal = proposed_direction == "Short Only"
    vwap_aligned = vwap_value is not None and (
        (long_proposal and current > vwap_value) or (short_proposal and current < vwap_value)
    )
    anchored_aligned = anchored_vwap is not None and (
        (long_proposal and current > anchored_vwap) or (short_proposal and current < anchored_vwap)
    )
    professional_structure_score = (
        2 + 2 + 2 + 1
        + (2 if vwap_aligned else 0)
        + (1 if anchored_aligned else 0)
    ) if trade_setup["confirmed"] else 0
    pattern_status = trade_setup["status"]
    if trade_setup["confirmed"]:
        pattern_status = "CORE RESEARCH SIGNAL — FULL LIVE GATES NOT AVAILABLE"
    professional_es = name == "ES"
    auto = {
        "engine_version": trade_setup["engine_version"],
        "direction": "No Trade" if professional_es else decision["direction"],
        "research_direction": proposed_direction,
        "delta_result": "Mixed",
        "entry_type": trade_setup.get("setup") or "Watch Zone → Trigger → Actual Entry",
        "entry": None if professional_es else trade_setup["entry"],
        "stop": None if professional_es else trade_setup["stop"],
        "target1": None if professional_es else trade_setup["target1"],
        "target2": None if professional_es else trade_setup["target2"],
        "risk_points": None if professional_es else trade_setup["risk_points"],
        "rr1": None if professional_es else trade_setup["rr1"],
        "rr2": None if professional_es else trade_setup["rr2"],
        "exit_plan": "No executable position. Full live gates are not connected." if professional_es else trade_setup["exit_plan"],
        "research_entry": trade_setup["entry"],
        "research_stop": trade_setup["stop"],
        "research_target1": trade_setup["target1"],
        "research_target2": trade_setup["target2"],
        "research_risk_points": trade_setup["risk_points"],
        "research_rr1": trade_setup["rr1"],
        "research_rr2": trade_setup["rr2"],
        "confirmation_time": trade_setup.get("confirmation_time"),
        "pattern_confirmed": trade_setup["confirmed"],
        "setup_confirmed": False if professional_es else trade_setup["confirmed"],
        "execution_eligible": False if professional_es else trade_setup["confirmed"],
        "strategy_mode": "OVERNIGHT-ONLY RESEARCH" if professional_es else "ZB V2",
        "validation_reason": "Research only: the recent combined overnight baseline produced PF 1.873 from only 11 trades, while the maximum-history Overnight High long test produced PF 0.536 from 151 trades and was rejected. No ES strategy is validated; display research levels only and never label them executable." if professional_es else "",
        "setup_status": pattern_status if professional_es else trade_setup["status"],
        "watch_levels": watch_levels,
        "liquidity_shift": "N/A — order-flow feed not connected",
        "order_flow_result": "Not Connected",
        "order_flow_score": None,
        "order_flow_connected": False,
        "todays_bias": decision["todays_bias"],
        "trade_plan_score": decision["trade_plan_score"],
        "trend_pro_daily_bullish_level": round_price(max(current, prev_day["high"])),
        "trend_pro_daily_bearish_level": round_price(min(current, prev_day["low"])),
        "trend_pro_240_bullish_level": structure["vwap"] or round_price(max(row["high"] for row in intraday[-16:])),
        "trend_pro_240_bearish_level": round_price(min(row["low"] for row in intraday[-16:])),
        "trend_pro_result": "Unavailable" if professional_es else htf_result,
        "trend_pro_source": "unavailable" if professional_es else "proxy",
        "trend_pro_score": 0 if professional_es else (15 if htf_result != "Neutral" else 7),
        "professional_trend_scores": trend_points,
        "structure_score": professional_structure_score,
        "volatility_score": volatility_score(name, vix, daily_atr),
        "vwap": structure["vwap"],
        "vwap_position": structure["vwap_position"],
        "vwap_distance": round_price(current - vwap_value) if vwap_value is not None else None,
        "anchored_vwap_2day": round_price(anchored_vwap),
        "anchored_vwap_2day_position": "Above" if anchored_vwap is not None and current > anchored_vwap else "Below" if anchored_vwap is not None and current < anchored_vwap else "Mixed",
        "anchored_vwap_2day_distance": round_price(current - anchored_vwap) if anchored_vwap is not None else None,
        "bb_position": None if bb_position is None else round(bb_position, 3),
        "chase_filter": chase_status,
        "data_quality_pass": data_quality_pass,
        "market_hours_pass": market_hours_pass,
        "data_quality_reason": "PASS" if data_quality_pass else ("DELAYED DATA — Planning Only" if not source_live else "OUTSIDE MONDAY–FRIDAY 9:30 AM–4:00 PM ET" if not market_hours_pass else "Execution confirmation feed not current"),
    }

    return {
        "automation": auto,
        "name": name,
        "symbol": symbol,
        "contract_selection": CONTRACT_SELECTION.get(name, {"mode": "provider supplied", "symbol": symbol}),
        "last": round_price(current),
        "last_time": last_time.strftime("%Y-%m-%d %H:%M UTC"),
        "last_time_et": last_time.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %-I:%M %p ET"),
        "price_source": ACTIVE_FUTURES_SOURCE,
        "price_basis": "Latest value in the 5-minute feed bar; the newest bar may still be forming",
        "trade_date": trade_date_for_row(five_minute[-1]).isoformat(),
        "last_candle_age_minutes": age_minutes,
        "data_status": data_status,
        "moving_averages": {key: round_price(value) for key, value in averages.items()},
        "exponential_moving_averages": {key: round_price(value) for key, value in exponential_averages.items()},
        "selector": selector,
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
        "atr_20m": round_price(intraday_atr),
        "atr_15m": round_price(intraday_atr),
        "bollinger_20_2_20m": bands,
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
    catalog["futures_prices"]["label"] = ACTIVE_FUTURES_SOURCE
    catalog["futures_prices"]["status"] = "primary" if ACTIVE_FUTURES_SOURCE.startswith("Databento") else "fallback-delayed"
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
            f"ES/ZB: {ACTIVE_FUTURES_SOURCE}; all futures technicals calculated locally from that feed. "
            "VIX and Treasury yields are delayed context. Macro events are tagged to official sources."
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
            "ES": instrument_snapshot("ES", rate_context["result"], generated_at_dt, volatility["vix"]),
            "ZB": instrument_snapshot("ZB", rate_context["result"], generated_at_dt, volatility["vix"]),
        }
        selection = choose_market(instruments)
        for instrument_name, instrument in instruments.items():
            auto = instrument["automation"]
            selector_eligible = (
                selection.get("market") == instrument_name
                and selection.get("decision") == f"TRADE {instrument_name}"
            )
            auto["selector_eligible"] = selector_eligible
            if auto.get("pattern_confirmed") and not selector_eligible:
                auto["setup_status"] = "CORE RESEARCH SKIP — MARKET SELECTOR DID NOT CHOOSE THIS INSTRUMENT"
            auto["hard_gates"] = {
                "data_quality": bool(auto.get("data_quality_pass")),
                "market_selection": selector_eligible,
                "pattern_confirmation": bool(auto.get("pattern_confirmed")),
                "actual_trend_pro": auto.get("trend_pro_source") == "actual",
                "verified_order_flow": bool(auto.get("order_flow_connected")),
                "risk_reward_2r": bool(auto.get("research_rr2") and auto["research_rr2"] >= 2),
            }
        return {
            "generated_at": generated_at,
            "provider": ACTIVE_FUTURES_SOURCE,
            "data_sources": source_status(economic_calendar),
            "yields": yields,
            "rate_context": rate_context,
            "economic_calendar": economic_calendar,
            "instruments": instruments,
            "market_selection": selection,
            "volatility": {**volatility, "vix_status": "delayed"},
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
