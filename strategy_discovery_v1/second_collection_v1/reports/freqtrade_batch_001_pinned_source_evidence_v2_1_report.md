# Freqtrade Batch 001 — Pinned-Source Evidence Extraction v2.1

**Status:** completed; evidence extraction only
**Approved source:** `https://github.com/freqtrade/freqtrade-strategies`
**Pinned commit:** `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`
**License:** GPL-3.0
**Batch:** existing 25-record `freqtrade-strategies-001` only
**Extraction version:** `deterministic_rule_extraction_v2_1`

## Authorization boundary

The user authorized re-fetching only the pinned Freqtrade commit for evidence extraction, explicitly excluding backtesting and trial creation. The temporary source checkout was used only as input. No full third-party source file was copied into the repository. The committed artifact contains structured fields, source hashes, exact GitHub path/commit locators, and short evidence snippets of at most eight lines.

No market data was downloaded. No Freqtrade engine was executed. No backtest, paper/live trade, DSR/PBO/CPCV calculation, trial creation, ledger update, candidate promotion, or deployment occurred.

## Source verification

| Check | Result |
| --- | --- |
| Repository remote | `https://github.com/freqtrade/freqtrade-strategies.git` |
| Checked-out commit | `eff78d3ce3456b52c68a4e9a33cc055a56b801ff` |
| Commit verification | Exact authorized SHA matched `HEAD` |
| License | Repository `LICENSE` begins with GNU GPL Version 3, recorded as GPL-3.0 |
| Selected records | Existing 25 paths only; no expansion to the remaining repository files |
| Source hash verification | All 25 re-fetched file hashes matched the historical raw-batch hashes |

## Classification result

| Re-evaluation status | Count |
| --- | ---: |
| `filter_rejected_primary` | 13 |
| `source_rule_complete` | 0 |
| `execution_assumption_required` | 0 |
| `needs_review` | 12 |
| `rejected_incomplete` | 0 |

The 13 `filter_rejected_primary` records have direct entry-condition evidence containing a lagging-indicator field or resolved condition token, with exact bounded source spans retained in the artifact. The 12 non-rejected records passed the primary-signal check but remain `needs_review` because source instrument applicability or, for one record, timeframe evidence was not established under the current source-rule gate. Therefore no record reached `source_rule_complete` or `execution_assumption_required`.

This result is not a claim that the source repository contains no usable strategies. It means the current mechanical gate either found a prohibited primary signal or could not establish every required source-rule field. Missing execution fields were not filled and were not used to reject the source-rule evidence prematurely.

## Primary Analyst claim

The authorized source re-fetch resolved the previous evidence-shortage problem. The extraction now uses full temporary source AST/control flow, verifies every file hash against the immutable historical batch, captures exact direct entry-condition spans, and retains only bounded snippets. The primary-signal classification is materially more auditable than the prior whole-file token summary.

## Adversarial Auditor objection

The adapter remains conservative and has known limits. It recognizes simple local condition assignments and list `append`/`extend` patterns, but a framework or helper abstraction not deterministically resolved from the source method may remain ambiguous. Some indicator-like variable names can be semantically broad; the rejection evidence must therefore be reviewed as direct condition spans, not accepted solely from token names. The current extractor also does not create normalized executable candidates and does not prove that a strategy would be correctly interpreted by the Freqtrade engine.

## Resolution

The classification is accepted as an evidence-stage result, not a performance or execution-stage result. The 13 primary rejections remain rejected under the unchanged taxonomy. The 12 pass-through records remain review-only until instrument applicability and all other source-rule requirements are explicitly evidenced. Execution assumptions remain separate and unfrozen. No ledger action is appropriate because no measured trial occurred.

## No-trial invariants

| Invariant | Value |
| --- | --- |
| `analysis_only` | `true` |
| `backtest_run` | `false` |
| `market_data_downloaded` | `false` |
| `trial_created` | `false` |
| `trial_ledger_n` | `893` |
| Global ledger `last_sequence` | `893` |
| Global ledger hash | `0767031c0bed43719415ac419de4d13ce20e6e72a95f52116ad388d465940ab7` |

## Validation

The extractor compiled successfully. All 25 source hashes matched the historical raw batch. There were 200 field claims. Every retained evidence excerpt and every direct primary-condition excerpt was between one and eight lines. The repository test suite remained passing before commit, and the protected historical artifacts were not used as write targets.

## Next task packet

```text
Next Task Title:
Review the 12 non-rejected Freqtrade records for source-rule completeness

Objective:
Audit the 12 records marked needs_review, focusing on explicit instrument applicability,
missing timeframe evidence, exit semantics, and any unresolved helper/control-flow paths.

Allowed action:
Read-only review of the already pinned source checkout or an exact re-fetch of the same
commit only if separately authorized. Produce evidence corrections as versioned artifacts.

Not authorized:
Backtest, market-data acquisition, trial creation, ledger update, DSR/PBO/CPCV,
promotion, deployment, or trading.

Current starting state:
13 filter_rejected_primary; 12 needs_review; 0 source_rule_complete;
ledger N=893; no measured trials.

Before any measured run:
A complete source-rule classification, a frozen execution-assumption manifest v1.1,
reconfirmed OHLCV manifest references, and separate explicit backtest authorization are required.
```
