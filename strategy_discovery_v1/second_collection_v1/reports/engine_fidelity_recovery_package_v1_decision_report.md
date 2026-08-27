# Finite Recovery Package v1 — Decision and Audit Report

**Status:** `RECOVERY_PACKAGE_VALIDATED_REQUEST_MEASUREMENT_APPROVAL`
**Scope:** Package creation and validation only; no candidate measurement was authorized or performed.
**Starting commit:** `5225f00b01fc37228c4326bd36bf0ed1b5f3a15a`

> **Finance disclaimer:** I am an AI, not a licensed financial advisor—this is research analysis, not guaranteed financial advice; trading losses remain possible.

## Primary Analyst claim

A bounded recovery package has been created and structurally audited. It allows one final, finite attempt to test whether this specific source/signal research direction can produce a cost-aware and statistically defensible candidate. The package permits **18 additional valid candidate families only**, divided into **three rounds of six**. If all 18 valid additional candidates fail the pre-declared survivor gates, the current research direction must be cancelled. No additional candidate search is allowed after that cutoff.

The package does not claim that a profitable strategy exists. The current evidence remains that v2.4 produced no validated profitable/reliable strategy: six of six candidates had negative native net results, and all six DSR gates failed. The package is therefore a finite recovery mechanism, not an automatic continuation license.

## Strongest Adversarial Auditor objection

The strongest objection is that the proposed repaired CPCV topology, untouched holdout boundary and cost-sensitivity ladder are **design constraints only** at this stage. They have not yet been run on a new candidate batch, and the pinned engine still has no global fixed adverse-slippage control. The base `slippage=0.0` policy can therefore never be interpreted as realistic frictionless execution. A second objection is that a fixed cutoff such as 18 candidates is a governance choice rather than a statistical theorem.

**Resolution:** The objections are accepted and explicitly bounded. The package labels the state `frozen_pre_measurement`, keeps all authorization flags false, requires a new authorization before measurement, and treats the 18-candidate budget as a pre-committed research-spend limit—not as evidence of future profitability. The package also requires a native fee sensitivity ladder and an untouched temporal holdout; failure of any gate fails the candidate family.

## Exact package and protected baseline

| Artifact | Exact value |
|---|---|
| Recovery package canonical SHA-256 | `fcf677c23199e3e9d4b024bc9ff4a09f0603ede6bc3326ca0815f9bd58119adc` |
| Recovery package actual file SHA-256 | `57a7269117bbeb41e89986e2ac90725a5ed56e710912e88d0443717bb8f9e16c` |
| Recovery schema actual SHA-256 | `d2c94f1970d1b6daaf6a75603d161aa7d2afbb669e6a0a0aa32cc3293c4de31a` |
| Recovery validator actual SHA-256 | `c030f4a3a63ba3f3ec7b0ad3a8446a0e8902e4cc1a8ce2d536126ad91a1c70a5` |
| Parent v2.4 package canonical SHA-256 | `ed2d4a8f4adfbd775e7b394649e57ed295dcceea05b6c5fc3624c02626bd5361` |
| Parent v2.4 package actual file SHA-256 | `b13d502783ed0c58e460c2bffb783faaf8da0763d39ad79ba8783c6c0cfbacaf` |
| Starting ledger state | `N=904`, `last_sequence=904` |
| Starting ledger canonical SHA-256 | `9e71eb377be3c15dd5d29bc09cac561ae1f837fc44fd136662db0d751062790e` |
| Starting ledger actual file SHA-256 | `1f51cb9b6c3e2d151d00054c9822cd0becf7b896bd406010f62ec585d388fae7` |
| Parent v2.4 statistics artifact actual SHA-256 | `d4299f96ba112a6e3a8c7be577a3e2278d38cb4d6fd44c9f0dfca7d9377fbfe6` |
| Frozen protocol SHA-256 | `c45a37fe99a2d5a8407e8c889ead173b8626ef53748930d2f5970a272782070e` |

The package is additive. It does not overwrite the v2.4 package, v2.4 execution manifest, v2.4 measurement artifacts, v2.4 statistical artifacts, historical statistics, or the global ledger.

## Finite budget and cancellation rule

| Rule | Frozen value |
|---|---:|
| Existing v2.4 failed candidate families | 6 |
| Additional valid candidate-family budget | **18** |
| Number of recovery rounds | 3 |
| Maximum candidates per round | 6 |
| Hard cancellation threshold | **18/18 additional valid candidates fail** |
| Maximum attempted leads | 30 |
| Minimum valid measurable candidates from those attempts | 18 |
| Maximum total measured-family budget including existing v2.4 | 24 |

A candidate family counts as a failure only after a valid native measurement exists and at least one survivor gate fails. Incomplete or invalid leads do not count as economic failures, but they consume the separate source-quality budget. If 18 valid measurable candidates cannot be obtained from 30 attempted leads, the current source universe is cancelled for insufficient executable supply.

The three rounds are `recovery_A`, `recovery_B` and `recovery_C`. Each has a maximum of six pre-registered candidate families. Candidate substitution after observing results is prohibited. The 18-candidate budget is hard: after Round C, no additional search under this direction is permitted without a new research thesis and a new authorization.

## Repaired CPCV design

The package defines a new, not-yet-executed protocol identifier: `dsr_pbo_cpcv_v2_12x2`. Its structural design is:

| Parameter | Frozen value |
|---|---:|
| Chronological groups | 12 |
| Test groups per split | 2 |
| Total splits | 66 |
| PBO paths | 11 |
| Purge | 30 days |
| Embargo | 30 days |
| Minimum training observations | 60 daily observations |
| Training rule | Any split below 60 training observations invalidates the package |
| Group assignment | Contiguous chronological groups; no random shuffling |
| Fit isolation | Transform and selection logic fit on training data only |

