# Strategy Redesign Research Results

## Purpose

This document records a pre-registered research comparison for causal market-structure and liquidity-mapping variants. It does not claim that any variant is profitable or suitable for live trading.

## Shared research controls

All variants use official Binance Futures 15-minute archive candles for BTCUSDT and ETHUSDT covering 2025, closed-bar information only, one-bar latency, taker fees, slippage, funding, conservative stop-first treatment when stop and target occur on the same candle, and chronological train/validation/untouched-test splits. Live execution remains disabled.

The strict structure variants require a causal displacement event, elevated relative volume, directional structure bias, and a narrow retest. The mixed variant includes strict `bos_retest_continuation` and `liquidity_sweep_reclaim`. The BOS-only ablation disables the sweep family because strategy-level diagnostics showed it contributed negative net R for both symbols.

## Results

| Variant | Symbol | Full-year trades | Full-year win rate | Full-year expectancy (R) | Full-year profit factor | Untouched OOS trades | OOS win rate | OOS expectancy (R) | OOS profit factor |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline confirmed bundle | BTCUSDT | 233 | 33.48% | -0.5296 | 0.4205 | 64 | 35.94% | -0.4304 | 0.4985 |
| Baseline confirmed bundle | ETHUSDT | 281 | 34.88% | -0.3298 | 0.5800 | 80 | 32.50% | -0.3878 | 0.5274 |
| Strict mixed structure | BTCUSDT | 284 | 27.46% | -0.4465 | 0.5501 | 57 | 35.09% | -0.1231 | 0.8571 |
| Strict mixed structure | ETHUSDT | 234 | 32.05% | -0.0968 | 0.8795 | 56 | 37.50% | 0.0764 | 1.1012 |
| Strict BOS-only ablation | BTCUSDT | 274 | 28.10% | -0.4256 | 0.5673 | 56 | 33.93% | -0.1641 | 0.8129 |
| Strict BOS-only ablation | ETHUSDT | 224 | 32.14% | -0.0923 | 0.8849 | 52 | 38.46% | 0.1126 | 1.1522 |

## Interpretation

The redesign improved the ETH untouched out-of-sample result relative to the baseline, and removing the liquidity-sweep family improved ETH OOS expectancy from `+0.0764R` in the mixed strict variant to `+0.1126R` in the BOS-only ablation. However, BTC remained negative and both assets remained negative over the full year. The positive ETH OOS result is therefore a promising hypothesis, not a validated production edge.

Strategy-level diagnostics also showed that the liquidity-sweep family was negative in the strict variant for both assets. The BOS-retest family was materially better, especially on ETH, but its full-year expectancy remained negative. Selectivity reduced drawdown and trade count, but selectivity alone did not establish robust positive expectancy.

## Redesign specification

The next research version should use a two-stage setup: first identify a higher-timeframe directional regime and a prior liquidity pool; then require a displacement break, the first clean retest, rejection in the regime direction, and sufficient distance to the next opposing liquidity pool after all costs. Entries should be rejected when the target is inside nearby opposing liquidity, when the retest is not the first retest, when the displacement candle is not materially larger than recent true range, or when expected net reward-to-risk is below the configured hurdle.

The system should evaluate BOS continuation and liquidity-sweep reversal as separate families rather than blending them into one score. A family should be eligible for paper observation only when it passes minimum trade-count, positive net expectancy, profit-factor, drawdown, and calibration gates in untouched out-of-sample data across multiple symbols and regimes. Thresholds must be chosen on train/validation data and then frozen before the untouched test.

## Current decision

No variant in this document is approved for live trading. The BOS-only ETH result should proceed to a new, untouched period and a second instrument universe only as a research hypothesis. BTC should not be traded by this research version. No accuracy percentage should be presented as a probability of profit; the reported win rate is an observed historical ratio under the stated simulator assumptions.
