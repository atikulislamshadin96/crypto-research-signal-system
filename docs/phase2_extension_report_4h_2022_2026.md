# Phase 2 Report: New-Asset Extension of Frozen BOS-ReTest Validation

**Author:** Manus AI
**Date:** 2026-08-19
**Scope:** BNBUSDT, XRPUSDT, and ADAUSDT at 4H only. No new assets beyond this Phase 2 family, no threshold tuning, no aggressor-flow rescue, and no paper trading.

## Executive verdict

> **NO VALIDATED EDGE FOUND.**

None of the three Phase 2 assets satisfies the hard validation requirement of at least **50 untouched-OOS trades per asset**. BNBUSDT and XRPUSDT are independently rejected by negative stability and performance evidence. ADAUSDT is also rejected by the frozen stability and uncertainty gates, in addition to being severely underpowered. No Phase 2 asset is approved for paper trading.

This result does not justify silently adding another asset family or tuning the BOS rules. Any further universe expansion would require a separately registered multiple-testing protocol.

## Data and audit coverage

The preferred source was the official Binance USDⓈ-M Futures archive [1] [2]. Each asset used 55 monthly 4H files from January 2022 through July 2026 and 17 daily 4H tail files for August 1–17, 2026. Binance Vision did not expose the August 2026 monthly archive or August 18–19 daily archives at retrieval time, so the honest cutoff is **2026-08-17 23:59:59.999 UTC**.

Every Phase 2 manifest entry matched the normalized CSV file’s SHA-256, byte count, and positive row count. This is **216/216 verified files**: 72 per asset, consisting of 55 monthly files and 17 daily-tail files.

| Asset | Observations | Monthly files | August daily files | Last timestamp | Manifest result |
|---|---:|---:|---:|---|---|
| BNBUSDT | 10,140 | 55 | 17 | 2026-08-17 | 72/72 |
| XRPUSDT | 10,110 | 55 | 17 | 2026-08-17 | 72/72 |
| ADAUSDT | 10,140 | 55 | 17 | 2026-08-17 | 72/72 |

## Frozen protocol and multiple-testing control

The BOS-retest parameters, entry and exit rules, execution model, latency, stop-first ambiguity policy, funding assumption, cost stress, eight walk-forward windows, purged CPCV, 18 pre-registered perturbation variants, bootstrap uncertainty, and prop-firm simulation were unchanged from the prior protocol. The order-flow confirmation filter remained disabled.

The Phase 2 family contained three new asset hypotheses. The registered family-wise alpha was 0.05, with a Bonferroni per-asset threshold of `0.05 / 3 = 0.0166667` for any p-value-based gate. The principal deterministic gate was stricter than this alone: each asset needed at least **50 final untouched-OOS trades** and had to satisfy the pre-existing performance and stability requirements. No OOS result was used to modify the rules.

## Results

| Asset | Final OOS trades | Expectancy | Win rate | Profit factor | Bootstrap P05 | Negative WF windows | CPCV P50 | CPCV positive paths | Base prop-firm return | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BNBUSDT | 19 | -1.085R | 0.00% | 0.000 | -1.102R | 6/8 | -0.270R | 25.0% | -5.03% | **Rejected** |
| XRPUSDT | 28 | -0.329R | 21.43% | 0.605 | -0.700R | 6/8 | -0.240R | 17.9% | -2.29% | **Rejected** |
| ADAUSDT | 14 | +0.172R | 35.71% | 1.257 | -0.555R | 5/8 | -0.038R | 39.3% | +0.59% | **Rejected / underpowered** |

BNBUSDT and XRPUSDT fail even before the sample-size issue is considered: their final OOS expectancy, win rate, profit factor, CPCV median, and walk-forward stability are negative. ADAUSDT has a positive point estimate but fails the 45% win-rate gate, has five negative walk-forward windows, a negative CPCV median, and a negative bootstrap fifth percentile. Its 14 trades cannot support a profitability claim.

## Execution-cost stress

| Asset | 5 bps expectancy | 10 bps expectancy | 15 bps expectancy |
|---|---:|---:|---:|
| BNBUSDT | -1.046R | -1.079R | -1.111R |
| XRPUSDT | -0.302R | -0.325R | -0.347R |
| ADAUSDT | +0.192R | +0.175R | +0.158R |

ADA’s positive cost-stress point estimates do not override the pre-registered trade-count, win-rate, walk-forward, CPCV, and uncertainty failures.

## Decision against the Phase 2 table

| Condition | Outcome |
|---|---|
| Any new asset with 50+ untouched-OOS trades and all gates passing | **None** |
| One validated asset | **No** |
| Multiple validated assets | **No** |
| BNB/XRP/ADA all fail with adequate sample | Not applicable because all remain below 50 trades |
| Any paper trading | **Not authorized** |

Therefore, Phase 2 produces **no validated edge**. BNBUSDT and XRPUSDT should be treated as rejected hypotheses. ADAUSDT should not be promoted from its positive point estimate; it is an underpowered and unstable result that fails the frozen gates. The broader BOS family remains closed for deployment purposes.

## Next-step boundary

The repository will not automatically add more assets, change thresholds, or start paper trading. A future extension would require a new written protocol specifying the full candidate universe, family-wise correction, minimum effective sample, and an untouched holdout that is not reused for selection.

## References

[1]: https://data.binance.vision/ "Binance Data Collection — official public archive"
[2]: https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-futures/api/rest-api/market-data "Binance USDⓈ-M Futures market-data documentation"
