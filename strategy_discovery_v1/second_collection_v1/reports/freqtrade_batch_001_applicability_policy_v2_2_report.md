# Freqtrade Batch 001 — Applicability Policy Decision v2.2

**Decision:** accept a uniformly frozen external research scope for Freqtrade applicability
**Source:** `https://github.com/freqtrade/freqtrade-strategies`
**Pinned commit:** `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`
**Input:** `freqtrade_batch_001_pinned_source_evidence_v2_1.json`
**Mode:** no-trial policy reassessment

## Final decision

The configured Freqtrade pairlist, venue/exchange, quote currency, and research timeframe scope may be supplied by one batch-level research harness. These values are **external assumptions**, not source facts. They must be declared explicitly, frozen before measurement, hashed, applied uniformly to every candidate, and included in every later trial identity and result provenance.

This is a controlled extension of the source-rule gate, not a relaxation of strategy logic requirements. The source must still explicitly and deterministically establish entry direction and condition, exit or custom-exit behavior, stop-loss/take-profit or time-exit behavior, timing, and any source-specific pair restriction. A source-specific pair restriction is inspected and retained as source evidence. A non-empty or unresolved informative-pair scope remains review-only. Runtime `metadata['pair']` usage and an empty `informative_pairs()` method do not constitute a trade-universe declaration.

## Primary Analyst claim

A Freqtrade strategy class commonly contains trading logic while the configured pairlist and exchange are supplied externally. Requiring every strategy class to repeat the deployment pairlist would conflate strategy logic with the research environment. A single fixed external scope is therefore acceptable for research-contract completeness, provided it is predeclared and uniform. Under this policy, 11 previously blocked records have complete source logic and move to `execution_assumption_required`.

## Adversarial Auditor objection

Pairlist, venue, and timeframe choices can materially change results. A scope selected after observing results creates selection bias, and a source may contain hidden pair-specific behavior. Treating framework defaults as if they were source rules would also make the evidence non-reproducible.

## Resolution

The objection is resolved by four controls. First, the v1.2 execution manifest must carry exact `instrument_universe`, `venue`, `quote_currency`, and `applicable_asset_timeframe_constraints` values with `origin=external_assumption`. Second, those values must be frozen and hashed before measurement. Third, the adapter inspects pair assignments, runtime pair restrictions, and informative-pair declarations; conflicts remain `needs_review`. Fourth, the same manifest applies uniformly to the batch, with only predeclared non-tunable exclusions.

## v2.2 reassessment result

| Status | Count |
| --- | ---: |
| `filter_rejected_primary` | 13 |
| `source_rule_complete` | 11 |
| `execution_assumption_required` | 11 |
| `needs_review` | 1 |
| `execution_contract_complete` | 0 |

The 13 historical primary-signal rejections are preserved. Eleven records have explicit source entry, exit, stop/target or time-exit logic and sufficient timing evidence, with applicability resolved through the new uniform external-scope policy. `FixedRiskRewardLoss.py` remains `needs_review` because its timeframe is not explicit. No record reaches `execution_contract_complete` because the manifest remains `template_not_frozen` and has no selected values.

## Research boundary

No market data was acquired. No Freqtrade engine was run. No backtest, paper/live trade, measured trial, ledger update, DSR/PBO/CPCV calculation, candidate promotion, or deployment occurred. The ledger remains `N=893` with `last_sequence=893` and hash `0767031c0bed43719415ac419de4d13ce20e6e72a95f52116ad388d465940ab7`.

Before any measured run, the v1.2 manifest must be populated and frozen; exact Bybit OHLCV manifest references must be reconfirmed; source hashes and evidence provenance must be retained; and a separate explicit authorization for the first measured backtest batch must be recorded.

## Validation

The v2.2 schema fixture accepted `uniform_external_research_scope` with all 20 external-assumption fields. The v2.2 policy validator passed, the new script compiled, and the repository test suite passed with 58 tests. Historical policy artifacts and the previous v2.1 reassessment were not overwritten.
