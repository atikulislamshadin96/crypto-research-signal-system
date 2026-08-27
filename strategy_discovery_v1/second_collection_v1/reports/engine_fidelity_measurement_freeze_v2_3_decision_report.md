# Engine-Fidelity Harness v2.3 Correction Decision Report

**Author:** Manus AI

**Status:** `V2_3_VALIDATED_REQUEST_MEASUREMENT_APPROVAL`

**Scope:** Actual Bybit historical funding-rate replacement for the zero-funding proxy; no measurement performed.

## সহজ সারাংশ

v2.2 package-এর প্রধান সমস্যা ছিল যে নতুন actual Bybit funding-rate data repository-তে থাকলেও frozen v1.2 execution manifest এখনও `zero_funding_proxy = 0.0` বলছিল। এতে package-এর data এবং execution assumption পরস্পরবিরোধী ছিল। এই mismatch ঠিক করতে নতুন additive v2.3 package তৈরি করা হয়েছে।

v2.3-এ actual historical Bybit funding-rate-কে native 8h funding input হিসেবে explicitly freeze করা হয়েছে। `zero_funding_proxy_allowed` এখন `false`। পুরোনো v1.2 manifest পরিবর্তন করা হয়নি; সেটি protected historical artifact হিসেবে অপরিবর্তিত রাখা হয়েছে। নতুন actual-funding policy-এর জন্য আলাদা `execution_assumption_manifest_v1_3_actual_funding_frozen.json` তৈরি হয়েছে।

এই কাজ **measurement authorization নয়**। কোনো backtest, strategy-over-data execution, trial ID, ledger update, return series, DSR/PBO/CPCV, WFO, cost stress, promotion বা trading করা হয়নি।

## Five corrections resolved

| Correction | Resolution |
|---|---|
| Zero-funding proxy remove | v1.3 additive manifest-এ actual historical funding model; zero proxy prohibited |
| Actual funding use | Native Bybit BTCUSDT/ETHUSDT 8h funding files explicitly bound |
| New assumption/hash freeze | New manifest canonical and filesystem hashes package integrity boundary-তে bound |
| Historical protection | v1.2, v2, v2.1, v2.2, historical trials, statistics, protocol এবং ledger protected |
| No-measurement state | v2.3 package authorization flags false; separate measurement approval still required |

## Primary Analyst claim

v2.3 package এখন execution policy এবং available futures data-কে একই versioned contract-এর মধ্যে আনে। Actual Bybit funding-rate manifest, normalized/native funding files, exact hashes, native timestamps এবং pinned Freqtrade funding loader path একে অপরের সঙ্গে সামঞ্জস্যপূর্ণ। Funding-rate values native 8h records থেকে ব্যবহার হবে; zero-funding proxy বা silent substitution অনুমোদিত নয়। Bybit-এর official funding-history API historical funding-rate records দেয়। [1]

Mark-price data-এর `volume=0` policy অপরিবর্তিতভাবে loader-only structural placeholder। এটি observed traded volume নয় এবং signal, indicator, sizing, fees, slippage, fills, funding, liquidation, liquidity অথবা performance calculation-এ ব্যবহারযোগ্য নয়। Mark-price endpoint-এর documented response fields-এর সঙ্গে এই সীমাটি সামঞ্জস্যপূর্ণ। [2]

## Strongest Adversarial Auditor objection

Actual funding data যুক্ত করলেই measurement correctness সম্পূর্ণ প্রমাণিত হয় না। Funding-rate timestamp-এর engine event-time interpretation, funding fee calculation, position direction, leverage/margin treatment এবং mark-price placeholder contamination future backtest-এ ভুল হলে result এখনও misleading হতে পারে। উপরন্তু, v1.3 manifest additive হওয়ায় future runner-কে নিশ্চিত করতে হবে যে v1.2 zero-funding manifest নয়, v2.3 actual-funding manifest-ই runtime configuration হিসেবে ব্যবহৃত হচ্ছে।

## Resolution and fail-closed controls

এই objection গ্রহণ করা হয়েছে। v2.3 package-এ actual-funding manifest path, canonical hash এবং filesystem hash explicitly bound। Validator actual manifest-এর self-canonical hash, filesystem hash, funding model, `zero_funding_proxy_allowed=false`, native 8h timeframe এবং actual-rate flag যাচাই করে। Validator একই সঙ্গে v1.2 manifest-এর protected hash যাচাই করে, যাতে পুরোনো artifact silently পরিবর্তন করা না যায়।

Pinned Freqtrade source-এ `_ft_has_params` override, native funding file loading এবং funding-rate in-memory alias যাচাই করা হয়েছে। Funding files persisted layout-এ `[date, funding_rate]`; engine-এর public history-loading path read-time compatibility-এর জন্য `open=funding_rate` alias তৈরি করে। Mark files persisted layout-এ `[date, open, high, low, close, volume]`, যেখানে `volume=0` কেবল loader-required structural field।

## v2.3 package identity

