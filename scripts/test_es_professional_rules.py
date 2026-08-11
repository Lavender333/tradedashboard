import unittest
from datetime import datetime, timezone

import build_template_snapshot as engine


ET = engine.ZoneInfo("America/New_York")


def bar(hour, minute, open_price, high, low, close):
    return {
        "time": datetime(2026, 5, 14, hour, minute, tzinfo=ET).astimezone(timezone.utc),
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": 100,
    }


class EsProfessionalRulesTest(unittest.TestCase):
    def setUp(self):
        self.watch = [{
            "rank": 1,
            "setup": "Overnight High Breakout Retest",
            "watch_level": 100,
            "trigger": "test",
        }]

    def test_accepts_ordered_setup_with_six_point_risk_and_cost_cap(self):
        rows = [
            bar(9, 50, 99.5, 100, 99, 99.75),
            bar(9, 55, 100.5, 101, 100.5, 100.75),
            bar(10, 0, 100.7, 101, 99, 100.5),
            bar(10, 5, 103, 106.2, 102, 106),
        ]
        result = engine.confirmed_trade_setup(
            "ES", "Bullish", self.watch, rows, 10, 0.65,
            datetime(2026, 5, 14, 10, 10, tzinfo=ET), True,
        )
        self.assertTrue(result["confirmed"])
        self.assertGreaterEqual(result["risk_points"], 6)
        self.assertLessEqual(result["transaction_cost_r"], 0.10)
        self.assertEqual(result["rr1"], 1.0)
        self.assertEqual(result["rr2"], 2.0)

    def test_rejects_confirmation_before_ten_et(self):
        rows = [
            bar(9, 35, 99.5, 100, 99, 99.75),
            bar(9, 40, 100.5, 101, 100.5, 100.75),
            bar(9, 45, 100.7, 101, 99, 100.5),
        ]
        result = engine.confirmed_trade_setup(
            "ES", "Bullish", self.watch, rows, 10, 0.65,
            datetime(2026, 5, 14, 9, 50, tzinfo=ET), True,
        )
        self.assertFalse(result["confirmed"])
        self.assertIn("10:00 AM", result["status"])

    def test_trend_score_is_symmetric(self):
        bounds = {"high": 105, "low": 95}
        long_averages = {f"ma{period}": value for period, value in zip(
            [20, 50, 72, 100, 200], [99, 98, 97, 96, 95]
        )}
        short_averages = {f"ma{period}": value for period, value in zip(
            [20, 50, 72, 100, 200], [101, 102, 103, 104, 105]
        )}
        expected = {"daily": 15, "weekly": 10, "monthly": 10, "aligned_daily_averages": 5}
        self.assertEqual(
            engine.professional_trend_scores(110, long_averages, bounds, bounds, "Long Only"),
            expected,
        )
        self.assertEqual(
            engine.professional_trend_scores(90, short_averages, bounds, bounds, "Short Only"),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
