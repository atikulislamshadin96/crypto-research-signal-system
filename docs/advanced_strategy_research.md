# Advanced Crypto Microstructure Research Framework

## Scope and non-claim

This document registers research hypotheses that are more specific than generic moving-average, RSI, or chart-pattern rules. It does **not** claim that any hypothesis is secret, unused, unexploited, or profitable. Public strategies can be crowded, and any apparent edge must survive realistic costs, latency, adverse selection, multiple-testing controls, and untouched out-of-sample evaluation.

The implementation remains **analysis-only**. No private account credentials, order endpoint, or live-execution path is enabled.

## Ranked hypotheses

| Rank | Hypothesis | Causal inputs | Intended role | Current evidence status |
|---:|---|---|---|---|
| 1 | **Toxicity/liquidity-state filter** | Signed trade flow, VPIN-style bucket imbalance, spread, depth imbalance, realized volatility, BTC/ETH cross-asset state | Decide whether to trade, reduce holding time, or widen the required edge | Public research supports market-dynamics predictability, but not profitability of this implementation [1] |
| 2 | **First-passage order-flow continuation/reversal** | Aggressor-side flow, depth imbalance, short-horizon price impact, displacement, first retest | Select only a small number of high-quality entry events | Implementable prospectively from OKX/Bybit public data; historical L2 replay is not yet available |
| 3 | **Perpetual basis/funding dislocation** | Perp-versus-index basis, funding, open interest, mark/index difference, execution-leg cost | Conditional regime or convergence filter, not standalone direction | Academic work motivates the hypothesis; borrow, funding, transfer, and leg costs remain material [2] |
| 4 | **Cross-venue price discovery** | Timestamp-aligned trades/quotes from OKX, Bybit, and another venue | Use the faster venue as a lead signal and the slower venue as execution context | Requires synchronized event data and venue-specific latency; not validated by 2025 OHLCV |
| 5 | **Liquidation-risk state classifier** | Volatility acceleration, OI change, funding extremes, spread/depth deterioration, liquidation proxies | Risk-off filter and holding-period control | Research lead only; not treated as an entry edge [3] |

## What is implemented

The repository now collects optional OKX public order-book and recent-trade snapshots. The parser records bid, ask, midpoint, spread in basis points, depth imbalance, buy volume, sell volume, total volume, signed-volume imbalance, timestamp, source, freshness, and warnings. Missing or malformed values are rejected rather than replaced with zero.

The live scanner attaches these observations to candidate evidence. By default, they are stored as `microstructure_observation` and are **not** allowed to confirm a signal. A research configuration can explicitly set `data.microstructure.use_for_confirmation: true`; in that mode, fresh directional depth/trade-flow evidence becomes a confirmation category and missing confirming microstructure creates a rejection reason.

The historical layer now supports the official Binance Futures monthly `aggTrades` archives. It reduces each source archive into 15-minute buckets containing aggressor-side buy/sell volume, signed volume, taker-buy ratio, trade count, VWAP, and a clearly labeled **signed flow-weighted price-deviation proxy**. This proxy is not Level-2 market impact and must not be described as spread or depth impact. All flow confirmation columns used by the backtester are shifted by one completed bar; missing observations fail closed.

The strict BOS-retest research configuration has an isolated, opt-in flow variant. Its pre-registered thresholds are a taker-buy ratio of at least 0.60 for longs or at most 0.40 for shorts, signed-volume imbalance of at least 0.15 in the relevant direction, and an absolute flow-weighted price-deviation proxy no greater than 15 basis points. The 15-basis-point bound is intentionally conservative only as a research gate; it was not optimized on trade outcomes.

## January 2025 sanity result

A complete BTCUSDT January 2025 official aggregate-trade archive was downloaded and reduced. The source zip was 692,363,439 bytes, its SHA-256 checksum was recorded in the local manifest, and the reduced artifact contained 2,976 15-minute buckets. This is an implementation and data-integrity sanity check, **not** a 2025 performance claim.

