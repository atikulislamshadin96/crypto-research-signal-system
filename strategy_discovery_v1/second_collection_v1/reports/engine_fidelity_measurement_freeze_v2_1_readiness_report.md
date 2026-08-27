# `engine_fidelity_harness_v2.1` Readiness Decision Packet

**Final status: `MEASUREMENT_READY`**
**Important boundary:** Measurement এখনও চালানো হয়নি এবং এই package নিজে measurement authorization দেয় না। কোনো backtest, OHLCV acquisition, trial ID, ledger update, DSR/PBO/CPCV, WFO, cost stress, promotion, paper trading, live trading, বা deployment করা হয়নি।

## সিদ্ধান্ত

### Primary Analyst claim

Authorized blocker-resolution scope-এর মধ্যে v2.1 package measurement-ready করা গেছে। Clean CPython `3.12.3` environment-এ hash-locked 149-package runtime sync হয়েছে এবং `pip check` pass করেছে। Pinned Freqtrade engine commit `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8`, technical dependency commit `720ff67483e346271165d49cf37265f78739c74c`, এবং Supertrend source hash pass করেছে। ছয়টি declared strategy module engine-native import/load smoke check pass করেছে। Public Bybit instrument metadata-তে উভয় frozen pair-এর price tick size, quantity step, minimum order quantity এবং minimum notional পাওয়া গেছে এবং response hashes record করা হয়েছে।

### Adversarial Auditor objection

এই readiness status-এর অর্থ **pre-run gates pass**, performance validity বা profitable trading নয়। Smoke validation strategy modules load করে, startup/timeframe declarations এবং pinned engine semantic source presence পরীক্ষা করে; এটি OHLCV-র উপর full backtest চালায়নি এবং তাই কোনো return, trade count, বা performance claim নেই। Zero-funding proxy, one-bar latency, static pairlist, fixed sizing/cost/fill এবং exact `15m` detail mapping এখনও external research assumptions। Exchange metadata current public response হিসেবে frozen হয়েছে; metadata বদলালে package version বদলাতে হবে।

### Resolution and confidence

Adversarial objection গ্রহণ করে status-টি কেবল **measurement readiness** হিসেবে নির্ধারণ করা হয়েছে। Candidate performance, robustness, promotion, বা live applicability সম্পর্কে কোনো inference করা হয়নি। Package-এ `measurement_authorized=false`, সব authorization flag `false`, `trial_ids_created=0`, এবং ledger `N=898` রাখা হয়েছে। Confidence: **High** for package-integrity and pre-run gate readiness; **Medium** for future engine-result reproducibility until an actually authorized run produces and independently validates its new trial artifacts.

## Exact package and runtime identity

