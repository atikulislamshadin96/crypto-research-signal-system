# Engine-Fidelity Harness v2.2 Decision Report

**Author:** Manus AI
**Status:** `V2_2_VALIDATED_REQUEST_MEASUREMENT_APPROVAL`
**Package:** `freqtrade_batch_001_engine_fidelity_measurement_freeze_v2_2`
**Package canonical SHA-256:** `835dfde97d3642d51d6582d90e5d841ec0e93a08f5d7b8e6ba41703286fce372`
**Package filesystem SHA-256:** `93939f072200a20bc26a3f431a4f388e221c83d54f2356ce67f80a7b11d60b7b`

## সিদ্ধান্তের সারাংশ

নতুন additive `engine_fidelity_harness_v2.2` package তৈরি ও validation সম্পন্ন হয়েছে। এটি Bybit historical funding-rate এবং exact 15m mark-price data-কে pinned Freqtrade futures data layout-এ যুক্ত করে। Bybit mark-price API-তে exchange-traded volume না থাকায় package-এ কেবল loader compatibility-এর জন্য প্রতিটি mark-price row-তে numeric `volume=0` রাখা হয়েছে। এই field-এর policy ID হলো `mark_price_volume_structural_placeholder_v1`। এটি observed market volume নয় এবং strategy signal, indicator, sizing, fee, slippage, fill, funding, liquidation বা performance calculation-এ ব্যবহারযোগ্য নয়।

এই সিদ্ধান্ত **measurement authorization নয়**। কোনো backtest, strategy-over-data execution, trial ID, ledger update, return series, statistical analysis, WFO, cost stress, promotion বা trading করা হয়নি। Package status কেবল পরবর্তী আলাদা measurement approval-এর জন্য প্রস্তুত।

## Primary Analyst claim

Pinned engine source evidence এবং non-trading loader smoke test দেখায় যে Freqtrade-এর persisted mark-price layout-এর `volume` field loader-এর OHLCV schema পূরণ করে, কিন্তু pinned `combine_funding_and_mark` path কেবল `date`, `open_mark` এবং `open_fund` ব্যবহার করে; mark `volume` সেখানে ব্যবহৃত হয় না। Funding-rate persisted layout আলাদা দুই-column `[date, funding_rate]`; Freqtrade read path-এর in-memory compatibility alias `open=funding_rate` যোগ করে। তাই explicit, uniform এবং fail-closed placeholder policy-সহ v2.2 package native data loading-এর জন্য validated। Pinned `_ft_has_params` mechanism-এ `mark_ohlcv_timeframe=15m` এবং `funding_fee_timeframe=8h` explicitly bound করা হয়েছে; framework defaults-এর ওপর নির্ভর করা হয়নি। [1] [2]

## Strongest Adversarial Auditor objection

`volume=0` নামটি ভুলভাবে real traded volume হিসেবে ব্যবহৃত হলে volume-based strategy logic, liquidity assumptions বা performance interpretation দূষিত হতে পারে। আরেকটি ঝুঁকি হলো future engine revision বা configuration override mark-price volume-কে কোনো calculation-এ ব্যবহার করতে পারে। একইভাবে, funding-rate-এর in-memory `open` alias ভুলভাবে persisted synthetic volume হিসেবে বোঝা যেতে পারে।

## Evidence

Pinned engine source hash `ad96d396adb1590abf0891c2da990648c8a6ac030c6e9475c0c3713e8c1dd138`-এর `combine_funding_and_mark` implementation-এর relevant columns হলো `date`, `open_mark`, এবং `open_fund`; mark volume merge বা funding-fee calculation-এ ব্যবহৃত হয় না। Pinned `candle_columns.py` source hash `01e153140d98545f84226ada6783010e1ab1768cc8019ff1d4e16af92309f1e4` mark OHLCV structural schema এবং funding-rate two-column schema নির্ধারণ করে। Pinned `idatahandler.py` এবং `jsondatahandler.py` যথাক্রমে file naming, column normalization এবং JSON loading behaviour-এর জন্য hash-bound।

