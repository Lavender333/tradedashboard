(function () {
  const DEFAULT_API = "https://lavender-schwab-market-data.antoinetteqwilliams.workers.dev/api/market-snapshot";

  function configuredApi() {
    return window.LAVENDER_MARKET_API || DEFAULT_API;
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
      if (quote && Number.isFinite(Number(quote.last))) {
        snapshot.instruments[name].live_quote = quote;
      }
    });
    snapshot.live_quote_provider = live.provider;
    snapshot.live_quote_generated_at = live.generated_at;
    snapshot.live_quote_status = live.status;
    return snapshot;
  }

  async function loadSnapshot(staticUrl) {
    const snapshot = await fetchJson(staticUrl, 10000);
    try {
      const live = await fetchJson(configuredApi(), 4000);
      return { snapshot: attachLiveQuotes(snapshot, live), live, liveError: null };
    } catch (error) {
      return { snapshot, live: null, liveError: error };
    }
  }

  window.MarketDataClient = { loadSnapshot, attachLiveQuotes, configuredApi };
})();
