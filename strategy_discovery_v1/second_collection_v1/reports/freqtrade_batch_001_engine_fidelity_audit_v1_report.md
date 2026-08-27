# Freqtrade Batch 001 — Engine-Fidelity Audit v1

**Decision:** `PREPARE_ONLY`

**Scope:** Audit-only review from commit `7ca70267de1686fc4bd69a49fee98936414fd389`. The five measured trials, their return series, and the cumulative ledger at `N=898` were treated as immutable. No new backtest, market-data acquisition, trial creation, ledger update, WFO, cost stress, promotion, or trading action occurred.

## Verified starting state

| Item | Verified value |
| --- | --- |
| Repository HEAD and `origin/main` | `7ca70267de1686fc4bd69a49fee98936414fd389` |
| Global ledger | `N=898`, `last_sequence=898` |
| Global ledger hash | `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e` |
| Frozen execution manifest | `freqtrade_batch_001_execution_assumptions_v1_2` |
| Frozen execution manifest hash | `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97` |
| Frozen DSR/PBO/CPCV protocol | `dsr_pbo_cpcv_v1` |
| Protected artifacts changed in audit | None |

The requested ledger hash, historical measured artifact, and frozen inputs were verified. The repository was clean and synchronized at the start of the audit.

## Primary audit findings

The historical `freqtrade_batch_001_research_harness_v1` is a deterministic compatibility harness, not a full Freqtrade engine. This distinction was already present in its metadata, and the audit confirms it is material rather than merely descriptive.

| Finding | Severity | Effect on historical results | Required future action |
| --- | --- | --- | --- |
| Custom-stoploss current-rate and monotonic update differ from Freqtrade | High | `CustomStoplossWithPSAR.py` cannot be treated as full-engine equivalent | Build `engine_fidelity_harness_v2` using high-based callback rate and monotonic stop state |
| Same-candle ordering differs | High | Exit counts and reasons can differ | Implement documented order: exit signal, stoploss, ROI, trailing stop |
| No detail-timeframe simulation | High | Intrabar outcomes on higher timeframes can differ | Require an explicitly available, pinned detail-timeframe dataset or keep candidate excluded |
| ROI fill behavior is simplified | Medium | ROI exit prices can differ | Reproduce candle-bound and ROI timing rules exactly |
| Startup-candle trimming is absent | Medium | Early signals can differ | Calculate indicators with declared startup history and trim the unstable period before measurement |
| Exchange-limit/configuration behavior is simplified | Medium | Quantity rounding and rejected entries can differ | Pin exchange precision/limits and configuration semantics, or keep them explicitly external and versioned |

Official Freqtrade documentation states that entries are generated on candle close and generally execute at the next candle open [1] [3]. It also documents that the backtesting sequence is exit signal, stoploss, ROI, then trailing stoploss, with stoploss evaluated before ROI within the stoploss portion of the candle [1]. The historical harness currently checks stop/ROI before scheduling a next-open exit signal, so its ordering is not engine-equivalent.

For custom stoploss, the official engine passes the candle-bound rate—high for a long trade—and evaluates the resulting stop against the low; it also maintains the rule that a stop can only move upward during a trade [2]. The historical harness uses candle close for the custom-stop calculation and does not model the full monotonic state transition. This is a high-severity mismatch.

Freqtrade also supports lower-timeframe detail data for active trades and invokes callbacks on each detail candle [1]. The historical run did not use detail data. Consequently, its metrics are valid only as versioned compatibility-harness measurements and cannot be upgraded retrospectively to full-engine results.

## Six exclusion decisions