Official Bybit mark-price endpoint timestamp ও mark-price OHLC দেয়, কিন্তু exchange-traded volume দেয় না। [3] Official Bybit funding-history endpoint native funding timestamps দেয়। [4] Existing acquisition manifest-এর raw response এবং normalized source hashes অপরিবর্তিত রেখে v2.2 native derivatives files তৈরি হয়েছে।

## Placeholder resolution

`volume=0` কেবল `mark_price` candle files-এ ব্যবহৃত হয়েছে। প্রতিটি native mark row-তে value numeric zero; regular OHLCV, funding-rate বা অন্য candle type-এ এটি যোগ করা হয়নি। Mark `date/open/high/low/close` normalized Bybit source থেকে exact copy হয়েছে। কোনো resampling, forward-fill, interpolation বা OHLC alteration হয়নি। Funding rows native `[date, funding_rate]` layout-এ আছে এবং Freqtrade-এর read-time `open` alias validator দ্বারা আলাদাভাবে যাচাই করা হয়েছে।

Package-এর uniform `_ft_has_params` override হলো `mark_ohlcv_timeframe=15m` এবং `funding_fee_timeframe=8h`; এই override pinned source-এর `build_ft_has` path-এ প্রয়োগ হয়। Static pairlist কেবল `BTC/USDT:USDT` এবং `ETH/USDT:USDT`। Dynamic pairlist, candidate-specific override এবং framework-default substitution নিষিদ্ধ।

## Exact future candidate eligibility

এই package-এ candidates **future measurement eligible only**; কোনো trial তৈরি হয়নি। প্রতিটি candidate-এর detail timeframe exact `15m`।

| Candidate | Main timeframe | Detail timeframe | Status |
|---|---:|---:|---|
| `user_data/strategies/CustomStoplossWithPSAR.py` | 1h | 15m | Eligible after v2.2 validation |
| `user_data/strategies/Heracles.py` | 4h | 15m | Eligible after v2.2 validation |
| `user_data/strategies/HourBasedStrategy.py` | 1h | 15m | Eligible after v2.2 validation |
| `user_data/strategies/MultiMa.py` | 4h | 15m | Eligible after v2.2 validation |
| `user_data/strategies/PatternRecognition.py` | 1d | 15m | Eligible after v2.2 validation |
| `user_data/strategies/Supertrend.py` | 1h | 15m | Eligible after v2.2 validation |

`BreakEven.py`, `Diamond.py`, `PowerTower.py` এবং `Strategy004.py` exact 5m data না থাকায় excluded। `GodStra.py` exact 12h data না থাকায় excluded। এই exclusions v2.2-এ reclassify করা হয়নি।

## Validation results

| Validation | Result |
|---|---|
| JSON Schema draft-07 | Pass |
| Package canonical/filesystem integrity | Pass |
| Acquisition manifest, raw and normalized hashes | Pass |
| Native mark/funding file hashes | Pass |
| Exact 15m mark continuity and boundaries | Pass |
| Native 8h funding uniqueness and cadence | Pass |
| Mark OHLC exact source copy | Pass |
| Every mark placeholder `volume == 0` | Pass |
| Funding files contain no synthetic volume | Pass |
| Pinned Freqtrade native loader smoke | Pass |
| `_ft_has_params` source-semantic check | Pass |
| Technical Supertrend parity fixtures | 13/13 pass |
| Repository tests | 58 passed |
| Python compilation and whitespace check | Pass |
| Fresh-clone verification | Pending final post-commit run |
| New backtest/trials/ledger update | None |

## Integrity and protected-artifact state

