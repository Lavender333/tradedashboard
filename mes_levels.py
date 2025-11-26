"""Shared logic for ES live level calculations and snapshot generation.

This version uses free (delayed) Yahoo Finance data via yfinance instead of
requiring a Finnhub API key.
"""

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

# =========================
#  CONFIG
# =========================

# ES=F is the S&P 500 Futures Continuous Contract
# Note: Data is delayed 10-15m by Yahoo unless you have a paid feed.
TICKER = "ES=F"
ROUND_TO = 4.0
ATR_PERIOD = 14


# =========================
#  DATA FETCHING
# =========================

def fetch_es_data() -> pd.DataFrame:
    """Fetch 5 days of 15m intraday data from Yahoo Finance.

    Includes fixes for recent yfinance API changes (MultiIndex columns).
    Returns an empty DataFrame on errors so callers can surface friendly messages.
    """
    try:
        df = yf.download(tickers=TICKER, period="5d", interval="15m", progress=False)

        # yfinance now returns a MultiIndex (Price, Ticker). Flatten if needed.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        df.columns = [str(c).lower() for c in df.columns]

        # Rename time column variations for consistency
        if "datetime" in df.columns:
            df = df.rename(columns={"datetime": "time"})
        elif "date" in df.columns:
            df = df.rename(columns={"date": "time"})

        required = ["time", "close", "high", "low"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise RuntimeError(f"Missing columns: {missing}. Got: {df.columns.tolist()}")

        df = df.dropna().sort_values("time").reset_index(drop=True)
        if df.empty:
            raise RuntimeError("Dataframe is empty after fetching.")

        return df
    except Exception as exc:  # pragma: no cover - network/data errors
        print(f"Data Fetch Error: {exc}")
        return pd.DataFrame()


# =========================
#  LEVEL & BIAS LOGIC
# =========================

def round_level(x: float, step: float = ROUND_TO) -> float:
    """Round to the nearest increment (e.g., nearest 4.0 or 5.0 points)."""
    return round(x / step) * step


def compute_true_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> float:
    """Compute the Average True Range using the classic Wilder formula."""
    df = df.copy()
    df["h-l"] = df["high"] - df["low"]
    df["h-pc"] = (df["high"] - df["close"].shift(1)).abs()
    df["l-pc"] = (df["low"] - df["close"].shift(1)).abs()

    df["tr"] = df[["h-l", "h-pc", "l-pc"]].max(axis=1)
    atr = df["tr"].rolling(period).mean().iloc[-1]

    return float(atr) if not pd.isna(atr) else 15.0  # pragmatic fallback


def compute_levels(df: pd.DataFrame, atr: float) -> dict:
    """Derive breakout/breakdown and zones from the last 24h of data."""
    last_time = df["time"].iloc[-1]
    start_window = last_time - timedelta(hours=24)
    session_df = df[df["time"] > start_window]

    # Fallback if 24h window is empty
    if session_df.empty:
        session_df = df.tail(20)

    session_high = session_df["high"].max()
    session_low = session_df["low"].min()

    breakout = round_level(session_high)
    breakdown = round_level(session_low)
    mid = (session_high + session_low) / 2.0

    dip_low = round_level(mid - 0.5 * atr)
    dip_high = round_level(mid + 0.5 * atr)

    supply_low = round_level(breakout + atr * 0.25)
    supply_high = round_level(breakout + atr * 0.75)

    return {
        "session_high": float(session_high),
        "session_low": float(session_low),
        "breakout": breakout,
        "breakdown": breakdown,
        "dip_zone": (dip_low, dip_high),
        "supply_zone": (supply_low, supply_high),
    }


def determine_bias(last_close: float, levels: dict, atr: float) -> tuple[str, str]:
    """Translate price position into a bias and suggested action."""
    breakout = levels["breakout"]
    breakdown = levels["breakdown"]
    dip_low, dip_high = levels["dip_zone"]

    buffer = 0.10 * atr

    if last_close > breakout - buffer:
        bias = "LONG / BREAKOUT"
        action = (
            f"Price pressing highs ({breakout}). Look for breakout > {breakout} "
            f"or pullback hold at {dip_high}."
        )
    elif last_close < breakdown + buffer:
        bias = "SHORT / BREAKDOWN"
        action = (
            f"Price pressing lows ({breakdown}). Watch for flush below {breakdown}. "
            f"Rallies to {dip_low} likely sold."
        )
    else:
        bias = "NEUTRAL / RANGE"
        action = (
            f"Chopping between {breakdown} and {breakout}. "
            f"Fade edges or wait for resolution. Mid-range is {dip_low}-{dip_high}."
        )

    return bias, action


def get_snapshot() -> dict:
    """Produce a clean snapshot for UI/CLI consumption."""
    df = fetch_es_data()

    if df.empty or len(df) < ATR_PERIOD + 2:
        return {"error": "Not enough data loaded."}

    atr = compute_true_atr(df)
    last_row = df.iloc[-1]
    last_close = float(last_row["close"])

    ts = last_row["time"]
    if isinstance(ts, str):
        last_time = ts
    else:
        last_time = ts.strftime("%Y-%m-%d %H:%M")

    levels = compute_levels(df, atr)
    bias, action = determine_bias(last_close, levels, atr)

    return {
        "last_time": last_time,
        "last_close": round(last_close, 2),
        "atr": round(atr, 2),
        "levels": {
            "breakout": levels["breakout"],
            "breakdown": levels["breakdown"],
            "dip_low": levels["dip_zone"][0],
            "dip_high": levels["dip_zone"][1],
            "supply_low": levels["supply_zone"][0],
            "supply_high": levels["supply_zone"][1],
        },
        "bias": bias,
        "action": action,
    }
