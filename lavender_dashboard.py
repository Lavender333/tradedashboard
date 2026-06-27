"""Minimal Flask dashboard that surfaces MES live levels in a lavender theme."""

from flask import Flask, jsonify, render_template_string

from mes_levels import get_snapshot

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MES Live Levels — Lavender Mode</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg: #f7f6fb;
      --card-bg: #ffffff;
      --purple: #7b61ff;
      --purple-soft: #e4ddff;
      --green: #2ecc71;
      --green-soft: #daf5e8;
      --yellow: #f4c542;
      --yellow-soft: #fff5d9;
      --text-main: #222222;
      --text-soft: #555555;
      --border-soft: #e0e0ee;
      --shadow-soft: 0 10px 25px rgba(0,0,0,0.04);
    }
    * {
      box-sizing: border-box;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
    }
    body {
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--text-main);
      display: flex;
      justify-content: center;
    }
    .page {
      max-width: 960px;
      width: 100%;
      padding: 24px 16px 40px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 16px;
    }
    .title {
      font-size: 1.4rem;
      font-weight: 700;
      letter-spacing: 0.03em;
    }
    .subtitle {
      font-size: 0.9rem;
      color: var(--text-soft);
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(0, 3fr);
      gap: 16px;
      margin-bottom: 16px;
    }
    @media (max-width: 720px) {
      .grid {
        grid-template-columns: minmax(0, 1fr);
      }
    }
    .card {
      background: var(--card-bg);
      border-radius: 16px;
      box-shadow: var(--shadow-soft);
      padding: 16px 18px;
      border: 1px solid var(--border-soft);
    }
    .card-title {
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.09em;
      color: var(--text-soft);
      margin-bottom: 8px;
    }
    .bias-card {
      display: flex;
      flex-direction: column;
      gap: 8px;
      border-left-width: 4px;
      border-left-style: solid;
    }
    .bias-long {
      border-left-color: var(--green);
      background: var(--green-soft);
    }
    .bias-short {
      border-left-color: var(--purple);
      background: var(--purple-soft);
    }
    .bias-neutral {
      border-left-color: var(--yellow);
      background: var(--yellow-soft);
    }
    .bias-label {
      font-size: 1.1rem;
      font-weight: 700;
    }
    .bias-long .bias-label {
      color: var(--green);
    }
    .bias-short .bias-label {
      color: var(--purple);
    }
    .bias-neutral .bias-label {
      color: var(--yellow);
    }
    .bias-text {
      font-size: 0.9rem;
      color: var(--text-soft);
    }
    .levels-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px 16px;
      font-size: 0.9rem;
    }
    @media (max-width: 480px) {
      .levels-list {
        grid-template-columns: minmax(0, 1fr);
      }
    }
    .level-label {
      color: var(--text-soft);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .level-value {
      font-weight: 600;
      margin-top: 2px;
    }
    .footer-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8rem;
      color: var(--text-soft);
      margin-top: 8px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 4px 10px;
      background: #eceaf7;
      color: #5b4cbf;
      font-size: 0.78rem;
    }
    .pill-dot {
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: #7b61ff;
    }
    .pill-fresh .pill-dot {
      background: var(--green);
    }
    .pill-stale .pill-dot,
    .pill-error .pill-dot {
      background: var(--yellow);
    }
    .error-box {
      display: none;
      margin-bottom: 16px;
      color: #7a4c00;
      background: var(--yellow-soft);
      border: 1px solid #f1d47d;
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 0.9rem;
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="header">
      <div>
        <div class="title">MES Live Levels</div>
        <div class="subtitle">Lavender mode · 15m candles · Calm decisions only</div>
      </div>
      <div class="pill" id="data-status-pill">
        <div class="pill-dot"></div>
        <span id="data-status-text">Connecting…</span>
      </div>
    </div>

    <div class="error-box" id="error-box"></div>

    <div class="grid">
      <!-- Bias Card -->
      <div class="card bias-card" id="bias-card">
        <div class="card-title">Bias & Next Action</div>
        <div class="bias-label" id="bias-label">—</div>
        <div class="bias-text" id="bias-text">
          Waiting for data…
        </div>
      </div>

      <!-- Levels Card -->
      <div class="card">
        <div class="card-title">Core Levels</div>
        <div class="levels-list">
          <div>
            <div class="level-label">Breakout trigger</div>
            <div class="level-value" id="lvl-breakout">—</div>
          </div>
          <div>
            <div class="level-label">Breakdown line</div>
            <div class="level-value" id="lvl-breakdown">—</div>
          </div>
          <div>
            <div class="level-label">Dip-buy zone</div>
            <div class="level-value" id="lvl-dip">—</div>
          </div>
          <div>
            <div class="level-label">Supply / fade zone</div>
            <div class="level-value" id="lvl-supply">—</div>
          </div>
          <div>
            <div class="level-label">Session high / low</div>
            <div class="level-value" id="lvl-session">—</div>
          </div>
          <div>
            <div class="level-label">Overnight high / low</div>
            <div class="level-value" id="lvl-overnight">—</div>
          </div>
          <div>
            <div class="level-label">Prior RTH high / low</div>
            <div class="level-value" id="lvl-prior-rth">—</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Session Info Card -->
    <div class="card">
      <div class="card-title">Session Info</div>
      <div class="levels-list">
        <div>
          <div class="level-label">Last 15m close</div>
          <div class="level-value" id="last-close">—</div>
        </div>
        <div>
          <div class="level-label">Last candle time</div>
          <div class="level-value" id="last-time">—</div>
        </div>
        <div>
          <div class="level-label">ATR(14, 15m)</div>
          <div class="level-value" id="atr-val">—</div>
        </div>
        <div>
          <div class="level-label">Provider / symbol</div>
          <div class="level-value" id="provider-symbol">—</div>
        </div>
        <div>
          <div class="level-label">Data age</div>
          <div class="level-value" id="data-age">—</div>
        </div>
        <div>
          <div class="level-label">ETH session</div>
          <div class="level-value" id="session-window">—</div>
        </div>
      </div>
      <div class="footer-row">
        <div>Act only on 15–30m closes at your lines.</div>
        <div>Let the market come to you.</div>
      </div>
    </div>
  </div>

  <script>
    function formatRange(left, right) {
      if (left === null || right === null || left === undefined || right === undefined) {
        return "—";
      }
      return left + " / " + right;
    }

    async function refreshSnapshot() {
      const errorBox = document.getElementById("error-box");
      const statusPill = document.getElementById("data-status-pill");
      const statusText = document.getElementById("data-status-text");

      try {
        const res = await fetch("/api/snapshot");
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || "Snapshot unavailable");
        }

        errorBox.style.display = "none";

        document.getElementById("last-close").textContent = data.last_close;
        document.getElementById("last-time").textContent = data.last_time;
        document.getElementById("atr-val").textContent = data.atr.toFixed(2);
        document.getElementById("provider-symbol").textContent = data.provider + " / " + data.symbol;
        document.getElementById("data-age").textContent =
          data.last_candle_age_minutes + "m (" + data.data_status + ")";
        document.getElementById("session-window").textContent =
          data.session.start + " → " + data.session.end;

        document.getElementById("lvl-breakout").textContent = data.levels.breakout;
        document.getElementById("lvl-breakdown").textContent = data.levels.breakdown;
        document.getElementById("lvl-dip").textContent =
          data.levels.dip_low + " – " + data.levels.dip_high;
        document.getElementById("lvl-supply").textContent =
          data.levels.supply_low + " – " + data.levels.supply_high;
        document.getElementById("lvl-session").textContent =
          formatRange(data.levels.session_high, data.levels.session_low);
        document.getElementById("lvl-overnight").textContent =
          formatRange(data.levels.overnight_high, data.levels.overnight_low);
        document.getElementById("lvl-prior-rth").textContent =
          formatRange(data.levels.prior_rth_high, data.levels.prior_rth_low);

        const biasCard = document.getElementById("bias-card");
        const biasLabel = document.getElementById("bias-label");
        const biasText = document.getElementById("bias-text");

        biasLabel.textContent = data.bias;
        biasText.textContent = data.action;

        biasCard.classList.remove("bias-long", "bias-short", "bias-neutral");
        if (data.bias.startsWith("LONG")) {
          biasCard.classList.add("bias-long");
        } else if (data.bias.startsWith("SHORT")) {
          biasCard.classList.add("bias-short");
        } else {
          biasCard.classList.add("bias-neutral");
        }

        statusPill.classList.remove("pill-fresh", "pill-stale", "pill-error");
        statusPill.classList.add(data.data_status === "fresh" ? "pill-fresh" : "pill-stale");
        statusText.textContent =
          data.data_status === "fresh" ? "Fresh data · auto-refresh 60s" : "Stale data · check feed";
      } catch (e) {
        statusPill.classList.remove("pill-fresh", "pill-stale");
        statusPill.classList.add("pill-error");
        statusText.textContent = "Data unavailable";
        errorBox.textContent = e.message;
        errorBox.style.display = "block";
      }
    }

    // Initial load
    refreshSnapshot();
    // Auto-refresh every 60 seconds
    setInterval(refreshSnapshot, 60000);
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Serve the lavender-themed single-page dashboard."""
    return render_template_string(TEMPLATE)


@app.route("/api/snapshot")
def api_snapshot():
    """Expose a JSON snapshot of the latest MES levels and bias."""
    try:
        snap = get_snapshot()
        return jsonify(snap)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
