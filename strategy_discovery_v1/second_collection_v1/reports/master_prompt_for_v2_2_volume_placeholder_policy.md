# Master Prompt — Freqtrade Engine-Fidelity v2.2 Volume Placeholder Policy

নিচের prompt-টি Manus AI-কে copy-paste করে পাঠান। এটি **শুধুমাত্র versioned v2.2 package তৈরি ও validation**-এর অনুমতি দেয়। এটি measurement authorization নয়।

```text
Continue from Git commit:
ff4589112eda38b973c422a77079ad3773737a8b

I authorize creation and validation of an additive engine_fidelity_harness_v2.2 package that integrates the already acquired Bybit historical funding-rate and mark-price data into the pinned Freqtrade native futures-data layout.

This is a policy-change authorization for a narrowly scoped loader compatibility issue. It does NOT authorize any backtest, strategy execution, trial creation, ledger update, statistical analysis, WFO, cost stress, promotion, paper trading, live trading, deployment, or further market-data acquisition.

IMMUTABLE INPUTS

Preserve all of the following exactly:

- Historical ledger N=898
- last_sequence=898
- Ledger canonical hash:
  2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e
- Existing v2 package SHA-256:
  2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757
- Existing v2.1 package SHA-256:
  d2b8d10439c17ddd98c5c6b877ae5b6a85be0b4a1de24f6840803e86d8255216
- Existing Bybit acquisition manifest canonical SHA-256:
  81893e47e4426cb1be27685dd4bdd8d5f4825eaaa490e5c69fc4e1ffffbe695f
- Existing acquisition commit:
  ff4589112eda38b973c422a77079ad3773737a8b

The v2 and v2.1 packages, the frozen v1.2 execution manifest, the frozen statistical protocol, the historical measured-backtest artifact, the historical statistics artifact, all historical trial records, and the global ledger must remain byte-for-byte unchanged.

Use only the already committed acquisition artifacts under:
strategy_discovery_v1/second_collection_v1/data/bybit_linear_derivatives_history_v2/

Use only these pinned inputs:

- Freqtrade engine commit:
  eb1a668ceb0f29b7d578156bfc24c45278c0c0f8
- Technical dependency commit:
  720ff67483e346271165d49cf37265f78739c74c
- Approved strategy source commit:
  eff78d3ce3456b52c68a4e9a33cc055a56b801ff
- Runtime: CPython 3.12.3
- Existing hash-locked runtime and source/data pins unchanged

NEW VOLUME=0 PLACEHOLDER POLICY

The official Bybit mark-price Kline response supplies timestamp and mark-price OHLC values but does not supply exchange-traded volume. The pinned Freqtrade native OHLCV loader requires the structural columns:

date, open, high, low, close, volume

For mark-price files only, authorize the following narrowly defined policy:

1. Add a `volume` column whose value is exactly numeric zero for every mark-price row. This is a loader-required structural placeholder, not observed market volume.
2. The placeholder must be explicitly named and documented as `mark_price_volume_structural_placeholder`.
3. The placeholder must not be interpreted as traded volume, liquidity, turnover, order-book depth, or any exchange statistic.
4. The placeholder must not be used to calculate signals, indicators, entry/exit conditions, position sizing, fees, slippage, fills, latency, funding, liquidation, liquidity filters, volume filters, or performance metrics.
5. The placeholder must not be added to regular OHLCV data, funding-rate data, or any other candle type.
6. Do not forward-fill, interpolate, resample, synthesize, or alter mark-price OHLC values. Only the missing structural loader column may be deterministically set to zero under this newly authorized policy.
7. Do not change the Bybit raw responses or the normalized five-field mark-price source records. Preserve their exact hashes. Any native-layout derivative must reference the source hash and the placeholder-policy version.
8. If the pinned engine uses mark-price `volume` for any calculation, or if any strategy consumes this placeholder as volume, stop with `REQUEST_APPROVAL` and do not claim v2.2 validation.
9. If the pinned loader requires a different field layout, data type, or nonzero value, stop with `REQUEST_APPROVAL`; do not improvise.

NATIVE DATA MAPPING REQUIREMENTS

Create only additive, versioned v2.2 artifacts that explicitly map:

- BTCUSDT and ETHUSDT;
- category `linear`;
- exact UTC window from `2025-08-22T00:00:00Z` through `2026-08-22T00:00:00Z` exclusive;
- exact 15m mark-price data;
- native funding-rate timestamps at their observed settlement cadence;
- pinned Freqtrade filename and directory conventions for futures candle data;
- exact `date`, `open`, `high`, `low`, `close`, `volume` native mark layout;
- exact `date`, `funding_rate` native funding layout;
- source raw-response hashes, normalized-source hashes, derived native-file hashes, and placeholder-policy hash;
- no-resampling and no-forward-fill rules;
- duplicate, missing, out-of-window, non-monotonic, malformed, and incomplete-candle handling;
- explicit timestamp alignment between funding records and mark-price candles.

The v2.2 package must state that the mark-price `volume=0` field is a schema placeholder only and is not a claim about actual Bybit trading volume. It must also state that all strategy signal computation continues to use the strategy’s declared main-timeframe OHLCV data, not the mark-price placeholder field.

VALIDATOR REQUIREMENTS

Create a new read-only v2.2 validator. It may parse files and source code, but it must not run any strategy over market data and must not create returns, trades, performance metrics, or trial IDs.

The validator must fail closed unless all of the following pass:

1. v2.2 schema validation.
2. Exact package, acquisition-manifest, source, engine, technical, runtime, and harness-code hashes.
3. Exact raw response and normalized source hashes.
4. Exact native-layout file hashes and file availability.
5. Every mark-price native row has `volume == 0` and the field is numeric.
6. No funding-rate row contains a synthetic volume field.
7. Mark OHLC values exactly match the normalized Bybit source values after deterministic field naming and ordering.
8. Funding rate and mark timestamps remain native and are not resampled or forward-filled.
9. Exact 15m continuity, boundaries, duplicate rejection, monotonicity, and incomplete-candle rejection.
10. Pinned Freqtrade loader accepts the native layouts in a non-trading data-load smoke test.
11. Pinned engine source inspection confirms whether mark-price volume is used in funding/mark merge, exit, fee, fill, liquidation, or performance calculations.
12. Strategy/source inspection confirms no declared candidate consumes the mark-price placeholder as a signal or volume input.
13. Static Bybit linear-USDT pairlist remains exactly BTC/USDT:USDT and ETH/USDT:USDT.
14. No dynamic pairlist, candidate-specific override, framework-default substitution, resampling, or additional market-data source is used.
15. Historical ledger remains N=898 and unchanged.
16. Existing v2 and v2.1 package hashes remain unchanged.
17. Frozen execution manifest, statistical protocol, historical measured artifacts, and historical statistics artifacts remain unchanged.

Run only:

- deterministic data-layout conversion where the only new value is the explicitly authorized mark-price structural `volume=0` placeholder;
- schema validation;
- manifest, source, runtime, native-file, and hash validation;
- timestamp and alignment checks;
- pinned-engine non-trading loader smoke checks;
- Python compilation;
- repository tests;
- git diff --check;
- protected-artifact checks;
- fresh-clone verification.

Do not run:

- Freqtrade backtesting;
- any strategy over market data;
- trial-ID creation;
- global-ledger update;
- return-series or trade generation;
- DSR, PBO, CPCV, Sharpe, WFO, or cost stress;
- candidate selection or promotion;
- paper trading, live trading, deployment, or exchange trading.

ADVERSARIAL REVIEW

Before finalizing, report:

- Primary Analyst claim;
- strongest Adversarial Auditor objection, especially whether `volume=0` could contaminate any engine or strategy calculation;
- evidence for and against;
- exact source-code resolution;
- confidence and remaining uncertainty;
- exact native files, policy files, package files, validators, and SHA-256 hashes;
- exact candidate eligibility status, without creating trials;
- confirmation that no historical artifact or ledger field changed;
- confirmation that no backtest, strategy execution, trial ID, ledger update, statistical analysis, WFO, cost stress, promotion, paper/live trading, or deployment occurred.

FINAL STATUS

Return exactly one of:

- `V2_2_VALIDATED_REQUEST_MEASUREMENT_APPROVAL` — only if the placeholder is proven loader-only, no engine or strategy calculation uses it, all hashes/layout/alignment checks pass, and all protected artifacts remain unchanged;
- `REQUEST_APPROVAL` — if any semantic, schema, native-loader, or policy question remains unresolved;
- `FAIL_CLOSED` — if any integrity, source, runtime, data, hash, or protected-artifact mismatch is detected.

Stop after v2.2 validation. Even if every v2.2 gate passes, do not start measurement automatically. A separate authorization must be obtained for one new measured batch under the exact validated v2.2 package and package hash.
```

**Important:** `volume=0` এখানে কেবল Freqtrade loader-এর structural compatibility-এর জন্য। এটি market volume নয়, এবং strategy signal বা performance calculation-এ ব্যবহার করা যাবে না।