Starting commit ছিল `6449a192bce770d5306c8e4a93bec27736a1341e`; current v2.2 package is additive। Historical ledger remains `N=898`, `last_sequence=898`, canonical hash `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e`। Existing v2 package SHA-256 `2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757` এবং v2.1 package SHA-256 `d2b8d10439c17ddd98c5c6b877ae5b6a85be0b4a1de24f6840803e86d8255216` unchanged। Frozen v1.2 execution manifest, statistical protocol, historical measured-backtest artifact এবং historical statistics artifact package validator দ্বারা protected reference হিসেবে bound করা হয়েছে।

## Confidence and remaining uncertainty

Confidence হলো **high for data-layout integrity and loader-only placeholder semantics**, কারণ exact source hashes, derived file hashes, schema, source-semantic assertions এবং non-trading loader smoke সব pass করেছে। Remaining uncertainty হলো future measurement command-এ package-এর `_ft_has_params` override এবং native datadir একইভাবে materialize করা হবে কি না; তাই future measured runner-কে v2.2 validator এবং exact package hash preflight gate হিসেবে ব্যবহার করতে হবে। কোনো changed runtime, source, package, data, precision, timing বা configuration assumption হলে নতুন v2.3 package এবং নতুন trial identity লাগবে।

## Final boundary and next authorization

`V2_2_VALIDATED_REQUEST_MEASUREMENT_APPROVAL` মানে package measurement-এর জন্য প্রস্তুত, কিন্তু measurement অনুমোদিত নয়। পরবর্তী measured batch-এর জন্য আলাদা authorization-এ exact v2.2 package canonical hash, filesystem hash, starting ledger N=898/hash, six-candidate list, expected trial increment `+6`, এবং no-WFO/no-cost-stress/no-DSR-PBO-CPCV/no-promotion/no-trading rules পুনরায় উল্লেখ করতে হবে।

```text
I separately authorize ONE new engine-native measured Freqtrade batch under the exact validated engine_fidelity_harness_v2.2 package.

Package canonical SHA-256:
835dfde97d3642d51d6582d90e5d841ec0e93a08f5d7b8e6ba41703286fce372

Package filesystem SHA-256:
93939f072200a20bc26a3f431a4f388e221c83d54f2356ce67f80a7b11d60b7b

Start from the exact clean remote-synchronized commit containing this package. Preserve immutable historical ledger N=898, last_sequence=898, and ledger canonical hash 2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e. Expected new trial increment is +6 only, one for each v2.2 eligible candidate: CustomStoplossWithPSAR.py (1h), Heracles.py (4h), HourBasedStrategy.py (1h), MultiMa.py (4h), PatternRecognition.py (1d), and Supertrend.py (1h), each with exact 15m detail data and the static BTC/USDT:USDT and ETH/USDT:USDT Bybit linear scope.

Use only the exact v2.2 runtime, engine, technical, strategy-source, execution, precision, funding, mark-price, native-data, and placeholder-policy hashes. Re-run every v2.2 preflight gate before creating any trial ID. The mark-price volume=0 field is only a loader-required structural placeholder and must not be interpreted or used as observed market volume, signals, indicators, sizing, fees, slippage, fills, funding, liquidation, liquidity, or performance data.

Do not run WFO, cost stress, DSR, PBO, CPCV, Sharpe-based selection, promotion, paper trading, live trading, or deployment in this batch. Stop after the six measured trial artifacts and immutable ledger append are validated; request separate authorization for any statistical analysis or promotion decision.
```

## References

[1]: https://github.com/freqtrade/freqtrade/blob/eb1a668ceb0f29b7d578156bfc24c45278c0c0f8/freqtrade/exchange/exchange.py "Pinned Freqtrade exchange source"
[2]: https://github.com/freqtrade/freqtrade/blob/eb1a668ceb0f29b7d578156bfc24c45278c0c0f8/freqtrade/data/history/datahandlers/idatahandler.py "Pinned Freqtrade data-handler source"
[3]: https://bybit-exchange.github.io/docs/v5/market/mark-kline "Bybit Get Mark Price Kline"
[4]: https://bybit-exchange.github.io/docs/v5/market/history-fund-rate "Bybit Get Funding Rate History"
