"""Core logic for MES live level calculations and snapshot generation."""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

import pandas as pd
import requests

SYMBOL = "MES=F"          # Micro E-mini S&P 500 futures
RESOLUTION = "15"         # 15-minute candles
LOOKBACK_HOURS = 24        # History window
ROUND_TO = 5.0             # Round levels to nearest 5 points


def _get_api_key() -> str:
    """Resolve the Alpha Vantage API key, falling back to the provided default."""
    return os.environ.get("ALPHAVANTAGE_API_KEY", "MTGUW7LBO905QET0")


def fetch_candles() -> pd.DataFrame:
    """Fetch recent MES candles from Alpha Vantage and return as a clean DataFrame."""
    api_key = _get_api_key()
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": SYMBOL,
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
    if "Note" in payload and not payload.get("Time Series (15min)"):
        raise RuntimeError(f"Alpha Vantage notice: {payload['Note']}")

    raw_series = payload.get("Time Series (15min)") or {}
    if not raw_series:
        raise RuntimeError("No candle data returned from Alpha Vantage.")

    rows = []
    for ts_str, values in raw_series.items():
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        rows.append(
            {
                "time": ts,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": float(values.get("5. volume", 0)),
            }
        )

    df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)

    # Filter to the configured lookback window
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    df = df[df["time"] >= cutoff].reset_index(drop=True)
    if df.empty:
        raise RuntimeError("No candle data available within the requested lookback window.")

    return df


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
    return float(atr)


def round_level(x: float, step: float = ROUND_TO) -> float:
    """Round a price level to the nearest increment."""
    return round(x / step) * step


@dataclass
class Levels:
    session_high: float
    session_low: float
    breakout: float
    breakdown: float
    dip_zone: Tuple[float, float]
    supply_zone: Tuple[float, float]


def compute_levels(df: pd.DataFrame, atr: float) -> Levels:
    """Derive actionable levels from the session range and ATR."""
    session_high = df["high"].max()
    session_low = df["low"].min()
    rng = session_high - session_low

    breakout = round_level(session_high - 0.30 * rng)
    breakdown = round_level(session_low + 0.30 * rng)

    mid = (session_high + session_low) / 2

    dip_low = round_level(breakdown - 0.25 * atr)
    dip_high = round_level(mid)

    supply_low = round_level(breakout + atr * 0.35)
    supply_high = round_level(breakout + atr * 0.60)

    return Levels(
        session_high=float(session_high),
        session_low=float(session_low),
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
    last_row = df.iloc[-1]
    last_close = float(last_row["close"])
    last_time = last_row["time"].strftime("%Y-%m-%d %H:%M")

    levels = compute_levels(df, atr)
    bias, action = determine_bias(last_close, levels, atr)

    return {
        "last_time": last_time,
        "last_close": round(last_close, 1),
        "atr": round(atr, 2),
        "levels": {
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

