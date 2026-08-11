const DEFAULT_AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize";
const DEFAULT_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token";
const DEFAULT_MARKET_DATA_URL = "https://api.schwabapi.com/marketdata/v1";
const TOKEN_KEY = "schwab:oauth-token";
const STATE_PREFIX = "schwab:oauth-state:";

export default {
  async fetch(request, env) {
    try {
      return await route(request, env);
    } catch (error) {
      console.error("Schwab worker error", error);
      return json({ error: "Market data service unavailable" }, 503, request, env);
    }
  },
};

async function route(request, env) {
  const url = new URL(request.url);
  if (request.method === "OPTIONS") return corsPreflight(request, env);
  if (request.method !== "GET") return json({ error: "Method not allowed" }, 405, request, env);

  if (url.pathname === "/api/health") {
    const stored = await env.SCHWAB_TOKENS.get(TOKEN_KEY, "json");
    return json({
      ok: true,
      provider: "Charles Schwab Trader API",
      connected: Boolean(stored?.refresh_token || stored?.access_token),
      server_time: new Date().toISOString(),
    }, 200, request, env);
  }

  if (url.pathname === "/schwab/login") return beginLogin(request, env);
  if (url.pathname === "/schwab/callback") return finishLogin(request, env);
  if (url.pathname === "/api/market-snapshot") return marketSnapshot(request, env);
  return json({ error: "Not found" }, 404, request, env);
}

async function beginLogin(request, env) {
  requireConfiguration(env);
  const state = crypto.randomUUID();
  await env.SCHWAB_TOKENS.put(`${STATE_PREFIX}${state}`, "pending", { expirationTtl: 600 });
  const authorize = new URL(env.SCHWAB_AUTH_URL || DEFAULT_AUTH_URL);
  authorize.searchParams.set("client_id", env.SCHWAB_CLIENT_ID);
  authorize.searchParams.set("redirect_uri", env.SCHWAB_CALLBACK_URL);
  authorize.searchParams.set("response_type", "code");
  authorize.searchParams.set("state", state);
  return Response.redirect(authorize.toString(), 302);
}

async function finishLogin(request, env) {
  requireConfiguration(env);
  const url = new URL(request.url);
  const error = url.searchParams.get("error");
  if (error) return html(`Schwab authorization was not completed: ${escapeHtml(error)}`, 400);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  if (!code || !state) return html("Missing Schwab authorization code or state.", 400);
  const stateKey = `${STATE_PREFIX}${state}`;
  const pending = await env.SCHWAB_TOKENS.get(stateKey);
  if (pending !== "pending") return html("This authorization link is invalid or expired. Start again.", 400);
  await env.SCHWAB_TOKENS.delete(stateKey);

  const token = await requestToken(env, {
    grant_type: "authorization_code",
    code,
    redirect_uri: env.SCHWAB_CALLBACK_URL,
  });
  await saveToken(env, token);
  return html("Schwab market data is connected. You can close this page and refresh the trade dashboard.", 200);
}

