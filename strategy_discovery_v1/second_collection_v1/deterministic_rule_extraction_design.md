# Safe Deterministic Rule Extraction Design

**Version:** `deterministic_rule_extraction_v2`
**Scope:** `strategy_discovery_v1/second_collection_v1/` only
**Purpose:** Separate explicit source-rule completeness from separately declared execution assumptions without weakening the final executable-contract gate.

## 1. Design decision

The existing normalizer correctly fails closed, but the collection layer stops too early: it records a paper, page, notebook, or source-code locator without acquiring the cited content or mapping explicit evidence into the normalized rule vocabulary. The safe improvement is therefore **not** to weaken `normalized_strategy.schema.json` and not to infer missing rules. It is to add a provenance-preserving intermediate extraction layer and distinguish source-rule completeness from execution-assumption completeness.

The intermediate layer creates an **evidence bundle** for each source. Every proposed field is accompanied by an exact source locator, a content snapshot hash, a page/line/character span, the verbatim quote or code fragment, and an extraction method. A field can be `explicit` only when the source states it directly or code control flow deterministically expresses it. A value inferred from a title, abstract, common convention, indicator name, chart, or video narration without a complete execution specification is never promoted to `explicit`.

The v2 contract has two independent completeness axes. `source_rule_complete` means the source explicitly determines the strategy logic: hypothesis, universe, clock/frequency, signal, entry, and exit/SL/TP behavior. `execution_assumption_required` means that source-rule completeness is achieved but one or more execution-environment fields—sizing, fees, slippage, spread, fill, latency, funding/borrow, or external configuration—must come from a separately frozen research manifest. These states are not equivalent to a production-ready or live-executable strategy. `execution_contract_complete` exists only when the source-rule evidence and the frozen manifest together satisfy the final normalized schema.

> **Safety invariant:** If one required executable field is absent, ambiguous, contradictory, or only inferred, the record becomes `needs_review` or `rejected_incomplete`; it never becomes a normalized strategy and never creates a trial.

## 2. Two-level completeness contract

| State | Source-rule logic | Execution environment | Permitted action |
| --- | --- | --- | --- |
| `source_rule_complete` | Explicit source evidence covers the strategy logic fields. | Not yet supplied or not needed for source classification. | Create a draft and proceed to the assumption gate; do not backtest yet. |
| `execution_assumption_required` | Source-rule fields are complete and evidence-backed. | One or more execution fields are absent from the source. | Apply one batch-level frozen assumption manifest; never choose defaults per candidate. |
| `execution_contract_complete` | Source-rule fields are complete. | All required execution fields are explicitly sourced or linked to a frozen manifest. | Eligible for the existing pre-backtest protocol if all other gates pass. |
| `needs_review` | One or more source-rule fields are ambiguous or contradictory. | Not applicable. | Review-only; no trial. |
| `rejected_incomplete` | Required source-rule fields are not established. | Not applicable. | No normalization or trial. |

A `source_rule_complete` record is not yet a complete normalized strategy. An `execution_assumption_required` record is not allowed to borrow framework defaults silently. A single frozen manifest must declare, at minimum, position sizing, commission, slippage, spread, fill rule, latency, funding/borrow treatment, and missing-data behavior. The manifest hash becomes part of the candidate’s execution-contract identity. Changing it creates a new trial if the candidate is measured.

## 3. Pipeline

| Stage | Input | Output | Fail-closed rule |
| --- | --- | --- | --- |
| 1. Acquire | Canonical URL or raw-code locator | Immutable content snapshot | HTTP errors, redirects to different content, unsupported format, or hash mismatch stop the record. |
| 2. Segment | PDF text/page, HTML block, notebook cell, or code line range | Addressable evidence spans | Text without stable page/line/character coordinates is review-only. |
| 3. Detect | Source-specific patterns or AST/control-flow facts | Field claims | Keyword-only hits are hints, not claims. |
| 4. Bind | Claim to exact quote/code and source hash | Evidence bundle | Every claim must have at least one exact evidence span. |
| 5. Normalize draft | Evidence bundle | Candidate draft in normalized vocabulary | No defaults, semantic guessing, or missing-field completion. |
| 6. Validate | Draft against existing normalized schema and cross-field invariants | `candidate_complete`, `needs_review`, or `rejected_incomplete` | Any missing/ambiguous/contradictory required field fails promotion. |
| 7. Human review queue | Failed or ambiguous bundles | Review task, not a strategy | Review cannot silently mutate the source snapshot or ledger. |

