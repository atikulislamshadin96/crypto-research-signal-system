# Engine Fidelity Harness v2.4 — Decision Report

**Final decision state:** `V2_4_VALIDATED_REQUEST_MEASUREMENT_APPROVAL`

**Core implementation commit:** `171e7f25d403fb454c3edf1ccdcd0bc5430eb778`
**Starting commit:** `afa73f470b3945d018d7fa147fef610636c6827d`
**Remote status at core commit:** `main` synchronized with `origin/main`.

## 1. Decision packet

### Primary Analyst claim

v2.4 একটি additive এবং reproducible pre-measurement freeze package হিসেবে validated হয়েছে। v2.3-এর actual historical Bybit funding policy অপরিবর্তিত রেখে non-native fixed adverse-slippage assumption সরানো হয়েছে। নতুন policy হলো: **pinned Freqtrade-এর native `--fee 0.00055` per side ব্যবহার করা হবে; global adverse slippage প্রয়োগ করা হবে না (`slippage=0.0`)**। OHLCV price alteration, return post-processing এবং engine patch—তিনটিই নিষিদ্ধ। এই policy pinned engine-এর execution semantics-এর সঙ্গে mechanically compatible।

### Strongest Adversarial Auditor objection

`slippage=0.0` বাস্তব execution friction-এর দাবি নয়; এটি market impact, spread, latency-related adverse movement বা fill uncertainty-এর জন্য optimistic research assumption। অতএব v2.4-এর পরবর্তী ফলাফল থাকলেও সেগুলোকে live profitability, robustness বা deployability-এর প্রমাণ বলা যাবে না। উপরন্তু, mark-price files-এর `volume=0` observed traded volume নয়; কোনো strategy, indicator, sizing, fill, liquidity, funding, liquidation বা performance logic এই field ব্যবহার করলে harness fail-closed হওয়া উচিত।

### Resolution

আপত্তিটি গ্রহণ করা হয়েছে এবং policy-তে স্পষ্টভাবে লেখা হয়েছে। v2.4 হলো **measurement-ready preparation**, performance conclusion নয়। Native mark/funding loader smoke এবং semantic parity pass করা হয়েছে, কিন্তু কোনো strategy market-data execution, backtest, trial, ledger append, statistical analysis, WFO বা cost stress করা হয়নি। `volume=0` কেবল loader-required structural placeholder হিসেবে bound করা হয়েছে।

**Confidence:** package integrity এবং execution-semantics resolution সম্পর্কে উচ্চ; real-world execution fidelity সম্পর্কে সীমিত, কারণ v2.4 ইচ্ছাকৃতভাবে zero-slippage policy ব্যবহার করছে এবং কোনো measurement হয়নি।

## 2. Frozen execution policy

| Field | Frozen value |
|---|---|
| Execution policy ID | `native_fee_only_v1` |
| Commission model | `VIP0_taker_base_rate_proxy` |
| Commission | `0.00055` per side |
| Native control | pinned Freqtrade CLI `--fee` override |
| Slippage model | `native_engine_no_global_adverse_slippage` |
| Slippage value | `0.0` |
| Global adverse-slippage control in pinned engine | `false` |
| Price post-processing | forbidden |
| Return post-processing | forbidden |
| Engine patching | forbidden |
| Funding | actual historical Bybit native 8h funding |
| Zero-funding proxy | prohibited |
| Data transformation | no resampling, no forward-fill, no dynamic pairlist |

**Manifest:** `execution_assumption_manifest_v1_4_native_fee_only_frozen.json`
**Manifest canonical SHA-256:** `1972e26f85feefe152abdef4b8b2812db9b12c4732d4f7366855b700f8a81d42`
**Manifest actual file SHA-256:** `1fbe398faac1a571817214e990149ebf3918f48a7f4c6c986757f69e2ce188ae`

## 3. Source evidence for the native fee-only resolution

Pinned Freqtrade engine commit: `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8`.