The 11 paths use a deterministic round-robin factorization of all `66` unordered pairs of the 12 groups. Each path contains six disjoint test pairs and every group pair appears exactly once. The audit confirmed `11` paths, `66` splits/pairs, no duplicate pair and no missing pair. This is a structural validation only; no CPCV return analysis was run in this package task.

## Untouched holdout rule

The package reserves a temporal holdout from `2026-06-23T00:00:00Z` through `2026-08-22T00:00:00Z` exclusive, with a minimum of 60 observations. The holdout cannot be used for rule selection, parameter tuning, candidate substitution or post-hoc repair. A candidate that fails positive after-cost holdout performance fails the survivor gate. This holdout policy is frozen before any future candidate measurement.

## Native-compatible cost gate

The package retains the pinned Freqtrade engine and uses its native `--fee` mechanism. The base fee is `0.00055` per side, with a pre-declared sensitivity ladder of `0.00055`, `0.00075` and `0.001` per side. No price modification, return post-processing or engine patch is allowed. The package records that the pinned engine has no global fixed adverse-slippage control; therefore `slippage=0.0` remains a limitation rather than a claim of realistic execution.

A future survivor must pass the pre-declared fee variants; a favorable fee variant cannot be selected after seeing results. The package does not authorize those future runs. It only freezes the gate.

## Exact survivor gates

A candidate family survives only if every gate passes:

| Gate | Requirement |
|---|---|
| Executability | Deterministic rules, exact data, native engine run and complete immutable artifact |
| After-cost economics | Positive total net return under the native base fee policy |
| Both-pair result | Positive after-cost result separately on both BTC/USDT:USDT and ETH/USDT:USDT |
| Activity floor | At least 30 trades for 1h/4h or 12 trades for 1d across the two pairs |
| DSR | DSR `>=0.95` using the full immutable ledger count at the decision point |
| CPCV/PBO | PBO `<=0.10` under the repaired protocol, with no invalid split |
| Untouched holdout | Positive after-cost result on the untouched holdout |
| Concentration | Result cannot depend solely on one pair or one isolated trade |

Failure of any one gate fails the candidate family. No post-result relaxation is permitted. A survivor is only eligible for a later independent review; it is not automatically selected, promoted or traded.

## Audit evidence

The following package-only checks passed:

| Check | Result |
|---|---|
| Clean baseline at `5225f00b01fc37228c4326bd36bf0ed1b5f3a15a` | Pass |
| Local and remote baseline synchronized | Pass |
| Ledger `N=904`, `last_sequence=904`, canonical hash preserved | Pass |
| Protected parent hashes | Pass |
| Recovery schema JSON syntax | Pass |
| Recovery package JSON syntax | Pass |
| JSON Schema conformance | Pass |
| Package canonical self-hash | Pass |
| 12-group/11-path/66-pair factorization | Pass |
| All authorization and current-state flags false | Pass |
| Candidate measurement/trial/statistics/ledger operations | Not run by design |

The first package build attempt exposed and corrected a factorization bug before validation; the final package contains the corrected complete 66-pair factorization. The validator path issue was also corrected before the final pass. These are implementation fixes, not changes to the declared recovery rules.

## No-measurement proof

No new market data was acquired. No strategy was executed over market data. No backtest, trial ID, statistics, WFO, cost stress, ledger append, candidate selection, promotion, paper trading, live trading or deployment occurred. The package state explicitly binds `measurement_authorized=false`, `trial_ids_created=false`, `ledger_changed=false` and `statistics_run=false`.

## Decision and next authorization

**Current decision:** `RECOVERY_PACKAGE_VALIDATED_REQUEST_MEASUREMENT_APPROVAL`.

The package is ready for review, not for execution. The current v2.4 evidence still contains no validated profitable/reliable strategy. The recovery plan creates one bounded final attempt; it does not promise a winner. If all 18 additional valid candidates fail, the current research direction must be cancelled.

### Separate future measurement authorization prompt

> I separately authorize **Round A only** under the exact validated finite recovery package `strategy_discovery_v1_recovery_package_v1`. Use the exact package canonical SHA-256 `fcf677c23199e3e9d4b024bc9ff4a09f0603ede6bc3326ca0815f9bd58119adc`, starting commit `5225f00b01fc37228c4326bd36bf0ed1b5f3a15a`, and the frozen parent ledger state `N=904`, canonical hash `9e71eb377be3c15dd5d29bc09cac561ae1f837fc44fd136662db0d751062790e`. Measure only the six pre-registered Round A candidate families after re-running all package gates. Do not acquire data, alter assumptions, use dynamic pairlists, resample, forward-fill, modify OHLCV, post-process returns, patch the engine, create extra candidates, append the ledger, run statistics, promote, paper trade, live trade or deploy unless separately authorized. Stop after the six Round A artifacts are validated and request separate authorization for any Round B or statistical analysis.

## References

[1]: https://github.com/atikulislamshadin96/crypto-research-signal-system/blob/5225f00b01fc37228c4326bd36bf0ed1b5f3a15a/strategy_discovery_v1/second_collection_v1/reports/engine_fidelity_statistics_v2_4_report.md "Immutable v2.4 statistical report"
[2]: https://github.com/atikulislamshadin96/crypto-research-signal-system/blob/5225f00b01fc37228c4326bd36bf0ed1b5f3a15a/strategy_discovery_v1/protocols/dsr_pbo_cpcv_v1.json "Frozen DSR/PBO/CPCV protocol"

**Compliance:** This is research and analysis only, not personalized financial advice.
