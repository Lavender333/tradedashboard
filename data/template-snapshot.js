window.templateSnapshotFallback = {
  "data_sources": {
    "active": [
      "Yahoo Finance delayed futures candles",
      "Yahoo Finance Treasury yield indexes",
      "Nasdaq Economic Calendar with official-source tagging"
    ],
    "catalog": {
      "economic_calendar": {
        "events": 1,
        "label": "Nasdaq Economic Calendar with official-source tagging",
        "primary_sources": [
          "Federal Reserve"
        ],
        "role": "scheduled reports, actual/consensus/previous when available",
        "status": "dynamic"
      },
      "futures_prices": {
        "label": "Yahoo Finance delayed futures candles",
        "role": "ES/ZB OHLC, overnight levels, moving averages, VWAP proxy",
        "status": "dynamic"
      },
      "official_macro_sources": {
        "label": "BLS / BEA / ISM / Conference Board / Treasury / Federal Reserve",
        "role": "primary source labels for macro events",
        "status": "mapped"
      },
      "rates": {
        "label": "Yahoo Finance Treasury yield indexes",
        "role": "2Y/10Y/30Y yield direction",
        "status": "dynamic"
      }
    },
    "summary": "Dynamic sources: futures/rates from Yahoo delayed feeds; macro calendar from Nasdaq; events tagged to official primary sources when recognized."
  },
  "economic_calendar": [
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-06-30",
      "impact": "medium",
      "note": "Previous 0.4 \u00b7 Actual 0.0",
      "primary_source": "Federal Reserve",
      "source": "Nasdaq Economic Calendar",
      "source_url": "https://www.federalreserve.gov/",
      "time_et": "6:30 AM",
      "title": "Dallas Fed Mfg Business Index"
    }
  ],
  "generated_at": "2026-06-30 14:58 UTC",
  "instruments": {
    "ES": {
      "atr_15m": 10.64,
      "atr_daily": 111.68,
      "automation": {
        "delta_result": "Mixed",
        "direction": "No Trade",
        "entry": null,
        "entry_type": "No Trade",
        "liquidity_shift": "Live order-flow feed not connected",
        "order_flow_result": "Neutral",
        "order_flow_score": 0,
        "stop": null,
        "structure_score": 5,
        "target1": null,
        "target2": null,
        "todays_bias": "Neutral",
        "trade_plan_score": 0,
        "trend_pro_240_bearish_level": 7491.5,
        "trend_pro_240_bullish_level": 7520.61,
        "trend_pro_daily_bearish_level": 7398.0,
        "trend_pro_daily_bullish_level": 7527.5,
        "trend_pro_result": "Bullish",
        "trend_pro_score": 15,
        "volatility_score": 4,
        "vwap": 7520.61,
        "vwap_position": "Above"
      },
      "data_status": "fresh",
      "higher_timeframe_trend": "Bullish",
      "last": 7527.5,
      "last_candle_age_minutes": 9,
      "last_time": "2026-06-30 14:48 UTC",
      "monthly_high": 7611.5,
      "monthly_low": 7199.5,
      "monthly_trend": {
        "result": "Bullish",
        "score": 6
      },
      "moving_averages": {
        "ma100": 7099.11,
        "ma20": 7469.38,
        "ma200": 6961.32,
        "ma50": 7405.03,
        "ma72": 7196.89
      },
      "name": "ES",
      "opening_range_high": 7528.0,
      "opening_range_low": 7495.75,
      "overnight_context": {
        "bias": "Bullish continuation favored",
        "date": "2026-06-30",
        "europe_direction": "Selling into NY open",
        "inventory": "Long overnight inventory",
        "open_confirmation": "Continuation above overnight high",
        "overnight_direction": "Recovered / Bullish",
        "overnight_high": 7517.5,
        "overnight_last": 7500.25,
        "overnight_low": 7357.25,
        "position": "Above overnight high",
        "summary": "Recovered / Bullish; Selling into NY open; Above overnight high; Continuation above overnight high. Bullish continuation favored."
      },
      "overnight_high": 7517.5,
      "overnight_low": 7357.25,
      "previous_day_high": 7505.0,
      "previous_day_low": 7398.0,
      "symbol": "ES=F",
      "trend": {
        "above_count": 5,
        "result": "Bullish",
        "score": 10
      },
      "weekly_high": 7599.25,
      "weekly_low": 7357.25,
      "weekly_trend": {
        "result": "Bullish",
        "score": 6
      }
    },
    "ZB": {
      "atr_15m": 0.09,
      "atr_daily": 0.79,
      "automation": {
        "delta_result": "Mixed",
        "direction": "No Trade",
        "entry": null,
        "entry_type": "No Trade",
        "liquidity_shift": "Live order-flow feed not connected",
        "order_flow_result": "Neutral",
        "order_flow_score": 0,
        "stop": null,
        "structure_score": 7,
        "target1": null,
        "target2": null,
        "todays_bias": "Neutral",
        "trade_plan_score": 0,
        "trend_pro_240_bearish_level": 113.72,
        "trend_pro_240_bullish_level": 113.84,
        "trend_pro_daily_bearish_level": 113.84,
        "trend_pro_daily_bullish_level": 114.34,
        "trend_pro_result": "Bullish",
        "trend_pro_score": 15,
        "volatility_score": 3,
        "vwap": 113.84,
        "vwap_position": "Above"
      },
      "data_status": "fresh",
      "higher_timeframe_trend": "Bullish",
      "last": 113.84,
      "last_candle_age_minutes": 10,
      "last_time": "2026-06-30 14:48 UTC",
      "monthly_high": 114.12,
      "monthly_low": 109.5,
      "monthly_trend": {
        "result": "Bullish",
        "score": 6
      },
      "moving_averages": {
        "ma100": 114.14,
        "ma20": 113.15,
        "ma200": 115.39,
        "ma50": 112.83,
        "ma72": 113.12
      },
      "name": "ZB",
      "opening_range_high": 113.94,
      "opening_range_low": 113.84,
      "overnight_context": {
        "bias": "Wait for confirmation",
        "date": "2026-06-30",
        "europe_direction": "Selling into NY open",
        "inventory": "Short overnight inventory",
        "open_confirmation": "Opening range inside overnight range",
        "overnight_direction": "Weak / Bearish",
        "overnight_high": 114.38,
        "overnight_last": 113.91,
        "overnight_low": 113.84,
        "position": "Inside overnight range",
        "summary": "Weak / Bearish; Selling into NY open; Inside overnight range; Opening range inside overnight range. Wait for confirmation."
      },
      "overnight_high": 114.38,
      "overnight_low": 113.84,
      "previous_day_high": 114.34,
      "previous_day_low": 113.94,
      "symbol": "ZB=F",
      "trend": {
        "above_count": 3,
        "result": "Neutral",
        "score": 6
      },
      "weekly_high": 114.62,
      "weekly_low": 112.5,
      "weekly_trend": {
        "result": "Bullish",
        "score": 6
      }
    }
  },
  "provider": "Dynamic delayed market data",
  "rate_context": {
    "result": "Bearish",
    "score": 1
  },
  "suggested_scores": {
    "es_daily_trend": 10,
    "macro_rates": 1,
    "zb_daily_trend": 6
  },
  "volatility": {
    "move": null,
    "vix": 17.07
  },
  "yields": {
    "10y": {
      "direction": "Up",
      "latest": 4.4,
      "previous": 4.37,
      "symbol": "^TNX"
    },
    "2y": {
      "direction": "Up",
      "latest": 3.74,
      "previous": 3.66,
      "symbol": "^IRX"
    },
    "30y": {
      "direction": "Up",
      "latest": 4.88,
      "previous": 4.86,
      "symbol": "^TYX"
    }
  }
};
