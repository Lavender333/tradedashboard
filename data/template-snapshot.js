window.templateSnapshotFallback = {
  "data_sources": {
    "active": [
      "Yahoo Finance delayed backup",
      "Yahoo Finance Treasury yield indexes",
      "Nasdaq Economic Calendar with official-source tagging"
    ],
    "catalog": {
      "economic_calendar": {
        "events": 0,
        "label": "Nasdaq Economic Calendar with official-source tagging",
        "primary_sources": [],
        "role": "scheduled reports, actual/consensus/previous when available",
        "status": "dynamic"
      },
      "futures_prices": {
        "label": "Yahoo Finance delayed backup",
        "role": "Single-source ES/ZB OHLCV for day-trading calculations",
        "status": "fallback-delayed"
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
    "summary": "ES/ZB: Yahoo Finance delayed backup; all futures technicals calculated locally from that feed. VIX and Treasury yields are delayed context. Macro events are tagged to official sources."
  },
  "economic_calendar": [],
  "generated_at": "2026-08-11 13:12 UTC",
  "instruments": {
    "ES": {
      "atr_15m": 5.31824,
      "atr_20m": 5.31824,
      "atr_daily": 88.54136,
      "automation": {
        "anchored_vwap_2day": 7779.76866,
        "anchored_vwap_2day_distance": 8.98134,
        "anchored_vwap_2day_position": "Above",
        "bb_position": 0.785,
        "chase_filter": "PASS \u2014 normal band position",
        "confirmation_time": null,
        "data_quality_pass": false,
        "data_quality_reason": "DELAYED DATA \u2014 Planning Only",
        "delta_result": "Mixed",
        "direction": "No Trade",
        "engine_version": "ES PRO V1",
        "entry": null,
        "entry_type": "Watch Zone \u2192 Trigger \u2192 Actual Entry",
        "execution_eligible": false,
        "exit_plan": "No executable position. Full live gates are not connected.",
        "hard_gates": {
          "actual_trend_pro": false,
          "data_quality": false,
          "market_selection": false,
          "pattern_confirmation": false,
          "risk_reward_2r": false,
          "verified_order_flow": false
        },
        "liquidity_shift": "N/A \u2014 order-flow feed not connected",
        "market_hours_pass": false,
        "order_flow_connected": false,
        "order_flow_result": "Not Connected",
        "order_flow_score": null,
        "pattern_confirmed": false,
        "professional_trend_scores": {
          "aligned_daily_averages": 0,
          "daily": 0,
          "monthly": 0,
          "weekly": 0
        },
        "research_direction": "No Trade",
        "research_entry": null,
        "research_risk_points": null,
        "research_rr1": null,
        "research_rr2": null,
        "research_stop": null,
        "research_target1": null,
        "research_target2": null,
        "risk_points": null,
        "rr1": null,
        "rr2": null,
        "selector_eligible": false,
        "setup_confirmed": false,
        "setup_status": "NO TRADE \u2014 LIVE DATA QUALITY GATE FAILED",
        "stop": null,
        "strategy_mode": "CORE RESEARCH",
        "structure_score": 0,
        "target1": null,
        "target2": null,
        "todays_bias": "Bull",
        "trade_plan_score": 0,
        "trend_pro_240_bearish_level": 7770.0,
        "trend_pro_240_bullish_level": 7796.0,
        "trend_pro_daily_bearish_level": 7763.0,
        "trend_pro_daily_bullish_level": 7798.0,
        "trend_pro_result": "Unavailable",
        "trend_pro_score": 0,
        "trend_pro_source": "unavailable",
        "validation_reason": "Actual Trend Pro and verified order flow are unavailable; full 100-point gate cannot pass.",
        "volatility_score": 5,
        "vwap": null,
        "vwap_distance": null,
        "vwap_position": "Mixed",
        "watch_levels": [
          {
            "rank": 1,
            "setup": "Overnight High Breakout Retest",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "5m acceptance above, retest, then reclaim",
            "watch_level": 7796.0
          },
          {
            "rank": 2,
            "setup": "Previous Day Low Rejection",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "sweep and completed 5m reclaim",
            "watch_level": 7763.0
          }
        ]
      },
      "bollinger_20_2_20m": {
        "lower": 7767.60828,
        "middle": 7781.075,
        "upper": 7794.54172
      },
      "contract_selection": {
        "mode": "Yahoo continuous fallback",
        "reason": "Webull unavailable or not configured",
        "symbol": "ES=F"
      },
      "data_status": "delayed",
      "exponential_moving_averages": {
        "ema20": 7624.11156,
        "ema50": 7522.59318
      },
      "higher_timeframe_trend": "Bullish",
      "last": 7788.75,
      "last_candle_age_minutes": 10,
      "last_time": "2026-08-11 13:02 UTC",
      "last_time_et": "2026-08-11 9:02 AM ET",
      "monthly_high": 7632.0,
      "monthly_low": 7324.0,
      "monthly_trend": {
        "result": "Bullish",
        "score": 10
      },
      "moving_averages": {
        "ma100": 7313.0981,
        "ma20": 7581.6375,
        "ma200": 7087.84925,
        "ma50": 7535.2186,
        "ma72": 7498.29417
      },
      "name": "ES",
      "opening_range_high": null,
      "opening_range_low": null,
      "overnight_context": {
        "bias": "Pre-open context only",
        "date": "2026-08-11",
        "europe_direction": "Buying into NY open",
        "inventory": "Long overnight inventory",
        "open_confirmation": "Waiting for RTH open confirmation",
        "overnight_direction": "Recovered / Bullish",
        "overnight_high": 7796.0,
        "overnight_last": 7788.75,
        "overnight_low": 7766.5,
        "position": "Inside overnight range",
        "summary": "Recovered / Bullish; Buying into NY open; Inside overnight range; Waiting for RTH open confirmation. Pre-open context only."
      },
      "overnight_high": 7796.0,
      "overnight_low": 7766.5,
      "previous_day_high": 7798.0,
      "previous_day_low": 7763.0,
      "price_basis": "Latest value in the 5-minute feed bar; the newest bar may still be forming",
      "price_source": "Yahoo Finance delayed backup",
      "selector": {
        "checks": {
          "confirmed_reaction": {
            "evidence": "2 five-minute close(s) vs None",
            "pass": false
          },
          "ema_alignment": {
            "evidence": "EMA20 7624.11156 vs EMA50 7522.59318",
            "pass": true
          },
          "htf_direction": {
            "evidence": "HTF Bullish; directional plan LONG",
            "pass": true
          },
          "meaningful_level": {
            "evidence": "Nearest: overnight_high 7796.0; distance 7.25",
            "pass": false
          },
          "room_to_target": {
            "evidence": "Next: overnight_high 7796.0; room 7.25",
            "pass": true
          },
          "vwap_alignment": {
            "evidence": "Price 7788.75 vs VWAP None",
            "pass": false
          }
        },
        "confirmed": false,
        "data_fresh": false,
        "decision_time": "10:00 ET",
        "direction": "LONG",
        "fib_50": 7780.5,
        "name": "ES",
        "pivot": 7779.25,
        "rating": "STALE",
        "ready": false,
        "score": 3,
        "target_room": 7.25,
        "target_room_atr": 1.363,
        "vwap_distance": null,
        "vwap_distance_atr": 0
      },
      "symbol": "ES=F",
      "trade_date": "2026-08-11",
      "trend": {
        "above_count": 5,
        "result": "Bullish",
        "score": 10
      },
      "weekly_high": 7820.25,
      "weekly_low": 7542.75,
      "weekly_trend": {
        "result": "Bullish",
        "score": 6
      }
    },
    "ZB": {
      "atr_15m": 0.11164,
      "atr_20m": 0.11164,
      "atr_daily": 0.95838,
      "automation": {
        "anchored_vwap_2day": null,
        "anchored_vwap_2day_distance": null,
        "anchored_vwap_2day_position": "Mixed",
        "bb_position": 1.0,
        "chase_filter": "LONG CHASE \u2014 wait for pullback/retest",
        "confirmation_time": null,
        "data_quality_pass": false,
        "data_quality_reason": "DELAYED DATA \u2014 Planning Only",
        "delta_result": "Mixed",
        "direction": "No Trade",
        "engine_version": "ZB V2",
        "entry": null,
        "entry_type": "Watch Zone \u2192 Trigger \u2192 Actual Entry",
        "execution_eligible": false,
        "exit_plan": "No position. Wait for confirmation.",
        "hard_gates": {
          "actual_trend_pro": false,
          "data_quality": false,
          "market_selection": false,
          "pattern_confirmation": false,
          "risk_reward_2r": false,
          "verified_order_flow": false
        },
        "liquidity_shift": "N/A \u2014 order-flow feed not connected",
        "market_hours_pass": false,
        "order_flow_connected": false,
        "order_flow_result": "Not Connected",
        "order_flow_score": null,
        "pattern_confirmed": false,
        "professional_trend_scores": {
          "aligned_daily_averages": 0,
          "daily": 0,
          "monthly": 0,
          "weekly": 0
        },
        "research_direction": "No Trade",
        "research_entry": null,
        "research_risk_points": null,
        "research_rr1": null,
        "research_rr2": null,
        "research_stop": null,
        "research_target1": null,
        "research_target2": null,
        "risk_points": null,
        "rr1": null,
        "rr2": null,
        "selector_eligible": false,
        "setup_confirmed": false,
        "setup_status": "NO TRADE \u2014 LIVE DATA QUALITY GATE FAILED",
        "stop": null,
        "strategy_mode": "ZB V2",
        "structure_score": 0,
        "target1": null,
        "target2": null,
        "todays_bias": "Bear",
        "trade_plan_score": 0,
        "trend_pro_240_bearish_level": 108.375,
        "trend_pro_240_bullish_level": 109.03125,
        "trend_pro_daily_bearish_level": 108.75,
        "trend_pro_daily_bullish_level": 109.65625,
        "trend_pro_result": "Bearish",
        "trend_pro_score": 15,
        "trend_pro_source": "proxy",
        "validation_reason": "",
        "volatility_score": 3,
        "vwap": null,
        "vwap_distance": null,
        "vwap_position": "Mixed",
        "watch_levels": [
          {
            "rank": 1,
            "setup": "Overnight Low Breakdown Retest",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "5m acceptance below, retest, then rejection",
            "watch_level": 108.375
          },
          {
            "rank": 2,
            "setup": "Previous Day High Rejection",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "sweep and completed 5m rejection",
            "watch_level": 109.65625
          }
        ]
      },
      "bollinger_20_2_20m": {
        "lower": 108.1653,
        "middle": 108.59844,
        "upper": 109.03157
      },
      "contract_selection": {
        "mode": "Yahoo continuous fallback",
        "reason": "Webull unavailable or not configured",
        "symbol": "ZB=F"
      },
      "data_status": "delayed",
      "exponential_moving_averages": {
        "ema20": 109.95449,
        "ema50": 111.09302
      },
      "higher_timeframe_trend": "Bearish",
      "last": 109.03125,
      "last_candle_age_minutes": 10,
      "last_time": "2026-08-11 13:01 UTC",
      "last_time_et": "2026-08-11 9:01 AM ET",
      "monthly_high": 112.90625,
      "monthly_low": 108.25,
      "monthly_trend": {
        "result": "Bearish",
        "score": 3
      },
      "moving_averages": {
        "ma100": 112.32281,
        "ma20": 109.92344,
        "ma200": 114.37687,
        "ma50": 111.56812,
        "ma72": 111.74913
      },
      "name": "ZB",
      "opening_range_high": null,
      "opening_range_low": null,
      "overnight_context": {
        "bias": "Pre-open context only",
        "date": "2026-08-11",
        "europe_direction": "Buying into NY open",
        "inventory": "Long overnight inventory",
        "open_confirmation": "Waiting for RTH open confirmation",
        "overnight_direction": "Recovered / Bullish",
        "overnight_high": 109.03125,
        "overnight_last": 109.03125,
        "overnight_low": 108.375,
        "position": "Inside overnight range",
        "summary": "Recovered / Bullish; Buying into NY open; Inside overnight range; Waiting for RTH open confirmation. Pre-open context only."
      },
      "overnight_high": 109.03125,
      "overnight_low": 108.375,
      "previous_day_high": 109.65625,
      "previous_day_low": 108.75,
      "price_basis": "Latest value in the 5-minute feed bar; the newest bar may still be forming",
      "price_source": "Yahoo Finance delayed backup",
      "selector": {
        "checks": {
          "confirmed_reaction": {
            "evidence": "2 five-minute close(s) vs 109.03125",
            "pass": false
          },
          "ema_alignment": {
            "evidence": "EMA20 109.95449 vs EMA50 111.09302",
            "pass": true
          },
          "htf_direction": {
            "evidence": "HTF Bearish; directional plan SHORT",
            "pass": true
          },
          "meaningful_level": {
            "evidence": "Nearest: overnight_high 109.03125; distance 0.0",
            "pass": true
          },
          "room_to_target": {
            "evidence": "Next: previous_day_low 108.75; room 0.28125",
            "pass": true
          },
          "vwap_alignment": {
            "evidence": "Price 109.03125 vs VWAP None",
            "pass": false
          }
        },
        "confirmed": false,
        "data_fresh": false,
        "decision_time": "08:30 ET",
        "direction": "SHORT",
        "fib_50": 109.20312,
        "name": "ZB",
        "pivot": 109.10417,
        "rating": "STALE",
        "ready": true,
        "score": 4,
        "target_room": 0.28125,
        "target_room_atr": 2.519,
        "vwap_distance": null,
        "vwap_distance_atr": 0
      },
      "symbol": "ZB=F",
      "trade_date": "2026-08-11",
      "trend": {
        "above_count": 0,
        "result": "Bearish",
        "score": 0
      },
      "weekly_high": 110.40625,
      "weekly_low": 108.71875,
      "weekly_trend": {
        "result": "Bearish",
        "score": 3
      }
    }
  },
  "market_selection": {
    "decision": "NOT READY",
    "market": null,
    "reason": "Wait for decision time and fresh market data."
  },
  "provider": "Yahoo Finance delayed backup",
  "rate_context": {
    "result": "Bearish",
    "score": 1
  },
  "suggested_scores": {
    "es_daily_trend": 10,
    "macro_rates": 1,
    "zb_daily_trend": 0
  },
  "volatility": {
    "move": null,
    "vix": 15.54,
    "vix_status": "delayed"
  },
  "yields": {
    "10y": {
      "direction": "Down",
      "latest": 4.694,
      "previous": 4.699,
      "symbol": "^TNX"
    },
    "2y": {
      "direction": "Up",
      "latest": 3.73,
      "previous": 3.718,
      "symbol": "^IRX"
    },
    "30y": {
      "direction": "Up",
      "latest": 5.245,
      "previous": 5.243,
      "symbol": "^TYX"
    }
  }
};