The exact pinned source shows the CLI declaration in `freqtrade/commands/cli_options.py`, lines 260–264: `--fee` is a float option and its help text states that it is applied twice, on trade entry and exit. `freqtrade/optimize/backtesting.py`, lines 268–281, reads the configured fee into `self.fee`; lines 1223–1224 pass the same fee as `fee_open` and `fee_close`. The live help output also exposes `--fee FLOAT` with the same entry/exit wording. `freqtrade/configuration/configuration.py`, line 307, contains the `--fee` configuration override mapping.

A scoped source search across the pinned engine’s CLI, configuration, generic backtesting path and related execution modules found no generic global adverse-slippage option. The only relevant `slippage` matches were in hyperopt loss helpers (`hyperopt_loss_sharpe_daily.py` and `hyperopt_loss_sortino_daily.py`), where `slippage_per_trade_ratio = 0.0005` is applied to a hyperopt loss calculation. Those helper adjustments are not a native generic backtesting execution control and are not used by v2.4. Therefore the former `0.0005` assumption cannot be represented as an unmodified pinned-engine global execution parameter and was removed from v2.4.

## 4. Frozen package and integrity references

| Artifact | Hash / value |
|---|---|
| v2.4 package canonical SHA-256 | `647e3616e7792daffc38155f8946706e7b5afbc2affede03c520c44ab5844f0d` |
| v2.4 package internal `package_filesystem_sha256` | `ca45fdc9938b9287cc3cc4221d47bd24299f3e4ae53025030edde9520f0afb6c` |
| v2.4 package actual file SHA-256 | `7f8d2ada661b9c14556ccea993b95fa9c1bd9441add4fd78f582cd0ef2b74e8e` |
| v2.4 schema actual SHA-256 | `59bce36fad027c781304152c89b3a1d2fb608f19d304329be6acd8a8e0cfeea5` |
| v2.4 validator actual SHA-256 | `9759843658d0de6af837b74c4541fb0dcd1ec9162f12a4723e8d3261c6163671` |
| Locked runtime file SHA-256 | `7d3e20fadf1dcffd00dc5396a1b1dca8ea426abe28f1e5c1649dbaa80b46b15d` |
| Freqtrade engine commit | `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8` |
| Technical dependency commit | `720ff67483e346271165d49cf37265f78739c74c` |
| Strategy-source commit | `eff78d3ce3456b52c68a4e9a33cc055a56b801ff` |
| Supertrend implementation SHA-256 | `8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838` |
| Bybit acquisition manifest canonical SHA-256 | `81893e47e4426cb1be27685dd4bdd8d5f4825eaaa490e5c69fc4e1ffffbe695f` |
| Bybit acquisition manifest actual file SHA-256 | `0d156005a9fb57d8c4bb8429d79b20b31eeb6b261ae1f51a742767dcc9b93ed1` |

The package also preserves and verifies the prior v2/v2.1/v2.2/v2.3 package hashes, the v1.2 and v1.3 execution manifests, the locked runtime, native layout, native mark/funding files, source evidence bundle, parity fixtures and repository scripts.

## 5. Candidate scope

The exact future measurement scope contains six candidates. This list is eligibility only; it is not a performance ranking.

| Candidate | Main timeframe | Detail timeframe | Status |
|---|---:|---:|---|
| `CustomStoplossWithPSAR.py` | `1h` | `15m` | eligible after v2.4 validation |
| `Heracles.py` | `4h` | `15m` | eligible after v2.4 validation |
| `HourBasedStrategy.py` | `1h` | `15m` | eligible after v2.4 validation |
| `MultiMa.py` | `4h` | `15m` | eligible after v2.4 validation |
| `PatternRecognition.py` | `1d` | `15m` | eligible after v2.4 validation |
| `Supertrend.py` | `1h` | `15m` | eligible after v2.4 validation |

The static market scope remains Bybit linear perpetuals, USDT settlement, `BTC/USDT:USDT` and `ETH/USDT:USDT`, with the exact UTC window 2025-08-22T00:00:00Z through 2026-08-22T00:00:00Z exclusive. The following remain excluded before any future measurement because exact detail data is outside the frozen scope: `BreakEven.py`, `Diamond.py`, `PowerTower.py`, and `Strategy004.py` for missing exact 5m data; `GodStra.py` for missing exact 12h data.

