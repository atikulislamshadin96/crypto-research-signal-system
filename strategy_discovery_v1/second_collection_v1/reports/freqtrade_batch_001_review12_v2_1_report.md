# Freqtrade Batch 001 — Review of 12 Non-Rejected Records

**Status:** completed; source-rule evidence review only
**Source:** `https://github.com/freqtrade/freqtrade-strategies`
**Pinned commit:** `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`
**License:** GPL-3.0
**Input evidence:** `freqtrade_batch_001_pinned_source_evidence_v2_1.json`
**Review queue:** `freqtrade_batch_001_review12_v2_1.json`

## Final decision

The 12 records that did not trigger the primary lagging-indicator rejection were reviewed against the fuller pinned source checkout. All 12 have explicit entry logic, exit logic, and stop/target or time-exit evidence. Eleven have explicit timeframe evidence. However, none has an explicit instrument applicability or pair/universe rule in the strategy source class. Under the frozen source-rule contract, this is a required source fact and cannot be silently replaced by a Freqtrade framework or external config default.

| Source-rule result | Count |
| --- | ---: |
| `source_rule_complete` | 0 |
| `execution_assumption_required` | 0 |
| `needs_review` | 12 |
| `rejected_incomplete` | 0 |

The 12 records remain `needs_review`, not because their entry/exit mechanics are absent, but because instrument applicability is not established. One record also lacks a literal source timeframe assignment.

## Reviewed records

| Record | Entry | Exit | Stop/target/time exit | Timeframe | Instrument applicability | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `BreakEven.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `CustomStoplossWithPSAR.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `Diamond.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `FixedRiskRewardLoss.py` | explicit | explicit | explicit | not found | not found | `needs_review` |
| `GodStra.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `Heracles.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `HourBasedStrategy.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `MultiMa.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `PatternRecognition.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `PowerTower.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `Strategy004.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |
| `Supertrend.py` | explicit | explicit | explicit | explicit | not found | `needs_review` |

## Primary Analyst claim

The source re-fetch resolved the prior short-snippet limitation for these records. The extractor verified each source file hash against the immutable historical batch and used full temporary AST/control-flow analysis. The entry and exit methods are directly evidenced, and the missing instrument-applicability status is a genuine source-contract gap rather than a parser failure for these 12 records.

## Adversarial Auditor objection

A Freqtrade strategy file may intentionally rely on the user’s configured pairlist and venue rather than declaring a pair universe in the strategy class. Treating that framework behavior as an explicit source rule would be convenient but would violate the no-default and no-inference policy. Conversely, rejecting the strategies as intrinsically unusable would overstate the evidence; a frozen batch-level applicability/execution manifest could potentially define the research universe later, if the policy explicitly permits that mapping and records it as `external_assumption`.

## Resolution

The conservative `needs_review` result is retained under the current policy because the current source-rule gate requires instrument applicability or pair scope. No candidate is promoted to `source_rule_complete`, and no execution-assumption status is issued. If the project owner wants Freqtrade pairlist/venue scope to be supplied by the common research harness, that must be a separately versioned policy decision before reassessment; it cannot be introduced silently during this review.

## Evidence and safety checks

All 12 source hashes matched the historical Batch 001 hashes. The evidence artifact retains only structured fields, exact pinned GitHub locators, and short snippets of at most eight lines. The 13 `filter_rejected_primary` records from the full 25-record batch were not changed by this review.

No market data was acquired. No Freqtrade engine was executed. No backtest, paper/live trade, trial creation, ledger update, DSR/PBO/CPCV calculation, candidate promotion, or deployment occurred. The global ledger remains `N=893` with `last_sequence=893` and hash `0767031c0bed43719415ac419de4d13ce20e6e72a95f52116ad388d465940ab7`.

## Next-task packet

```text
Next Task Title:
Policy decision on Freqtrade instrument applicability as a batch-level research assumption

Objective:
Decide whether Freqtrade strategies that use the configured pairlist/venue may satisfy
instrument applicability through one pre-frozen, uniformly applied research manifest,
while preserving explicit source-rule evidence and no candidate-specific defaults.

Allowed now:
Policy analysis, schema review, versioned amendment design, and no-trial diagnostics.

Approval required for measurement:
A complete source-rule policy, frozen execution-assumption manifest v1.1,
reconfirmed OHLCV manifest references, and separate explicit backtest authorization.

Current state:
13 filter_rejected_primary; 12 needs_review; 0 source_rule_complete;
ledger N=893; no measured trials.

Stop conditions:
Do not treat Freqtrade framework defaults as source facts. Do not backtest, acquire market data,
create trials, update the ledger, calculate DSR/PBO/CPCV, or promote candidates.
```
