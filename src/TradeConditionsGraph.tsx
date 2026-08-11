import React, { useState } from 'react';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Line, ComposedChart, Bar, ReferenceLine, Area
} from 'recharts';

// ─── Asset-class seasonal data ────────────────────────────────────────────────
const assetClasses = {
  es: {
    label: "ES — E-mini S&P 500",
    ticker: "ES",
    color: "#38bdf8",
    description: "CME E-mini S&P 500 futures. Tracks the S&P 500 index. Driven by earnings seasons, quarterly roll cycles, institutional rebalancing, and the September/October seasonal effect.",
    source: "NinjaTrader 15-yr ES seasonality · S&P 500 data 1928–2025 (RBC, LPL, Yardeni)",
    data: [
      { month:"Jan", fullMonth:"January",   volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Strong institutional re-entry after year-end. January Effect favors small-caps. ES tends to grind higher into late January." },
      { month:"Feb", fullMonth:"February",  volume:"Moderate", volatility:"Moderate", suitability:"Decent",    volumeScore:2, volatilityScore:2, suitabilityScore:2, dayTrading:"Yes",      miniSwing:"Marginal", swingTerm:"Yes",      longTerm:"Yes",      note:"Historically one of the weakest average-return months. Mid-Feb chop is common; first half tends to see pullbacks." },
      { month:"Mar", fullMonth:"March",     volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"One of the best months over the last 10 years. Q1 earnings prep and buyback activity drive institutional buying." },
      { month:"Apr", fullMonth:"April",     volume:"High",     volatility:"Low",      suitability:"Very Good", volumeScore:3, volatilityScore:1, suitabilityScore:4, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Highest avg return of any month (+1.7% since 1928). ES 15-yr seasonal peaks in late April. Q1 earnings catalyst + low vol = prime window." },
      { month:"May", fullMonth:"May",       volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"'Sell in May' is largely overstated in data. ES 15-yr seasonal shows slight weakness late May but overall still positive." },
      { month:"Jun", fullMonth:"June",      volume:"Low",      volatility:"Low",      suitability:"Decent",    volumeScore:1, volatilityScore:1, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Marginal", swingTerm:"Yes",      longTerm:"Yes",      note:"ES 15-yr seasonal shows lower prices through end of June. Buyback blackouts begin mid-June. Summer doldrums start; volume -10–15%." },
      { month:"Jul", fullMonth:"July",      volume:"Low",      volatility:"Low",      suitability:"Good",      volumeScore:1, volatilityScore:1, suitabilityScore:3, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Best avg return since 1928 (+1.7%). ES seasonality rallies in July despite thin volume. Low vol aids trend-following." },
      { month:"Aug", fullMonth:"August",    volume:"Low",      volatility:"High",     suitability:"Difficult", volumeScore:1, volatilityScore:3, suitabilityScore:1, dayTrading:"No",       miniSwing:"No",       swingTerm:"Marginal", longTerm:"Marginal", note:"ES 15-yr seasonal shows lower prices in August. One of two historically negative-average-return months. Low volume amplifies sudden drops." },
      { month:"Sep", fullMonth:"September", volume:"High",     volatility:"High",     suitability:"Difficult", volumeScore:3, volatilityScore:3, suitabilityScore:1, dayTrading:"No",       miniSwing:"No",       swingTerm:"No",       longTerm:"Marginal", note:"Worst month since 1928 (-1.2% avg). ES declines 55%+ of years. Mutual fund tax-loss selling, fiscal year-end, and Fed meetings all collide." },
      { month:"Oct", fullMonth:"October",   volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"ES seasonality recovers sharply in October. Q3 earnings catalyst, buybacks resume, and institutional re-accumulation drives a reliable bounce." },
      { month:"Nov", fullMonth:"November",  volume:"High",     volatility:"Low",      suitability:"Very Good", volumeScore:3, volatilityScore:1, suitabilityScore:4, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Second strongest avg return (+1.5%). ES 15-yr seasonal holds higher prices through all of November. Santa Rally setup begins; window dressing adds fuel." },
      { month:"Dec", fullMonth:"December",  volume:"Moderate", volatility:"Low",      suitability:"Good",      volumeScore:2, volatilityScore:1, suitabilityScore:3, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Santa Claus Rally historically runs the final 5 days + first 2 of January. Tax-loss selling front half, year-end window dressing provides a late-month lift." },
    ]
  },
  zb: {
    label: "ZB — 30-Year T-Bond",
    ticker: "ZB",
    color: "#4ade80",
    description: "CME 30-Year U.S. Treasury Bond futures. Inversely correlated to equity risk. Driven by Fed policy, inflation expectations, flight-to-safety flows, and Treasury auction cycles.",
    source: "MRCI ZB 15-yr seasonal data · TLT seasonality 2015–2024 (TradingView, Barchart)",
    data: [
      { month:"Jan", fullMonth:"January",   volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"ZB/TLT shows consistent positive returns in January. Flight-to-safety positioning after equity year-end, plus coupon reinvestment flows from December bond holdings." },
      { month:"Feb", fullMonth:"February",  volume:"Moderate", volatility:"Moderate", suitability:"Decent",    volumeScore:2, volatilityScore:2, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Mixed month. When equities rally (as they often do in Feb), ZB faces headwinds. Rate expectation repricing after Jan jobs data adds volatility." },
      { month:"Mar", fullMonth:"March",     volume:"High",     volatility:"High",     suitability:"Decent",    volumeScore:3, volatilityScore:3, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Marginal", swingTerm:"Yes",      longTerm:"Yes",      note:"FOMC meeting month. High vol from rate decisions and inflation prints. Historically choppy for ZB; direction is heavily data-dependent." },
      { month:"Apr", fullMonth:"April",     volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"April marks the start of ZB's strongest seasonal window (Apr–Aug). Coupon payment reinvestments and early fiscal-year Treasury demand support prices." },
      { month:"May", fullMonth:"May",       volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Continues the Apr–Aug bullish seasonal. ZB 15-yr seasonal shows consistent upward drift. May refunding auctions create brief dips; then buyers return." },
      { month:"Jun", fullMonth:"June",      volume:"Moderate", volatility:"Low",      suitability:"Good",      volumeScore:2, volatilityScore:1, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"FOMC decision month; outcome-dependent. Historically ZB benefits from summer flight-to-quality as equities thin out. Generally constructive." },
      { month:"Jul", fullMonth:"July",      volume:"Moderate", volatility:"Low",      suitability:"Very Good", volumeScore:2, volatilityScore:1, suitabilityScore:4, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Peak of ZB's bullish seasonal window. 87% hit rate (13/15 years) of ZB closing higher from May through early August per MRCI data. Low equity vol = flight-to-quality flows thin." },
      { month:"Aug", fullMonth:"August",    volume:"Moderate", volatility:"Moderate", suitability:"Good",      volumeScore:2, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Final month of the bullish Apr–Aug window. TLT mixed in August historically, but ZB futures maintain an upward bias into early August before fading. Risk-off equity flows support." },
      { month:"Sep", fullMonth:"September", volume:"High",     volatility:"High",     suitability:"Difficult", volumeScore:3, volatilityScore:3, suitabilityScore:1, dayTrading:"No",       miniSwing:"Marginal", swingTerm:"Marginal", longTerm:"Marginal", note:"Historically weak for ZB. Heavy Treasury issuance (fiscal year-end supply) pressures prices. Despite equity weakness, bond supply overwhelms flight-to-safety demand." },
      { month:"Oct", fullMonth:"October",   volume:"High",     volatility:"High",     suitability:"Difficult", volumeScore:3, volatilityScore:3, suitabilityScore:1, dayTrading:"No",       miniSwing:"No",       swingTerm:"Marginal", longTerm:"Marginal", note:"TLT and ZB show consistent weakness in October. New Treasury issuance continues; equity recovery reduces flight-to-safety. Often the worst month for bond prices." },
      { month:"Nov", fullMonth:"November",  volume:"Moderate", volatility:"Moderate", suitability:"Decent",    volumeScore:2, volatilityScore:2, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Mixed but improving. As equity momentum fades late month, ZB sees renewed interest. FOMC meeting adds event-driven volatility mid-month." },
      { month:"Dec", fullMonth:"December",  volume:"Low",      volatility:"Moderate", suitability:"Good",      volumeScore:1, volatilityScore:2, suitabilityScore:3, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Year-end institutional rotation into safe assets benefits ZB. TLT shows strong performances in December historically. Thin markets can amplify moves." },
    ]
  },
  forex: {
    label: "Forex — Major Pairs",
    ticker: "FX",
    color: "#a78bfa",
    description: "EUR/USD, GBP/USD, USD/JPY and commodity currencies. Driven by central bank cycles, fiscal year flows, and institutional month/quarter-end rebalancing.",
    source: "Post-Bretton Woods data 1971–2025 (StoneX/forex.com, FXEmpire)",
    data: [
      { month:"Jan", fullMonth:"January",   volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"January Effect in FX: currencies of strong-equity countries appreciate. High institutional re-entry from year-end rebalancing. USD/JPY often strengthens." },
      { month:"Feb", fullMonth:"February",  volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Flows normalize. Central bank meeting season begins, driving directional FX moves on major pairs." },
      { month:"Mar", fullMonth:"March",     volume:"High",     volatility:"High",     suitability:"Decent",    volumeScore:3, volatilityScore:3, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Marginal", swingTerm:"Yes",      longTerm:"Yes",      note:"Japan fiscal year ends March 31 — JPY strengthens sharply as repatriation flows surge. High volatility across all major pairs." },
      { month:"Apr", fullMonth:"April",     volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"JPY typically weakens in April as fiscal-year repatriation reverses. Active month for major pairs with cleaner trend setups." },
      { month:"May", fullMonth:"May",       volume:"Moderate", volatility:"High",     suitability:"Decent",    volumeScore:2, volatilityScore:3, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Marginal", swingTerm:"Yes",      longTerm:"Yes",      note:"Historically second-worst month for EUR/USD (-0.62% avg) and GBP/USD (-0.37% avg). Dollar tends to strengthen. Momentum reversals are common." },
      { month:"Jun", fullMonth:"June",      volume:"Moderate", volatility:"Moderate", suitability:"Good",      volumeScore:2, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Month-end and quarter-end rebalancing create consistent institutional flow patterns. FOMC decision adds event-driven setups." },
      { month:"Jul", fullMonth:"July",      volume:"Moderate", volatility:"Low",      suitability:"Decent",    volumeScore:2, volatilityScore:1, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Summer liquidity thins. UK volumes noticeably lower. Spreads widen on major pairs mid-session. Ranges tighten; momentum fades." },
      { month:"Aug", fullMonth:"August",    volume:"Low",      volatility:"High",     suitability:"Difficult", volumeScore:1, volatilityScore:3, suitabilityScore:1, dayTrading:"No",       miniSwing:"No",       swingTerm:"Marginal", longTerm:"Marginal", note:"Weakest month for GBP/USD and AUD/USD historically. FX volumes drop 30–50% in late August. Low liquidity amplifies volatility; unexpected gaps common." },
      { month:"Sep", fullMonth:"September", volume:"High",     volatility:"Moderate", suitability:"Very Good", volumeScore:3, volatilityScore:2, suitabilityScore:4, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"EUR/USD second-best month historically (+0.63% avg over 50+ years). Volume surges back from summer. Strong directional setups form as institutional positioning resumes." },
      { month:"Oct", fullMonth:"October",   volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"EUR/USD historically modestly bullish in October (+0.30% avg). Active month-end rebalancing flows. Good range for swing setups across major pairs." },
      { month:"Nov", fullMonth:"November",  volume:"Moderate", volatility:"Moderate", suitability:"Good",      volumeScore:2, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"MSCI rebalances and quarter-end flows drive institutional activity. USD often strengthens heading into year-end on repatriation flows." },
      { month:"Dec", fullMonth:"December",  volume:"Low",      volatility:"High",     suitability:"Difficult", volumeScore:1, volatilityScore:3, suitabilityScore:1, dayTrading:"No",       miniSwing:"No",       swingTerm:"Marginal", longTerm:"Marginal", note:"FX volumes drop 30–50% in late December. USD typically weakens into year-end as traders lock profits. Thin books cause erratic, stop-hunting price action." },
    ]
  },
  crypto: {
    label: "Crypto — Bitcoin (BTC)",
    ticker: "BTC",
    color: "#fb923c",
    description: "Bitcoin and correlated crypto assets. Driven by halving cycles, macro risk-on/off sentiment, retail participation, and increasingly by institutional positioning.",
    source: "Coinglass BTC data 2013–2025 · Bitcoin Suisse Research · forecaster.biz",
    data: [
      { month:"Jan", fullMonth:"January",   volume:"Moderate", volatility:"High",     suitability:"Decent",    volumeScore:2, volatilityScore:3, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Mixed signals. Longs win ~60% (5-yr) but shorts dominate over 10-yr. Early-year shakeouts are common before trend establishes." },
      { month:"Feb", fullMonth:"February",  volume:"Moderate", volatility:"Moderate", suitability:"Good",      volumeScore:2, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Historically bullish. Long trades win 67–80% across 3, 5, and 10-year lookbacks. Post-January recovery rally typically begins in February." },
      { month:"Mar", fullMonth:"March",     volume:"High",     volatility:"High",     suitability:"Decent",    volumeScore:3, volatilityScore:3, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Seasonally robust but volatile. Strong momentum month historically; wide stops required for short-term strategies." },
      { month:"Apr", fullMonth:"April",     volume:"High",     volatility:"Moderate", suitability:"Good",      volumeScore:3, volatilityScore:2, suitabilityScore:3, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Historically strong. Halving cycle proximity has amplified April performance. Risk appetite generally elevated mid-Q2." },
      { month:"May", fullMonth:"May",       volume:"Moderate", volatility:"High",     suitability:"Decent",    volumeScore:2, volatilityScore:3, suitabilityScore:2, dayTrading:"Marginal", miniSwing:"Marginal", swingTerm:"Yes",      longTerm:"Yes",      note:"Volatile mid-spring. Flash corrections common. Macro events (Fed, CPI) disproportionately amplify BTC moves vs equities." },
      { month:"Jun", fullMonth:"June",      volume:"Moderate", volatility:"Moderate", suitability:"Decent",    volumeScore:2, volatilityScore:2, suitabilityScore:2, dayTrading:"Yes",      miniSwing:"Marginal", swingTerm:"Yes",      longTerm:"Yes",      note:"Mixed history. Some years show significant drawdowns in June; overall neutral-to-slightly-negative on average." },
      { month:"Jul", fullMonth:"July",      volume:"High",     volatility:"Moderate", suitability:"Very Good", volumeScore:3, volatilityScore:2, suitabilityScore:4, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Historically resilient — one of BTC's most consistently bullish months. Ideal for mid-year accumulation. Long trades succeed 70%+ across timeframes." },
      { month:"Aug", fullMonth:"August",    volume:"Moderate", volatility:"High",     suitability:"Difficult", volumeScore:2, volatilityScore:3, suitabilityScore:1, dayTrading:"No",       miniSwing:"No",       swingTerm:"Marginal", longTerm:"Marginal", note:"Average return -0.54%. Historically weak alongside September. Volatility spikes in both directions; whipsaws frequent." },
      { month:"Sep", fullMonth:"September", volume:"Moderate", volatility:"High",     suitability:"Difficult", volumeScore:2, volatilityScore:3, suitabilityScore:1, dayTrading:"No",       miniSwing:"No",       swingTerm:"No",       longTerm:"Marginal", note:"Worst month for BTC: -3.77% avg over 12 years (Coinglass 2013–2025). Short setups win 80–100% historically. Avoid new longs." },
      { month:"Oct", fullMonth:"October",   volume:"High",     volatility:"High",     suitability:"Very Good", volumeScore:3, volatilityScore:3, suitabilityScore:4, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"'Uptober': avg gains exceed 21%. One of the strongest months for BTC longs. High vol + high momentum = scalping and swing both viable." },
      { month:"Nov", fullMonth:"November",  volume:"High",     volatility:"High",     suitability:"Very Good", volumeScore:3, volatilityScore:3, suitabilityScore:4, dayTrading:"Yes",      miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Best month for BTC historically: +46% avg return. Institutional and retail momentum compounds. All strategies viable but size risk appropriately given volatility." },
      { month:"Dec", fullMonth:"December",  volume:"Moderate", volatility:"High",     suitability:"Good",      volumeScore:2, volatilityScore:3, suitabilityScore:3, dayTrading:"Marginal", miniSwing:"Yes",      swingTerm:"Yes",      longTerm:"Yes",      note:"Often strong late Dec (Santa Rally parallel). Year-end positioning and retail inflows support price. Tax-loss selling creates dip opportunities early month." },
    ]
  }
};

const strategies = [
  { key:"dayTrading", label:"Day Trading", color:"#38bdf8" },
  { key:"miniSwing",  label:"Mini Swing",  color:"#a78bfa" },
  { key:"swingTerm",  label:"Swing Term",  color:"#f472b6" },
  { key:"longTerm",   label:"Long Term",   color:"#fbbf24" },
];

const strategyScore = { "Yes": 3, "Marginal": 2, "No": 1 };

const suitabilityMeta = {
  1: { label:"Difficult",  color:"#ef4444", glyph:"▼" },
  2: { label:"Decent",     color:"#f59e0b", glyph:"◆" },
  3: { label:"Good",       color:"#22d3ee", glyph:"▲" },
  4: { label:"Very Good",  color:"#4ade80", glyph:"★" },
};
const suitabilityOrder = [4, 3, 2, 1];

const fitMeta = {
  "Yes":      { bg:"rgba(74,222,128,0.15)",  border:"#4ade80", text:"#4ade80", dot:"●" },
  "Marginal": { bg:"rgba(251,191,36,0.15)",  border:"#fbbf24", text:"#fbbf24", dot:"◐" },
  "No":       { bg:"rgba(239,68,68,0.12)",   border:"#ef4444", text:"#ef4444", dot:"○" },
};

// ─── Sub-components ───────────────────────────────────────────────────────────

const ScoreBar = ({ score, max=3, color }) => (
  <div style={{ height:5, background:"rgba(255,255,255,0.08)", borderRadius:3, flex:1 }}>
    <div style={{ height:5, width:`${(score/max)*100}%`, background:color, borderRadius:3 }} />
  </div>
);

const Pill = ({ value }) => {
  const m = fitMeta[value];
  return (
    <span style={{
      background:m.bg, border:`1px solid ${m.border}`, color:m.text,
      borderRadius:4, padding:"2px 7px", fontSize:10, fontWeight:700,
      letterSpacing:"0.04em", display:"inline-block", minWidth:58, textAlign:"center",
    }}>{m.dot} {value}</span>
  );
};

const MonthCard = ({ d, acColor, onClose }) => {
  const suit = suitabilityMeta[d.suitabilityScore];
  return (
    <div style={{
      background:"linear-gradient(135deg,#1e2942 0%,#141b2d 100%)",
      border:`1px solid ${acColor}40`, borderRadius:12, padding:"18px 22px",
      marginBottom:16, position:"relative", boxShadow:"0 8px 32px rgba(0,0,0,0.4)",
    }}>
      <button onClick={onClose} style={{ position:"absolute", top:12, right:14, background:"none", border:"none", color:"#64748b", cursor:"pointer", fontSize:16 }}>✕</button>
      <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:10 }}>
        <span style={{ color:suit.color, fontSize:20 }}>{suit.glyph}</span>
        <div>
          <div style={{ color:"#e2e8f0", fontWeight:800, fontSize:16 }}>{d.fullMonth}</div>
          <div style={{ color:suit.color, fontSize:11, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase" }}>{suit.label}</div>
        </div>
      </div>
      <p style={{ color:"#94a3b8", fontSize:12, marginBottom:14, lineHeight:1.65 }}>{d.note}</p>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:6 }}>
        {strategies.map(s => (
          <div key={s.key} style={{ textAlign:"center" }}>
            <div style={{ color:"#64748b", fontSize:9, textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:4 }}>{s.label.split(" ")[0]}</div>
            <Pill value={d[s.key]} />
          </div>
        ))}
      </div>
    </div>
  );
};

const ChartTooltip = ({ active, payload, acColor }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const suit = suitabilityMeta[d.suitabilityScore];
  return (
    <div style={{ background:"#1e2942", border:`1px solid ${acColor}50`, borderRadius:8, padding:"12px 16px", boxShadow:"0 8px 24px rgba(0,0,0,0.5)", maxWidth:230 }}>
      <div style={{ color:"#e2e8f0", fontWeight:700, marginBottom:6 }}>{d.fullMonth}</div>
      <div style={{ color:"#94a3b8", fontSize:11, marginBottom:8, lineHeight:1.55 }}>{d.note}</div>
      <div style={{ borderTop:"1px solid #1e2d42", paddingTop:8, display:"flex", flexDirection:"column", gap:3 }}>
        <div style={{ color:"#64748b", fontSize:11 }}>Volume: <span style={{ color:"#e2e8f0", fontWeight:600 }}>{d.volume}</span></div>
        <div style={{ color:"#64748b", fontSize:11 }}>Volatility: <span style={{ color:"#e2e8f0", fontWeight:600 }}>{d.volatility}</span></div>
        <div style={{ color:"#64748b", fontSize:11 }}>Suitability: <span style={{ color:suit.color, fontWeight:700 }}>{suit.label}</span></div>
      </div>
    </div>
  );
};

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function TradeConditionsGraph() {
  const [activeAsset, setActiveAsset] = useState("es");
  const [activeTab, setActiveTab]     = useState("conditions");
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [heatFilter, setHeatFilter]   = useState(null);

  const asset   = assetClasses[activeAsset];
  const data    = asset.data;
  const acColor = asset.color;

  const selectedData = selectedMonth ? data.find(d => d.fullMonth === selectedMonth) : null;

  const primeCount  = data.filter(d => d.suitabilityScore >= 3).length;
  const dangerCount = data.filter(d => d.suitabilityScore <= 1).length;
  const bestLabel   = data.filter(d => d.suitabilityScore >= 3).map(d => d.month).join(", ");
  const avoidLabel  = data.filter(d => d.suitabilityScore <= 1).map(d => d.month).join(", ");

  const tabs = [
    { id:"conditions", label:"Conditions" },
    { id:"heatmap",    label:"Heatmap"    },
    { id:"scorecard",  label:"Scorecard"  },
  ];

  const assetKeys = Object.keys(assetClasses);

  return (
    <div style={{ fontFamily:"'Inter','Segoe UI',system-ui,sans-serif", background:"#0d1424", minHeight:"100vh", color:"#e2e8f0", padding:"20px 16px" }}>
      <div style={{ maxWidth:880, margin:"0 auto" }}>

        <nav style={{ display:"flex", gap:8, flexWrap:"wrap", justifyContent:"flex-end", marginBottom:16 }}>
          <a href="trade-board.html" style={{ color:"#e2e8f0", background:"#172033", border:"1px solid #2d3f60", borderRadius:8, padding:"7px 12px", textDecoration:"none", fontSize:11, fontWeight:700 }}>Live Trade Board</a>
          <a href="trading-template-es.html" style={{ color:"#94a3b8", background:"#111827", border:"1px solid #1e2d42", borderRadius:8, padding:"7px 12px", textDecoration:"none", fontSize:11, fontWeight:700 }}>Full ES Worksheet</a>
          <a href="trading-template-zb.html" style={{ color:"#94a3b8", background:"#111827", border:"1px solid #1e2d42", borderRadius:8, padding:"7px 12px", textDecoration:"none", fontSize:11, fontWeight:700 }}>Full ZB Worksheet</a>
        </nav>

        {/* ── Header ── */}
        <div style={{ marginBottom:20 }}>
          <div style={{ color:acColor, fontSize:10, fontWeight:700, letterSpacing:"0.15em", textTransform:"uppercase", marginBottom:4 }}>
            Seasonal Trading Intelligence
          </div>
          <h1 style={{ margin:"0 0 6px", fontSize:24, fontWeight:800, letterSpacing:"-0.02em", color:"#f1f5f9" }}>
            Market Conditions Calendar
          </h1>
          <p style={{ color:"#64748b", fontSize:12, margin:0 }}>
            Month-by-month volume, volatility & strategy fit — by asset class.
          </p>
        </div>

        {/* ── Asset Selector ── */}
        <div style={{ display:"flex", gap:8, marginBottom:14, flexWrap:"wrap" }}>
          {assetKeys.map(key => {
            const ac = assetClasses[key];
            const active = activeAsset === key;
            return (
              <button key={key} onClick={() => { setActiveAsset(key); setSelectedMonth(null); setHeatFilter(null); }} style={{
                background: active ? `${ac.color}18` : "rgba(255,255,255,0.03)",
                border:`1px solid ${active ? ac.color : "#1e2d42"}`,
                borderRadius:8, padding:"7px 14px", cursor:"pointer",
                color: active ? ac.color : "#64748b",
                fontSize:12, fontWeight:700, transition:"all 0.2s",
                display:"flex", alignItems:"center", gap:6,
              }}>
                <span style={{ fontFamily:"monospace", fontSize:11, opacity:0.8 }}>{ac.ticker}</span>
                {ac.label.split("—")[1]?.trim()}
              </button>
            );
          })}
        </div>

        {/* Asset description */}
        <div style={{ background:"rgba(255,255,255,0.02)", border:"1px solid #1e2d42", borderRadius:8, padding:"10px 14px", marginBottom:14, display:"flex", flexWrap:"wrap", justifyContent:"space-between", gap:8 }}>
          <p style={{ color:"#94a3b8", fontSize:12, margin:0, flex:1 }}>{asset.description}</p>
          <span style={{ color:"#2d3f60", fontSize:10, alignSelf:"flex-end", flexShrink:0, textAlign:"right" }}>{asset.source}</span>
        </div>

        {/* ── Summary Badges ── */}
        <div style={{ display:"flex", gap:10, marginBottom:20, flexWrap:"wrap" }}>
          <div style={{ background:`${acColor}10`, border:`1px solid ${acColor}28`, borderRadius:8, padding:"8px 14px", display:"flex", alignItems:"center", gap:10 }}>
            <span style={{ color:acColor, fontWeight:800, fontSize:18 }}>{primeCount}</span>
            <div>
              <div style={{ color:"#64748b", fontSize:9, textTransform:"uppercase", letterSpacing:"0.08em" }}>Good+ months</div>
              <div style={{ color:"#4ade80", fontSize:11 }}>{bestLabel}</div>
            </div>
          </div>
          {dangerCount > 0 && (
            <div style={{ background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.2)", borderRadius:8, padding:"8px 14px", display:"flex", alignItems:"center", gap:10 }}>
              <span style={{ color:"#ef4444", fontWeight:800, fontSize:18 }}>{dangerCount}</span>
              <div>
                <div style={{ color:"#64748b", fontSize:9, textTransform:"uppercase", letterSpacing:"0.08em" }}>Difficult months</div>
                <div style={{ color:"#ef4444", fontSize:11 }}>{avoidLabel}</div>
              </div>
            </div>
          )}
        </div>

        {/* ── Tabs ── */}
        <div style={{ display:"flex", gap:3, background:"rgba(255,255,255,0.03)", borderRadius:10, padding:3, border:"1px solid #1e2d42", marginBottom:20 }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              flex:1, padding:"8px 10px", borderRadius:7, border:"none", cursor:"pointer",
              fontSize:12, fontWeight:600, transition:"all 0.2s",
              background: activeTab===t.id ? "#1e2942" : "transparent",
              color: activeTab===t.id ? acColor : "#64748b",
              boxShadow: activeTab===t.id ? "0 2px 8px rgba(0,0,0,0.3)" : "none",
            }}>{t.label}</button>
          ))}
        </div>

        {/* ── Month Detail Card ── */}
        {selectedData && <MonthCard d={selectedData} acColor={acColor} onClose={() => setSelectedMonth(null)} />}

        {/* ─── Conditions Chart ──────────────────────────────────────────── */}
        {activeTab==="conditions" && (
          <div style={{ background:"#111827", border:"1px solid #1e2d42", borderRadius:12, padding:"16px 14px 8px" }}>
            <div style={{ color:"#64748b", fontSize:11, marginBottom:8 }}>Click any bar or point to inspect a month →</div>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data} margin={{ top:10, right:10, left:-10, bottom:4 }}
                onClick={e => e?.activePayload && setSelectedMonth(e.activePayload[0].payload.fullMonth)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d42" />
                <XAxis dataKey="month" tick={{ fill:"#64748b", fontSize:11 }} axisLine={{ stroke:"#1e2d42" }} />
                <YAxis domain={[0,3]} ticks={[1,2,3]}
                  tickFormatter={v => ({ 1:"Low", 2:"Med", 3:"High" }[v] || "")}
                  tick={{ fill:"#64748b", fontSize:10 }} axisLine={{ stroke:"#1e2d42" }} width={36} />
                <Tooltip content={<ChartTooltip acColor={acColor} />} />
                <ReferenceLine y={2} stroke="#2d3f60" strokeDasharray="4 4" />
                <Bar dataKey="volumeScore"     name="Volume"     fill="#1d4ed8" radius={[3,3,0,0]} barSize={13} opacity={0.85} cursor="pointer" />
                <Bar dataKey="volatilityScore" name="Volatility" fill="#be123c" radius={[3,3,0,0]} barSize={13} opacity={0.85} cursor="pointer" />
                <Area type="monotone" dataKey="suitabilityScore" name="Suitability"
                  fill={`${acColor}10`} stroke={acColor} strokeWidth={2.5}
                  dot={{ r:4, fill:acColor, stroke:"#0d1424", strokeWidth:2 }} />
              </ComposedChart>
            </ResponsiveContainer>
            <div style={{ display:"flex", gap:16, marginTop:8, padding:"10px 4px", borderTop:"1px solid #1e2d42", flexWrap:"wrap" }}>
              {[
                { color:"#1d4ed8", label:"Volume (liquidity)" },
                { color:"#be123c", label:"Volatility (risk)"  },
                { color:acColor,   label:"Suitability (overall)" },
              ].map(({ color, label }) => (
                <div key={label} style={{ display:"flex", alignItems:"center", gap:6, fontSize:11, color:"#64748b" }}>
                  <span style={{ width:10, height:10, borderRadius:2, background:color, display:"inline-block" }} />
                  {label}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── Heatmap ───────────────────────────────────────────────────── */}
        {activeTab==="heatmap" && (
          <div style={{ background:"#111827", border:"1px solid #1e2d42", borderRadius:12, overflow:"hidden" }}>
            <div style={{ display:"flex", gap:8, padding:"12px 16px", borderBottom:"1px solid #1e2d42", flexWrap:"wrap", alignItems:"center" }}>
              <span style={{ color:"#64748b", fontSize:11, marginRight:2 }}>Filter:</span>
              {["Yes","Marginal","No"].map(f => {
                const m = fitMeta[f];
                return (
                  <button key={f} onClick={() => setHeatFilter(heatFilter===f ? null : f)} style={{
                    background: heatFilter===f ? m.bg : "rgba(255,255,255,0.04)",
                    border:`1px solid ${heatFilter===f ? m.border : "#2d3f60"}`,
                    borderRadius:20, padding:"3px 12px",
                    color: heatFilter===f ? m.text : "#64748b",
                    fontSize:11, fontWeight:600, cursor:"pointer", transition:"all 0.2s",
                  }}>{m.dot} {f}</button>
                );
              })}
            </div>
            <div style={{ overflowX:"auto" }}>
              <table style={{ width:"100%", borderCollapse:"collapse", minWidth:500 }}>
                <thead>
                  <tr style={{ background:"#0d1424" }}>
                    <th style={{ padding:"10px 14px", textAlign:"left", color:"#64748b", fontSize:10, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", borderBottom:"1px solid #1e2d42" }}>Month</th>
                    <th style={{ padding:"10px 8px", textAlign:"center", color:"#64748b", fontSize:10, fontWeight:700, textTransform:"uppercase", letterSpacing:"0.06em", borderBottom:"1px solid #1e2d42" }}>Fit</th>
                    {strategies.map(s => (
                      <th key={s.key} style={{ padding:"10px 6px", textAlign:"center", borderBottom:"1px solid #1e2d42" }}>
                        <span style={{ color:s.color, fontSize:10, fontWeight:700 }}>{s.label}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.map((d, i) => {
                    const suit = suitabilityMeta[d.suitabilityScore];
                    const highlighted = !heatFilter || strategies.some(s => d[s.key]===heatFilter);
                    return (
                      <tr key={d.month} onClick={() => setSelectedMonth(d.fullMonth)}
                        style={{ background: i%2===0 ? "rgba(255,255,255,0.01)" : "transparent", opacity: heatFilter&&!highlighted ? 0.2 : 1, cursor:"pointer", transition:"all 0.15s" }}
                        onMouseEnter={e => e.currentTarget.style.background=`${acColor}08`}
                        onMouseLeave={e => e.currentTarget.style.background = i%2===0 ? "rgba(255,255,255,0.01)" : "transparent"}
                      >
                        <td style={{ padding:"9px 14px", fontWeight:700, color:"#e2e8f0", fontSize:12, borderBottom:"1px solid #1e2d42" }}>{d.fullMonth}</td>
                        <td style={{ padding:"9px 8px", textAlign:"center", borderBottom:"1px solid #1e2d42" }}>
                          <span style={{ color:suit.color, fontWeight:800, title:suit.label }}>{suit.glyph}</span>
                        </td>
                        {strategies.map(s => {
                          const m = fitMeta[d[s.key]];
                          const dimmed = heatFilter && d[s.key]!==heatFilter;
                          return (
                            <td key={s.key} style={{ padding:"6px 5px", textAlign:"center", borderBottom:"1px solid #1e2d42" }}>
                              <div style={{
                                background: dimmed ? "rgba(255,255,255,0.03)" : m.bg,
                                border:`1px solid ${dimmed ? "#1e2d42" : m.border}`,
                                color: dimmed ? "#334155" : m.text,
                                borderRadius:4, padding:"3px 4px", fontSize:10, fontWeight:700, transition:"all 0.2s",
                              }}>{d[s.key]}</div>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ─── Scorecard ─────────────────────────────────────────────────── */}
        {activeTab==="scorecard" && (
          <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
            {data.map((d, i) => {
              const suit = suitabilityMeta[d.suitabilityScore];
              const totalYes  = strategies.filter(s => d[s.key]==="Yes").length;
              const totalMarg = strategies.filter(s => d[s.key]==="Marginal").length;
              return (
                <div key={d.month} onClick={() => setSelectedMonth(d.fullMonth)}
                  style={{ background:"#111827", border:"1px solid #1e2d42", borderRadius:10, padding:"12px 16px", cursor:"pointer", transition:"border-color 0.2s" }}
                  onMouseEnter={e => e.currentTarget.style.borderColor=acColor+"60"}
                  onMouseLeave={e => e.currentTarget.style.borderColor="#1e2d42"}
                >
                  <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:8 }}>
                    <span style={{ color:suit.color, fontSize:16, width:18, textAlign:"center" }}>{suit.glyph}</span>
                    <div style={{ flex:1 }}>
                      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"baseline" }}>
                        <span style={{ fontWeight:700, color:"#e2e8f0", fontSize:13 }}>{d.fullMonth}</span>
                        <span style={{ fontSize:11 }}>
                          {totalYes>0  && <span style={{ color:"#4ade80", marginRight:6 }}>✓{totalYes}</span>}
                          {totalMarg>0 && <span style={{ color:"#fbbf24", marginRight:6 }}>◐{totalMarg}</span>}
                          <span style={{ color:"#64748b" }}>/{strategies.length}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                  <div style={{ display:"flex", gap:10, alignItems:"center", flexWrap:"wrap" }}>
                    <div style={{ flex:1, minWidth:140 }}>
                      {[
                        { label:"Volume",     score:d.volumeScore,     text:d.volume,     color:"#1d4ed8" },
                        { label:"Volatility", score:d.volatilityScore, text:d.volatility, color:"#be123c" },
                      ].map(({ label, score, text, color }) => (
                        <div key={label} style={{ display:"flex", alignItems:"center", gap:6, marginBottom:3 }}>
                          <span style={{ color:"#64748b", fontSize:9, width:52, textAlign:"right", textTransform:"uppercase", letterSpacing:"0.06em" }}>{label}</span>
                          <ScoreBar score={score} max={3} color={color} />
                          <span style={{ color:"#94a3b8", fontSize:10, width:46 }}>{text}</span>
                        </div>
                      ))}
                    </div>
                    <div style={{ display:"flex", gap:4 }}>
                      {strategies.map(s => {
                        const m = fitMeta[d[s.key]];
                        return (
                          <div key={s.key} style={{ textAlign:"center" }}>
                            <div style={{ color:"#64748b", fontSize:8, marginBottom:2, textTransform:"uppercase", letterSpacing:"0.05em" }}>{s.label.split(" ")[0]}</div>
                            <div style={{ width:34, height:24, background:m.bg, border:`1px solid ${m.border}`, borderRadius:4, display:"flex", alignItems:"center", justifyContent:"center", color:m.text, fontSize:9, fontWeight:700 }}>
                              {d[s.key]==="Marginal" ? "MRG" : d[s.key]}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Footer ── */}
        <div style={{ marginTop:24, padding:"14px 0", borderTop:"1px solid #1e2d42", display:"flex", flexWrap:"wrap", gap:20, justifyContent:"space-between", alignItems:"flex-start" }}>
          <div>
            <div style={{ color:"#64748b", fontSize:9, textTransform:"uppercase", letterSpacing:"0.1em", marginBottom:5 }}>Strategy Fit</div>
            <div style={{ display:"flex", gap:12 }}>
              {["Yes","Marginal","No"].map(f => {
                const m = fitMeta[f];
                return (
                  <div key={f} style={{ display:"flex", alignItems:"center", gap:4, fontSize:11 }}>
                    <span style={{ color:m.text, fontWeight:800 }}>{m.dot}</span>
                    <span style={{ color:"#64748b" }}>{f}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div>
            <div style={{ color:"#64748b", fontSize:9, textTransform:"uppercase", letterSpacing:"0.1em", marginBottom:5 }}>Suitability</div>
            <div style={{ display:"flex", gap:12 }}>
              {suitabilityOrder.map(k => {
                const m = suitabilityMeta[k];
                return (
                  <div key={m.label} style={{ display:"flex", alignItems:"center", gap:4, fontSize:11 }}>
                    <span style={{ color:m.color, fontWeight:800 }}>{m.glyph}</span>
                    <span style={{ color:"#64748b" }}>{m.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div style={{ color:"#1e3a5f", fontSize:10, alignSelf:"flex-end" }}>Historical averages — not a guarantee of future results.</div>
        </div>

      </div>
    </div>
  );
}