| Item | Frozen value |
|---|---|
| Package | `strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2_1.json` |
| Package SHA-256 | `d2b8d10439c17ddd98c5c6b877ae5b6a85be0b4a1de24f6840803e86d8255216` |
| Hash-locked runtime | `strategy_discovery_v1/second_collection_v1/data/engine_fidelity_runtime_v2.hashlocked.lock` |
| Hash-locked runtime SHA-256 | `7d3e20fadf1dcffd00dc5396a1b1dca8ea426abe28f1e5c1649dbaa80b46b15d` |
| Environment | Clean CPython `3.12.3`, 149 resolved packages, `pip check` PASS |
| Engine | Freqtrade commit `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8` |
| Technical dependency | commit `720ff67483e346271165d49cf37265f78739c74c` |
| Strategy source | `freqtrade/freqtrade-strategies` commit `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`, GPL-3.0; no full source vendored |
| Frozen v1.2 execution manifest | canonical SHA `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97` |
| OHLCV manifest | SHA `d4ec91de7ec0193e8459b4dea6db5f44a6f3aac471ec62ae465c9ff59fbd7c9f`; existing 10 exact files |
| Historical ledger | `N=898`, `last_sequence=898`, canonical hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e` |

## Engine-native and public-metadata validation

The clean environment was synchronized from the hash-locked runtime and reported no broken requirements. The non-trading smoke check imported the pinned engine, loaded the six declared strategy modules, verified their declared main timeframes and required `15m` detail mapping, checked startup-candle declarations, inspected the pinned exit-ordering and custom-stoploss source tokens, confirmed static pairlist/no-resampling policy, and rechecked the pinned Supertrend source hash. No OHLCV file was read and no performance output was produced.

The authorized public Bybit metadata artifact is `bybit_linear_instrument_metadata_v2.json`, SHA-256 `fa151da10522dbef66d5b2a0b28d93d303cbb2a695c14a03f748da7febc8996f`. Required values are:

| Pair | Price tick size | Quantity step | Minimum order quantity | Minimum notional |
|---|---:|---:|---:|---:|
| BTCUSDT | `0.10` | `0.001` | `0.001` | `5` |
| ETHUSDT | `0.01` | `0.01` | `0.01` | `5` |

The artifact records the exact public URLs, retrieval timestamps, HTTP responses, and per-response SHA-256 hashes. It contains instrument metadata only; `ohlcv_acquired=false` and `funding_data_acquired=false`.

## Final candidate eligibility

The exact static scope is **Bybit linear perpetual, USDT settlement, pairs `BTC/USDT:USDT` and `ETH/USDT:USDT`**, with exact main files for `1h`, `4h`, and `1d`, and exact `15m` detail files. No resampling and no dynamic pairlist are allowed.

| Candidate | Main timeframe | Detail timeframe | Final status |
|---|---:|---:|---|
| `user_data/strategies/CustomStoplossWithPSAR.py` | `1h` | `15m` | Measurement-ready |
| `user_data/strategies/Heracles.py` | `4h` | `15m` | Measurement-ready |
| `user_data/strategies/HourBasedStrategy.py` | `1h` | `15m` | Measurement-ready |
| `user_data/strategies/MultiMa.py` | `4h` | `15m` | Measurement-ready |
| `user_data/strategies/PatternRecognition.py` | `1d` | `15m` | Measurement-ready |
| `user_data/strategies/Supertrend.py` | `1h` | `15m` | Measurement-ready; pinned technical parity pass |

The five exact-data exclusions remain unchanged: `BreakEven.py`, `Diamond.py`, `PowerTower.py`, and `Strategy004.py` require absent exact `5m` data; `GodStra.py` requires absent exact `12h` data. They were not measured or reclassified.

## Validation and protected-artifact results

| Check | Result |
|---|---|
| v2.1 package schema | PASS |
| Hash-locked runtime sync | PASS; 149 packages |
| Environment dependency check | PASS; no broken requirements |
| Engine-native six-strategy smoke check | PASS; no market data, performance, or trial IDs |
| Public Bybit metadata completeness | PASS; four required fields for both pairs |
| Pinned engine/technical/source hashes | PASS |
| Exact main/detail CSV hash and availability checks | PASS |
| Static pairlist/no-resampling/fail-closed policy checks | PASS |
| Semantic-only v2 parity fixtures | PASS; 13/13 |
| Repository tests | PASS; 58 passed |
| Python compilation and `git diff --check` | PASS |
| Historical ledger | UNCHANGED; `N=898` |
| Historical v2 package | UNCHANGED; SHA `2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757` |
| Measurement | NOT RUN |

All changes are additive under `strategy_discovery_v1/second_collection_v1/`. The original v2 package remains preserved; v2.1 exists because the authorized public instrument metadata and hash-locked runtime are new versioned inputs.

## Separate authorization required for the first measured batch

The following prompt is intentionally separate. It must not be treated as already granted by the current blocker-resolution authorization:

> I separately authorize one new measured Freqtrade batch only under the exact `engine_fidelity_harness_v2.1` package SHA-256 `d2b8d10439c17ddd98c5c6b877ae5b6a85be0b4a1de24f6840803e86d8255216`, starting from immutable ledger `N=898`, `last_sequence=898`, canonical ledger hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`. Measure only these six candidates and timeframes: `CustomStoplossWithPSAR.py` (1h), `Heracles.py` (4h), `HourBasedStrategy.py` (1h), `MultiMa.py` (4h), `PatternRecognition.py` (1d), and `Supertrend.py` (1h). Require exact `15m` detail data, the Bybit OHLCV manifest SHA-256 `d4ec91de7ec0193e8459b4dea6db5f44a6f3aac471ec62ae465c9ff59fbd7c9f`, the frozen execution-manifest canonical SHA-256 `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97`, the hash-locked runtime SHA-256 `7d3e20fadf1dcffd00dc5396a1b1dca8ea426abe28f1e5c1649dbaa80b46b15d`, Bybit metadata artifact SHA-256 `fa151da10522dbef66d5b2a0b28d93d303cbb2a695c14a03f748da7febc8996f`, pinned Freqtrade engine commit `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8`, pinned technical commit `720ff67483e346271165d49cf37265f78739c74c`, and approved source commit `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`. Expected trial increment is at most `+6`, only when all six pre-run gates pass; create new trial identities and never reuse historical IDs. Do not measure excluded 5m/12h strategies. Do not run WFO, cost stress, DSR/PBO/CPCV, promote candidates, paper trade, live trade, or deploy unless separately authorized later.

## References

[1]: ../data/engine_fidelity_measurement_freeze_package_v2_1.json "v2.1 measurement-ready package"
[2]: ../data/engine_fidelity_runtime_v2.hashlocked.lock "hash-locked runtime"
[3]: ../data/bybit_linear_instrument_metadata_v2.json "public Bybit instrument metadata"
[4]: ../schemas/engine_fidelity_measurement_freeze_package_v2_1.schema.json "v2.1 package schema"
[5]: ../data/engine_fidelity_measurement_freeze_package_v2.json "preserved v2 package"
[6]: ../data/engine_fidelity_parity_fixtures_v2.json "semantic-only parity fixtures"
[7]: ../../data/bybit_ohlcv_drive_roundtrip_manifest.json "verified Bybit OHLCV manifest"
[8]: ../../protocols/dsr_pbo_cpcv_v1.json "frozen DSR/PBO/CPCV protocol"
[9]: https://github.com/freqtrade/freqtrade/tree/eb1a668ceb0f29b7d578156bfc24c45278c0c0f8 "pinned Freqtrade engine"
[10]: https://github.com/freqtrade/technical/tree/720ff67483e346271165d49cf37265f78739c74c "pinned technical dependency"
[11]: https://github.com/freqtrade/freqtrade-strategies/tree/eff78d3ce3456b52c68a4e9a33cc055a56b801ff "approved strategy source"

**Basis:** This is a deterministic readiness and reproducibility assessment, not a performance or investment recommendation.

**Time:** Repository commit and public metadata retrieval timestamps are recorded in the attached artifacts; OHLCV window is UTC `2025-08-22` through `2026-08-21`.

**Assumptions:** Frozen external execution assumptions remain in force, including static Bybit scope, fixed sizing/cost/fill/latency, zero-funding proxy, exact detail data, and no resampling.

**Sources & confidence:** Pinned public repositories, exact local manifests, the clean hash-locked environment, and public Bybit instrument metadata were used. Performance remains unknown because measurement was not run.

**Compliance:** This is research and analysis only, not personalized financial advice.
