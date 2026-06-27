"""Core logic for MES live level calculations and snapshot generation."""

import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo

import pandas as pd
import requests

SYMBOL = os.environ.get("MES_SYMBOL", "MES.c.0")  # Databento continuous MES by default
RESOLUTION = int(os.environ.get("MES_RESOLUTION_MINUTES", "15"))
LOOKBACK_HOURS = int(os.environ.get("MES_LOOKBACK_HOURS", "72"))
ROUND_TO = 5.0
EXCHANGE_TZ = ZoneInfo("America/New_York")
DATA_PROVIDER = os.environ.get("MES_DATA_PROVIDER", "databento").lower()
DATABENTO_DATASET = os.environ.get("DATABENTO_DATASET", "GLBX.MDP3")
STALE_AFTER_MINUTES = int(os.environ.get("MES_STALE_AFTER_MINUTES", str(RESOLUTION * 3)))
RTH_START = time(9, 30)
RTH_END = time(16, 0)
ETH_OPEN = time(18, 0)
ETH_CLOSE = time(17, 0)


def _get_api_key() -> str:
    """Resolve the Alpha Vantage API key for the legacy fallback provider."""
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("Set ALPHAVANTAGE_API_KEY to use the Alpha Vantage provider.")
    return api_key


def _require_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize the candle frame used by the calculator."""
    required = {"time", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Candle data missing required columns: {', '.join(sorted(missing))}")

    cleaned = df.copy()
    cleaned["time"] = pd.to_datetime(cleaned["time"], utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
    cleaned = cleaned.dropna(subset=["time", "open", "high", "low", "close"])
    cleaned = cleaned.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    if cleaned.empty:
        raise RuntimeError("No valid candle rows returned by the data provider.")
    return cleaned


def _normalize_databento_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Databento fixed-precision prices when the client returns raw integers."""
    normalized = df.copy()
    for col in ["open", "high", "low", "close"]:
        if col in normalized and normalized[col].abs().max() > 1_000_000:
            normalized[col] = normalized[col] / 1_000_000_000
    return normalized


def _resample_candles(df: pd.DataFrame, minutes: int = RESOLUTION) -> pd.DataFrame:
    """Resample provider candles to the configured candle interval."""
    cleaned = _require_columns(df)
    indexed = cleaned.set_index("time")
    rule = f"{minutes}min"
    out = indexed.resample(rule, label="right", closed="right").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )
    out = out.dropna(subset=["open", "high", "low", "close"]).reset_index()
    return _require_columns(out)


def fetch_databento_candles() -> pd.DataFrame:
    """Fetch recent MES futures candles from Databento."""
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set DATABENTO_API_KEY for accurate MES futures candles, or set "
            "MES_DATA_PROVIDER=alphavantage for the legacy fallback."
        )

    try:
        import databento as db
    except ImportError as exc:
        raise RuntimeError("Install databento with `pip install databento`.") from exc

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=LOOKBACK_HOURS)

    client = db.Historical(api_key)
    data = client.timeseries.get_range(
        dataset=DATABENTO_DATASET,
        symbols=[SYMBOL],
        schema="ohlcv-1m",
        start=start.isoformat(),
        end=end.isoformat(),
    )
    df = data.to_df().reset_index()
    df = df.rename(columns={"ts_event": "time", "symbol": "provider_symbol"})
    df = _normalize_databento_prices(df)
    return _resample_candles(df)


def fetch_alphavantage_candles() -> pd.DataFrame:
    """Fetch recent candles from Alpha Vantage as a legacy fallback."""
    api_key = _get_api_key()
    symbol = os.environ.get("ALPHAVANTAGE_SYMBOL", "MES=F")
    series_key = f"Time Series ({RESOLUTION}min)"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": f"{RESOLUTION}min",
        "outputsize": "compact",
        "datatype": "json",
        "apikey": api_key,
    }

    response = requests.get("https://www.alphavantage.co/query", params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "Error Message" in payload:
        raise RuntimeError(f"Alpha Vantage request failed: {payload['Error Message']}")
    if "Note" in payload and not payload.get(series_key):
        raise RuntimeError(f"Alpha Vantage notice: {payload['Note']}")

    raw_series = payload.get(series_key) or {}
    if not raw_series:
        raise RuntimeError(
            "No candle data returned from Alpha Vantage. For accurate MES futures data, "
            "use MES_DATA_PROVIDER=databento with DATABENTO_API_KEY."
        )

    rows = []
    for ts_str, values in raw_series.items():
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=EXCHANGE_TZ)
        rows.append(
            {
                "time": ts.astimezone(timezone.utc),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": float(values.get("5. volume", 0)),
            }
        )

    df = _require_columns(pd.DataFrame(rows))

    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    df = df[df["time"] >= cutoff].reset_index(drop=True)
    if df.empty:
        raise RuntimeError("No candle data available within the requested lookback window.")

    return df