| Artifact | Identity |
|---|---|
| Package ID | `freqtrade_batch_001_engine_fidelity_measurement_freeze_v2_3` |
| Package version | `2.3.0` |
| Package canonical SHA-256 | `fb6f352d3710be7e836d3873bcb09be6d4c36885c902235a00189a89399bf60d` |
| Package actual filesystem SHA-256 | `5983aef407027a4cfe61de38a1dc3c890c94bd05e63a2f407d8d5b93c275a9f0` |
| Package internal non-self filesystem hash | `cd9672c989cd520100cf7f0ee55d307b6f1c1b03949741cecb4cc4f7c11e688f` |
| v2.3 schema SHA-256 | `aa5b05ba34b6fa4a71c6d5d700c89d97b1d25057d12221fb539d6e87b57bc0ea` |
| v2.3 validator SHA-256 | `c96ce20c2b9b4850577839cd6347dfde5318663cb12f1a9a0372548b12e77049` |
| Actual-funding manifest canonical SHA-256 | `cd4679e1e8278e224add40836f0a25e4d9f6599c6a6360580b3306b23aba6898` |
| Actual-funding manifest filesystem SHA-256 | `993d2ba9d3aa52710d9751342db3a637e8e245f9655c726181f9b49d38668266` |

## Frozen measurement scope after correction

The six candidates remain future-measurement eligible only. Each candidate uses exact 15m detail data, static Bybit linear USDT-perpetual scope, and the actual historical 8h funding inputs.

| Candidate | Main timeframe | Detail timeframe | Status |
|---|---:|---:|---|
| `CustomStoplossWithPSAR.py` | 1h | 15m | Eligible after v2.3 validation |
| `Heracles.py` | 4h | 15m | Eligible after v2.3 validation |
| `HourBasedStrategy.py` | 1h | 15m | Eligible after v2.3 validation |
| `MultiMa.py` | 4h | 15m | Eligible after v2.3 validation |
| `PatternRecognition.py` | 1d | 15m | Eligible after v2.3 validation |
| `Supertrend.py` | 1h | 15m | Eligible after v2.3 validation |

`BreakEven.py`, `Diamond.py`, `PowerTower.py` এবং `Strategy004.py` exact 5m data না থাকায় excluded। `GodStra.py` exact 12h data না থাকায় excluded। এই exclusions reclassify করা হয়নি।

## Validation results

| Validation | Result |
|---|---|
| v2.3 JSON Schema draft-07 | Pass |
| Actual-funding manifest canonical self-hash | Pass |
| Package canonical and non-self filesystem integrity | Pass |
| Acquisition manifest and raw/normalized data hashes | Pass |
| Native mark/funding file hashes | Pass |
| Exact 15m mark continuity and boundaries | Pass |
| Exact native 8h funding cadence and non-zero actual records | Pass |
| Mark OHLC exact source copy | Pass |
| `volume=0` placeholder-only enforcement | Pass |
| No resampling and no forward-fill | Pass |
| Pinned Freqtrade native history-loader smoke | Pass |
| `_ft_has_params` source-semantic check | Pass |
| Technical Supertrend parity fixtures | 13/13 pass |
| Six candidate source/timeframe loading | Pass |
| Repository tests | 58 passed |
| Python compilation | Pass |
| `git diff --check` | Pass |
| v1.2/v2/v2.1/v2.2/ledger protected hash checks | Pass |
| New backtest, trial IDs, or ledger append | None |
| Fresh-clone verification | Pass at commit `42d6e93f95cc8e4ad2558f0dfdc832aa7b741a02` |

## Immutable state

Starting commit was `ed2caaab1bdd6a20b1185c79a5f257c8d68927bf` and the repository was clean and remote-synchronized before v2.3 creation. The final additive v2.3 commit is `42d6e93f95cc8e4ad2558f0dfdc832aa7b741a02`, and its independent sparse fresh-clone verification passed. Historical ledger remains `N=898`, `last_sequence=898`, with canonical hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e` and filesystem hash `9642d0daa824d2ab49d7f4018d72f9b5e2e29cdea13bdcb73cd8af69653722eb`.

The v1.2 execution manifest remains byte-for-byte protected with filesystem hash `7820c7c832c1a0a4eabf0fc02a4d38b48699f851feadfbfd57a477ac7691f51e`. Existing v2, v2.1 and v2.2 packages remain protected with filesystem hashes `2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757`, `d2b8d10439c17ddd98c5c6b877ae5b6a85be0b4a1de24f6840803e86d8255216` এবং `93939f072200a20bc26a3f431a4f388e221c83d54f2356ce67f80a7b11d60b7b` respectively.

## Confidence and remaining uncertainty

Confidence is **high for the manifest/data-policy reconciliation and native data-layout validation**. The actual funding source is now explicitly versioned, hashed and separated from the old zero-funding manifest. Remaining uncertainty concerns only the final independent fresh-clone check and the future runner’s correct use of the v1.3 manifest at runtime. These must pass before any measured batch.

## Final decision and next authorization boundary

Final decision: `V2_3_VALIDATED_REQUEST_MEASUREMENT_APPROVAL`. The v2.3 package is ready to be considered for a later measured batch, but this task did not authorize measurement. A separate authorization must name the final v2.3 package canonical/filesystem hashes, preserve ledger `N=898`, specify the six candidates and expected increment `+6`, and prohibit WFO, cost stress, DSR/PBO/CPCV, promotion and trading until separately authorized.

## References

[1]: https://bybit-exchange.github.io/docs/v5/market/history-fund-rate "Bybit Get Funding Rate History"
[2]: https://bybit-exchange.github.io/docs/v5/market/mark-kline "Bybit Get Mark Price Kline"
