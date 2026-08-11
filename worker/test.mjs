import assert from "node:assert/strict";
import { chooseLiquidContract, futuresContractCandidates, normalizeQuote } from "./src/index.js";

const quote = normalizeQuote("ES", "/ES", {
  symbol: "/ESU26",
  quote: {
    lastPrice: 6789.25,
    bidPrice: 6789,
    askPrice: 6789.25,
    quoteTimeInLong: Date.parse("2026-08-11T15:30:00Z"),
    totalVolume: 123456,
    openInterest: 987654,
  },
  reference: { symbol: "/ESU26", description: "E-mini S&P 500 Sep 2026" },
}, "2026-08-11T15:31:00Z");

assert.equal(quote.last, 6789.25);
assert.equal(quote.symbol, "/ESU26");
assert.equal(quote.quote_time, "2026-08-11T15:30:00.000Z");
assert.equal(quote.delayed, false);

const midpoint = normalizeQuote("ZB", "/ZB", {
  quote: { bidPrice: 117.25, askPrice: 117.28125 },
}, "2026-08-11T15:31:00Z");
assert.equal(midpoint.last, 117.265625);

assert.deepEqual(
  futuresContractCandidates("/ES", new Date("2026-08-11T12:00:00Z")),
  ["/ESU26", "/ESZ26"],
);
assert.equal(chooseLiquidContract([
  { symbol: "/ESU26", volume: 1200, open_interest: 9000 },
  { symbol: "/ESZ26", volume: 1500, open_interest: 4000 },
]).symbol, "/ESZ26");

console.log("Schwab quote normalization tests passed");