| Variant | Trades | Win rate | Average/expectancy R | Profit factor | Interpretation |
|---|---:|---:|---:|---:|---|
| Strict BOS-only | 25 | 20.0% | -0.5952R | 0.421 | Negative January sample |
| Strict BOS + lagged aggregate flow | 16 | 18.75% | -0.6874R | 0.368 | Negative January sample; rejected as a positive hypothesis |

The flow filter reduced the number of trades but did not improve January expectancy. It is therefore **not** a deployment candidate and does not overturn the previously rejected 2025 baseline conclusions. The complete 2025 two-symbol aggregate-trade comparison was not claimed because Binance Vision intermittently stalled during subsequent monthly archive retrieval in this environment. The downloader is resumable and skips completed reduced months; a future run must finish the remaining months before any full-year flow result is reported.

## Data availability boundary

The existing 2025 OHLCV dataset cannot validate order-book imbalance, VPIN, queue position, event-time price impact, or cross-venue lead-lag. Those features require timestamped trades and order-book snapshots/deltas. The aggregate-trade reduction adds an **order-flow proxy**, not historical Level-2 depth. The system must not fabricate L2 fields from candles or treat the aggregate-trade proxy as a spread measurement.

Therefore, there are three separate tracks:

1. **Historical OHLCV research:** evaluate bar-based structure strategies with realistic fees, slippage, funding assumptions, chronological splits, and untouched out-of-sample windows.
2. **Historical aggregate-flow research:** complete the official monthly archive set, freeze thresholds using training data only, and compare the strict BOS baseline against lagged flow confirmation on the same cost model and untouched OOS window.
3. **Prospective microstructure paper research:** collect OKX/Bybit event data, persist raw payloads and reconnect gaps, generate signals only after timestamp alignment, and score outcomes after expiry. No performance claim is allowed until the prospective ledger has sufficient observations and an untouched evaluation period.

## Prospective event collector

The separate `collect-microstructure` command archives public OKX and Bybit WebSocket messages as append-only JSONL files. It records exchange payloads, local receipt time, venue, connection identifier, subscription events, connection errors, cancellation, and sequence-gap events. OKX uses `books5` and `trades`; Bybit uses linear `orderbook.50` and `publicTrade` streams. The collector never calls an order endpoint and never emits a signal.

Sequence tracking is intentionally conservative. A reported previous-sequence mismatch or sequence jump creates an audit event; it does not silently repair the order book. Reconnection uses bounded exponential backoff. The raw archive and audit log must later be replayed into a timestamp-alignment and gap-exclusion pipeline before any paper-trading evaluation.

## Pre-registration rules

A candidate variant must be registered before evaluation with its symbol universe, event horizon, entry delay, spread/impact assumptions, funding treatment, stop/target logic, maximum holding period, and exclusion rules. Thresholds must be selected only on training data. Validation and test periods must remain untouched until the variant is frozen.

A variant is rejected if it depends on unavailable historical inputs, has negative net expectancy after costs in the untouched period, has profit factor below one, is driven by one symbol or one event, lacks minimum trade evidence, or shows instability across walk-forward windows. Lowering the confirmation threshold to manufacture more signals is not an acceptable remedy.

## References

[1]: https://stoye.economics.cornell.edu/docs/Easley_ssrn-4814346.pdf "Easley, O'Hara, Yang, and Zhang, Microstructure and Market Dynamics in Crypto Markets"
[2]: https://ideas.repec.org/p/arx/papers/2212.06888.html "Fundamentals of Perpetual Futures"
[3]: https://arxiv.org/abs/2607.27070 "Research lead on crypto-perpetual liquidation cascades"
[4]: https://www.okx.com/docs-v5/en/ "OKX API documentation"
[5]: https://bybit-exchange.github.io/docs/v5/market/orderbook "Bybit public order-book documentation"
[6]: https://data.binance.vision/ "Binance Vision public historical data"
[7]: https://www.okx.com/historical-data "OKX historical market data"
