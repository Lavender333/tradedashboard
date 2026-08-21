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
        "events": 8,
        "label": "Nasdaq Economic Calendar with official-source tagging",
        "primary_sources": [
          "Federal Reserve"
        ],
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
        "role": "2Y/10Y/30Y yield direction",
        "status": "dynamic"
      }
    },
    "summary": "ES/ZB: Yahoo Finance delayed backup; all futures technicals calculated locally from that feed. VIX and Treasury yields are delayed context. Macro events are tagged to official sources."
  },
  "economic_calendar": [
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-08-21",
      "impact": "medium",
      "note": "Consensus 24.1 \u00b7 Previous 41.4 \u00b7 Actual 47.4",
      "primary_source": "Federal Reserve",
      "source": "Nasdaq Economic Calendar",
      "source_url": "https://www.federalreserve.gov/",
      "time_et": "4:30 AM",
      "title": "Philadelphia Fed Manufacturing Index"
    },
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-08-21",
      "impact": "medium",
      "note": "Previous 34.4 \u00b7 Actual 73.6",
      "primary_source": "Federal Reserve",
      "source": "Nasdaq Economic Calendar",
      "source_url": "https://www.federalreserve.gov/",
      "time_et": "4:30 AM",
      "title": "Philly Fed Business Conditions"
    },
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-08-21",
      "impact": "medium",
      "note": "Previous 30.10 \u00b7 Actual 48.20",
      "primary_source": "Federal Reserve",
      "source": "Nasdaq Economic Calendar",
      "source_url": "https://www.federalreserve.gov/",
      "time_et": "4:30 AM",
      "title": "Philly Fed CAPEX Index"
    },
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-08-21",
      "impact": "medium",
      "note": "Previous 10.0 \u00b7 Actual 27.9",
      "primary_source": "Federal Reserve",
      "source": "Nasdaq Economic Calendar",
      "source_url": "https://www.federalreserve.gov/",
      "time_et": "4:30 AM",
      "title": "Philly Fed Employment"
    },
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-08-21",
      "impact": "medium",
      "note": "Previous 37.0 \u00b7 Actual 30.1",
      "primary_source": "Federal Reserve",
      "source": "Nasdaq Economic Calendar",
      "source_url": "https://www.federalreserve.gov/",
      "time_et": "4:30 AM",
      "title": "Philly Fed New Orders"
    },
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-08-21",
      "impact": "medium",
      "note": "Previous 53.90 \u00b7 Actual 40.90",
      "primary_source": "Federal Reserve",
      "source": "Nasdaq Economic Calendar",
      "source_url": "https://www.federalreserve.gov/",
      "time_et": "4:30 AM",
      "title": "Philly Fed Prices Paid"
    },
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-08-21",
      "impact": "medium",
      "note": "Previous 6,760B \u00b7 Actual 6,746B",
      "primary_source": "Federal Reserve",
      "source": "Nasdaq Economic Calendar",
      "source_url": "https://www.federalreserve.gov/",
      "time_et": "12:30 PM",
      "title": "Fed's Balance Sheet"
    },
    {
      "category": "fed",
      "country": "United States",
      "date": "2026-08-21",
      "impact": "medium",
      "note": "Previous 2.947T \u00b7 Actual 2.930T",
      "primary_source": "Economic calendar provider",
      "source": "Nasdaq Economic Calendar",
      "source_url": "",
      "time_et": "12:30 PM",
      "title": "Reserve Balances with Federal Reserve Banks"
    }
  ],
  "gemini_context": {
    "answers": [],
    "available_items": [],
    "disclaimer": "Gemini may ask for missing data and analyze provided data, but it must not invent live prices, order flow, volume profile, confirmation candles, or institutional gate status.",
    "gate_effect": "No gate override. Missing hard-gate data keeps the institutional gate failed until a connected source supplies it.",
    "message": "Set the GEMINI_API_KEY GitHub secret to enable Gemini missing-data questions.",
    "model": "gemini-2.5-flash",
    "professional_note": "Ask for the missing live inputs first. Use Gemini only as context and checklist support.",
    "requested_items": [
      "Exact current ES price from a live broker/CME-quality source; current snapshot is delayed at 2026-08-21 9:45 AM ET",
      "ES order flow: footprint, DOM, cumulative delta, absorption, and whether buyers are lifting offers or sellers are hitting bids",
      "ES volume profile: POC, VAH, VAL, major high-volume nodes, low-volume rejection zones",
      "ES completed 5-minute and 15-minute confirmation candles around the breakout/retest level",
      "ES institutional gate pass/fail inputs: data quality, market selection, pattern confirmation, actual Trend Pro, order flow, and 2:1 risk/reward",
      "Exact current ZB price from a live broker/CME-quality source; current snapshot is delayed at 2026-08-21 9:45 AM ET",
      "ZB order flow: footprint, DOM, cumulative delta, absorption, and whether buyers are lifting offers or sellers are hitting bids",
      "ZB volume profile: POC, VAH, VAL, major high-volume nodes, low-volume rejection zones",
      "ZB completed 5-minute and 15-minute confirmation candles around the breakout/retest level",
      "ZB institutional gate pass/fail inputs: data quality, market selection, pattern confirmation, actual Trend Pro, order flow, and 2:1 risk/reward"
    ],
    "status": "not_configured"
  },
  "generated_at": "2026-08-21 13:55 UTC",
  "instruments": {
    "ES": {
      "atr_15m": 6.71136,
      "atr_20m": 6.71136,
      "atr_daily": 76.95532,
      "automation": {
        "anchored_vwap_2day": 7692.98997,
        "anchored_vwap_2day_distance": -4.73997,
        "anchored_vwap_2day_position": "Below",
        "bb_position": 0.458,
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
        "todays_bias": "Bull",
        "trade_plan_score": 0,
        "trend_pro_240_bearish_level": 7681.25,
        "trend_pro_240_bullish_level": 7686.43651,
        "trend_pro_daily_bearish_level": 7657.75,
        "trend_pro_daily_bullish_level": 7746.5,
        "trend_pro_result": "Unavailable",
        "trend_pro_score": 0,
        "trend_pro_source": "unavailable",
        "validation_reason": "Research only: the recent combined overnight baseline produced PF 1.873 from only 11 trades, while the maximum-history Overnight High long test produced PF 0.536 from 151 trades and was rejected. No ES strategy is validated; display research levels only and never label them executable.",
        "volatility_score": 5,
        "vwap": 7686.43651,
        "vwap_distance": 1.81349,
        "vwap_position": "Above",
        "watch_levels": [
          {
            "rank": 1,
            "setup": "Overnight High Breakout Retest",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "5m acceptance above, later retest, then reclaim",
            "watch_level": 7704.75
          }
        ]
      },
      "bollinger_20_2_20m": {
        "lower": 7678.09823,
        "middle": 7689.1875,
        "upper": 7700.27677
      },
      "contract_selection": {
        "mode": "Yahoo continuous fallback",
        "reason": "Webull unavailable or not configured",
        "symbol": "ES=F"
      },
      "data_status": "delayed",
      "exponential_moving_averages": {
        "ema20": 7683.24007,
        "ema50": 7581.20508
      },
      "higher_timeframe_trend": "Bullish",
      "last": 7688.25,
      "last_candle_age_minutes": 9,
      "last_time": "2026-08-21 13:45 UTC",
      "last_time_et": "2026-08-21 9:45 AM ET",
      "monthly_high": 7632.0,
      "monthly_low": 7324.0,
      "monthly_trend": {
        "result": "Bullish",
        "score": 10
      },
      "moving_averages": {
        "ma100": 7408.1818,
        "ma20": 7669.95,
        "ma200": 7122.5905,
        "ma50": 7575.6536,
        "ma72": 7547.74556
      },
      "name": "ES",
      "opening_range_high": null,
      "opening_range_low": null,
      "overnight_context": {
        "bias": "Wait for confirmation",
        "date": "2026-08-21",
        "europe_direction": "Buying into NY open",
        "inventory": "Long overnight inventory",
        "open_confirmation": "Opening range inside overnight range",
        "overnight_direction": "Recovered / Bullish",
        "overnight_high": 7704.75,
        "overnight_last": 7695.75,
        "overnight_low": 7661.25,
        "position": "Inside overnight range",
        "summary": "Recovered / Bullish; Buying into NY open; Inside overnight range; Opening range inside overnight range. Wait for confirmation."
      },
      "overnight_high": 7704.75,
      "overnight_low": 7661.25,
      "previous_day_high": 7746.5,
      "previous_day_low": 7657.75,
      "price_basis": "Latest value in the 5-minute feed bar; the newest bar may still be forming",
      "price_source": "Yahoo Finance delayed backup",
      "selector": {
        "checks": {
          "confirmed_reaction": {
            "evidence": "2 five-minute close(s) vs 7688.91667",
            "pass": false
          },
          "ema_alignment": {
            "evidence": "EMA20 7683.24007 vs EMA50 7581.20508",
            "pass": true
          },
          "htf_direction": {
            "evidence": "HTF Bullish; directional plan LONG",
            "pass": true
          },
          "meaningful_level": {
            "evidence": "Nearest: pivot 7688.91667; distance 0.66667",
            "pass": true
          },
          "room_to_target": {
            "evidence": "Next: fib_50 7702.125; room 13.875",
            "pass": true
          },
          "vwap_alignment": {
            "evidence": "Price 7688.25 vs VWAP 7686.43651",
            "pass": true
          }
        },
        "confirmed": false,
        "data_fresh": false,
        "decision_time": "10:00 ET",
        "direction": "LONG",
        "fib_50": 7702.125,
        "name": "ES",
        "pivot": 7688.91667,
        "rating": "STALE",
        "ready": false,
        "score": 5,
        "target_room": 13.875,
        "target_room_atr": 2.067,
        "vwap_distance": 1.81349,
        "vwap_distance_atr": 0.27
      },
      "symbol": "ES=F",
      "trade_date": "2026-08-21",
      "trend": {
        "above_count": 5,
        "result": "Bullish",
        "score": 10
      },
      "weekly_high": 7838.5,
      "weekly_low": 7738.0,
      "weekly_trend": {
        "result": "Bearish",
        "score": 0
      }
    },
    "ZB": {
      "atr_15m": 0.13474,
      "atr_20m": 0.13474,
      "atr_daily": 1.01561,
      "automation": {
        "anchored_vwap_2day": null,
        "anchored_vwap_2day_distance": null,
        "anchored_vwap_2day_position": "Mixed",
        "bb_position": 0.047,
        "chase_filter": "SHORT CHASE \u2014 wait for pullback/retest",
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
        "todays_bias": "Bear",
        "trade_plan_score": 0,
        "trend_pro_240_bearish_level": 109.0625,
        "trend_pro_240_bullish_level": 109.15032,
        "trend_pro_daily_bearish_level": 108.96875,
        "trend_pro_daily_bullish_level": 110.28125,
        "trend_pro_result": "Bearish",
        "trend_pro_score": 15,
        "trend_pro_source": "proxy",
        "validation_reason": "",
        "volatility_score": 3,
        "vwap": 109.15032,
        "vwap_distance": 0.03718,
        "vwap_position": "Above",
        "watch_levels": [
          {
            "rank": 1,
            "setup": "Overnight Low Breakdown Retest",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "5m acceptance below, retest, then rejection",
            "watch_level": 109.15625
          },
          {
            "rank": 2,
            "setup": "Previous Day High Rejection",
            "status": "WAITING FOR CONFIRMATION",
            "trigger": "sweep and completed 5m rejection",
            "watch_level": 110.28125
          }
        ]
      },
      "bollinger_20_2_20m": {
        "lower": 109.16643,
        "middle": 109.39219,
        "upper": 109.61795
      },
      "contract_selection": {
        "mode": "Yahoo continuous fallback",
        "reason": "Webull unavailable or not configured",
        "symbol": "ZB=F"
      },
      "data_status": "delayed",
      "exponential_moving_averages": {
        "ema20": 109.52366,
        "ema50": 110.56288
      },
      "higher_timeframe_trend": "Bearish",
      "last": 109.1875,
      "last_candle_age_minutes": 9,
      "last_time": "2026-08-21 13:45 UTC",
      "last_time_et": "2026-08-21 9:45 AM ET",
      "monthly_high": 112.90625,
      "monthly_low": 108.25,
      "monthly_trend": {
        "result": "Bearish",
        "score": 3
      },
      "moving_averages": {
        "ma100": 111.99594,
        "ma20": 109.39062,
        "ma200": 114.015,
        "ma50": 111.0375,
        "ma72": 111.32335
      },
      "name": "ZB",
      "opening_range_high": null,
      "opening_range_low": null,
      "overnight_context": {
        "bias": "Buyers defended overnight low",
        "date": "2026-08-21",
        "europe_direction": "Selling into NY open",
        "inventory": "Short overnight inventory",
        "open_confirmation": "Rejected overnight low",
        "overnight_direction": "Weak / Bearish",
        "overnight_high": 109.59375,
        "overnight_last": 109.15625,
        "overnight_low": 109.15625,
        "position": "Inside overnight range",
        "summary": "Weak / Bearish; Selling into NY open; Inside overnight range; Rejected overnight low. Buyers defended overnight low."
      },
      "overnight_high": 109.59375,
      "overnight_low": 109.15625,
      "previous_day_high": 110.28125,
      "previous_day_low": 108.96875,
      "price_basis": "Latest value in the 5-minute feed bar; the newest bar may still be forming",
      "price_source": "Yahoo Finance delayed backup",
      "selector": {
        "checks": {
          "confirmed_reaction": {
            "evidence": "2 five-minute close(s) vs 109.15625",
            "pass": false
          },
          "ema_alignment": {
            "evidence": "EMA20 109.52366 vs EMA50 110.56288",
            "pass": true
          },
          "htf_direction": {
            "evidence": "HTF Bearish; directional plan SHORT",
            "pass": true
          },
          "meaningful_level": {
            "evidence": "Nearest: overnight_low 109.15625; distance 0.03125",
            "pass": true
          },
          "room_to_target": {
            "evidence": "Next: previous_day_low 108.96875; room 0.21875",
            "pass": true
          },
          "vwap_alignment": {
            "evidence": "Price 109.1875 vs VWAP 109.15032",
            "pass": false
          }
        },
        "confirmed": false,
        "data_fresh": false,
        "decision_time": "08:30 ET",
        "direction": "SHORT",
        "fib_50": 109.625,
        "name": "ZB",
        "pivot": 109.57292,
        "rating": "STALE",
        "ready": true,
        "score": 4,
        "target_room": 0.21875,
        "target_room_atr": 1.623,
        "vwap_distance": 0.03718,
        "vwap_distance_atr": 0.276
      },
      "symbol": "ZB=F",
      "trade_date": "2026-08-21",
      "trend": {
        "above_count": 0,
        "result": "Bearish",
        "score": 0
      },
      "weekly_high": 110.125,
      "weekly_low": 108.375,
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
    "vix": 15.47,
    "vix_status": "delayed"
  },
  "yields": {
    "10y": {
      "direction": "Up",
      "latest": 4.716,
      "previous": 4.696,
      "symbol": "^TNX"
    },
    "2y": {
      "direction": "Up",
      "latest": 3.707,
      "previous": 3.703,
      "symbol": "^IRX"
    },
    "30y": {
      "direction": "Up",
      "latest": 5.258,
      "previous": 5.237,
      "symbol": "^TYX"
    }
  }
};
