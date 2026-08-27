# Freqtrade Batch 001 — Flexible Completeness Reassessment v2

**Status:** analysis-only readiness diagnostic; no backtest or promotion occurred.  
**Input:** immutable `freqtrade_raw_batch_001.json`  
**Source:** `https://github.com/freqtrade/freqtrade-strategies`  
**Pinned source commit:** `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`  
**License recorded by the batch:** GPL-3.0  
**Reassessment version:** `freqtrade_strategy_v2_flexible_completeness`

## Result

The new rules distinguish explicit strategy logic from missing execution-environment assumptions. The reassessment consumed only the existing 25 structured records and their retained short evidence snippets. It did not acquire new source, run a backtest, download market data, create trials, modify the historical filter result, or change the global ledger.

| Reassessment status | Count |
| --- | ---: |
| `filter_rejected_primary` | 0 |
| `source_rule_complete` | 0 |
| `execution_assumption_required` | 0 |
| `needs_review` | 25 |
| `rejected_incomplete` | 0 |

All 25 records were conservatively placed in `needs_review` because the retained entry fragments were bounded excerpts and could not be parsed as complete, auditable AST/control-flow evidence. This is not a finding that the underlying strategies lack deterministic rules. It is a finding that the existing short-fragment evidence is insufficient to establish the primary entry condition under the new mechanical contract.

## Policy change applied

A source may now be classified as `source_rule_complete` when explicit evidence establishes the strategy logic—timeframe, entry condition, exit condition, and stop/target or other explicit exit behavior—even if execution-environment values are absent from the source. Missing sizing, risk budget, fees, spread, slippage, fill, latency, funding/borrow, external configuration, and data-handling behavior are recorded as `execution_assumption_required` rather than guessed.

A separate, single batch-level execution-assumption manifest must be frozen before a candidate can become `execution_contract_complete`. Its values must apply uniformly to the batch, be labelled `external_assumption`, and be included in the measured-trial identity. The template in `execution_assumption_manifest_v1.template.json` is intentionally not frozen and is not sufficient to authorize a backtest.

The lagging-indicator taxonomy was not relaxed. The new classifier inspects only the direct entry-condition AST/control-flow fragment; imports and whole-file indicator summaries are not enough. An explicit primary lagging-indicator condition would remain `filter_rejected_primary`. An opaque, truncated, or unparsable fragment is `needs_review`.

## Ledger and authorization boundary

The global ledger remains at **N=893**. No measured trial was appended. The existing `freqtrade_filtered_batch_001.json` and all historical collection artifacts remain immutable. Any later measured run must first use a frozen execution-assumption manifest, re-confirm the existing OHLCV manifest and hashes, start from ledger N=893, and use the frozen DSR/PBO/CPCV protocol. This reassessment alone authorizes none of those actions.
