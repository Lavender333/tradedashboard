"""Core logic for MES live level calculations and snapshot generation."""

import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Tuple

import finnhub
import pandas as pd

SYMBOL = "MES=F"          # Micro E-mini S&P 500 futures
RESOLUTION = "15"         # 15-minute candles
LOOKBACK_HOURS = 24        # History window
ROUND_TO = 5.0             # Round levels to nearest 5 points


def get_client() -> finnhub.Client:
    """Instantiate a Finnhub client using the FINNHUB_API_KEY environment variable."""
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        raise RuntimeError("FINNHUB_API_KEY not found. Set it as an environment variable.")
    return finnhub.Client(api_key=api_key)


def fetch_candles(client: finnhub.Client) -> pd.DataFrame:
    """Fetch recent MES candles and return as a clean DataFrame."""
    now = int(time.time())
    start = int((datetime.now() - timedelta(hours=LOOKBACK_HOURS)).timestamp())

    raw = client.stock_candles(SYMBOL, RESOLUTION, start, now)
    if raw.get("s") != "ok":
        raise RuntimeError(f"Finnhub candle request failed: {raw}")

    df = pd.DataFrame(raw)
    df.rename(columns={
        "c": "close",
        "h": "high",
        "l": "low",
        "o": "open",
        "v": "volume",
        "t": "ts",
    }, inplace=True)

    df["time"] = pd.to_datetime(df["ts"], unit="s")
    df = df[["time", "open", "high", "low", "close", "volume"]].sort_values("time").reset_index(drop=True)
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
    client = get_client()
    df = fetch_candles(client)
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

