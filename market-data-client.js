(function () {
  const timestamp = value => Date.parse(String(value || '').replace(' UTC', 'Z').replace(' ', 'T'));

  function validate(snapshot) {
    if (!snapshot || snapshot.error) throw new Error(snapshot?.error || 'Snapshot unavailable');
    const generated = timestamp(snapshot.generated_at);
    if (!Number.isFinite(generated) || generated > Date.now() + 60000) {
      throw new Error('Snapshot has an invalid generation time');
    }
    if (!snapshot.instruments?.ES || !snapshot.instruments?.ZB) {
      throw new Error('Snapshot is missing ES or ZB market data');
    }
    // Clone so the bundled fallback remains an immutable copy of what was published.
    const result = JSON.parse(JSON.stringify(snapshot));
    for (const context of Object.values(result.instruments)) {
      const candleTime = timestamp(context.last_time);
      const age = Number.isFinite(candleTime) ? Math.max(0, (Date.now() - candleTime) / 60000) : Infinity;
      context.last_candle_age_minutes = Math.ceil(age);
      const expired = age > 30 || Date.now() - generated > 30 * 60000;
      if (expired) context.data_status = 'stale';
      if (expired || age > 7 || context.data_status !== 'live') {
        if (context.automation) {
          context.automation.data_quality_pass = false;
          context.automation.execution_eligible = false;
          context.automation.selector_eligible = false;
          if (context.automation.hard_gates) context.automation.hard_gates.data_quality = false;
        }
        if (context.selector) {
          context.selector.data_fresh = false;
          context.selector.rating = expired ? 'STALE' : 'PLANNING ONLY';
        }
        result.market_selection = { market: null, decision: 'NOT READY', reason: 'Current verified market data is required. Historical levels are for planning only.' };
      }
    }
    return result;
  }

  const DEFAULT_API = "data/market-quotes.json";

  function configuredApi() {
    if (window.LAVENDER_MARKET_API) return window.LAVENDER_MARKET_API;
    return ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname)
      ? '/api/market-quotes' : DEFAULT_API;
  }

  async function fetchJson(url, timeoutMs) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const separator = url.includes("?") ? "&" : "?";
      const response = await fetch(`${url}${separator}t=${Date.now()}`, {
        cache: "no-store",
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally {
      window.clearTimeout(timer);
    }
  }

  function attachLiveQuotes(snapshot, live) {
    if (!snapshot?.instruments || !live?.instruments) return snapshot;
    Object.keys(snapshot.instruments).forEach((name) => {
      const quote = live.instruments[name];
      if (quote && quote.last !== null && quote.last !== "" && Number.isFinite(Number(quote.last))) {
        snapshot.instruments[name].live_quote = quote;
      }
    });
    snapshot.live_quote_provider = live.provider;
    snapshot.live_quote_generated_at = live.generated_at;
    snapshot.live_quote_status = live.status;
    return snapshot;
  }

  async function loadSnapshot(staticUrl) {
    const snapshot = validate(await fetchJson(staticUrl, 10000));
    try {
      const live = await fetchJson(configuredApi(), 4000);
      return { snapshot: attachLiveQuotes(snapshot, live), live, liveError: null };
    } catch (error) {
      return { snapshot, live: null, liveError: error };
    }
  }

  window.MarketDataClient = { loadSnapshot, attachLiveQuotes, configuredApi, validate, timestamp };
})();