The extractor is source-aware. Academic PDFs use page/character spans and explicit mathematical or prose statements. HTML research pages use DOM-path plus character spans. Notebooks use notebook hash, cell index, and source code cell text. Code uses immutable repository revision, file path, line range, and explicit control-flow fragments. A social post or video is **lead-only** unless a stable transcript or cited primary source is acquired; it cannot directly enter the normalized candidate set.

## 4. Evidence contract

Each field claim has the following structure:

```json
{
  "field_path": "entry.trigger",
  "value": {"op": "gt", "left": {"op": "field", "field": "zscore"}, "right": {"op": "constant", "value": 2.0}},
  "status": "explicit",
  "evidence": [{
    "source_url": "https://…",
    "snapshot_sha256": "64-hex-digest",
    "locator_type": "pdf_page_chars|html_dom_chars|code_lines|notebook_cell",
    "locator": "page=4; chars=1201-1320",
    "verbatim": "…"
  }],
  "extraction_method": "deterministic_pattern|ast_control_flow|structured_table",
  "ambiguity_flags": []
}
```

Allowed statuses are `explicit`, `explicit_but_ambiguous`, `not_found`, and `contradictory`. Only `explicit` can contribute to a complete candidate, and even then all cross-field checks must pass. `derived` values are retained for analysis but are not executable claims; for example, a paper's annualization convention cannot be silently converted into a clock or sizing rule.

The evidence bundle also records `source_class`, `document_id`, `document_version`, `retrieved_at`, `content_type`, `content_sha256`, `source_snapshot_hash`, `extraction_version`, `adapter_id`, and `analysis_only=true`. The bundle is append-only from the audit perspective and is never a substitute for the global trial ledger.

## 5. Required completeness gate

The intermediate source-rule gate can emit `source_rule_complete` only when explicit evidence exists for the strategy hypothesis, instrument applicability, clock/frequency, signal, entry direction/condition, and exit/SL/TP or time-exit logic. It must not mark missing sizing or cost mechanics as source facts. The final gate can emit `candidate_complete` or `execution_contract_complete` only when every required normalized field is present and missing execution fields are supplied by one frozen, uniformly applied, hashed manifest.

| Area | Required explicit facts |
| --- | --- |
| Clock | Timezone, decision frequency, signal timestamp rule, and data cutoff rule. |
| Universe | Instrument set, venue, quote currency, and any selection/rebalance rule. |
| Signal | Exact condition, inputs, windows, thresholds, and lookback alignment. |
| Entry | Direction, trigger, order type, fill rule, latency, and same-bar policy. |
| Exit | At least one explicit rule, precedence, and missing-exit behavior; stop, target, or time exit parameters must be stated when claimed. |
| Risk | Position sizing, risk budget, notional/leverage caps, rounding, and insufficient-margin behavior. |
| Costs | Commission, slippage, spread, funding/borrow treatment, and source references. |
| Constraints | Concurrent positions, pyramiding, cooldown, missing-data behavior, and invalid-bar behavior. |

The gate also checks that no `lead` operation is used in a causal signal, no same-bar fill is asserted without an explicit source statement, no future information is referenced, and no source field conflicts with another source span. If a paper reports only a backtest result without executable mechanics, it remains a research lead.

## 6. Source adapters

The first implementation should use narrow adapters rather than one general-purpose parser.

