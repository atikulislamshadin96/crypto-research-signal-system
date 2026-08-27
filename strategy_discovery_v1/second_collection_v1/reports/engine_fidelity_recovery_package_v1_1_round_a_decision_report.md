# Finite Recovery Package v1.1 — Round A Candidate Amendment

**Status:** `ROUND_A_REGISTRY_VALIDATED_REQUEST_MEASUREMENT_APPROVAL`
**Scope:** Candidate-registry amendment and audit only; no market-data acquisition, adapter execution, backtest, trial ID, statistics, ledger append, promotion or trading.
**Parent package:** `strategy_discovery_v1_recovery_package_v1`
**Parent baseline commit:** `5225f00b01fc37228c4326bd36bf0ed1b5f3a15a`

> **Finance disclaimer:** I am an AI, not a licensed financial advisor—this is research analysis, not guaranteed financial advice; trading losses remain possible.

## Primary Analyst claim

Option B has been implemented as a deterministic source-family amendment. The official `QuantConnect/Lean` repository was audited at commit `07fb0182bfe229edd9445cf675ac6509d0069539`, and six Round A candidates were frozen by path ordering and exact-scope eligibility—not by backtest result, visual appeal or analyst preference. The amendment adds only the missing candidate identities and source snapshot hashes; all finite-budget, CPCV, holdout, cost and survivor rules are inherited unchanged from the validated parent package.

The six candidates are all bound to a fixed `1d` main timeframe and `15m` detail timeframe for the existing Bybit linear-perpetual scope. Their QuantConnect-to-Freqtrade adapter implementations are **not yet measured or authorized**. Before any future measurement, those adapters must be created, hashed and independently audited; a candidate that cannot be mapped faithfully fails closed.

## Strongest Adversarial Auditor objection

The source repository is an independent implementation family, but QuantConnect Alpha Framework models are not native Freqtrade strategies. Translating Alpha insights, pair handling, resolution semantics and portfolio behavior into Freqtrade can introduce semantic drift. The registry therefore cannot be treated as proof that these are already executable Freqtrade candidates. A second objection is that `ConstantAlphaModel` is intentionally non-selective and may be a weak economic baseline rather than a plausible alpha source.

**Resolution:** Both objections are accepted. The amendment freezes these six mechanically ordered source candidates because the finite plan requires a bounded, non-cherry-picked Round A—not because they are expected to be profitable. Adapter fidelity is a separate hard gate. `ConstantAlphaModel` remains because deterministic ordering must not be altered after observing expectations; it is a baseline candidate and can fail the survivor gates. No result-based substitution is allowed.

## Source-family evidence and licensing boundary

The official QuantConnect repository is [QuantConnect/Lean][1]. Its repository page identifies LEAN as QuantConnect’s algorithmic trading engine and exposes the `Algorithm.Framework/Alphas` directory. The official Alpha documentation describes built-in Null, Constant, Historical Returns, EMA Cross, MACD, RSI, Base Pairs Trading and Pearson Correlation Pairs Trading models.[2] The source repository’s license page identifies Apache License 2.0 and requires preservation of notices and attribution conditions.[3]

The separate AlphaStreams SDK was not used. Only candidate metadata, source paths, commit identity, file hashes and fixed adapter parameters are retained in this repository; full third-party source is not vendored.

## Deterministic eligibility rule

The registry enumerates Python files in `Algorithm.Framework/Alphas`, normalizes repository paths, sorts them bytewise lexically, requires a deterministic executable AlphaModel class, applies the current exact-timeframe rule, and takes the first six eligible paths. `Resolution.DAILY` maps to `1d`. `Resolution.MINUTE` is ineligible because the current scope has no exact 1-minute main data and resampling is prohibited. The resulting sequence is therefore mechanical.

| Rank | Candidate ID | Source path | Source class | Source snapshot SHA-256 | Adapter main/detail |
|---:|---|---|---|---|---|
| 1 | `quantconnect-lean-round-a-001-basepairs-1d` | `Algorithm.Framework/Alphas/BasePairsTradingAlphaModel.py` | `BasePairsTradingAlphaModel` | `4946e12eb3ef36dbb7695bf754bd58408915c397a8a50c5f233a6e5fa076f166` | `1d / 15m` |
| 2 | `quantconnect-lean-round-a-002-constant-1d` | `Algorithm.Framework/Alphas/ConstantAlphaModel.py` | `ConstantAlphaModel` | `4630051dbf3655a9476c41b3358f71570013aa8bb4abcd22cacee50b2e80ea65` | `1d / 15m` |
| 3 | `quantconnect-lean-round-a-003-emacross-1d` | `Algorithm.Framework/Alphas/EmaCrossAlphaModel.py` | `EmaCrossAlphaModel` | `9779224202a749e0371049239a9a975390af36a536f3674775f07a630b4f9d08` | `1d / 15m` |
| 4 | `quantconnect-lean-round-a-004-historicalreturns-1d` | `Algorithm.Framework/Alphas/HistoricalReturnsAlphaModel.py` | `HistoricalReturnsAlphaModel` | `43004946edfd02dbcb0010a6bde405ac9f65b3fbcfaed82c2065911300bee5d9` | `1d / 15m` |
| 5 | `quantconnect-lean-round-a-005-macd-1d` | `Algorithm.Framework/Alphas/MacdAlphaModel.py` | `MacdAlphaModel` | `978fa9eb1f5cf9d0051f27e1e765c897ee580a06d2a71f7ade14a3318e954a13` | `1d / 15m` |
| 6 | `quantconnect-lean-round-a-006-rsi-1d` | `Algorithm.Framework/Alphas/RsiAlphaModel.py` | `RsiAlphaModel` | `5cba110dc89dffe8ef6f4c386a25ce25c896e04d4616a4809041604652294c15` | `1d / 15m` |

