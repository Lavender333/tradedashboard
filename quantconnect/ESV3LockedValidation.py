# region imports
from AlgorithmImports import *
from collections import Counter, deque
from datetime import datetime, timedelta, time
import json
import math
# endregion


class EsV3LockedValidation(QCAlgorithm):
    """Simulation-only validation of the locked ES V3 rules."""

    EVAL_START = datetime(2024, 8, 13).date()
    EVAL_END = datetime(2026, 8, 10).date()
    TICK = 0.25
    POINT_VALUE = 50.0
    ROUND_TURN_FEES = 5.0
    SLIPPAGE_TICKS_PER_SIDE = 1.0

    def initialize(self):
        self.set_start_date(2023, 6, 1)  # HTF warm-up precedes the validation window.
        self.set_end_date(2026, 8, 10)
        self.set_cash(100000)
        self.set_time_zone("America/New_York")

        future = self.add_future(
            Futures.Indices.SP_500_E_MINI,
            Resolution.MINUTE,
            data_mapping_mode=DataMappingMode.OPEN_INTEREST,
            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
            contract_depth_offset=0,
            extended_market_hours=True,
        )
        future.set_filter(0, 182)
        self.es = future.symbol
        self.consolidate(self.es, timedelta(minutes=5), self.on_five_minute)

        self.five = deque(maxlen=1200)
        self.daily = []
        self.current_trade_date = None
        self.daily_bar = None
        self.overnight_high = None
        self.overnight_low = None
        self.opening_high = None
        self.opening_low = None
        self.traded_today = False
        self.counted_session = False
        self.open_trade = None
        self.trades = []
        self.rejections = Counter()
        self.eval_sessions = 0
        self.set_warm_up(timedelta(days=260))

    @staticmethod
    def trade_date(stamp):
        return stamp.date() + timedelta(days=1) if stamp.hour >= 18 else stamp.date()

    def on_five_minute(self, bar):
        end = self.time
        start = end - timedelta(minutes=5)
        trade_date = self.trade_date(start)
        row = {
            "time": start,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
        }

        if trade_date != self.current_trade_date:
            self.finish_daily_bar()
            self.current_trade_date = trade_date
            self.daily_bar = None
            self.overnight_high = None
            self.overnight_low = None
            self.opening_high = None
            self.opening_low = None
            self.traded_today = False
            self.counted_session = False

        self.update_daily_bar(row)
        self.five.append(row)

        minute = start.hour * 60 + start.minute
        if minute >= 18 * 60 or minute < 9 * 60 + 30:
            self.overnight_high = row["high"] if self.overnight_high is None else max(self.overnight_high, row["high"])
            self.overnight_low = row["low"] if self.overnight_low is None else min(self.overnight_low, row["low"])

        if 9 * 60 + 30 <= minute < 10 * 60:
            self.opening_high = row["high"] if self.opening_high is None else max(self.opening_high, row["high"])
            self.opening_low = row["low"] if self.opening_low is None else min(self.opening_low, row["low"])

        in_eval = self.EVAL_START <= trade_date <= self.EVAL_END
        if in_eval and not self.counted_session and minute == 9 * 60 + 30:
            self.eval_sessions += 1
            self.counted_session = True

        if self.open_trade is not None:
            self.manage_trade(row, minute)

        if not in_eval or self.is_warming_up:
            return
        if start.weekday() >= 5 or minute < 10 * 60 or minute >= 14 * 60:
            return
        if self.traded_today or self.open_trade is not None:
            return

        setup, reason = self.find_setup(row)
        if setup is None:
            self.rejections[reason] += 1
            return
        self.open_trade = setup
        self.traded_today = True

    def update_daily_bar(self, row):
        if self.daily_bar is None:
            self.daily_bar = {
                "date": self.current_trade_date,
                "open": row["open"], "high": row["high"], "low": row["low"],
                "close": row["close"], "volume": row["volume"],
            }
            return
        self.daily_bar["high"] = max(self.daily_bar["high"], row["high"])
        self.daily_bar["low"] = min(self.daily_bar["low"], row["low"])
        self.daily_bar["close"] = row["close"]
        self.daily_bar["volume"] += row["volume"]

    def finish_daily_bar(self):
        if self.daily_bar is not None:
            self.daily.append(self.daily_bar)
            if len(self.daily) > 900:
                self.daily.pop(0)

    @staticmethod
    def sma(values, period):
        return sum(values[-period:]) / period if len(values) >= period else None

    @staticmethod
    def range_vote(price, high, low):
        if price > high:
            return "Bullish"
        if price < low:
            return "Bearish"
        return "Bullish" if price >= (high + low) / 2 else "Bearish"

    def prior_period_range(self, key_function):
        buckets = []
        key = None
        bucket = []
        for row in self.daily:
            next_key = key_function(row["date"])
            if key is not None and next_key != key:
                buckets.append(bucket)
                bucket = []
            key = next_key
            bucket.append(row)
        if bucket:
            buckets.append(bucket)
        if not buckets:
            return None
        selected = buckets[-2] if len(buckets) > 1 else buckets[0]
        return max(row["high"] for row in selected), min(row["low"] for row in selected)

    def htf_direction(self, price):
        closes = [row["close"] for row in self.daily]
        averages = [self.sma(closes, period) for period in (20, 50, 72, 100, 200)]
        if any(value is None for value in averages):
            return "Neutral"
        above = sum(price > value for value in averages)
        daily_vote = "Bullish" if above >= 4 else "Bearish" if above <= 1 else "Neutral"
        weekly = self.prior_period_range(lambda value: value.isocalendar()[:2])
        monthly = self.prior_period_range(lambda value: (value.year, value.month))
        if weekly is None or monthly is None:
            return "Neutral"
        votes = [daily_vote, self.range_vote(price, *weekly), self.range_vote(price, *monthly)]
        if votes.count("Bullish") >= 2:
            return "Bullish"
        if votes.count("Bearish") >= 2:
            return "Bearish"
        return "Neutral"

    def twenty_minute_rows(self):
        buckets = {}
        for row in self.five:
            stamp = row["time"]
            key = stamp.replace(minute=(stamp.minute // 20) * 20, second=0, microsecond=0)
            if key not in buckets:
                buckets[key] = {
                    "open": row["open"], "high": row["high"], "low": row["low"],
                    "close": row["close"], "volume": row["volume"],
                }
            else:
                item = buckets[key]
                item["high"] = max(item["high"], row["high"])
                item["low"] = min(item["low"], row["low"])
                item["close"] = row["close"]
                item["volume"] += row["volume"]
        return [buckets[key] for key in sorted(buckets)]

    @staticmethod
    def atr(rows, period=14):
        if len(rows) < period + 1:
            return None
        ranges = []
        for index in range(1, len(rows)):
            high, low, previous = rows[index]["high"], rows[index]["low"], rows[index - 1]["close"]
            ranges.append(max(high - low, abs(high - previous), abs(low - previous)))
        value = sum(ranges[:period]) / period
        for true_range in ranges[period:]:
            value = ((period - 1) * value + true_range) / period
        return value

    @staticmethod
    def bb_position(rows, period=20):
        if len(rows) < period:
            return None
        closes = [row["close"] for row in rows[-period:]]
        middle = sum(closes) / period
        variance = sum((value - middle) ** 2 for value in closes) / period
        deviation = math.sqrt(variance)
        width = 4 * deviation
        return (closes[-1] - (middle - 2 * deviation)) / width if width else None

    def find_setup(self, confirmation):
        if None in (self.opening_high, self.opening_low, self.overnight_high, self.overnight_low):
            return None, "LEVELS_NOT_READY"
        direction = self.htf_direction(confirmation["close"])
        if direction not in ("Bullish", "Bearish"):
            return None, "HTF_DIRECTION_NOT_READY"

        long_side = direction == "Bullish"
        watches = [
            ("Opening Range Breakout Retest" if long_side else "Opening Range Breakdown Retest",
             self.opening_high if long_side else self.opening_low),
            ("Overnight High Breakout Retest" if long_side else "Overnight Low Breakdown Retest",
             self.overnight_high if long_side else self.overnight_low),
        ]
        candidates = [item for item in watches if (
            confirmation["close"] > item[1] and confirmation["close"] > confirmation["open"]
            if long_side else
            confirmation["close"] < item[1] and confirmation["close"] < confirmation["open"]
        )]
        if not candidates:
            return None, "NO_LEVEL_CONFIRMATION"

        twenty = self.twenty_minute_rows()
        atr_value = self.atr(twenty)
        bb = self.bb_position(twenty)
        if atr_value is None or bb is None:
            return None, "INDICATORS_NOT_READY"
        body_atr = abs(confirmation["close"] - confirmation["open"]) / atr_value
        if body_atr > 0.35:
            return None, "CONFIRMATION_BODY_ABOVE_0.35_ATR"
        if long_side and not 0.60 <= bb <= 0.75:
            return None, "LONG_BB_OUTSIDE_0.60_0.75"
        if not long_side and bb < 0.15:
            return None, "SHORT_BB_CHASE_BELOW_0.15"

        completed = list(self.five)[-24:]
        confirmation_index = len(completed) - 1
        saw_sequence = False
        risk_reason = None
        for setup_name, level in candidates:
            for break_index in range(confirmation_index - 1, -1, -1):
                breakout = completed[break_index]
                broke = breakout["close"] >= level + 2 * self.TICK if long_side else breakout["close"] <= level - 2 * self.TICK
                if not broke:
                    continue
                sequence = completed[break_index + 1:confirmation_index + 1]
                if long_side:
                    failed = any(item["low"] < level - 6 * self.TICK for item in sequence)
                    retests = [break_index + 1 + i for i, item in enumerate(sequence)
                               if level - 6 * self.TICK <= item["low"] <= level + 4 * self.TICK]
                else:
                    failed = any(item["high"] > level + 6 * self.TICK for item in sequence)
                    retests = [break_index + 1 + i for i, item in enumerate(sequence)
                               if level - 4 * self.TICK <= item["high"] <= level + 6 * self.TICK]
                if failed or not retests:
                    continue
                saw_sequence = True
                retest_index = retests[-1]
                structure = completed[max(retest_index - 1, break_index):confirmation_index + 1]
                entry = confirmation["close"]
                stop = min(item["low"] for item in structure) - self.TICK if long_side else max(item["high"] for item in structure) + self.TICK
                risk = entry - stop if long_side else stop - entry
                risk_atr = risk / atr_value if atr_value else 0
                if risk <= 0 or risk_atr < 0.45:
                    risk_reason = "STRUCTURAL_RISK_BELOW_0.45_ATR"
                    continue
                if risk_atr > 1.0:
                    risk_reason = "STRUCTURAL_RISK_ABOVE_1.0_ATR"
                    continue
                return {
                    "date": self.current_trade_date.isoformat(),
                    "time": confirmation["time"].strftime("%Y-%m-%d %I:%M %p ET"),
                    "direction": "Long" if long_side else "Short",
                    "setup": setup_name,
                    "entry": entry,
                    "stop": stop,
                    "target1": entry + risk if long_side else entry - risk,
                    "target2": entry + 2 * risk if long_side else entry - 2 * risk,
                    "risk": risk,
                    "risk_atr": risk_atr,
                    "bb_position": bb,
                    "confirmation_body_atr": body_atr,
                    "t1_hit": False,
                }, None
        if risk_reason:
            return None, risk_reason
        return None, "BREAKOUT_RETEST_SEQUENCE_FAILED" if saw_sequence else "NO_PRIOR_ACCEPTED_BREAK_RETEST"

    def manage_trade(self, row, minute):
        trade = self.open_trade
        long_side = trade["direction"] == "Long"
        stop_hit = row["low"] <= trade["stop"] if long_side else row["high"] >= trade["stop"]
        t1_hit_now = row["high"] >= trade["target1"] if long_side else row["low"] <= trade["target1"]
        t2_hit = row["high"] >= trade["target2"] if long_side else row["low"] <= trade["target2"]
        if stop_hit:
            self.close_trade("STOP_AFTER_T1" if trade["t1_hit"] else "STOP", 0.0 if trade["t1_hit"] else -1.0)
            return
        if not trade["t1_hit"] and t1_hit_now:
            trade["t1_hit"] = True
        if trade["t1_hit"] and t2_hit:
            self.close_trade("TARGET_2", 1.5)
            return
        if minute >= 15 * 60 + 55:
            open_r = ((row["close"] - trade["entry"]) / trade["risk"] if long_side
                      else (trade["entry"] - row["close"]) / trade["risk"])
            gross_r = 0.5 + 0.5 * open_r if trade["t1_hit"] else open_r
            self.close_trade("SESSION_CLOSE", max(-1.0, min(1.5, gross_r)))

    def close_trade(self, result, gross_r):
        trade = self.open_trade
        cost_points = 2 * self.SLIPPAGE_TICKS_PER_SIDE * self.TICK + self.ROUND_TURN_FEES / self.POINT_VALUE
        cost_r = cost_points / trade["risk"]
        trade.update({
            "result": result,
            "gross_r": round(gross_r, 4),
            "cost_r": round(cost_r, 4),
            "net_r": round(gross_r - cost_r, 4),
        })
        self.trades.append(trade)
        self.open_trade = None

    def on_end_of_algorithm(self):
        self.finish_daily_bar()
        if self.open_trade is not None:
            self.close_trade("END_OF_TEST", 0.0)
        returns = [trade["net_r"] for trade in self.trades]
        gross_wins = sum(value for value in returns if value > 0)
        gross_losses = -sum(value for value in returns if value < 0)
        curve = peak = drawdown = 0.0
        for value in returns:
            curve += value
            peak = max(peak, curve)
            drawdown = max(drawdown, peak - curve)
        by_setup = {}
        for setup_name in sorted(set(trade["setup"] for trade in self.trades)):
            subset = [trade for trade in self.trades if trade["setup"] == setup_name]
            positives = sum(trade["net_r"] for trade in subset if trade["net_r"] > 0)
            negatives = -sum(trade["net_r"] for trade in subset if trade["net_r"] < 0)
            by_setup[setup_name] = {
                "trades": len(subset),
                "wins": sum(trade["net_r"] > 0 for trade in subset),
                "net_r": round(sum(trade["net_r"] for trade in subset), 3),
                "profit_factor": round(positives / negatives, 3) if negatives else None,
            }
        summary = {
            "engine": "ES V3 LOCKED",
            "data": "QuantConnect continuous ES minute data consolidated to 5-minute bars",
            "mapping": "OpenInterest / BackwardsRatio / depth 0",
            "evaluation_start": self.EVAL_START.isoformat(),
            "evaluation_end": self.EVAL_END.isoformat(),
            "completed_rth_sessions": self.eval_sessions,
            "trades": len(self.trades),
            "wins": sum(value > 0 for value in returns),
            "losses": sum(value < 0 for value in returns),
            "win_rate": round(100 * sum(value > 0 for value in returns) / len(returns), 2) if returns else 0,
            "net_r": round(sum(returns), 3),
            "expectancy_r": round(sum(returns) / len(returns), 3) if returns else 0,
            "profit_factor": round(gross_wins / gross_losses, 3) if gross_losses else None,
            "max_drawdown_r": round(drawdown, 3),
            "costs": "$5 round turn + 1 ES tick entry + 1 ES tick exit",
            "setup_results": by_setup,
            "rejected_counts": dict(self.rejections),
        }
        summary["validation_pass"] = bool(
            summary["trades"] >= 30 and summary["expectancy_r"] > 0 and
            summary["profit_factor"] is not None and summary["profit_factor"] >= 1.5
        )
        summary["extend_history"] = summary["trades"] < 30
        clean_trades = [
            {key: value for key, value in trade.items() if key != "t1_hit"}
            for trade in self.trades
        ]
        report = {
            "source": "QuantConnect",
            "project": "Sleepy Yellow-Green Beaver",
            "summary": summary,
            "trades": clean_trades,
        }
        object_key = "es-v3-locked-validation-500.json"
        saved = self.object_store.save(object_key, json.dumps(report, separators=(",", ":")))
        self.debug("ESV3_SUMMARY|" + json.dumps(summary, separators=(",", ":")))
        self.debug("ESV3_OBJECT_STORE|key=" + object_key + "|saved=" + str(saved))