def fetch_candles() -> pd.DataFrame:
    """Fetch recent MES candles from the configured provider."""
    if DATA_PROVIDER == "databento":
        return fetch_databento_candles()
    if DATA_PROVIDER == "alphavantage":
        return fetch_alphavantage_candles()
    raise RuntimeError(f"Unsupported MES_DATA_PROVIDER: {DATA_PROVIDER}")


def compute_atr(df: pd.DataFrame, period: int = 14) -> float:
    """Compute the Average True Range for the provided candles."""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean().iloc[-1]
    if pd.isna(atr):
        raise RuntimeError(f"Not enough candle data to compute ATR({period}).")
    return float(atr)


def round_level(x: float, step: float = ROUND_TO) -> float:
    """Round a price level to the nearest increment."""
    return round(x / step) * step


@dataclass
class Levels:
    session_high: float
    session_low: float
    overnight_high: Optional[float]
    overnight_low: Optional[float]
    prior_rth_high: Optional[float]
    prior_rth_low: Optional[float]
    breakout: float
    breakdown: float
    dip_zone: Tuple[float, float]
    supply_zone: Tuple[float, float]


@dataclass
class SessionWindow:
    name: str
    start: datetime
    end: datetime


def _combine_et(day: date, value: time) -> datetime:
    return datetime.combine(day, value, tzinfo=EXCHANGE_TZ)


def current_eth_window(now: Optional[datetime] = None) -> SessionWindow:
    """Return the active or most recently active CME equity futures ETH window."""
    now_et = (now or datetime.now(timezone.utc)).astimezone(EXCHANGE_TZ)
    today_open = _combine_et(now_et.date(), ETH_OPEN)
    today_close = _combine_et(now_et.date(), ETH_CLOSE)

    if now_et.time() >= ETH_OPEN:
        start = today_open
        end = _combine_et(now_et.date() + timedelta(days=1), ETH_CLOSE)
    elif now_et.time() < ETH_CLOSE:
        start = _combine_et(now_et.date() - timedelta(days=1), ETH_OPEN)
        end = today_close
    else:
        start = _combine_et(now_et.date() - timedelta(days=1), ETH_OPEN)
        end = today_close

    return SessionWindow("ETH", start.astimezone(timezone.utc), end.astimezone(timezone.utc))


def current_rth_window(now: Optional[datetime] = None) -> SessionWindow:
    """Return the active or most recently active regular trading hours window."""
    now_et = (now or datetime.now(timezone.utc)).astimezone(EXCHANGE_TZ)
    if now_et.time() < RTH_START:
        session_day = now_et.date() - timedelta(days=1)
    else:
        session_day = now_et.date()
    return SessionWindow(
        "RTH",
        _combine_et(session_day, RTH_START).astimezone(timezone.utc),
        _combine_et(session_day, RTH_END).astimezone(timezone.utc),
    )


def previous_rth_window(now: Optional[datetime] = None) -> SessionWindow:
    """Return the prior regular trading hours window."""
    current = current_rth_window(now)
    start_et = current.start.astimezone(EXCHANGE_TZ) - timedelta(days=1)
    end_et = current.end.astimezone(EXCHANGE_TZ) - timedelta(days=1)
    return SessionWindow("Prior RTH", start_et.astimezone(timezone.utc), end_et.astimezone(timezone.utc))


def filter_window(df: pd.DataFrame, window: SessionWindow) -> pd.DataFrame:
    mask = (df["time"] >= window.start) & (df["time"] <= window.end)
    return df.loc[mask].reset_index(drop=True)


def _range_for_window(df: pd.DataFrame, window: SessionWindow) -> Tuple[Optional[float], Optional[float]]:
    window_df = filter_window(df, window)
    if window_df.empty:
        return None, None
    return float(window_df["high"].max()), float(window_df["low"].min())


def compute_levels(df: pd.DataFrame, atr: float, session_df: Optional[pd.DataFrame] = None) -> Levels:
    """Derive actionable levels from the session range and ATR."""
    working = session_df if session_df is not None and not session_df.empty else df
    session_high = working["high"].max()
    session_low = working["low"].min()
    rng = session_high - session_low

    breakout = round_level(session_high - 0.30 * rng)
    breakdown = round_level(session_low + 0.30 * rng)

    mid = (session_high + session_low) / 2

    dip_low = round_level(breakdown - 0.25 * atr)
    dip_high = round_level(mid)

    supply_low = round_level(breakout + atr * 0.35)
    supply_high = round_level(breakout + atr * 0.60)

    eth = current_eth_window()
    rth = current_rth_window()
    prior_rth = previous_rth_window()
    overnight_df = filter_window(df, SessionWindow("Overnight", eth.start, rth.start))
    overnight_high = float(overnight_df["high"].max()) if not overnight_df.empty else None
    overnight_low = float(overnight_df["low"].min()) if not overnight_df.empty else None
    prior_rth_high, prior_rth_low = _range_for_window(df, prior_rth)

    return Levels(
        session_high=float(session_high),
        session_low=float(session_low),
        overnight_high=overnight_high,
        overnight_low=overnight_low,
        prior_rth_high=prior_rth_high,
        prior_rth_low=prior_rth_low,
        breakout=breakout,
        breakdown=breakdown,
        dip_zone=(dip_low, dip_high),
        supply_zone=(supply_low, supply_high),
    )


