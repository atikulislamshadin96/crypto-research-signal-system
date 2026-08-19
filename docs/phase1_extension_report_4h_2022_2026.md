# Phase 1 Extension Report: Frozen BOS-ReTest Validation

**Author:** Manus AI  
**Date:** 2026-08-19  
**Scope:** BTCUSDT, ETHUSDT, and SOLUSDT at 4H only. No new assets, no threshold tuning, no aggressor-flow rescue, and no paper trading.

## Executive verdict

> **Phase 1 did not validate the BOS-retest hypothesis.**

BTCUSDT remains rejected. ETHUSDT and SOLUSDT remain **inconclusive because they are still underpowered**, despite positive point estimates. No asset meets the precommitted conditions for paper trading.

The current decision is therefore neither forced acceptance nor premature death of the entire implementation:

> **BTC 4H: rejected. ETH 4H: inconclusive. SOL 4H: inconclusive. No paper trading.**

## Data period and source availability

The study used official Binance USDⓈ-M Futures 4H archives from January 2022 through July 2026, supplemented by official daily 4H archives for August 1–17, 2026. Binance Vision did not expose the August 2026 monthly archive or the August 18–19 daily archives at retrieval time, so the honest cutoff is **2026-08-17 23:59:59.999 UTC**, not August 19 [1].

All 55 monthly files and all 17 August daily-tail files per asset were present, row-count consistent, and SHA-256 matched the normalized CSV bytes recorded in their manifests. The three assets therefore have 72 verified files each: 55 monthly plus 17 daily-tail files.

| Asset | Observations | First timestamp | Last timestamp | Monthly files | Daily tail files |
|---|---:|---|---|---:|---:|
| BTCUSDT | 10,140 | 2022-01-01 | 2026-08-17 | 55 | 17 |
| ETHUSDT | 10,140 | 2022-01-01 | 2026-08-17 | 55 | 17 |
| SOLUSDT | 10,110 | 2022-01-01 | 2026-08-17 | 55 | 17 |

The kline normalizer was also hardened for headerless Binance historical CSVs. It uses Binance’s documented positional kline schema and does not infer market values.

## Frozen protocol

The existing strict BOS-retest rules were used unchanged. The rejected historical aggressor-flow filter remained explicitly disabled. The execution model remained closed-bar, event-driven, stop-first on ambiguous bars, and included the same funding and slippage assumptions. The validation runner used the same 5/10/15 bps cost stress, eight walk-forward windows, purged CPCV, 18 one-at-a-time parameter perturbation variants, 5,000-iteration bootstrap uncertainty, and prop-firm risk simulation as the prior focused protocol.

The final untouched OOS trade-count review threshold remained 30 trades. A result below that threshold cannot be promoted to a validated strategy regardless of its point estimate.

## Results

| Asset | Final OOS trades | Final OOS expectancy | Win rate | Profit factor | Bootstrap P05 | 5 bps expectancy | 10 bps expectancy | 15 bps expectancy | Negative WF windows | CPCV P50 | CPCV positive paths | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BTCUSDT | 16 | -0.040R | 31.25% | 0.947 | -0.675R | +0.007R | -0.032R | -0.071R | 4/8 | -0.003R | 50.0% | **Rejected** |
| ETHUSDT | 25 | +0.296R | 40.00% | 1.465 | -0.247R | +0.325R | +0.301R | +0.277R | 2/8 | +0.381R | 96.4% | **Inconclusive; underpowered** |
| SOLUSDT | 12 | +0.936R | 58.33% | 3.130 | +0.083R | +0.958R | +0.940R | +0.922R | 3/8 | +0.416R | 85.7% | **Inconclusive; underpowered** |

The positive ETH and SOL point estimates are not enough to validate the hypothesis. ETH has only 25 final untouched-OOS trades and a final-OOS win rate below the frozen 45% gate; its bootstrap P05 is also negative. SOL has only 12 final untouched-OOS trades. The positive SOL bootstrap P05 does not overcome the severe sample-size limitation.

BTC fails independently on negative final-OOS expectancy, sub-45% win rate, sub-1.20 profit factor, four negative walk-forward windows, a non-positive CPCV median, and a negative bootstrap P05.

The prop-firm simulation did not hit its hard drawdown or daily-loss limits in the final ledgers, but survival of a low-risk simulation is not evidence of predictive edge. Final simulated returns were approximately -0.17% for BTC, +1.85% for ETH, and +2.83% for SOL under the base execution assumptions.

## Decision against the precommitted table

| Precommitted condition | Phase 1 outcome |
|---|---|
| ETH 4H with 50+ trades and all gates passing | Not reached: 25 trades and win-rate/bootstrap failures |
| SOL 4H with 30+ trades and all gates passing | Not reached: 12 trades |
| Both validated | No |
| One validated | No |
| Both fail with adequate sample | Not yet applicable because ETH/SOL remain underpowered |
| Still underpowered | **Yes** |

Accordingly, Phase 1 ends as **BTC rejected; ETH and SOL inconclusive**. The protocol does not authorize paper trading. The next permitted step, if approved, is the previously defined Phase 2 multiple-testing extension; it is not being started automatically in this report.

## Reproducibility artifacts

The extended datasets are locally ignored and are not published to the repository because of size. The code, manifests, checksum verifier, frozen runner, and reports are reproducible from the official source URLs. The Phase 1 artifacts are written under `artifacts/bos-4h-daily/phase1_bos_extension/` in the working environment.

## References

[1]: https://data.binance.vision/ "Binance Data Collection — official public market-data archive"
[2]: https://github.com/binance/binance-public-data "Binance public data documentation and archive conventions"
