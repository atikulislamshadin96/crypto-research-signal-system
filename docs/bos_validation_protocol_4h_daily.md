# Frozen BOS-retest validation protocol

**Author:** Manus AI  
**Status:** Pre-registered research protocol  
**Scope:** BTCUSDT, ETHUSDT, SOLUSDT on 4H and 1D Binance USDⓈ-M Futures OHLCV

## Research question

Does the existing strict `bos_retest_continuation` hypothesis retain positive, cost-adjusted performance across assets, timeframes, chronological out-of-sample windows, and non-overlapping purged combinatorial paths when evaluated without parameter changes after final OOS results are observed?

This document is a validation protocol, not a promise to produce a strategy. The final verdict must be **NO VALIDATED EDGE FOUND** if the hypothesis fails the pre-registered gates.

## Frozen entry definition

The entry rule is the existing strict implementation. A prior completed candle must close beyond a prior swing over a 20-bar structure lookback with displacement at least 1.25 ATR. The current completed candle must be the first directional retest within 0.10 ATR of the break close, close in the continuation direction, satisfy the same structural bias, and have volume ratio at least 1.25. All indicators use completed bars only. The flow filter is disabled and frozen as rejected.

The stop is 1.25 ATR and the first target is 3.00 ATR. The current engine's one-bar latency, conservative stop-first treatment for an ambiguous bar, bounded strategy history, and eight-bar expiry are retained unless a pre-existing implementation defect is discovered. Any defect correction must be documented before rerunning all results.

## Dataset and chronology

The primary historical source is the official Binance Vision USDⓈ-M monthly kline archive. The longest immediately reliable common sample is requested as complete calendar years 2023–2025, subject to file availability and checksum validation. If a month is unavailable or invalid for any asset/timeframe, the common sample is shortened and the missing interval is reported; it is never backfilled with another venue without explicit labeling.

The primary BOS test uses OHLCV only. Hyperliquid funding and Deribit DVOL remain context variables, not entry filters, because adding them to the BOS hypothesis would create a new composite hypothesis and violate the focused validation scope. They may be studied independently later.

## Execution and stress tests

Every asset/timeframe is evaluated using the existing event-driven execution model with fees, slippage, funding, one-bar latency, and stop-first ambiguity. Cost stress is run at total round-trip execution-cost settings of 5, 10, and 15 basis points, with the exact fee/slippage decomposition recorded. No result may be reported gross-only as evidence of a tradable edge.

## Validation design

The chronological report contains a training segment, a validation segment, and an untouched final OOS segment. In addition, at least eight sequential walk-forward OOS windows are created with a one-window purge/embargo around train-test boundaries. Each window records trades, expectancy, win rate, profit factor, maximum drawdown, losing streak, and warnings for low sample size.

Purged CPCV is run only when the asset/timeframe has enough observations and at least the pre-registered minimum number of completed trades. Observations are split into eight chronological groups. Test paths use two groups at a time; training observations overlapping the test interval or within the purge/embargo boundary are removed. CPCV paths are used for distributional uncertainty, not for selecting a favorable path.

The perturbation grid is fixed before final OOS evaluation: structure lookback 18/20/22; minimum displacement 1.125/1.25/1.375 ATR; minimum volume ratio 1.125/1.25/1.375; retest tolerance 0.08/0.10/0.12 ATR; stop 1.125/1.25/1.375 ATR; target 2.70/3.00/3.30 ATR. Perturbations are reported as robustness evidence only. The baseline is not replaced by the best perturbation.

## Acceptance and rejection gates

The hypothesis is not considered validated unless all required gates pass on the aggregate evidence and no material asset/timeframe concentration invalidates the conclusion. The strict pre-registered rejection criteria are:

| Gate | Rejection condition |
|---|---|
| CPCV expectancy | P50 expectancy below +0.05% of risk per trade |
| Walk-forward stability | Four or more of eight OOS windows have negative expectancy |
| Win rate | Below 45% on the relevant OOS aggregate |
| Profit factor | Below 1.20 on the relevant OOS aggregate |
| Costs | Edge disappears at the specified realistic cost stress |
| Sample uncertainty | Confidence interval includes materially negative expectancy with no adequate trade count |
| Asset dependence | Result is driven by one asset or one regime without stable replication |
| Drawdown | Prop-firm simulation breaches the pre-registered daily or total drawdown limits |

A pass at one asset or timeframe is not sufficient to claim a general strategy. A mixed result is reported as mixed, not promoted to paper trading.

## Prop-firm drawdown simulation

For each chronological trade ledger, simulate starting equity of 100,000 units, 0.25% risk per trade, maximum three trades per day, a three-loss cooldown, a 5% daily loss limit, and a 10% total drawdown limit. The simulation is a capital-preservation diagnostic, not a claim about any specific firm's current rules. It records breach frequency, time to breach, maximum drawdown, and the percentage of paths surviving the full sample.

## Separate liquidity-sweep event study

The strict liquidity-sweep-reclaim rule is evaluated as an event label, not as a trading strategy. For each event, forward returns are measured over fixed 1, 3, 6, and 12-bar horizons in the event direction, with volatility normalization and bootstrap confidence intervals. The study reports event frequency, mean/median forward return, hit rate, confidence intervals, and comparison with matched non-event bars. Only an economically meaningful and statistically robust event effect can justify a separately registered strategy hypothesis.

## Reporting rule

No tuning is performed after final OOS results are viewed. The rejected aggressor-flow filter remains frozen. If no hypothesis satisfies all gates, the report must state exactly:

> **NO VALIDATED EDGE FOUND.**

## References

[1]: https://data.binance.vision/ "Binance Data Collection"

[2]: https://github.com/binance/binance-public-data "Binance public-data repository"

[3]: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data "Hyperliquid historical data documentation"

[4]: https://docs.deribit.com/api-reference/market-data/public-get-historical-volatility "Deribit historical volatility API documentation"
