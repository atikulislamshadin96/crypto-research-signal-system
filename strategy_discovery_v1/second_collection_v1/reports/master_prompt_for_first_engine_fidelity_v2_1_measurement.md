# Manus AI-কে পাঠানোর জন্য Master Prompt

নিচের prompt-টি **শুধুমাত্র তখনই পাঠাবেন**, যখন আপনি সত্যিই প্রথম নতুন measured batch চালানোর অনুমতি দিতে চান। এটি v2.1 package-এর অধীনে একটি নতুন measured batch অনুমোদন করে; WFO, cost stress, DSR/PBO/CPCV, promotion বা trading অনুমোদন করে না।

```text
Continue from Git commit:
7c7b39e51d4dbc6308c81751066d650d6c0c0d21

I separately authorize ONE new measured Freqtrade batch only under the exact engine_fidelity_harness_v2.1 package:

Package path:
strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2_1.json

Package SHA-256:
d2b8d10439c17ddd98c5c6b877ae5b6a85be0b4a1de24f6840803e86d8255216

This authorization is limited to the single first measured batch. It does NOT authorize WFO, cost stress, DSR/PBO/CPCV, statistical selection, candidate promotion, paper trading, live trading, deployment, or any trading activity.

IMMUTABLE STARTING STATE

Treat all historical artifacts as immutable. Start from:
- Historical ledger N=898
- last_sequence=898
- Historical ledger canonical hash:
  2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e
- Existing v2 package SHA-256, which must remain unchanged:
  2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757

Never overwrite, delete, rerun, or reuse the five historical measured trial IDs. Never modify the historical measured-backtest artifact, historical statistics artifact, frozen v1.2 execution manifest, frozen DSR/PBO/CPCV protocol, original normalized-strategy schema, source evidence, or global ledger history except for one new additive ledger append after the new measurements are successfully completed.

EXACT ENGINE, DEPENDENCY, SOURCE, RUNTIME, AND DATA INPUTS

Use only:
- Freqtrade engine commit:
  eb1a668ceb0f29b7d578156bfc24c45278c0c0f8
- Freqtrade technical dependency commit:
  720ff67483e346271165d49cf37265f78739c74c
- Approved strategy source repository:
  https://github.com/freqtrade/freqtrade-strategies
- Approved strategy source commit:
  eff78d3ce3456b52c68a4e9a33cc055a56b801ff
- Runtime Python:
  CPython 3.12.3
- Hash-locked runtime file:
  strategy_discovery_v1/second_collection_v1/data/engine_fidelity_runtime_v2.hashlocked.lock
- Hash-locked runtime SHA-256:
  7d3e20fadf1dcffd00dc5396a1b1dca8ea426abe28f1e5c1649dbaa80b46b15d
- Frozen execution-manifest canonical SHA-256:
  041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97
- Existing Bybit OHLCV manifest SHA-256:
  d4ec91de7ec0193e8459b4dea6db5f44a6f3aac471ec62ae465c9ff59fbd7c9f
- Bybit instrument metadata artifact SHA-256:
  fa151da10522dbef66d5b2a0b28d93d303cbb2a695c14a03f748da7febc8996f

Do not acquire new OHLCV, funding history, or any other market data. Use only the exact existing CSV files declared by the package. Do not resample, forward-fill, synthesize, or silently substitute any timeframe.

FROZEN MARKET SCOPE

Use only the uniform static scope:
- Venue: Bybit
- Market type: linear perpetual
- Settlement/quote currency: USDT
- Static pairs: BTC/USDT:USDT and ETH/USDT:USDT
- Dynamic pairlists are prohibited
- Main timeframes: exact 1h, 4h, and 1d files only
- Detail timeframe: exact 15m files only
- No resampling

Use the frozen Bybit precision and limits metadata:
- BTCUSDT: price tick size 0.10; quantity step 0.001; minimum order quantity 0.001; minimum notional 5
- ETHUSDT: price tick size 0.01; quantity step 0.01; minimum order quantity 0.01; minimum notional 5

If any declared precision, limit, CSV hash, metadata hash, runtime hash, engine hash, technical hash, source hash, execution-manifest hash, or harness-code hash differs, STOP with FAIL_CLOSED and do not create any trial ID.

ONLY AUTHORIZED CANDIDATES

Measure exactly these six candidates and no others:
1. user_data/strategies/CustomStoplossWithPSAR.py — main timeframe 1h — detail timeframe 15m
2. user_data/strategies/Heracles.py — main timeframe 4h — detail timeframe 15m
3. user_data/strategies/HourBasedStrategy.py — main timeframe 1h — detail timeframe 15m
4. user_data/strategies/MultiMa.py — main timeframe 4h — detail timeframe 15m
5. user_data/strategies/PatternRecognition.py — main timeframe 1d — detail timeframe 15m
6. user_data/strategies/Supertrend.py — main timeframe 1h — detail timeframe 15m

Do not measure these excluded candidates:
- BreakEven.py — exact 5m data absent
- Diamond.py — exact 5m data absent
- PowerTower.py — exact 5m data absent
- Strategy004.py — exact 5m data absent
- GodStra.py — exact 12h data absent

PRE-RUN GATE: MUST PASS BEFORE ANY TRIAL ID

Before creating any trial ID or running any candidate over data, perform and report all of the following:

1. Verify the exact v2.1 package SHA-256.
2. Verify the immutable ledger N=898, last_sequence=898, and canonical hash.
3. Verify the hash-locked runtime installation in a clean CPython 3.12.3 environment and run the dependency integrity check.
4. Verify the pinned Freqtrade engine commit and critical engine file hashes.
5. Verify the pinned technical commit and Supertrend source hash:
   8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838
6. Verify the approved strategy source commit and every declared source snapshot hash.
7. Verify the exact main and 15m detail CSV availability, byte size, and SHA-256.
8. Verify the Bybit instrument metadata artifact, response hashes, tick sizes, quantity steps, minimum quantities, and minimum notionals.
9. Verify static pairlist enforcement and reject dynamic pairlist behavior.
10. Verify no resampling, no candidate-specific override, no unlisted configuration override, and no framework-default substitution.
11. Verify Freqtrade-native startup-candle trimming and fail closed if any candidate lacks required startup history.
12. Verify engine-native exit-signal, stoploss, ROI, trailing-stop, custom-stoploss, order-fill, and detail-timeframe semantics.
13. Verify the pinned Supertrend implementation inside the locked environment.
14. Run the deterministic semantic parity fixtures and require 13/13 pass.
15. Run the repository/schema/hash validators and require all protected-artifact checks to pass.

If any pre-run gate fails, do not partially measure the batch and do not create trial IDs. Return REQUEST_APPROVAL or FAIL_CLOSED with the exact failed gate.

MEASUREMENT RULES

Only after every pre-run gate passes may you create new trial identities. Create new IDs strictly after immutable ledger sequence 898, never reuse historical IDs, and include at minimum:
- package ID and package SHA-256
- runtime lock SHA-256
- engine commit and critical file hashes
- technical commit and Supertrend file hash
- strategy source commit and source snapshot hash
- exact main/detail manifest references and CSV hashes
- execution-manifest canonical SHA-256
- static venue/pairlist scope
- precision/limits metadata SHA-256
- strategy path and declared main/detail timeframes
- protocol version

The expected trial increment is at most +6, one per authorized candidate, and only if all six pre-run gates pass. Do not create trial IDs for failed, excluded, or unmeasured candidates.

Run a full engine-native Freqtrade measurement only. Do not use the old compatibility harness and do not describe compatibility-harness output as full Freqtrade equivalence.

Use the frozen execution assumptions without tuning:
- fixed notional sizing
- frozen risk and notional caps
- frozen commission, slippage, spread, fill, latency, funding proxy, leverage, and rounding rules
- exact Bybit precision/minimum-limit behavior
- exact closed-bar signal timing and next-bar-open fill behavior
- exact 15m detail execution
- fail-closed missing-data and invalid-bar behavior

Do not optimize, tune, select, or alter any candidate-specific parameter. Do not change the date window, pairlist, timeframe, detail mapping, costs, fill model, latency, risk budget, or exchange assumptions.

POST-RUN BOUNDARY

After the one measured batch completes:
- Stop immediately.
- Do not run WFO.
- Do not run cost stress.
- Do not calculate DSR, PBO, CPCV, or any statistical selection metric.
- Do not promote any candidate.
- Do not paper trade, live trade, deploy, or connect to an exchange for trading.
- Do not run a second batch.

Create only additive measurement artifacts and the new ledger append required by the existing protocol. Preserve all historical artifacts. Recompute and report the new ledger hash, but do not alter historical trial records.

SELF-AUDIT AND FINAL REPORT

Before finalizing, conduct an explicit internal audit and report the result in this structure:

- Primary Analyst claim
- Strongest Adversarial Auditor objection
- Evidence for and against
- Resolution
- Confidence and remaining uncertainty
- Exact candidate/trial distribution
- Any failed or excluded candidate and precise reason
- New ledger N, last_sequence, and hash
- Protected-artifact status
- Exact files and hashes created
- Confirmation that no WFO, cost stress, DSR/PBO/CPCV, promotion, paper/live trading, or deployment occurred
- The next required authorization, if any

Final output must be one of:
- MEASURED_BATCH_COMPLETE — only if the authorized batch completed under every exact frozen input; or
- REQUEST_APPROVAL — if any required gate or artifact condition remains unresolved; or
- FAIL_CLOSED — if an integrity, data, source, runtime, precision, limits, engine, or policy mismatch is detected.

Do not infer profitability, robustness, statistical significance, or deployability from this first measured batch.
```

## ব্যবহার নির্দেশনা

এই prompt পাঠানোর পরে Manus AI-কে আরেকটি আলাদা “continue” বা “run” prompt পাঠাবেন না। Manus-কে অবশ্যই pre-run gate pass করে একবারেই থামতে হবে। কোনো hash mismatch, missing file, runtime difference, precision-limit ambiguity বা engine-semantic failure হলে measurement বন্ধ থাকবে।

প্রথম batch-এর output পাওয়ার পর সেটি আলাদাভাবে audit না করা পর্যন্ত promotion বা statistical analysis-এর authorization দেবেন না।
