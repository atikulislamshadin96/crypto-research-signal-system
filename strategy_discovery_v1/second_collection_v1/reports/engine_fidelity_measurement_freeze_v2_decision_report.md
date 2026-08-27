# `engine_fidelity_harness_v2` Measurement-Freeze Decision Packet

**Status: `REQUEST_APPROVAL`**
**Scope:** pre-measurement freeze preparation only. No new backtest, market-data acquisition, trial ID, ledger update, DSR/PBO/CPCV, WFO, cost stress, promotion, paper trading, live trading, or deployment was performed.

## সংক্ষিপ্ত সিদ্ধান্ত

### Primary Analyst claim

`engine_fidelity_harness_v2`-এর জন্য একটি additive, versioned, measurement-free freeze package প্রস্তুত করা গেছে। এতে pinned Freqtrade engine commit `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8`, pinned technical dependency commit `720ff67483e346271165d49cf37265f78739c74c`, approved strategy-source commit `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`, frozen execution manifest reference, exact ten-file Bybit OHLCV manifest, static pairlist, 15m detail-data mapping, candidate/exclusion policy, fail-closed rules এবং read-only hash validator আছে। Semantic-only parity fixture-এর 13টি case pass করেছে।

### Adversarial Auditor objection

এই ফলাফলকে **measurement-ready full-engine freeze** বলা যাবে না। Existing parity runner isolated semantic fixtures এবং pinned Supertrend source পরীক্ষা করে; এটি candidate strategy load, full Freqtrade backtest path, startup-candle trimming, detail timeframe execution, exchange precision/minimum limits, অথবা complete transitive dependency installation প্রমাণ করে না। Runtime lock artifact আছে, কিন্তু এটি বর্তমান design environment-এর complete snapshot; cryptographic wheel/source hashes বা container digest-সহ clean reproducible installation এখনও validated নয়। তাছাড়া frozen execution assumptions-এ quantity rounding আছে, কিন্তু exact price tick size, minimum order quantity এবং minimum notional metadata unresolved।

### Resolution

Auditor-এর objection গ্রহণ করা হয়েছে। Package-টি `pre_measurement_freeze_prepared` অবস্থায় রাখা হয়েছে এবং `candidate_eligibility.final_status = conditional_not_measurement_ready`। ফলে **actual measurement-eligible count = 0**; ছয়টি candidate কেবল conditional future set হিসেবে তালিকাভুক্ত। এটি historical v1 compatibility results-এর reclassification নয় এবং কোনো historical trial পুনরায় চালানো হয়নি।

**Confidence:** High যে package integrity, historical immutability এবং fail-closed policy সঠিকভাবে ধরা হয়েছে; Medium যে ভবিষ্যৎ clean engine-native installation নির্ধারিত runtime lock-এ reproducibly resolve হবে, কারণ clean install/container execution এখনও validated নয়।

## Frozen package identity এবং integrity boundary

