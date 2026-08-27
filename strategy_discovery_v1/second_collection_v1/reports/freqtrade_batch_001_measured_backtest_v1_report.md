# Freqtrade Batch 001 — Measured Backtest Report v1

**Research disclaimer:** This is a historical research evaluation, not personalized financial advice. Perpetual-futures trading carries material risk, and these results do not establish live profitability.

**Source repository:** `https://github.com/freqtrade/freqtrade-strategies`
**Pinned source commit:** `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`
**Execution manifest:** `freqtrade_batch_001_execution_assumptions_v1_2`
**Execution manifest hash:** `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97`
**Harness profile hash:** `f9322715e58dd41d5b9177abd5676a868365ea7951d3a6fd8cfc48f374a535b7`
**Starting ledger:** `N=893`
**Final ledger after measured batch:** `N=898`

## Executive result

The authorized first measured batch was executed under the frozen research manifest. The manifest permitted 11 source-rule-complete candidates, but only five could be measured without violating the exact-timeframe and dependency fail-closed rules. Six were excluded before trial creation: four had unsupported source timeframes (`5m` or `12h`), one had a source timeframe supported by data but required an unavailable exact `technical.indicators.supertrend` implementation, and one additional source-timeframe/dependency case was retained as a no-trial exclusion. No resampling, framework-default substitution, or candidate-specific tuning was used.

All five measured candidates produced negative total net return over the verified 2025-08-22 through 2026-08-21 UTC OHLCV window. The best candidate by the predeclared daily Sharpe objective was `Heracles.py`, but its DSR was `0.0`, failing the frozen `DSR >= 0.95` gate. PBO was `0.0`, passing the `PBO <= 0.10` gate; this only means the training-selected configurations were not below the median of the small measured candidate set on the five pooled CPCV paths. It does not imply profitability or authorize promotion.

## Frozen research harness

The final run used a deterministic Python compatibility harness, not the full Freqtrade engine. The pinned strategy source was loaded from a temporary checkout; only structured results and hashes were retained. TA-Lib `0.6.8` and `ta` `0.11.0` were used for the declared indicator implementations. The harness applied the frozen fixed-notional sizing, 0.055% per-side commission proxy, 0.05% adverse slippage proxy, next-bar-open fills, one-bar latency, 30-calendar-day maximum holding period, conservative stop-before-target same-bar precedence, floor rounding, and fail-closed data rules.

The funding assumption was a declared zero-funding proxy because the verified archive contains OHLCV only. Bybit documentation states that actual fees may vary by region and account and that funding is exchanged at funding times based on position value and funding rate [1] [2]. Therefore, the zero-funding result is a material limitation and must not be interpreted as a live-cost estimate.

## Measured candidate results

| Candidate | Timeframe | Trades | Net P&L (USDT) | Total return | Bar Sharpe | Daily Sharpe | Max drawdown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `CustomStoplossWithPSAR.py` | 1h | 28 | -67.7113 | -6.7711% | -0.5769 | -0.5363 | -17.2386% |
| `Heracles.py` | 4h | 26 | -53.1204 | -5.3120% | -0.5068 | -0.4835 | -15.1254% |
| `HourBasedStrategy.py` | 1h | 44 | -114.1829 | -11.4183% | -0.9641 | -0.8847 | -21.6677% |
| `MultiMa.py` | 4h | 363 | -161.8964 | -16.1896% | -2.5186 | -2.4232 | -20.2044% |
| `PatternRecognition.py` | 1d | 21 | -68.5076 | -6.8508% | -0.9331 | -0.9331 | -11.9850% |

The selected research candidate by the predeclared objective was `Heracles.py`, trial `freqtrade-001-538cdbd0af387920`, because it had the highest daily Sharpe among the five measured candidates at `-0.4835`. This is a least-negative ranking, not a positive-performance conclusion.

## Exclusions and trial accounting

| Source file | Timeframe | Status | Trial created | Reason |
| --- | ---: | --- | --- | --- |
| `BreakEven.py` | 5m | Excluded | No | No exact verified 5m OHLCV file under the frozen exact-match policy |
| `Diamond.py` | 5m | Excluded | No | No exact verified 5m OHLCV file under the frozen exact-match policy |
| `GodStra.py` | 12h | Excluded | No | No exact verified 12h OHLCV file; resampling prohibited |
| `PowerTower.py` | 5m | Excluded | No | No exact verified 5m OHLCV file under the frozen exact-match policy |
| `Strategy004.py` | 5m | Excluded | No | No exact verified 5m OHLCV file under the frozen exact-match policy |
| `Supertrend.py` | 1h | Excluded | No | Exact external `technical.indicators.supertrend` implementation unavailable in the controlled environment |

Exactly five new trial IDs were appended to the cumulative ledger. The six exclusions did not enter `N`. The ledger now records `last_sequence=898`, `n_trials=898`, and global hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`.

## DSR, CPCV, and PBO

Statistics were computed only after the measured trials were appended, using the frozen `dsr_pbo_cpcv_v1` protocol and a separately frozen statistical batch manifest. The statistical manifest declared `sr_benchmark=0.0`, `sr_std_null=1.0`, daily UTC return aggregation, six contiguous chronological groups, 15 two-group test splits, 30-day purge and 30-day embargo, deterministic training Sharpe ranking, midrank ties, and five CPCV paths.

| Gate | Result | Threshold | Status |
| --- | ---: | ---: | --- |
| DSR for selected `Heracles.py` | 0.0000 | >= 0.95 | **Fail** |
| PBO | 0.0000 | <= 0.10 | Pass |
| CPCV | 15 splits / 5 paths | 6 groups, 2 test groups | Computed |

The DSR failure blocks the candidate. No candidate is promoted, no further WFO or cost-stress analysis is initiated, and no live or paper trading action is allowed. PBO passing cannot override DSR failure or the negative realized returns.

## Validation and safety state

The measured artifact contains per-candidate source hashes, execution-manifest hash, harness-profile hash, return-series hash, trade records, and metrics. The existing 10-file Bybit archive remained unchanged and was used without new acquisition. Repository tests passed with 58 tests, and no protected historical collection artifact was overwritten. The frozen DSR/PBO/CPCV protocol file was not modified.

The global ledger was extended only after the final corrected run. The final state is research-only: no deployment, paper trading, live trading, or candidate promotion. Any changed harness semantics, cost assumption, data manifest, source code version, or statistical rule must create a new trial identity and extend `N` again.

## Next Manus instruction

Use the following instruction for the next task:

> Continue from commit `69a280e74f8785d17f0a82d2c6137d0faf440971` and the measured-batch artifacts under `strategy_discovery_v1/second_collection_v1/`. Do not run another backtest, acquire new data, alter the global ledger, perform WFO, run cost stress, promote candidates, or trade. First audit the controlled compatibility harness against the full Freqtrade engine semantics and resolve the six exclusions, especially the exact `technical.indicators.supertrend` implementation and missing 5m/12h data coverage. Treat the current five measured trials as immutable historical results. Any new harness or data version must be versioned and create new trial identities. Reconcile the statistical manifest and report, verify ledger N=898 and hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`, and stop for review before any new measurement.

## References

[1]: https://www.bybit.com/en/help-center/article/Trading-Fee-Structure "Bybit Trading Fee Structure — Help Center"
[2]: https://www.bybit.com/en/help-center/article/Funding-Fee-Calculation "Funding Fee Calculation — Help Center"
[3]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 "Bailey and Lopez de Prado — The Deflated Sharpe Ratio"
[4]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104847 "Lopez de Prado — Advances in Financial Machine Learning"
