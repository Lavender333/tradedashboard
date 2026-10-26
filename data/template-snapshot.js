window.templateSnapshotFallback = {
  "data_sources": {
    "active": [
      "Yahoo Finance delayed backup",
      "Yahoo Finance Treasury yield indexes",
      "Nasdaq Economic Calendar with official-source tagging",
      "Gemini missing-data assistant not configured"
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
      "gemini_missing_data": {
        "label": "Gemini missing-data assistant",
        "role": "Requests unavailable ES/ZB prices, order flow, volume profile, candles, and gate inputs without inventing them",
        "status": "optional"
      },
      "official_macro_sources": {
        "label": "BLS / BEA / ISM / Conference Board / Treasury / Federal Reserve",
        "role": "primary source labels for macro events",
        "status": "mapped"
      },
      "rates": {
        "label": "Yahoo Finance Treasury yield indexes",
        "role": "13-week/10Y/30Y yield direction",
        "status": "dynamic"
      }
    },
    "summary": "ES/ZB: Yahoo Finance delayed backup; all futures technicals calculated locally from that feed. VIX and Treasury yields are delayed context. Macro events are tagged to official sources."
  },
  "economic_calendar": [],
  "gemini_context": {
    "answers": [],
    "available_items": [],
    "disclaimer": "Gemini may ask for missing data and analyze provided data, but it must not invent live prices, order flow, volume profile, confirmation candles, or institutional gate status.",
    "gate_effect": "No gate override. Missing hard-gate data keeps the institutional gate failed until a connected source supplies it.",
    "message": "Set the GEMINI_API_KEY GitHub secret to enable Gemini missing-data questions.",
    "model": "gemini-2.5-flash",
    "professional_note": "Ask for the missing live inputs first. Use Gemini only as context and checklist support.",
    "requested_items": [
      "Exact current ES price from a live broker/CME-quality source; current snapshot is delayed at 2026-10-26 9:24 AM ET",
      "ES order flow: footprint, DOM, cumulative delta, absorption, and whether buyers are lifting offers or sellers are hitting bids",
      "ES volume profile: POC, VAH, VAL, major high-volume nodes, low-volume rejection zones",
      "ES completed 5-minute and 15-minute confirmation candles around the breakout/retest level",
      "ES institutional gate pass/fail inputs: data quality, market selection, pattern confirmation, actual Trend Pro, order flow, and 2:1 risk/reward",
      "Exact current ZB price from a live broker/CME-quality source; current snapshot is delayed at 2026-10-26 9:24 AM ET",
      "ZB order flow: footprint, DOM, cumulative delta, absorption, and whether buyers are lifting offers or sellers are hitting bids",
      "ZB volume profile: POC, VAH, VAL, major high-volume nodes, low-volume rejection zones",
      "ZB completed 5-minute and 15-minute confirmation candles around the breakout/retest level",
      "ZB institutional gate pass/fail inputs: data quality, market selection, pattern confirmation, actual Trend Pro, order flow, and 2:1 risk/reward"
    ],
    "status": "not_configured"
  },
  "generated_at": "2026-10-26 13:34 UTC",
  "instruments": {
    "ES": {
      "atr_15m": 9.28262,
      "atr_20m": 9.28262,
      "atr_daily": 79.57591,
      "automation": {
        "anchored_vwap_2day": 7675.77878,
        "anchored_vwap_2day_distance": 4.22122,
        "anchored_vwap_2day_position": "Above",
        "bb_position": 0.592,
        "chase_filter": "PASS \u2014 normal band position",
        "confirmation_time": null,
        "data_quality_pass": false,
        "data_quality_reason": "DELAYED DATA \u2014 Planning Only",
        "delta_result": "Mixed",
        "direction": "No Trade",
        "engine_version": "ES OVERNIGHT-ONLY RESEARCH V1",
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
        "market_hours_pass": true,
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
        "strategy_mode": "OVERNIGHT-ONLY RESEARCH",
        "structure_score": 0,
        "target1": null,
        "target2": null,
        "todays_bias": "Neutral",
        "trade_plan_score": 0,
        "trend_pro_240_bearish_level": 7661.5,
        "trend_pro_240_bullish_level": 7695.0,
        "trend_pro_daily_bearish_level": 7648.5,
        "trend_pro_daily_bullish_level": 7714.25,
        "trend_pro_result": "Unavailable",
        "trend_pro_score": 0,
        "trend_pro_source": "unavailable",
        "validation_reason": "Research only: the recent combined overnight baseline produced PF 1.873 from only 11 trades, while the maximum-history Overnight High long test produced PF 0.536 from 151 trades and was rejected. No ES strategy is validated; display research levels only and never label them executable.",
        "volatility_score": 4,
        "vwap": null,
        "vwap_distance": null,
        "vwap_position": "Mixed",
        "watch_levels": [
          {
            "rank": 1,
            "setup": "Overnight High",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "wait for bullish HTF direction and confirmed break/retest",
            "watch_level": 7697.75
          },
          {
            "rank": 2,
            "setup": "Overnight Low",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "wait for bearish HTF direction and confirmed break/retest",
            "watch_level": 7651.75
          }
        ]
      },
      "bollinger_20_2_20m": {
        "lower": 7662.89888,
        "middle": 7677.35,
        "upper": 7691.80112
      },
      "contract_selection": {
        "mode": "Yahoo continuous fallback",
        "reason": "Webull unavailable or not configured",
        "symbol": "ES=F"
      },
      "data_status": "delayed",
      "exponential_moving_averages": {
        "ema20": 7750.3646,
        "ema50": 7718.98089
      },
      "higher_timeframe_trend": "Neutral",
      "last": 7680.0,
      "last_candle_age_minutes": 10,
      "last_time": "2026-10-26 13:24 UTC",
      "last_time_et": "2026-10-26 9:24 AM ET",
      "monthly_high": 7848.5,
      "monthly_low": 7509.25,
      "monthly_trend": {
        "result": "Bullish",
        "score": 6
      },
      "moving_averages": {
        "ma100": 7637.8253,
        "ma20": 7774.5625,
        "ma200": 7324.42705,
        "ma50": 7729.472,
        "ma72": 7692.3382
      },
      "name": "ES",
      "opening_range_high": null,
      "opening_range_low": null,
      "overnight_context": {
        "bias": "Pre-open context only",
        "date": "2026-10-26",
        "europe_direction": "Buying into NY open",
        "inventory": "Short overnight inventory",
        "open_confirmation": "Waiting for RTH open confirmation",
        "overnight_direction": "Balanced",
        "overnight_high": 7697.75,
        "overnight_last": 7680.0,
        "overnight_low": 7651.75,
        "position": "Inside overnight range",
        "summary": "Balanced; Buying into NY open; Inside overnight range; Waiting for RTH open confirmation. Pre-open context only."
      },
      "overnight_high": 7697.75,
      "overnight_low": 7651.75,
      "previous_day_high": 7714.25,
      "previous_day_low": 7648.5,
      "price_basis": "Latest value in the 5-minute feed bar; the newest bar may still be forming",
      "price_source": "Yahoo Finance delayed backup",
      "selector": {
        "checks": {
          "confirmed_reaction": {
            "evidence": "2 five-minute close(s) vs 7681.375",
            "pass": false
          },
          "ema_alignment": {
            "evidence": "EMA20 7750.3646 vs EMA50 7718.98089",
            "pass": false
          },
          "htf_direction": {
            "evidence": "HTF Neutral; directional plan NONE",
            "pass": false
          },
          "meaningful_level": {
            "evidence": "Nearest: fib_50 7681.375; distance 1.375",
            "pass": true
          },
          "room_to_target": {
            "evidence": "Next: - None; room 0.0",
            "pass": false
          },
          "vwap_alignment": {
            "evidence": "Price 7680.0 vs VWAP None",
            "pass": false
          }
        },
        "confirmed": false,
        "data_fresh": false,
        "decision_time": "10:00 ET",
        "direction": "NONE",
        "fib_50": 7681.375,
        "name": "ES",
        "pivot": 7674.16667,
        "rating": "STALE",
        "ready": false,
        "score": 1,
        "target_room": 0.0,
        "target_room_atr": 0.0,
        "vwap_distance": null,
        "vwap_distance_atr": 0
      },
      "symbol": "ES=F",
      "trade_date": "2026-10-26",
      "trend": {
        "above_count": 2,
        "result": "Neutral",
        "score": 0
      },
      "weekly_high": 7812.25,
      "weekly_low": 7648.5,
      "weekly_trend": {
        "result": "Bearish",
        "score": 3
      }
    },
    "ZB": {
      "atr_15m": 0.1202,
      "atr_20m": 0.1202,
      "atr_daily": 1.18007,
      "automation": {
        "anchored_vwap_2day": null,
        "anchored_vwap_2day_distance": null,
        "anchored_vwap_2day_position": "Mixed",
        "bb_position": 0.898,
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
        "market_hours_pass": true,
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
        "todays_bias": "Bull",
        "trade_plan_score": 0,
        "trend_pro_240_bearish_level": 107.15625,
        "trend_pro_240_bullish_level": 107.53125,
        "trend_pro_daily_bearish_level": 107.0,
        "trend_pro_daily_bullish_level": 107.9375,
        "trend_pro_result": "Bullish",
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
            "setup": "Overnight High Breakout Retest",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "5m acceptance above, retest, then reclaim",
            "watch_level": 107.59375
          },
          {
            "rank": 2,
            "setup": "Previous Day Low Rejection",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "sweep and completed 5m reclaim",
            "watch_level": 107.0
          }
        ]
      },
      "bollinger_20_2_20m": {
        "lower": 107.18688,
        "middle": 107.34375,
        "upper": 107.50062
      },
      "contract_selection": {
        "mode": "Yahoo continuous fallback",
        "reason": "Webull unavailable or not configured",
        "symbol": "ZB=F"
      },
      "data_status": "delayed",
      "exponential_moving_averages": {
        "ema20": 105.45439,
        "ema50": 106.44012
      },
      "higher_timeframe_trend": "Bullish",
      "last": 107.46875,
      "last_candle_age_minutes": 10,
      "last_time": "2026-10-26 13:24 UTC",
      "last_time_et": "2026-10-26 9:24 AM ET",
      "monthly_high": 109.5,
      "monthly_low": 102.5,
      "monthly_trend": {
        "result": "Bullish",
        "score": 6
      },
      "moving_averages": {
        "ma100": 108.97781,
        "ma20": 104.26719,
        "ma200": 111.75,
        "ma50": 106.6025,
        "ma72": 107.56901
      },
      "name": "ZB",
      "opening_range_high": null,
      "opening_range_low": null,
      "overnight_context": {
        "bias": "Pre-open context only",
        "date": "2026-10-26",
        "europe_direction": "Selling into NY open",
        "inventory": "Long overnight inventory",
        "open_confirmation": "Waiting for RTH open confirmation",
        "overnight_direction": "Recovered / Bullish",
        "overnight_high": 107.59375,
        "overnight_last": 107.46875,
        "overnight_low": 107.0,
        "position": "Inside overnight range",
        "summary": "Recovered / Bullish; Selling into NY open; Inside overnight range; Waiting for RTH open confirmation. Pre-open context only."
      },
      "overnight_high": 107.59375,
      "overnight_low": 107.0,
      "previous_day_high": 107.9375,
      "previous_day_low": 107.0,
      "price_basis": "Latest value in the 5-minute feed bar; the newest bar may still be forming",
      "price_source": "Yahoo Finance delayed backup",
      "selector": {
        "checks": {
          "confirmed_reaction": {
            "evidence": "2 five-minute close(s) vs 107.46875",
            "pass": false
          },
          "ema_alignment": {
            "evidence": "EMA20 105.45439 vs EMA50 106.44012",
            "pass": false
          },
          "htf_direction": {
            "evidence": "HTF Bullish; directional plan LONG",
            "pass": true
          },
          "meaningful_level": {
            "evidence": "Nearest: fib_50 107.46875; distance 0.0",
            "pass": true
          },
          "room_to_target": {
            "evidence": "Next: overnight_high 107.59375; room 0.125",
            "pass": true
          },
          "vwap_alignment": {
            "evidence": "Price 107.46875 vs VWAP None",
            "pass": false
          }
        },
        "confirmed": false,
        "data_fresh": false,
        "decision_time": "08:30 ET",
        "direction": "LONG",
        "fib_50": 107.46875,
        "name": "ZB",
        "pivot": 107.39583,
        "rating": "STALE",
        "ready": true,
        "score": 3,
        "target_room": 0.125,
        "target_room_atr": 1.04,
        "vwap_distance": null,
        "vwap_distance_atr": 0
      },
      "symbol": "ZB=F",
      "trade_date": "2026-10-26",
      "trend": {
        "above_count": 2,
        "result": "Neutral",
        "score": 0
      },
      "weekly_high": 107.9375,
      "weekly_low": 104.71875,
      "weekly_trend": {
        "result": "Bullish",
        "score": 6
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
    "result": "Neutral",
    "score": 3
  },
  "suggested_scores": {
    "es_daily_trend": 0,
    "macro_rates": 3,
    "zb_daily_trend": 0
  },
  "volatility": {
    "move": null,
    "vix": 19.07,
    "vix_status": "delayed"
  },
  "yields": {
    "10y": {
      "direction": "Flat",
      "latest": 4.988,
      "previous": 4.988,
      "symbol": "^TNX"
    },
    "2y": {
      "direction": "Up",
      "latest": 4.043,
      "previous": 4.032,
      "symbol": "^IRX"
    },
    "30y": {
      "direction": "Down",
      "latest": 5.305,
      "previous": 5.315,
      "symbol": "^TYX"
    }
  }
};