async function marketSnapshot(request, env) {
  requireConfiguration(env);
  const token = await validAccessToken(env);
  const requested = {
    ES: env.SCHWAB_ES_SYMBOL || "/ES",
    ZB: env.SCHWAB_ZB_SYMBOL || "/ZB",
  };
  const requestTime = new Date();
  const candidates = Object.fromEntries(Object.entries(requested).map(([name, symbol]) => [
    name,
    isRootSymbol(symbol) ? futuresContractCandidates(symbol, requestTime, 2) : [symbol],
  ]));
  const url = new URL(`${env.SCHWAB_MARKET_DATA_URL || DEFAULT_MARKET_DATA_URL}/quotes`);
  url.searchParams.set("symbols", Object.values(candidates).flat().join(","));
  url.searchParams.set("fields", "quote,reference");
  url.searchParams.set("indicative", "false");
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const detail = (await response.text()).slice(0, 300);
    throw new Error(`Schwab quotes failed (${response.status}): ${detail}`);
  }
  const payload = await response.json();
  const generatedAt = new Date().toISOString();
  const instruments = {};
  for (const [name, requestedSymbol] of Object.entries(requested)) {
    const choices = candidates[name]
      .map((symbol) => normalizeQuote(name, symbol, findQuote(payload, symbol), generatedAt))
      .filter((item) => Number.isFinite(item.last));
    instruments[name] = chooseLiquidContract(choices) || normalizeQuote(name, requestedSymbol, null, generatedAt);
    instruments[name].contract_selection = {
      mode: isRootSymbol(requestedSymbol) ? "automatic liquidity rollover" : "configured contract",
      candidates: candidates[name],
      reason: isRootSymbol(requestedSymbol)
        ? "highest volume, then open interest, among the nearest two unexpired quarterly contracts"
        : "explicit SCHWAB symbol configuration",
    };
  }
  const usable = Object.values(instruments).filter((item) => Number.isFinite(item.last));
  if (!usable.length) throw new Error("Schwab returned no usable ES or ZB futures quotes");
  return json({
    provider: "Charles Schwab Trader API",
    generated_at: generatedAt,
    status: usable.length === 2 ? "live" : "partial",
    instruments,
  }, 200, request, env, 15);
}