| Adapter | Safe extraction | Intentionally not inferred |
| --- | --- | --- |
| `arxiv_pdf_v1` | Page text, equations/tables, explicit threshold/window/holding-period statements, cited algorithm boxes | Entry/exit semantics from abstract keywords, unreported costs, instrument universe from examples, missing order/fill rules |
| `quantconnect_code_v1` | Repository revision, file path, line ranges, literals, method calls, and simple control-flow conditions | Portfolio/execution semantics spread across framework classes, implicit defaults in engine configuration, missing risk/cost/latency rules |
| `published_html_v1` | Stable DOM text and explicit tables/algorithm descriptions | Marketing language, charts, qualitative factor descriptions, implied trading rules |
| `notebook_v1` | Markdown/code cell text, cell IDs, literal parameters, imports, and execution order | Runtime state not represented in the snapshot, hidden external data, implicit framework defaults |
| `social_video_lead_v1` | URL, author/channel, transcript availability, publication time, cited primary sources | Direct strategy promotion from a tweet, post, screenshot, or video claim; any performance claim without primary evidence |

For code and notebooks, the adapter must retain the original artifact and a normalized line/cell map. For PDFs and HTML, the adapter must retain the extracted text or a reproducible snapshot hash. The POC below implements the acquisition, span, and deterministic pattern layers and intentionally stops before candidate promotion.

For `freqtrade_strategy_v1`, the adapter should classify fields in two passes. First, it parses explicit strategy logic from `populate_entry_trend`/`populate_buy_trend`, `populate_exit_trend`/`populate_sell_trend` or a declared custom-exit path, plus literal `timeframe`, `minimal_roi`, `stoploss`, and `trailing_stop` assignments. Second, it records absent execution fields such as sizing, commission, slippage, fill, latency, and external configuration as `execution_assumption_required` rather than rejecting the source-rule evidence. A hardcoded source value is explicit; a value found only in an unfetched config or framework default is not a source fact.

The unchanged rejection taxonomy still applies at the primary-signal level. For code, an RSI/EMA/Bollinger import or auxiliary filter is not by itself proof that the lagging indicator is the primary entry signal. The adapter must bind any `lagging_indicator_primary` rejection to the exact primary condition span. This semantic clarification requires a separately versioned code-source filter run; it does not mutate historical filter outputs.

## 7. Optional comparison of social/video sources

Twitter/X posts, public handles, and YouTube videos may be useful for discovering terminology or locating a primary paper/code repository, but they are lower in the source hierarchy than academic papers, stable open code, exchange documentation, or institutional research. They should enter a separate `lead_only` queue with a lower prior trust score. A video can only become evidence after a stable transcript is captured and its claims are corroborated against a primary source; screenshots and verbal performance claims are never enough for a deterministic candidate.

## 8. POC success criteria

The proof of concept is considered successful if it can: acquire at least one real collected source from each tested adapter family; produce exact evidence spans and content hashes; extract explicit facts where present; label absent or ambiguous facts without filling them; produce a machine-readable review queue; reject incomplete drafts; preserve the existing normalized schema and global ledger; and leave `trial_ledger_n=0`, `backtest_run=false`, and `market_data_downloaded=false`.

A positive POC result means **evidence extraction worked**, not that a strategy is valid or profitable. Only a later separately authorized stage may run the existing DSR/PBO/CPCV and out-of-sample protocol after a complete candidate passes normalization.

## 9. References

[1]: ../schemas/normalized_strategy.schema.json "Existing deterministic normalized strategy schema"
[2]: ../source_registry.json "Allowed source registry"
[3]: https://info.arxiv.org/help/api/user-manual.html "arXiv API User's Manual"
[4]: https://github.com/QuantConnect/Research "QuantConnect Research repository"
[5]: https://github.com/QuantConnect/Lean "QuantConnect LEAN repository"
[6]: https://www.aqr.com/Insights/Research "AQR Research index"
[7]: https://www.man.com/insights "Man Insights hub"
[8]: ./schemas/extraction_evidence_bundle_v2.schema.json "Versioned two-level evidence-bundle schema"
[9]: ./master_prompt_v2_amendment.md "Additive master-prompt completeness amendment"