The fixed source-compatible parameters are recorded in the registry. They are not tunable parameters: Base Pairs uses `lookback=1`, `threshold=1`; Constant uses explicit `PRICE/UP/1-day`; EMA Cross uses `fast=12`, `slow=26`; Historical Returns uses `lookback=1`; MACD uses `12/26/9/Exponential`; and RSI uses `period=14`.

`PearsonCorrelationPairsTradingAlphaModel.py` is excluded before measurement because its declared default is `Resolution.MINUTE`, which is outside the exact current timeframe scope. Its source SHA-256 is `9cb269d82d8cbd7bd44ccc98c7168a17b9bc2603f2fffa1a8814a2916b2b890e`. It is not counted as a strategy-family failure.

## Exact amendment hashes and inherited state

| Artifact | Exact value |
|---|---|
| Amendment package canonical SHA-256 | `c44dcd528f581c97d34dd8315a925f0b69b300519b38526269227ccb4b1ae27d` |
| Amendment package actual file SHA-256 | `be4b689fee659f21c8dc2f96c85b83d7e5eac7253a7e742f54b90bfd1fb7761d` |
| Amendment schema actual SHA-256 | `b2fbb3e214bb82b7f9137e85f1148c09a25271d707d9b19bc5bd50847fcbbdf8` |
| Candidate registry actual SHA-256 | `ad1326f94606a4f84a2bf6efb42b383c5af7a0388e80c923f4b86e8134e778d0` |
| Amendment validator actual SHA-256 | `eca6740a1b42869b80080da56762c85067df39e14053924e1f23d5dad7fe87c8` |
| Parent recovery package canonical SHA-256 | `fcf677c23199e3e9d4b024bc9ff4a09f0603ede6bc3326ca0815f9bd58119adc` |
| Parent recovery package actual file SHA-256 | `57a7269117bbeb41e89986e2ac90725a5ed56e710912e88d0443717bb8f9e16c` |
| Parent ledger baseline | `N=904`, `last_sequence=904` |
| Parent ledger canonical SHA-256 | `9e71eb377be3c15dd5d29bc09cac561ae1f837fc44fd136662db0d751062790e` |
| QuantConnect source commit | `07fb0182bfe229edd9445cf675ac6509d0069539` |
| QuantConnect source license | Apache-2.0 |

The inherited policy remains: additional valid candidate budget `18`, three rounds of six, hard cancellation after `18/18` additional valid failures, 30 attempted leads with at least 18 valid measurable candidates, 12 chronological CPCV groups, 66 splits, 11 paths, 30-day purge/embargo, minimum 60 training observations, untouched holdout, native `--fee` base `0.00055` plus the frozen sensitivity ladder, no price/return modification, and exact survivor gates.

## Audit results

| Check | Result |
|---|---|
| Exact baseline commit and remote synchronization | Pass |
| Parent package canonical/file hash | Pass |
| Candidate registry source commit | Pass |
| Six source snapshot hashes | Pass |
| Official repository remote identity | Pass |
| Apache-2.0 license page review | Pass |
| Deterministic path ordering | Pass |
| Exact six eligible candidates | Pass |
| Pearson minute-resolution exclusion | Pass |
| Amendment JSON Schema conformance | Pass |
| Amendment canonical self-hash | Pass |
| Inherited parent policy equality | Pass |
| All measurement/trial/statistics/ledger flags | False / not authorized |

## No-measurement boundary

This amendment phase acquired and audited only public source code for candidate identity purposes. It did not acquire market data, create Freqtrade adapters for execution, run any strategy on market data, run a backtest, create trial IDs, append the ledger, calculate DSR/PBO/CPCV, run WFO, run cost stress, select a candidate, promote, paper trade, live trade or deploy.

The amendment remains `frozen_pre_measurement`; `measurement_authorized=false`, `trial_ids_created=false`, `ledger_changed=false` and `statistics_run=false`. A future Round A measurement requires a separate authorization after adapter implementation and adapter-integrity validation.

## Decision and next authorization

**Decision state:** `ROUND_A_REGISTRY_VALIDATED_REQUEST_MEASUREMENT_APPROVAL`.

The exact candidate-identity blocker has been resolved additively. The research direction is still not proven profitable; this amendment only creates a fair, bounded test set. The next safe task is adapter construction and audit, not immediate backtesting.

### Separate future measurement authorization prompt

> I separately authorize preparation and audit of deterministic Freqtrade adapters for the six frozen Round A candidates under amendment package `strategy_discovery_v1_recovery_package_v1_1_round_a`, canonical SHA-256 `c44dcd528f581c97d34dd8315a925f0b69b300519b38526269227ccb4b1ae27d`. Do not run a backtest, acquire market data, create trial IDs, append the ledger, calculate statistics, run WFO/cost stress, select, promote or trade. First prove source-to-Freqtrade semantic mapping, hash every adapter, and stop for a separate measurement authorization.

## References

[1]: https://github.com/QuantConnect/Lean "Official QuantConnect LEAN repository"
[2]: https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/alpha/supported-models "QuantConnect Alpha Framework supported models"
[3]: https://github.com/QuantConnect/Lean/blob/master/LICENSE "QuantConnect LEAN Apache-2.0 license"

**Compliance:** This is research and analysis only, not personalized financial advice.