| Item | Frozen value / result |
|---|---|
| Package path | `strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2.json` |
| Package SHA-256 | `2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757` |
| Full runtime lock SHA-256 | `e46d3a20e0dc2afb38672843579b5163d1a7071596b518e64329a76d277a50fa` |
| Direct runtime pin lock SHA-256 | `d3dc12e18a9f26d66bd61972051ffe53528ea4c9e2a3be3358f5ac357bf33355` |
| Runtime declaration | CPython `3.12.3`; full lock includes pinned Freqtrade and technical git revisions plus observed package versions |
| Freqtrade engine | commit `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8`; pinned audit file hashes validated |
| Technical dependency | commit `720ff67483e346271165d49cf37265f78739c74c`; `technical/indicators/supertrend.py` SHA-256 `8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838` |
| Approved strategy source | `freqtrade/freqtrade-strategies`, commit `eff78d3ce3456b52c68e4a33cc055a56b801ff`, GPL-3.0; no full third-party source vendored |
| Frozen execution manifest | canonical SHA `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97`; filesystem SHA `7820c7c832c1a0a4eabf0fc02a4d38b48699f851feadfbfd57a477ac7691f51e` |
| OHLCV manifest | filesystem SHA `d4ec91de7ec0193e8459b4dea6db5f44a6f3aac471ec62ae465c9ff59fbd7c9f`; ten exact local CSVs, 127,750 candles in the existing provenance record |
| Frozen statistical protocol | `strategy_discovery_v1/protocols/dsr_pbo_cpcv_v1.json`, SHA `c45a37fe99a2d5a8407e8c889ead173b8626ef53748930d2f5970a272782070e` |
| Historical ledger | `N=898`, `last_sequence=898`, canonical hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`; filesystem SHA `9642d0daa824d2ab49d7f4018d72f9b5e2e29cdea13bdcb73cd8af69653722eb` |

## Scope, detail data, and candidate decision

The package freezes the uniform external research scope as **Bybit linear perpetual, USDT settlement, static pairs `BTC/USDT:USDT` and `ETH/USDT:USDT`**. Dynamic pairlists are prohibited. Main strategy timeframes must be exact matches from `1h`, `4h`, or `1d`; no resampling is permitted.

The existing exact `15m` files are formally mapped as detail data for future `1h`, `4h`, and `1d` candidates. The mapping is valid only when every declared file exists and matches the package hash. It is not an automatic permission to use a different detail timeframe or to synthesize missing data. Exact `5m` main data and exact `12h` main data are absent, so the five historical exclusions remain excluded.

| Future conditional candidate | Main timeframe | Required detail timeframe | Current decision |
|---|---:|---:|---|
| `user_data/strategies/CustomStoplossWithPSAR.py` | `1h` | `15m` | Conditional; full engine-native validation pending |
| `user_data/strategies/Heracles.py` | `4h` | `15m` | Conditional; full engine-native validation pending |
| `user_data/strategies/HourBasedStrategy.py` | `1h` | `15m` | Conditional; full engine-native validation pending |
| `user_data/strategies/MultiMa.py` | `4h` | `15m` | Conditional; full engine-native validation pending |
| `user_data/strategies/PatternRecognition.py` | `1d` | `15m` | Conditional; full engine-native validation pending |
| `user_data/strategies/Supertrend.py` | `1h` | `15m` | Conditional; pinned technical source hash/parity pass; full engine-native validation pending |

`BreakEven.py`, `Diamond.py`, `PowerTower.py`, and `Strategy004.py` remain excluded because exact `5m` data is not present and resampling is prohibited. `GodStra.py` remains excluded because exact `12h` data is not present. `Supertrend.py` is no longer blocked by the missing technical source, but it remains conditional until the pinned implementation is exercised inside the locked, engine-native environment.

## Execution and fail-closed policy

The package preserves the frozen v1.2 execution assumptions as an immutable reference rather than silently changing them. It explicitly requires Freqtrade-native startup-candle trimming, exact main/detail files, closed-bar signal timing, static pairlist behavior, and rejection of candidate-specific overrides. Missing bars, invalid required series, unsupported strategy features, configuration overrides, hash mismatches, absent detail data, and unavailable startup history must fail closed.

The quantity rounding rule is explicitly retained as **floor to six base-asset decimal places, skip zero quantity**. However, exact exchange `price_tick_size`, `minimum_order_qty`, and `minimum_notional` are not frozen in the current package. Their status is `unresolved_external_exchange_metadata`, and the package requires them before any measurement. This is the principal execution-limit blocker; no default exchange values were invented.

## Validation results

| Check | Result |
|---|---|
| Package JSON Schema validation | PASS |
| Runtime, manifest, CSV, protocol, evidence, reassessment, exclusion, and harness hash checks | PASS |
| Pinned engine and technical temporary-clone file hash checks | PASS |
| Static pairlist and no-resampling policy checks | PASS |
| Conditional candidate/exclusion policy checks | PASS |
| Ledger immutability check | PASS; `N=898`, no update |
| Python compilation | PASS |
| Semantic-only v2 parity fixtures | PASS; 13/13; no performance metrics; no trial IDs |
| Repository tests | PASS; 58 passed |
| `git diff --check` | PASS |
| New measurement | NOT RUN |
| New trial IDs | 0 |
| Market-data acquisition | NOT RUN |

The parity result is deliberately not described as full Freqtrade engine equivalence. It verifies deterministic semantic fixtures and the pinned Supertrend source contract only.

## Protected-artifact status

No historical file was overwritten. The ledger, five measured compatibility trials, historical statistics, frozen v1.2 execution manifest, frozen DSR/PBO/CPCV protocol, original normalized-strategy schema, historical raw/filter/evidence outputs, and prior v2 design artifacts remain unchanged. The new files are additive and scoped under `strategy_discovery_v1/second_collection_v1/`.

## Required next input before measurement authorization

To move from `REQUEST_APPROVAL` to a genuinely measurement-ready freeze, provide or authorize the following specific inputs: **(1)** a clean engine-native Freqtrade environment built from commit `eb1a668...` with a cryptographically reproducible complete dependency lock or container digest; **(2)** exact Bybit linear contract precision and minimum-limit metadata for the frozen pair scope, with provenance and hashes; and **(3)** a validation run inside that locked environment proving strategy loading, startup trimming, main/detail execution, callback/ROI/exit ordering, and the pinned Supertrend implementation. These inputs must be versioned if they differ from the package.

## Separate future authorization prompt — do not execute automatically

After the blockers above are separately resolved and the package is re-issued or explicitly accepted as measurement-ready, the following must be sent as a separate authorization; the present task did **not** grant it:

> I separately authorize a new measured Freqtrade batch only under the exact frozen `engine_fidelity_harness_v2` package SHA-256 `2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757`, starting from immutable ledger `N=898`, `last_sequence=898`, canonical ledger hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`. The only conditional candidate paths/timeframes are: `CustomStoplossWithPSAR.py` (1h), `Heracles.py` (4h), `HourBasedStrategy.py` (1h), `MultiMa.py` (4h), `PatternRecognition.py` (1d), and `Supertrend.py` (1h), each requiring exact 15m detail data. Use the exact Bybit OHLCV manifest SHA-256 `d4ec91de7ec0193e8459b4dea6db5f44a6f3aac471ec62ae465c9ff59fbd7c9f`, the frozen execution-manifest canonical SHA-256 `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97`, the pinned Freqtrade engine commit `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8`, the pinned technical commit `720ff67483e346271165d49cf37265f78739c74c`, and the approved strategy-source commit `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`. The expected trial increment is at most `+6` only if all six conditional candidates pass the pre-run gates; create new identities and never reuse historical trial IDs. Do not acquire data, resample, change pairlists, tune candidates, run WFO, run cost stress, calculate DSR/PBO/CPCV, promote a candidate, paper trade, live trade, or deploy unless separately authorized in a later instruction.

