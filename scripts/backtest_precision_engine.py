#!/usr/bin/env python3
"""Configurable-session, simulation-only backtest of the dashboard confirmation engine."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

import build_template_snapshot as engine


def recent_five_minute_candles(symbol, calendar_days=59):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=calendar_days)
    payload = engine.get_json(
        engine.YAHOO_URL.format(symbol=symbol),
        params={
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "5m",
            "includePrePost": "true",
        },
        headers=engine.HEADERS,
        timeout=30,
    )
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"{symbol}: {chart['error']}")
    result = (chart.get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"{symbol}: no chart data returned")
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
        raise RuntimeError(f"{symbol}: no usable five-minute candles")
    return rows


def rth(row):
    local = engine.ny_time(row)
    minutes = local.hour * 60 + local.minute
    return local.weekday() < 5 and 9 * 60 + 30 <= minutes < 16 * 60


def completed_rth_dates(rows):
    grouped = {}
    for row in rows:
        if rth(row):
            grouped.setdefault(engine.trade_date_for_row(row), []).append(row)
    return [
        day for day, bars in sorted(grouped.items())
        if max(engine.ny_time(bar).hour * 60 + engine.ny_time(bar).minute for bar in bars) >= 15 * 60 + 55
    ]


def prior_rth(rows, session_date):
    previous_dates = sorted({engine.trade_date_for_row(row) for row in rows if rth(row) and engine.trade_date_for_row(row) < session_date})
    if not previous_dates:
        return None
    prior_date = previous_dates[-1]
    bars = [row for row in rows if rth(row) and engine.trade_date_for_row(row) == prior_date]
    return {
        "high": max(row["high"] for row in bars),
        "low": min(row["low"] for row in bars),
        "close": bars[-1]["close"],
    }


def htf_direction(daily, session_date, current):
    history = [row for row in daily if row["time"].date() < session_date]
    closes = [row["close"] for row in history]
    averages = {f"ma{period}": engine.sma(closes, period) for period in [20, 50, 72, 100, 200]}
    daily_result = engine.trend_score(current, averages)["result"]
    weekly = engine.period_range(history, lambda value: value.isocalendar()[:2])
    monthly = engine.period_range(history, lambda value: (value.year, value.month))
    weekly_result = engine.range_break_result(current, weekly["high"], weekly["low"])["result"]
    monthly_result = engine.range_break_result(current, monthly["high"], monthly["low"])["result"]
    return engine.combined_htf_result(daily_result, weekly_result, monthly_result)


def outcome(setup, future, session_close):
    long_side = setup["direction"] == "Long Only"
    entry, stop = setup["entry"], setup["stop"]
    target1, target2 = setup["target1"], setup["target2"]
    risk = setup["risk_points"]
    t1_hit = False

    for bar in future:
        stop_hit = bar["low"] <= stop if long_side else bar["high"] >= stop
        first_hit = bar["high"] >= target1 if long_side else bar["low"] <= target1
        second_hit = bar["high"] >= target2 if long_side else bar["low"] <= target2

        # A five-minute OHLC bar cannot reveal intrabar ordering. Use stop-first.
        if stop_hit:
            return {"result": "STOP AFTER T1" if t1_hit else "STOP", "r": 0.0 if t1_hit else -1.0, "t1": t1_hit, "t2": False}
        if not t1_hit and first_hit:
            t1_hit = True
        if t1_hit and second_hit:
            return {"result": "TARGET 2", "r": 1.5, "t1": True, "t2": True}

    open_r = (session_close - entry) / risk if long_side else (entry - session_close) / risk
    final_r = 0.5 + 0.5 * open_r if t1_hit else open_r
    return {"result": "SESSION CLOSE", "r": round(max(-1.0, min(1.5, final_r)), 3), "t1": t1_hit, "t2": False}


def backtest(name, symbol, session_count):
    five = recent_five_minute_candles(symbol)
    daily = engine.candles(symbol, "1y", "1d")
    dates = completed_rth_dates(five)[-session_count:]
    trades = []
    no_trade_days = []

    for session_date in dates:
        previous = prior_rth(five, session_date)
        session_bars = [row for row in five if rth(row) and engine.trade_date_for_row(row) == session_date]
        if previous is None or not session_bars:
            no_trade_days.append({"date": session_date.isoformat(), "reason": "PRIOR SESSION NOT READY"})
            continue

        found = None
        for confirmation_index, bar in enumerate(session_bars):
            local = engine.ny_time(bar)
            if local.hour * 60 + local.minute < 10 * 60:
                continue
            generated_at = bar["time"] + timedelta(minutes=5)
            available = [row for row in five if row["time"] <= bar["time"]]
            context = engine.session_market_context(available)
            twenty = engine.aggregate_candles(available, 20)
            atr20 = engine.atr(twenty)
            bands = engine.bollinger(twenty)
            width = bands["upper"] - bands["lower"] if bands["upper"] is not None else None
            bb_position = ((bar["close"] - bands["lower"]) / width) if width else None
            direction = htf_direction(daily, session_date, bar["close"])
            watches = engine.ranked_watch_levels(direction, context, previous["high"], previous["low"])
            setup = engine.confirmed_trade_setup(name, direction, watches, available, atr20, bb_position, generated_at, True)
            if setup["confirmed"]:
                previous_volume = [item.get("volume") or 0 for item in available[-21:-1]]
                average_volume = sum(previous_volume) / len(previous_volume) if previous_volume else 0
                volume_ratio = (bar.get("volume") or 0) / average_volume if average_volume else None
                closes20 = [item["close"] for item in twenty]
                ema20 = engine.ema(closes20, 20)
                ema50 = engine.ema(closes20, 50)
                found = (confirmation_index, setup, {
                    "risk_atr": round(setup["risk_points"] / atr20, 3) if atr20 else None,
                    "volume_ratio": round(volume_ratio, 3) if volume_ratio is not None else None,
                    "confirmation_body_atr": round(abs(bar["close"] - bar["open"]) / atr20, 3) if atr20 else None,
                    "ema20_50_aligned": bool(
                        ema20 is not None and ema50 is not None and
                        ((setup["direction"] == "Long Only" and ema20 > ema50) or
                         (setup["direction"] == "Short Only" and ema20 < ema50))
                    ),
                    "bb_position": round(bb_position, 3) if bb_position is not None else None,
                    "confirmation_minutes_et": local.hour * 60 + local.minute,
                })
                break

        if found is None:
            no_trade_days.append({"date": session_date.isoformat(), "reason": "NO COMPLETE VALID SETUP"})
            continue

        confirmation_index, setup, features = found
        result = outcome(setup, session_bars[confirmation_index + 1 :], session_bars[-1]["close"])
        trades.append({
            "date": session_date.isoformat(),
            "time": setup["confirmation_time"],
            "direction": setup["direction"],
            "setup": setup["setup"],
            "entry": setup["entry"],
            "stop": setup["stop"],
            "target1": setup["target1"],
            "target2": setup["target2"],
            "risk_points": setup["risk_points"],
            **features,
            **result,
        })

    curve = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for trade in trades:
        curve += trade["r"]
        peak = max(peak, curve)
        max_drawdown = max(max_drawdown, peak - curve)

    gross_wins = sum(trade["r"] for trade in trades if trade["r"] > 0)
    gross_losses = -sum(trade["r"] for trade in trades if trade["r"] < 0)
    return {
        "instrument": name,
        "symbol": symbol,
        "sessions": [day.isoformat() for day in dates],
        "sessions_tested": len(dates),
        "trades": len(trades),
        "winning_trades": sum(trade["r"] > 0 for trade in trades),
        "losing_trades": sum(trade["r"] < 0 for trade in trades),
        "flat_trades": sum(trade["r"] == 0 for trade in trades),
        "t1_hits": sum(trade["t1"] for trade in trades),
        "t2_hits": sum(trade["t2"] for trade in trades),
        "net_r": round(sum(trade["r"] for trade in trades), 3),
        "average_r": round(sum(trade["r"] for trade in trades) / len(trades), 3) if trades else 0.0,
        "profit_factor": round(gross_wins / gross_losses, 3) if gross_losses else None,
        "max_drawdown_r": round(max_drawdown, 3),
        "trade_log": trades,
        "no_trade_days": no_trade_days,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=10)
    args = parser.parse_args()
    if args.sessions < 1 or args.sessions > 40:
        parser.error("--sessions must be between 1 and 40")

    results = [backtest("ES", "ES=F", args.sessions), backtest("ZB", "ZB=F", args.sessions)]
    combined_trades = [trade for result in results for trade in result["trade_log"]]
    combined_wins = sum(trade["r"] for trade in combined_trades if trade["r"] > 0)
    combined_losses = -sum(trade["r"] for trade in combined_trades if trade["r"] < 0)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": {
            "data": "Yahoo Finance continuous futures, five-minute historical bars",
            "window": f"Last {args.sessions} completed RTH sessions available",
            "position_management": "50% at 1R, 50% at 2R; original stop retained",
            "intrabar_rule": "Stop first when stop and target occur in the same five-minute bar",
            "costs": "No commission or slippage",
        },
        "combined": {
            "trades": len(combined_trades),
            "winning_trades": sum(trade["r"] > 0 for trade in combined_trades),
            "losing_trades": sum(trade["r"] < 0 for trade in combined_trades),
            "flat_trades": sum(trade["r"] == 0 for trade in combined_trades),
            "t1_hits": sum(trade["t1"] for trade in combined_trades),
            "t2_hits": sum(trade["t2"] for trade in combined_trades),
            "net_r": round(sum(trade["r"] for trade in combined_trades), 3),
            "average_r": round(sum(trade["r"] for trade in combined_trades) / len(combined_trades), 3) if combined_trades else 0.0,
            "profit_factor": round(combined_wins / combined_losses, 3) if combined_losses else None,
        },
        "results": results,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
