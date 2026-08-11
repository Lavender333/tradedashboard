#!/usr/bin/env python3
"""Configurable-session, simulation-only backtest of the dashboard confirmation engine."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import build_template_snapshot as engine


ES_TICK_SIZE = 0.25
ES_POINT_VALUE = 50.0


def load_ninjatrader_bars(path, source_timezone="America/New_York"):
    """Load NinjaTrader bar exports or conventional timestamp/OHLCV CSV files."""
    source = Path(path)
    if not source.exists():
        raise RuntimeError(f"NinjaTrader export not found: {source}")
    lines = [line.strip() for line in source.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"NinjaTrader export is empty: {source}")

    local_zone = ZoneInfo(source_timezone)
    rows = []
    first = lines[0].lower()
    has_header = any(label in first for label in ("open", "high", "timestamp", "date"))

    def parse_time(value):
        text = str(value).strip()
        formats = (
            "%Y%m%d %H%M%S", "%Y%m%d %H%M", "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
        )
        parsed = None
        for format_ in formats:
            try:
                parsed = datetime.strptime(text, format_)
                break
            except ValueError:
                pass
        if parsed is None:
            try:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError as exc:
                raise RuntimeError(f"Unsupported NinjaTrader timestamp: {text}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=local_zone)
        return parsed.astimezone(timezone.utc)

    if has_header:
        delimiter = ";" if lines[0].count(";") > lines[0].count(",") else ","
        reader = csv.DictReader(lines, delimiter=delimiter)
        for record in reader:
            normalized = {str(key).strip().lower().replace(" ", "_"): value for key, value in record.items()}
            timestamp = normalized.get("timestamp") or normalized.get("datetime") or normalized.get("date_time") or normalized.get("time") or normalized.get("date")
            try:
                rows.append({
                    "time": parse_time(timestamp),
                    "open": float(normalized["open"]),
                    "high": float(normalized["high"]),
                    "low": float(normalized["low"]),
                    "close": float(normalized["close"]),
                    "volume": float(normalized.get("volume") or 0),
                })
            except (KeyError, TypeError, ValueError):
                continue
    else:
        for line in lines:
            delimiter = ";" if line.count(";") >= 5 else ","
            fields = [field.strip() for field in line.split(delimiter)]
            if len(fields) < 6:
                continue
            try:
                rows.append({
                    "time": parse_time(fields[0]),
                    "open": float(fields[1]),
                    "high": float(fields[2]),
                    "low": float(fields[3]),
                    "close": float(fields[4]),
                    "volume": float(fields[5] or 0),
                })
            except ValueError:
                continue

    rows.sort(key=lambda row: row["time"])
    unique = {row["time"]: row for row in rows}
    rows = [unique[key] for key in sorted(unique)]
    if not rows:
        raise RuntimeError("No usable OHLCV bars were found in the NinjaTrader export")
    return rows


def daily_from_five_minute(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(engine.trade_date_for_row(row), []).append(row)
    daily = []
    for trade_date, bars in sorted(grouped.items()):
        daily.append({
            "time": datetime.combine(trade_date, datetime.min.time(), timezone.utc),
            "open": bars[0]["open"],
            "high": max(bar["high"] for bar in bars),
            "low": min(bar["low"] for bar in bars),
            "close": bars[-1]["close"],
            "volume": sum(bar.get("volume") or 0 for bar in bars),
        })
    return daily


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


def outcome(setup, future, session_close, commission_round_turn=0.0, slippage_ticks=0.0):
    long_side = setup["direction"] == "Long Only"
    entry, stop = setup["entry"], setup["stop"]
    target1, target2 = setup["target1"], setup["target2"]
    risk = setup["risk_points"]
    t1_hit = False
    transaction_cost_points = (2 * slippage_ticks * ES_TICK_SIZE) + (commission_round_turn / ES_POINT_VALUE)
    transaction_cost_r = transaction_cost_points / risk

    def net_result(result, gross_r, t1, t2):
        return {
            "result": result,
            "gross_r": round(gross_r, 3),
            "transaction_cost_r": round(transaction_cost_r, 3),
            "r": round(gross_r - transaction_cost_r, 3),
            "t1": t1,
            "t2": t2,
        }

    for bar in future:
        stop_hit = bar["low"] <= stop if long_side else bar["high"] >= stop
        first_hit = bar["high"] >= target1 if long_side else bar["low"] <= target1
        second_hit = bar["high"] >= target2 if long_side else bar["low"] <= target2

        # A five-minute OHLC bar cannot reveal intrabar ordering. Use stop-first.
        if stop_hit:
            return net_result("STOP AFTER T1" if t1_hit else "STOP", 0.0 if t1_hit else -1.0, t1_hit, False)
        if not t1_hit and first_hit:
            t1_hit = True
        if t1_hit and second_hit:
            return net_result("TARGET 2", 1.5, True, True)

    open_r = (session_close - entry) / risk if long_side else (entry - session_close) / risk
    final_r = 0.5 + 0.5 * open_r if t1_hit else open_r
    return net_result("SESSION CLOSE", max(-1.0, min(1.5, final_r)), t1_hit, False)


def backtest(name, symbol, session_count, five=None, daily=None, commission_round_turn=0.0, slippage_ticks=0.0):
    five = five if five is not None else recent_five_minute_candles(symbol)
    daily = daily if daily is not None else engine.candles(symbol, "1y", "1d")
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
        result = outcome(
            setup,
            session_bars[confirmation_index + 1 :],
            session_bars[-1]["close"],
            commission_round_turn,
            slippage_ticks,
        )
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
    parser.add_argument("--input", help="NinjaTrader ES five-minute bar export")
    parser.add_argument("--instrument", choices=("ES", "BOTH"), default="BOTH")
    parser.add_argument("--source-timezone", default="America/New_York", help="Timezone used by timestamps without an offset")
    parser.add_argument("--commission-round-turn", type=float, default=5.00, help="ES commission and fees per round turn in dollars")
    parser.add_argument("--slippage-ticks", type=float, default=1.0, help="Slippage in ES ticks on each side of the trade")
    args = parser.parse_args()
    maximum_sessions = 250 if args.input else 40
    if args.sessions < 1 or args.sessions > maximum_sessions:
        parser.error(f"--sessions must be between 1 and {maximum_sessions}")
    if args.commission_round_turn < 0 or args.slippage_ticks < 0:
        parser.error("cost assumptions cannot be negative")

    if args.input:
        five = load_ninjatrader_bars(args.input, args.source_timezone)
        daily = daily_from_five_minute(five)
        results = [backtest(
            "ES",
            "NinjaTrader ES export",
            args.sessions,
            five=five,
            daily=daily,
            commission_round_turn=args.commission_round_turn,
            slippage_ticks=args.slippage_ticks,
        )]
        data_description = f"NinjaTrader ES five-minute export: {Path(args.input).name}"
        cost_description = (
            f"${args.commission_round_turn:.2f} commission/fees per round turn; "
            f"{args.slippage_ticks:g} ES tick slippage on entry and exit"
        )
    elif args.instrument == "ES":
        results = [backtest(
            "ES",
            "ES=F",
            args.sessions,
            commission_round_turn=args.commission_round_turn,
            slippage_ticks=args.slippage_ticks,
        )]
        data_description = "Yahoo Finance ES continuous futures, five-minute historical bars"
        cost_description = (
            f"${args.commission_round_turn:.2f} commission/fees per round turn; "
            f"{args.slippage_ticks:g} ES tick slippage on entry and exit"
        )
    else:
        results = [backtest("ES", "ES=F", args.sessions), backtest("ZB", "ZB=F", args.sessions)]
        data_description = "Yahoo Finance continuous futures, five-minute historical bars"
        cost_description = "No commission or slippage"
    combined_trades = [trade for result in results for trade in result["trade_log"]]
    combined_wins = sum(trade["r"] for trade in combined_trades if trade["r"] > 0)
    combined_losses = -sum(trade["r"] for trade in combined_trades if trade["r"] < 0)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": {
            "data": data_description,
            "window": f"Last {args.sessions} completed RTH sessions available",
            "engine_policy": "Professional ES automatable execution core; excludes unavailable actual Trend Pro and historical order flow, so this is not a full-template validation; ZB V2 unchanged",
            "position_management": "50% at 1R, 50% at 2R; original stop retained",
            "intrabar_rule": "Stop first when stop and target occur in the same five-minute bar",
            "costs": cost_description,
            "validation_thresholds": {
                "minimum_profit_factor": 1.5,
                "positive_expectancy_required": True,
                "minimum_qualifying_trades": 25,
            },
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
    primary = results[0]
    report["validation"] = {
        "profit_factor_pass": primary["profit_factor"] is not None and primary["profit_factor"] >= 1.5,
        "positive_expectancy_pass": primary["average_r"] > 0,
        "sample_size_pass": primary["trades"] >= 25,
        "max_drawdown_r": primary["max_drawdown_r"],
        "extend_to_250_sessions": bool(args.input and args.sessions == 120 and primary["trades"] < 25),
        "overall_pass": bool(
            primary["profit_factor"] is not None and primary["profit_factor"] >= 1.5 and
            primary["average_r"] > 0 and primary["trades"] >= 25
        ),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