## References

[1]: ../data/engine_fidelity_measurement_freeze_package_v2.json "v2 measurement-free freeze package"
[2]: ../data/execution_assumption_manifest_v1_2_frozen.json "frozen v1.2 execution-assumption manifest"
[3]: ../../data/bybit_ohlcv_drive_roundtrip_manifest.json "verified Bybit OHLCV round-trip manifest"
[4]: ../data/engine_fidelity_harness_v2_contract.json "engine-fidelity v2 contract"
[5]: ../data/freqtrade_batch_001_exclusion_resolution_v2.json "v2 exclusion resolution"
[6]: ../data/engine_fidelity_parity_fixtures_v2.json "semantic-only parity fixtures"
[7]: ../../protocols/dsr_pbo_cpcv_v1.json "frozen DSR/PBO/CPCV protocol"
[8]: https://github.com/freqtrade/freqtrade/tree/eb1a668ceb0f29b7d578156bfc24c45278c0c0f8 "pinned Freqtrade engine commit"
[9]: https://github.com/freqtrade/technical/tree/720ff67483e346271165d49cf37265f78739c74c "pinned Freqtrade technical commit"
[10]: https://github.com/freqtrade/freqtrade-strategies/tree/eff78d3ce3456b52c68e4a9e33cc055a56b801ff "approved strategy source commit"

**Basis:** This packet reports deterministic package and repository-integrity checks, not investment performance or a trading recommendation.
**Time:** Repository and package state checked against the current task baseline at commit `2393b16e379ac2250e8fae7a9e1c38fce8f8c927`; data window is UTC `2025-08-22` through `2026-08-21`.
**Assumptions:** Frozen external execution assumptions remain in force, including static Bybit scope, fixed sizing/cost/fill/latency, zero-funding proxy limitation, and exact no-resampling rules.
**Sources & confidence:** Evidence is limited to pinned repository commits, immutable local manifests, existing artifacts, and the validated temporary audit clones; clean engine-native installation and exact exchange limits remain unresolved.
**Compliance:** This is research and analysis only, not personalized financial advice.