| Source | Timeframe | Decision | Reason |
| --- | ---: | --- | --- |
| `BreakEven.py` | 5m | Remain excluded | The frozen archive contains no exact 5m OHLCV file. Resampling is prohibited and no new data was acquired. |
| `Diamond.py` | 5m | Remain excluded | Same exact-data limitation. |
| `GodStra.py` | 12h | Remain excluded | The frozen archive contains no exact 12h OHLCV file. Resampling is prohibited. |
| `PowerTower.py` | 5m | Remain excluded | Same exact-data limitation. |
| `Strategy004.py` | 5m | Remain excluded | Same exact-data limitation. |
| `Supertrend.py` | 1h | Resolved for a future version only | The exact public `technical.indicators.supertrend` implementation was located, but it was not part of the historical harness and was not measured. |

The exact Supertrend implementation was audited from `freqtrade/technical` commit `720ff67483e346271165d49cf37265f78739c74c`, file `technical/indicators/supertrend.py`, SHA-256 `8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838`. This resolves the ambiguity for future work only. It does not authorize rerunning `Supertrend.py`, and it does not change the historical trial identity.

The 5m and 12h exclusions remain genuine under the current frozen data policy. A future data-coverage expansion would require a new data manifest and new trial identities; it cannot be achieved by silently resampling the existing 15m, 30m, 1h, 4h, or 1d files.

## Adversarial review

**Primary analyst position:** The six exclusions can be resolved by pinning the missing technical dependency and expanding exact timeframe coverage in a future version.

**Adversarial auditor objection:** Even after the exclusions are technically resolved, the historical compatibility results should not be rerun or pooled with the existing five trials because the engine semantics, data detail, and dependency versions would change the experiment. Treating them as the same trials would undercount selection exposure and contaminate the DSR/PBO ledger.

**Resolution:** The objection is accepted. The correct action is to prepare a new versioned full-engine-fidelity harness and, if later authorized, create new trial IDs that include the engine commit, technical dependency commit, data manifest, detail timeframe, harness code hash, and all execution assumptions. The existing five trial IDs and `N=898` remain immutable.

## Final decision and next gate

`PREPARE_ONLY` is the final decision. No new measurement is justified under the current audit scope because the historical harness has high-severity semantic differences from the full engine. The current measured result remains non-promoted: the prior selected candidate failed DSR, despite PBO passing. That outcome is not reversed by this audit.

The next gate is a separate review of a versioned `engine_fidelity_harness_v2` design. It must first pin the full Freqtrade engine commit, the technical dependency commit, exact detail-timeframe data availability, startup trimming, custom-stoploss semantics, ROI/exit ordering, exchange precision, and an immutable test fixture. Only after those are validated should a separate authorization for new measurements be considered.

## Ready-to-run next-task packet

> Continue from commit `7ca70267de1686fc4bd69a49fee98936414fd389`. Treat the five measured trials, their return series, and ledger `N=898` as immutable. Do not run a backtest, acquire market data, update the ledger, run WFO, perform cost stress, promote candidates, or trade. Design and validate only a versioned `freqtrade_batch_001_engine_fidelity_harness_v2` in a new scoped path. Pin Freqtrade engine commit `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8`, technical dependency commit `720ff67483e346271165d49cf37265f78739c74c`, and all dependency hashes. Reproduce official semantics for startup-candle trimming, next-open entries, exit-signal/stoploss/ROI/trailing ordering, custom-stoploss high-bound callback rate, monotonic stop updates, ROI candle-bound fills, exchange precision, and optional detail-timeframe behavior. Keep 5m/12h candidates excluded unless a new exact-data manifest is separately approved. Create immutable fixtures and parity tests; do not execute candidate measurements. Verify ledger hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`, then stop and report readiness.

## References

[1]: https://www.freqtrade.io/en/stable/backtesting/ "Freqtrade Backtesting"
[2]: https://www.freqtrade.io/en/stable/strategy-callbacks/ "Freqtrade Strategy Callbacks"
[3]: https://www.freqtrade.io/en/stable/strategy-customization/ "Freqtrade Strategy Customization"
[4]: https://github.com/freqtrade/technical/blob/720ff67483e346271165d49cf37265f78739c74c/technical/indicators/supertrend.py "Pinned Freqtrade Technical Supertrend Implementation"
