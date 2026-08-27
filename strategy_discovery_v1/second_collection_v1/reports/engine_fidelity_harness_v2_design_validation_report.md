# Freqtrade Engine-Fidelity Harness v2 — Design Validation Report

**Final decision:** `PREPARE_ONLY`

**Authorization boundary:** The user authorized design, audit, and semantic parity validation only. No new measured backtest, market-data acquisition, trial creation, ledger update, DSR/PBO/CPCV calculation, WFO, cost stress, promotion, paper trading, live trading, or deployment was performed.

## Verified baseline

| Item | Result |
| --- | --- |
| Starting and final repository commit | `ebc259c815051ef7b13e10dbc25f9d8bae141c85` before this scoped change |
| Repository state | Clean and synchronized before edits |
| Historical ledger | `N=898`, `last_sequence=898` |
| Historical ledger hash | `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e` |
| Frozen execution manifest | `freqtrade_batch_001_execution_assumptions_v1_2`, hash `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97` |
| Historical measured trials | Five, immutable |
| Protected historical files | Not modified |

The historical v1 compatibility harness, five measured trials, statistical artifact, frozen manifest, ledger, and protocol remain immutable. The new files are additive and scoped under `strategy_discovery_v1/second_collection_v1/`.

## Primary Analyst and Adversarial Auditor

**Primary Analyst claim:** A v2 contract with pinned Freqtrade engine and technical dependency commits, engine-native callback semantics, exact data requirements, deterministic identity fields, and semantic fixtures can establish a safer basis for future measurement.

**Adversarial objection:** A compatibility shim can appear deterministic while producing materially different trades through incorrect stoploss bounds, same-candle ordering, ROI prices, startup trimming, detail-timeframe handling, or exchange limits. Reusing historical trial IDs would undercount selection exposure and make DSR/PBO results non-comparable.

**Resolution:** The objection is accepted. The v2 artifacts explicitly prohibit compatibility-mode measurement, require engine-native loading semantics, require exact data and detail-timeframe checks, and require new trial identities for every changed engine, dependency, data, execution, or harness field. Historical v1 results remain labelled compatibility-harness-only.

## v2 contract delivered

The contract and design specify the following required behavior:

| Semantic area | v2 rule |
| --- | --- |
| Strategy loading | Pinned Freqtrade engine loader only; home-grown shim is not measurement-eligible |
| Parameters | Source/config precedence is pinned and parameter hash is recorded |
| Startup history | Calculate with startup history, then trim unstable candles; missing history fails closed |
| Entry | Closed main-timeframe signal, next main-timeframe open |
| Exit ordering | Exit signal, stoploss, ROI, trailing stoploss |
| Custom stoploss | Engine-native bound rate, high/low handling, monotonic stop state |
| ROI | Engine-native candle-bound and timing rules |
| Detail data | Exact smaller timeframe required when declared; no silent resampling |
| Pairlist | Static uniform scope only; dynamic pairlists prohibited |
| Precision/limits | Explicit pinned exchange limits or fail closed |
| Identity | Source, engine, technical, runtime, data, manifest, harness, protocol, parameters, timeframe, and pairlist hashes |

The exact public `technical.indicators.supertrend` implementation was pinned to `freqtrade/technical` commit `720ff67483e346271165d49cf37265f78739c74c`, with source SHA-256 `8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838`. This resolves the dependency ambiguity for a future version only; it does not alter the historical Supertrend trial status.

## Parity validation

The deterministic runner passed **13 semantic-only cases** covering next-open entry, same-candle ordering, custom-stoploss high-bound behavior, monotonic stop updates, ROI candle bounds, startup trimming, missing detail data, static/dynamic pairlist policy, quantity precision, end-of-data exit, and the pinned Supertrend output contract. The runner created no performance metrics, return series, trade counts, trial IDs, or ledger entries.

Repository tests also passed: **58 passed**. Python compilation, JSON Schema validation, `git diff --check`, ledger invariant checks, and protected-file checks passed.

## Six exclusion resolutions

| Candidate | Decision |
| --- | --- |
| `BreakEven.py`, `Diamond.py`, `PowerTower.py`, `Strategy004.py` | Remain excluded: exact 5m OHLCV is absent; no new data or resampling is authorized |
| `GodStra.py` | Remain excluded: exact 12h OHLCV is absent; no new data or resampling is authorized |
| `Supertrend.py` | `dependency_resolved_pending_new_measurement`: exact technical implementation is pinned, but no historical rerun occurred |

## Next gate

The next gate is not an automatic backtest. A later measured task must first freeze a v2 runtime/container or package lock, confirm exact main and detail data manifests, verify full engine parity, print the final candidate list, and create new trial IDs from the immutable historical ledger at `N=898`. The historical five trials must never be overwritten or pooled under old identities.

## Ready-to-run later measurement authorization

> I separately authorize a new measured Freqtrade batch only under the newly validated and explicitly frozen `freqtrade_batch_001_engine_fidelity_harness_v2`, its exact pinned engine and technical dependencies, its exact approved main/detail data manifests, and its exact trial-identity rules. Start from immutable ledger `N=898` with hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`; do not overwrite historical trials. Measure only candidates and timeframes explicitly marked eligible. Before execution, print the final candidate list, source hashes, engine/dependency hashes, main/detail data files and hashes, execution manifest hash, costs, fills, latency, precision, and expected trial-count increment. Stop and request approval if any input differs. No promotion, WFO, cost stress, paper trading, live trading, or deployment is authorized by this instruction.

## References

[1]: https://www.freqtrade.io/en/stable/backtesting/ "Freqtrade Backtesting"
[2]: https://www.freqtrade.io/en/stable/strategy-callbacks/ "Freqtrade Strategy Callbacks"
[3]: https://www.freqtrade.io/en/stable/strategy-customization/ "Freqtrade Strategy Customization"
[4]: https://github.com/freqtrade/technical/blob/720ff67483e346271165d49cf37265f78739c74c/technical/indicators/supertrend.py "Pinned Technical Supertrend Source"
