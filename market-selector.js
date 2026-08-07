(function () {
  const checkLabels = {
    htf_direction: "HTF direction",
    ema_alignment: "EMA 20/50 aligned",
    vwap_alignment: "VWAP aligned",
    meaningful_level: "At meaningful level",
    room_to_target: "Room to target",
    confirmed_reaction: "1-2 five-minute closes"
  };

  function addStyles() {
    if (document.getElementById("market-selector-styles")) return;
    const style = document.createElement("style");
    style.id = "market-selector-styles";
    style.textContent = `
      .market-selector { margin: 0 0 18px; padding: 18px; background: #fff; border: 1px solid #e0e0ee; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,.04); }
      .market-selector__head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:14px; }
      .market-selector__title { font-size:1rem; font-weight:750; }
      .market-selector__note { color:#666; font-size:.78rem; margin-top:3px; }
      .market-selector__decision { padding:7px 12px; border-radius:999px; font-weight:750; white-space:nowrap; background:#fff3cd; color:#765b00; }
      .market-selector__decision.trade { background:#daf5e8; color:#17663b; }
      .market-selector__decision.skip { background:#fbe1e1; color:#8a2929; }
      .market-selector table { width:100%; border-collapse:collapse; font-size:.82rem; }
      .market-selector th, .market-selector td { padding:8px 7px; text-align:left; border-top:1px solid #ececf3; vertical-align:top; }
      .market-selector th:not(:first-child), .market-selector td:not(:first-child) { width:34%; }
      .market-selector__pass { color:#168a55; font-weight:750; }
      .market-selector__fail { color:#a23b3b; font-weight:750; }
      .market-selector__evidence { display:block; color:#70707b; font-size:.72rem; font-weight:400; margin-top:2px; }
      .market-selector__score { font-weight:800; }
      @media (max-width:640px) {
        .market-selector__head { flex-direction:column; }
        .market-selector { overflow-x:auto; }
        .market-selector table { min-width:590px; }
      }
      @media print { .market-selector { box-shadow:none; break-inside:avoid; } }
    `;
    document.head.appendChild(style);
  }

  function cell(check) {
    const td = document.createElement("td");
    const mark = document.createElement("span");
    mark.className = check?.pass ? "market-selector__pass" : "market-selector__fail";
    mark.textContent = check?.pass ? "✓ Pass" : "✕ No";
    const evidence = document.createElement("span");
    evidence.className = "market-selector__evidence";
    evidence.textContent = check?.evidence || "No evidence available";
    td.append(mark, evidence);
    return td;
  }

  window.renderMarketSelector = function renderMarketSelector(snapshot) {
    const instruments = snapshot?.instruments;
    if (!instruments?.ES?.selector || !instruments?.ZB?.selector) return;
    addStyles();

    let panel = document.getElementById("market-selector-panel");
    if (!panel) {
      panel = document.createElement("section");
      panel.id = "market-selector-panel";
      panel.className = "market-selector";
      const anchor = document.querySelector(".auto-context") || document.querySelector(".layout");
      anchor?.parentNode.insertBefore(panel, anchor);
    }
    panel.replaceChildren();

    const selection = snapshot.market_selection || {};
    const head = document.createElement("div");
    head.className = "market-selector__head";
    const heading = document.createElement("div");
    heading.innerHTML = '<div class="market-selector__title">Daily ES vs ZB Market Selector</div><div class="market-selector__note">5–6 = A+ · 4 = wait for confirmation · 0–3 = skip. Delayed data; confirm live order flow before entry.</div>';
    const decision = document.createElement("div");
    decision.className = "market-selector__decision";
    if ((selection.decision || "").startsWith("TRADE")) decision.classList.add("trade");
    if ((selection.decision || "").startsWith("SKIP")) decision.classList.add("skip");
    decision.textContent = selection.decision || "WAIT";
    decision.title = selection.reason || "";
    head.append(heading, decision);
    panel.appendChild(head);

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    ["Check", `ES · ${instruments.ES.selector.decision_time}`, `ZB · ${instruments.ZB.selector.decision_time}`].forEach((text) => {
      const th = document.createElement("th");
      th.textContent = text;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    Object.entries(checkLabels).forEach(([key, label]) => {
      const row = document.createElement("tr");
      const name = document.createElement("td");
      name.textContent = label;
      row.append(name, cell(instruments.ES.selector.checks[key]), cell(instruments.ZB.selector.checks[key]));
      tbody.appendChild(row);
    });
    const scoreRow = document.createElement("tr");
    const scoreLabel = document.createElement("td");
    scoreLabel.className = "market-selector__score";
    scoreLabel.textContent = "Total / decision";
    scoreRow.appendChild(scoreLabel);
    ["ES", "ZB"].forEach((key) => {
      const selector = instruments[key].selector;
      const td = document.createElement("td");
      td.className = "market-selector__score";
      td.textContent = `${selector.score}/6 · ${selector.rating} · ${selector.direction}`;
      scoreRow.appendChild(td);
    });
    tbody.appendChild(scoreRow);
    table.appendChild(tbody);
    panel.appendChild(table);

    const select = document.getElementById("instrument");
    if (select && selection.decision?.startsWith("TRADE") && selection.market && select.value !== selection.market) {
      select.value = selection.market;
    }
  };
})();