function findQuote(payload, requestedSymbol) {
  if (!payload || typeof payload !== "object") return null;
  if (payload[requestedSymbol]) return payload[requestedSymbol];
  const normalized = requestedSymbol.replace(/^\//, "").toUpperCase();
  return Object.entries(payload).find(([key, value]) => {
    const candidates = [key, value?.symbol, value?.reference?.symbol]
      .filter(Boolean).map((item) => String(item).replace(/^\//, "").toUpperCase());
    return candidates.includes(normalized);
  })?.[1] || null;
}

function isRootSymbol(symbol) {
  return /^\/[A-Z]{1,3}$/.test(String(symbol || "").toUpperCase());
}

export function futuresContractCandidates(rootSymbol, now = new Date(), count = 2) {
  const root = String(rootSymbol).toUpperCase().replace(/^\//, "");
  const monthCodes = [[2, "H"], [5, "M"], [8, "U"], [11, "Z"]];
  const contracts = [];
  for (let year = now.getUTCFullYear(); year <= now.getUTCFullYear() + 2; year += 1) {
    for (const [month, code] of monthCodes) {
      const expiry = thirdFridayUtc(year, month);
      if (expiry.getTime() + 24 * 60 * 60 * 1000 < now.getTime()) continue;
      contracts.push({ symbol: `/${root}${code}${String(year).slice(-2)}`, expiry });
    }
  }
  return contracts.sort((left, right) => left.expiry - right.expiry).slice(0, count).map((item) => item.symbol);
}

function thirdFridayUtc(year, month) {
  const first = new Date(Date.UTC(year, month, 1));
  const firstFriday = 1 + ((5 - first.getUTCDay() + 7) % 7);
  return new Date(Date.UTC(year, month, firstFriday + 14, 23, 59, 59));
}

export function chooseLiquidContract(choices) {
  return [...choices].sort((left, right) =>
    (Number(right.volume) || 0) - (Number(left.volume) || 0) ||
    (Number(right.open_interest) || 0) - (Number(left.open_interest) || 0)
  )[0] || null;
}

export function normalizeQuote(name, requestedSymbol, row, fallbackTime) {
  const quote = row?.quote || row || {};
  const reference = row?.reference || {};
  const last = firstNumber(
    quote.lastPrice,
    quote.regularMarketLastPrice,
    quote.mark,
    quote.bidPrice && quote.askPrice ? (Number(quote.bidPrice) + Number(quote.askPrice)) / 2 : null,
  );
  const timeMs = firstNumber(
    quote.tradeTimeInLong,
    quote.regularMarketTradeTimeInLong,
    quote.quoteTimeInLong,
  );
  const quoteTime = timeMs && timeMs > 1e12 ? new Date(timeMs).toISOString() : fallbackTime;
  return {
    name,
    requested_symbol: requestedSymbol,
    symbol: reference.symbol || row?.symbol || requestedSymbol,
    description: reference.description || "",
    last,
    bid: firstNumber(quote.bidPrice),
    ask: firstNumber(quote.askPrice),
    volume: firstNumber(quote.totalVolume, quote.volume),
    open_interest: firstNumber(quote.openInterest),
    quote_time: quoteTime,
    delayed: Boolean(quote.isDelayed || row?.isDelayed),
    source: "Charles Schwab Trader API",
  };
}

async function validAccessToken(env) {
  let stored = await env.SCHWAB_TOKENS.get(TOKEN_KEY, "json");
  if (!stored) throw new Error("Schwab is not connected. Visit /schwab/login first.");
  if (stored.access_token && Number(stored.expires_at || 0) > Date.now() + 60_000) return stored.access_token;
  if (!stored.refresh_token) throw new Error("Schwab authorization expired. Visit /schwab/login again.");
  const refreshed = await requestToken(env, {
    grant_type: "refresh_token",
    refresh_token: stored.refresh_token,
  });
  stored = { ...stored, ...refreshed, refresh_token: refreshed.refresh_token || stored.refresh_token };
  await saveToken(env, stored);
  return stored.access_token;
}

async function requestToken(env, fields) {
  const credentials = btoa(`${env.SCHWAB_CLIENT_ID}:${env.SCHWAB_CLIENT_SECRET}`);
  const body = new URLSearchParams(fields);
  const response = await fetch(env.SCHWAB_TOKEN_URL || DEFAULT_TOKEN_URL, {
    method: "POST",
    headers: {
      Authorization: `Basic ${credentials}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });
  if (!response.ok) {
    const detail = (await response.text()).slice(0, 300);
    throw new Error(`Schwab token request failed (${response.status}): ${detail}`);
  }
  const token = await response.json();
  if (!token.access_token) throw new Error("Schwab token response did not contain an access token");
  return token;
}

async function saveToken(env, token) {
  const stored = {
    ...token,
    obtained_at: Date.now(),
    expires_at: Date.now() + Number(token.expires_in || 1800) * 1000,
  };
  await env.SCHWAB_TOKENS.put(TOKEN_KEY, JSON.stringify(stored));
}

function requireConfiguration(env) {
  if (!env.SCHWAB_TOKENS || !env.SCHWAB_CLIENT_ID || !env.SCHWAB_CLIENT_SECRET || !env.SCHWAB_CALLBACK_URL) {
    throw new Error("Schwab worker is not configured");
  }
}

function firstNumber(...values) {
  for (const value of values) {
    const numeric = Number(value);
    if (value !== null && value !== undefined && value !== "" && Number.isFinite(numeric)) return numeric;
  }
  return null;
}

function allowedOrigin(request, env) {
  const origin = request.headers.get("Origin");
  if (!origin) return "*";
  const allowed = String(env.ALLOWED_ORIGINS || "https://lavender333.github.io")
    .split(",").map((item) => item.trim()).filter(Boolean);
  return allowed.includes(origin) ? origin : "null";
}

function corsHeaders(request, env) {
  return {
    "Access-Control-Allow-Origin": allowedOrigin(request, env),
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function corsPreflight(request, env) {
  if (allowedOrigin(request, env) === "null") return new Response(null, { status: 403 });
  return new Response(null, { status: 204, headers: corsHeaders(request, env) });
}

function json(body, status, request, env, maxAge = 0) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": maxAge ? `public, max-age=${maxAge}` : "no-store",
      ...corsHeaders(request, env),
    },
  });
}

function html(message, status) {
  return new Response(`<!doctype html><meta charset="utf-8"><title>Schwab connection</title><main style="font:18px system-ui;max-width:680px;margin:15vh auto;padding:24px"><h1>Lavender market data</h1><p>${message}</p></main>`, {
    status,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}