## 6. Validation evidence

| Gate | Result |
|---|---|
| v1.4 manifest JSON syntax | pass |
| v1.4 manifest canonical self-hash | pass |
| v2.4 schema JSON syntax | pass |
| v2.4 package JSON syntax and draft-07 schema validation | pass |
| v2.4 package canonical/internal filesystem self-consistency | pass |
| Runtime lock hash | pass |
| Pinned engine/technical/strategy clone commits | pass; all exact and clean |
| Source evidence and six candidate snapshot hashes | pass |
| Native mark/funding layout and file hashes | pass |
| Native loader smoke | pass; 35,040 mark rows and 1,095 funding rows per symbol |
| Actual funding policy | pass; zero-funding proxy false |
| Mark volume placeholder rule | pass; numeric zero only in native mark loader files |
| Six non-data candidate imports | pass |
| Semantic parity fixtures | 13/13 pass; performance metrics not created |
| Full repository tests | 58 passed |
| Protected artifact SHA checks | pass |
| `git diff --check` | pass |
| Trial IDs created | 0 |
| Backtest / strategy-over-market-data execution | not run |

The only Freqtrade command invoked for source evidence was the non-executing `backtesting --help` help path. No `freqtrade backtesting` measurement run was invoked.

## 7. Protected state

The immutable global ledger remains **N=898**, `last_sequence=898`, canonical SHA-256 `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`, and actual file SHA-256 `9642d0daa824d2ab49d7f4018d72f9b5e2e29cdea13bdcb73cd8af69653722eb`. The v1.2 manifest, v1.3 actual-funding manifest, v2/v2.1/v2.2/v2.3 packages, historical five-trial artifact, historical statistics artifact, protocol, original data, and prior native files were not edited. Only the four additive v2.4 files in this package commit were introduced; this report is an additional additive report file.

## 8. Explicit stop boundary

This task stops here. No new trial ID, backtest, ledger append, DSR, PBO, CPCV, Sharpe selection, WFO, cost stress, promotion, paper trading, live trading or deployment was performed. `V2_4_VALIDATED_REQUEST_MEASUREMENT_APPROVAL` means a separate authorization may be requested; it does not authorize measurement by itself.

## 9. Separate future authorization prompt — do not execute now

> I separately authorize **one new engine-native measured Freqtrade batch** under the exact validated `engine_fidelity_harness_v2.4` package from the clean remote-synchronized commit identified in the decision report.
>
> Use package canonical SHA-256 `647e3616e7792daffc38155f8946706e7b5afbc2affede03c520c44ab5844f0d`, package internal filesystem SHA-256 `ca45fdc9938b9287cc3cc4221d47bd24299f3e4ae53025030edde9520f0afb6c`, actual package file SHA-256 `7f8d2ada661b9c14556ccea993b95fa9c1bd9441add4fd78f582cd0ef2b74e8e`, and v1.4 execution manifest canonical SHA-256 `1972e26f85feefe152abdef4b8b2812db9b12c4732d4f7366855b700f8a81d42`.
>
> Preserve immutable ledger N=898, `last_sequence=898`, canonical hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`, and actual ledger file hash `9642d0daa824d2ab49d7f4018d72f9b5e2e29cdea13bdcb73cd8af69653722eb`. Re-run every v2.4 preflight gate before any trial ID. Measure exactly the six eligible candidates and the two static Bybit pairs, with exact main timeframes and exact 15m detail data, actual native 8h funding, native Freqtrade `--fee 0.00055`, and `slippage=0.0`.
>
> Do not alter OHLCV prices, post-process returns, patch the engine, use the mark `volume=0` placeholder for any logic, add data, resample, forward-fill, use dynamic pairlists, or include the five excluded strategies. Do not run WFO, cost stress, DSR, PBO, CPCV, Sharpe-based selection, promotion, paper/live trading, deployment, or any trial beyond the six-candidate batch. Stop after the six measured artifacts and a validated immutable append, then request separate authorization for statistical analysis.
