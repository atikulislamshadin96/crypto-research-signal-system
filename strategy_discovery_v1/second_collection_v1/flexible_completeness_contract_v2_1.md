# Flexible Completeness Contract v2.1

**Status:** versioned contract reconciliation; analysis-only  
**Scope:** `strategy_discovery_v1/second_collection_v1/`  
**Purpose:** Make the v2.1 evidence schema, execution-assumption template, and Freqtrade reassessment script expose one identical machine-checkable harness field set.

## Reconciled contract

The canonical execution-assumption field list contains 20 fields. The same list is present in the v2.1 evidence schema enum, the v1.1 manifest template, and `re_evaluate_freqtrade_v2_1.py`. Its canonical SHA-256 is emitted by the validator and reassessment artifact as `a04027344f46a94667a42eb047214cb7eb52e48b186c97bf53f92d31561e3526`.

| Field group | Fields | Origin rule |
| --- | --- | --- |
| Applicability | `instrument_universe`, `venue`, `quote_currency`, `applicable_asset_timeframe_constraints` | Must be source-explicit where strategy applicability is part of the source rule; otherwise batch-level external assumption must be declared before measurement. |
| Risk and sizing | `position_sizing`, `risk_budget`, `notional_cap`, `leverage_cap`, `rounding_rule`, `insufficient_margin_behavior` | Never guessed per candidate; a common harness value must carry `origin=external_assumption`. |
| Trading costs and execution | `commission`, `slippage`, `spread`, `fill_rule`, `latency`, `funding_or_borrow` | Must be fixed before the first measured trial and included in trial identity. |
| Data and configuration | `external_config`, `missing_data_behavior`, `invalid_bar_behavior`, `ohlcv_manifest_refs` | Every reference must be deterministic; absent or invalid values block a frozen manifest. |

Each populated manifest field uses the common structure `{origin, value, unit?, model?, reference?, source_manifest_hash?}`. `origin` must equal `external_assumption`. Source evidence claims continue to use `claim_origin=source`; the harness cannot retroactively become source evidence.

A manifest with `status=template_not_frozen` is not executable. A future frozen manifest must have a deterministic `manifest_sha256`, complete required values, exact data-manifest references, and uniform applicability rules. The v2.1 evidence schema requires that hash when the execution status is `execution_contract_complete`.

## Operational boundary

This repair does not fetch source, download market data, run a backtest, create a trial, increment the global ledger, calculate DSR/PBO/CPCV, promote a candidate, or modify historical artifacts. The v2.1 reassessment remains a no-trial diagnostic over the existing 25 structured Freqtrade records and reports `needs_review=25` because retained snippets are insufficient for complete AST/control-flow proof.

Before any future evidence-recovery task, separately authorize re-fetching only the pinned Freqtrade source commit. Before any future measured task, separately freeze the manifest and authorize the first measured batch. The ledger starting count remains `N=893`.
