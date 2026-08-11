# Schwab market-data worker

This Cloudflare Worker keeps Schwab OAuth credentials and refresh tokens off
GitHub Pages. It exposes only normalized ES/ZB quote data to the dashboard.

## One-time setup

1. Create a Cloudflare Worker and KV namespace.
2. Replace the KV namespace placeholder in `wrangler.toml`.
3. Add the custom hostname `api.thetruelavender.online` to the Worker.
4. In the Schwab app, set the callback URL exactly to
   `https://api.thetruelavender.online/schwab/callback`.
5. Enter the real values directly into Cloudflare, never this repository:

   ```text
   npx wrangler secret put SCHWAB_CLIENT_ID
   npx wrangler secret put SCHWAB_CLIENT_SECRET
   ```

6. Deploy from this directory with `npx wrangler deploy`.
7. Open `https://api.thetruelavender.online/schwab/login`, approve the Schwab
   connection, then check `/api/health` and `/api/market-snapshot`.

The default symbols are Schwab futures roots `/ES` and `/ZB`. The Worker expands
each root to the nearest two unexpired quarterly contracts and selects the one
with the most volume, using open interest as the tie-breaker. This provides
automatic rollover. After the first connection, confirm that the response shows
the expected active contracts and that `delayed` is false. An explicit contract
can still be set with `SCHWAB_ES_SYMBOL` or `SCHWAB_ZB_SYMBOL` if needed.

The dashboard uses Schwab only for the displayed current quote. Its levels,
VWAP, ATR, Bollinger position, and trade gate remain based on the published
five-minute calculation snapshot. This separation prevents a fresh quote from
making stale calculations look executable.
