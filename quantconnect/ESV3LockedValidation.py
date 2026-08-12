# region imports
from AlgorithmImports import *
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta
import json
import math
# endregion


class ESVwapRvolResearch(QCAlgorithm):
    """Locked ES VWAP-RVOL reclaim research; no parameter optimization."""

    TICK = 0.25
    POINT_VALUE = 50.0
    ROUND_TURN_FEES = 5.0
    SLIPPAGE_TICKS_PER_SIDE = 1.0
    RVOL_MIN = 2.0
    RECLAIM_TICKS = 2
    MIN_RISK_ATR = 0.45
    MAX_RISK_ATR = 1.0
    MIN_REWARD_R = 1.5
    DEVELOPMENT_END = datetime(2023, 12, 31).date()
    VALIDATION_START = datetime(2024, 1, 1).date()

    def initialize(self):
        self.set_start_date(2019, 12, 1)
        self.set_end_date(2026, 8, 10)
        self.set_cash(250000)
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

        self.trade_date = None
        self.session_pv = 0.0
        self.session_p2v = 0.0
        self.session_volume = 0.0
        self.prev_close = None
        self.prev_vwap = None
        self.traded_today = False
        self.open_trade = None
        self.five = deque(maxlen=80)
        self.volume_history = defaultdict(lambda: deque(maxlen=20))
        self.trades = []
        self.rejections = Counter()

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

    def on_five_minute(self, bar):
        stamp = self.time - timedelta(minutes=5)
        row = {
            "time": stamp,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
        }
        minute = stamp.hour * 60 + stamp.minute
        current_date = stamp.date()
        if current_date != self.trade_date:
            self.trade_date = current_date
            self.session_pv = self.session_p2v = self.session_volume = 0.0
            self.prev_close = self.prev_vwap = None
            self.traded_today = False

        self.five.append(row)
        in_rth = 9 * 60 + 30 <= minute < 16 * 60
        if not in_rth:
            if self.open_trade is not None and minute >= 16 * 60:
                self.close_trade("SESSION_CLOSE", row["close"])
            return

        typical = (row["high"] + row["low"] + row["close"]) / 3.0
        self.session_pv += typical * row["volume"]
        self.session_p2v += typical * typical * row["volume"]
        self.session_volume += row["volume"]
        vwap = self.session_pv / self.session_volume if self.session_volume else row["close"]
        variance = max(0.0, self.session_p2v / self.session_volume - vwap * vwap) if self.session_volume else 0.0
        upper_band = vwap + math.sqrt(variance)

        if self.open_trade is not None:
            self.manage_trade(row)

        time_key = stamp.strftime("%H:%M")
        history = self.volume_history[time_key]
        ready = len(history) == 20
        average_volume = sum(history) / len(history) if history else 0.0
        rvol = row["volume"] / average_volume if ready and average_volume else 0.0

        eligible_time = 10 * 60 <= minute < 14 * 60
        if eligible_time and not self.traded_today and self.open_trade is None:
            self.evaluate_signal(row, vwap, upper_band, rvol, ready)

        history.append(row["volume"])
        self.prev_close = row["close"]
        self.prev_vwap = vwap

    def evaluate_signal(self, row, vwap, upper_band, rvol, volume_ready):
        if not volume_ready:
            self.rejections["RVOL_HISTORY_NOT_READY"] += 1
            return
        if self.prev_close is None or self.prev_vwap is None or self.prev_close > self.prev_vwap:
            self.rejections["NO_CROSS_FROM_BELOW"] += 1
            return
        if not (row["low"] < vwap and row["close"] >= vwap + self.RECLAIM_TICKS * self.TICK):
            self.rejections["NO_TWO_TICK_VWAP_RECLAIM"] += 1
            return
        if rvol < self.RVOL_MIN:
            self.rejections["RVOL_BELOW_2"] += 1
            return
        atr_value = self.atr(list(self.five), 14)
        if atr_value is None:
            self.rejections["ATR_NOT_READY"] += 1
            return
        entry = row["close"]
        stop = row["low"] - self.TICK
        risk = entry - stop
        risk_atr = risk / atr_value if atr_value else 0.0
        if risk_atr < self.MIN_RISK_ATR:
            self.rejections["RISK_BELOW_0.45_ATR"] += 1
            return
        if risk_atr > self.MAX_RISK_ATR:
            self.rejections["RISK_ABOVE_1.0_ATR"] += 1
            return
        reward = upper_band - entry
        if reward < self.MIN_REWARD_R * risk:
            self.rejections["UPPER_BAND_ROOM_BELOW_1.5R"] += 1
            return
        self.open_trade = {
            "date": self.trade_date.isoformat(),
            "period": "development" if self.trade_date <= self.DEVELOPMENT_END else "validation",
            "time": row["time"].strftime("%Y-%m-%d %I:%M %p ET"),
            "entry": entry,
            "stop": stop,
            "target": upper_band,
            "risk": risk,
            "risk_atr": round(risk_atr, 4),
            "rvol": round(rvol, 4),
            "reward_r": round(reward / risk, 4),
        }
        self.traded_today = True

    def manage_trade(self, row):
        trade = self.open_trade
        stop_hit = row["low"] <= trade["stop"]
        target_hit = row["high"] >= trade["target"]
        if stop_hit:
            self.close_trade("SAME_BAR_CONSERVATIVE_STOP" if target_hit else "STOP", trade["stop"])
        elif target_hit:
            self.close_trade("TARGET", trade["target"])

    def close_trade(self, result, exit_price):
        trade = self.open_trade
        gross_r = (exit_price - trade["entry"]) / trade["risk"]
        cost_points = 2 * self.SLIPPAGE_TICKS_PER_SIDE * self.TICK + self.ROUND_TURN_FEES / self.POINT_VALUE
        net_r = gross_r - cost_points / trade["risk"]
        trade.update({"result": result, "gross_r": round(gross_r, 4), "net_r": round(net_r, 4)})
        self.trades.append(trade)
        self.open_trade = None

    @staticmethod
    def metrics(trades):
        returns = [trade["net_r"] for trade in trades]
        wins = [value for value in returns if value > 0]
        losses = [value for value in returns if value < 0]
        curve = peak = drawdown = 0.0
        for value in returns:
            curve += value
            peak = max(peak, curve)
            drawdown = max(drawdown, peak - curve)
        return {
            "trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(100 * len(wins) / len(trades), 2) if trades else 0,
            "net_r": round(sum(returns), 3),
            "expectancy_r": round(sum(returns) / len(returns), 3) if returns else 0,
            "profit_factor": round(sum(wins) / -sum(losses), 3) if losses else None,
            "max_drawdown_r": round(drawdown, 3),
        }

    def on_end_of_algorithm(self):
        if self.open_trade is not None:
            self.close_trade("END_OF_TEST", self.open_trade["entry"])
        development = [trade for trade in self.trades if trade["period"] == "development"]
        validation = [trade for trade in self.trades if trade["period"] == "validation"]
        summary = {
            "engine": "ES VWAP-RVOL RECLAIM RESEARCH V1 LOCKED",
            "data": "QuantConnect continuous ES minute data consolidated to 5-minute bars",
            "mapping": "OpenInterest / BackwardsRatio / depth 0",
            "rules": "RVOL>=2.0; prior close below VWAP; low below VWAP; close >= VWAP+2 ticks; 5m ATR risk 0.45-1.0; initial +1sigma band room >=1.5R",
            "costs": "$5 round turn + 1 ES tick entry + 1 ES tick exit",
            "news_lockout": "not applied: no point-in-time Tier-1 release calendar supplied",
            "development_2020_2023": self.metrics(development),
            "validation_2024_2026": self.metrics(validation),
            "combined": self.metrics(self.trades),
            "rejected_counts": dict(self.rejections),
        }
        validation_result = summary["validation_2024_2026"]
        summary["validation_pass"] = bool(
            validation_result["trades"] >= 300 and validation_result["expectancy_r"] > 0.25 and
            validation_result["profit_factor"] is not None and validation_result["profit_factor"] >= 1.5
        )
        self.debug("ES_VWAP_RVOL_SUMMARY|" + json.dumps(summary, separators=(",", ":")))
        for period in ("development_2020_2023", "validation_2024_2026", "combined"):
            for key, value in summary[period].items():
                self.debug("ES_VWAP_RVOL_METRIC|" + period + "|" + key + "=" + json.dumps(value, separators=(",", ":")))
        self.debug("ES_VWAP_RVOL_METRIC|validation_pass=" + json.dumps(summary["validation_pass"]))
        for reason, count in summary["rejected_counts"].items():
            self.debug("ES_VWAP_RVOL_REJECTION|" + reason + "=" + str(count))
        try:
            saved = self.object_store.save("es-vwap-rvol-research-v1.json", json.dumps({"summary": summary, "trades": self.trades}, separators=(",", ":")))
            self.debug("ES_VWAP_RVOL_OBJECT_STORE|saved=" + str(saved))
        except Exception as error:
            self.debug("ES_VWAP_RVOL_OBJECT_STORE|saved=false|reason=" + str(error))