def determine_bias(last_close: float, levels: Levels, atr: float) -> Tuple[str, str]:
    """Determine directional bias and the next action based on price relative to levels."""
    breakout = float(levels.breakout)
    breakdown = float(levels.breakdown)
    dip_low, dip_high = levels.dip_zone
    supply_low, supply_high = levels.supply_zone

    buffer = 0.10 * atr

    if last_close > breakout + buffer:
        bias = "LONG"
        action = (
            f"Look for dip/reclaim above {breakout} or pullback into ~{dip_high} "
            f"with a confident green 15–30m candle. Favor longs; let shorts prove themselves."
        )
    elif last_close < breakdown - buffer:
        bias = "SHORT"
        action = (
            f"Look for breakdown retest near {breakdown} to short, aiming toward recent lows or {dip_low}. "
            f"Avoid new longs until price reclaims {breakdown} and holds on a 15–30m close."
        )
    else:
        bias = "NEUTRAL / WAIT"
        action = (
            f"Price is between {breakdown} and {breakout} (middle of the range). "
            "Best move: wait for acceptance above breakout for longs or below breakdown for shorts. "
            "No need to trade the chop."
        )

    return bias, action


def get_snapshot() -> Dict[str, object]:
    """Return the latest candle snapshot with levels and bias guidance."""
    df = fetch_candles()
    if len(df) < 20:
        raise RuntimeError("Not enough candle data to compute ATR/levels.")

    atr = compute_atr(df)
    eth = current_eth_window()
    rth = current_rth_window()
    session_df = filter_window(df, eth)
    if len(session_df) < 20:
        session_df = df

    last_row = df.iloc[-1]
    last_close = float(last_row["close"])
    last_time_utc = pd.Timestamp(last_row["time"]).to_pydatetime()
    last_time_et = last_time_utc.astimezone(EXCHANGE_TZ)
    last_age = datetime.now(timezone.utc) - last_time_utc.astimezone(timezone.utc)
    stale = last_age > timedelta(minutes=STALE_AFTER_MINUTES)

    levels = compute_levels(df, atr, session_df)
    bias, action = determine_bias(last_close, levels, atr)

    return {
        "provider": DATA_PROVIDER,
        "symbol": SYMBOL if DATA_PROVIDER == "databento" else os.environ.get("ALPHAVANTAGE_SYMBOL", "MES=F"),
        "data_status": "stale" if stale else "fresh",
        "stale_after_minutes": STALE_AFTER_MINUTES,
        "last_candle_age_minutes": round(last_age.total_seconds() / 60, 1),
        "last_time": last_time_et.strftime("%Y-%m-%d %H:%M %Z"),
        "last_close": round(last_close, 1),
        "atr": round(atr, 2),
        "session": {
            "active": eth.name,
            "start": eth.start.astimezone(EXCHANGE_TZ).strftime("%Y-%m-%d %H:%M %Z"),
            "end": eth.end.astimezone(EXCHANGE_TZ).strftime("%Y-%m-%d %H:%M %Z"),
            "rth_start": rth.start.astimezone(EXCHANGE_TZ).strftime("%Y-%m-%d %H:%M %Z"),
            "rth_end": rth.end.astimezone(EXCHANGE_TZ).strftime("%Y-%m-%d %H:%M %Z"),
        },
        "levels": {
            "session_high": round(levels.session_high, 1),
            "session_low": round(levels.session_low, 1),
            "overnight_high": None if levels.overnight_high is None else round(levels.overnight_high, 1),
            "overnight_low": None if levels.overnight_low is None else round(levels.overnight_low, 1),
            "prior_rth_high": None if levels.prior_rth_high is None else round(levels.prior_rth_high, 1),
            "prior_rth_low": None if levels.prior_rth_low is None else round(levels.prior_rth_low, 1),
            "breakout": levels.breakout,
            "breakdown": levels.breakdown,
            "dip_low": levels.dip_zone[0],
            "dip_high": levels.dip_zone[1],
            "supply_low": levels.supply_zone[0],
            "supply_high": levels.supply_zone[1],
        },
        "bias": bias,
        "action": action,
    }
