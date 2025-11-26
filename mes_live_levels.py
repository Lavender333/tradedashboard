import os
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Tuple

import finnhub
import pandas as pd
from colorama import Fore, Style, init

# Initialize colorama (for colored terminal output)
init(autoreset=True)

# =========================
#  CONFIG
# =========================

SYMBOL = "MES=F"          # Micro E-mini S&P 500 futures
RESOLUTION = "15"         # 15-minute candles for decisions
LOOKBACK_HOURS = 24        # How far back to look for structure
ROUND_TO = 5.0             # Round levels to nearest 5 points


# =========================
#  HELPER FUNCTIONS
# =========================

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


def determine_bias(last_close: float, levels: Levels, atr: float) -> tuple[str, str]:
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
            f"with a strong green 15–30m candle. Favor longs."
        )

    elif last_close < breakdown - buffer:
        bias = "SHORT"
        action = (
            f"Look for breakdown retest near {breakdown} to short. "
            f"Target prior lows or {dip_low}. Avoid longs until reclaim."
        )

    else:
        bias = "NEUTRAL / WAIT"
        action = (
            f"Price is between {breakdown} and {breakout}. Wait for acceptance above breakout "
            f"for longs or below breakdown for shorts."
        )

    return bias, action


def print_header() -> None:
    """Print the script header."""
    print(Fore.CYAN + Style.BRIGHT + "\n==============================")
    print("  MES LIVE LEVEL HELPER")
    print("==============================\n" + Style.RESET_ALL)


def print_levels(levels: Levels) -> None:
    """Display the computed levels."""
    print(Fore.WHITE + Style.BRIGHT + "=== CORE LEVELS ===" + Style.RESET_ALL)
    print(f"Breakout trigger:     {levels.breakout:.1f}")
    print(f"Breakdown line:       {levels.breakdown:.1f}")
    print(f"Dip-buy zone:         {levels.dip_zone[0]:.1f} – {levels.dip_zone[1]:.1f}")
    print(f"Supply / fade zone:   {levels.supply_zone[0]:.1f} – {levels.supply_zone[1]:.1f}\n")


def print_bias_section(bias: str, action: str) -> None:
    """Display the directional bias and next action guidance."""
    if bias.startswith("LONG"):
        color = Fore.GREEN + Style.BRIGHT
    elif bias.startswith("SHORT"):
        color = Fore.MAGENTA + Style.BRIGHT   # PURPLE instead of RED
    else:
        color = Fore.YELLOW + Style.BRIGHT

    print(color + "=== BIAS ===" + Style.RESET_ALL)
    print(color + f"Bias: {bias}" + Style.RESET_ALL)
    print("Next action:")
    print(action + "\n")


# =========================
#  MAIN
# =========================

def main() -> None:
    """Execute the MES level calculation workflow."""
    print_header()
    client = get_client()
    df = fetch_candles(client)

    if len(df) < 20:
        raise RuntimeError("Not enough candle data to compute ATR/levels.")

    atr = compute_atr(df)
    last_close = float(df.iloc[-1]["close"])
    last_time = df.iloc[-1]["time"]

    levels = compute_levels(df, atr)
    bias, action = determine_bias(last_close, levels, atr)

    print(f"Last candle: {last_time}  |  Close: {last_close:.1f}")
    print(f"ATR(14, {RESOLUTION}m): {atr:.2f}\n")

    print_levels(levels)
    print_bias_section(bias, action)

    print(Fore.CYAN + "Reminder:" + Style.RESET_ALL,
          "Use only 15–30m candle closes at your levels. No chasing. Let the market come to you.\n")


if __name__ == "__main__":
    main()
