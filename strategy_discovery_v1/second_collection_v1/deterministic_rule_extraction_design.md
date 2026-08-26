# Safe Deterministic Rule Extraction Design

**Version:** `deterministic_rule_extraction_v1`  
**Scope:** `strategy_discovery_v1/second_collection_v1/` only  
**Purpose:** Convert source text or code into executable strategy candidates only when every required rule is explicitly evidenced.

## 1. Design decision

The existing normalizer correctly fails closed, but the collection layer stops too early: it records a paper, page, notebook, or source-code locator without acquiring the cited content or mapping explicit evidence into the normalized rule vocabulary. The safe improvement is therefore **not** to weaken `normalized_strategy.schema.json` and not to infer missing rules. It is to add a provenance-preserving intermediate extraction layer.

The intermediate layer creates an **evidence bundle** for each source. Every proposed field is accompanied by an exact source locator, a content snapshot hash, a page/line/character span, the verbatim quote or code fragment, and an extraction method. A field can be `explicit` only when the source states it directly or code control flow deterministically expresses it. A value inferred from a title, abstract, common convention, indicator name, chart, or video narration without a complete execution specification is never promoted to `explicit`.

> **Safety invariant:** If one required executable field is absent, ambiguous, contradictory, or only inferred, the record becomes `needs_review` or `rejected_incomplete`; it never becomes a normalized strategy and never creates a trial.

## 2. Pipeline

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

## 3. Evidence contract

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

## 4. Required completeness gate

A source can become `candidate_complete` only when explicit evidence exists for every required normalized field: `hypothesis`, `universe`, `clock`, `signal`, `entry`, `exit`, `risk`, `costs`, `constraints`, `provenance`, and `analysis_only`. The nested execution requirements are mandatory as well.

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

## 5. Source adapters

The first implementation should use narrow adapters rather than one general-purpose parser.

| Adapter | Safe extraction | Intentionally not inferred |
| --- | --- | --- |
| `arxiv_pdf_v1` | Page text, equations/tables, explicit threshold/window/holding-period statements, cited algorithm boxes | Entry/exit semantics from abstract keywords, unreported costs, instrument universe from examples, missing order/fill rules |
| `quantconnect_code_v1` | Repository revision, file path, line ranges, literals, method calls, and simple control-flow conditions | Portfolio/execution semantics spread across framework classes, implicit defaults in engine configuration, missing risk/cost/latency rules |
| `published_html_v1` | Stable DOM text and explicit tables/algorithm descriptions | Marketing language, charts, qualitative factor descriptions, implied trading rules |
| `notebook_v1` | Markdown/code cell text, cell IDs, literal parameters, imports, and execution order | Runtime state not represented in the snapshot, hidden external data, implicit framework defaults |
| `social_video_lead_v1` | URL, author/channel, transcript availability, publication time, cited primary sources | Direct strategy promotion from a tweet, post, screenshot, or video claim; any performance claim without primary evidence |

For code and notebooks, the adapter must retain the original artifact and a normalized line/cell map. For PDFs and HTML, the adapter must retain the extracted text or a reproducible snapshot hash. The POC below implements the acquisition, span, and deterministic pattern layers and intentionally stops before candidate promotion.

## 6. Optional comparison of social/video sources

Twitter/X posts, public handles, and YouTube videos may be useful for discovering terminology or locating a primary paper/code repository, but they are lower in the source hierarchy than academic papers, stable open code, exchange documentation, or institutional research. They should enter a separate `lead_only` queue with a lower prior trust score. A video can only become evidence after a stable transcript is captured and its claims are corroborated against a primary source; screenshots and verbal performance claims are never enough for a deterministic candidate.

## 7. POC success criteria

The proof of concept is considered successful if it can: acquire at least one real collected source from each tested adapter family; produce exact evidence spans and content hashes; extract explicit facts where present; label absent or ambiguous facts without filling them; produce a machine-readable review queue; reject incomplete drafts; preserve the existing normalized schema and global ledger; and leave `trial_ledger_n=0`, `backtest_run=false`, and `market_data_downloaded=false`.

A positive POC result means **evidence extraction worked**, not that a strategy is valid or profitable. Only a later separately authorized stage may run the existing DSR/PBO/CPCV and out-of-sample protocol after a complete candidate passes normalization.

## 8. References

[1]: ../schemas/normalized_strategy.schema.json "Existing deterministic normalized strategy schema"
[2]: ../source_registry.json "Allowed source registry"
[3]: https://info.arxiv.org/help/api/user-manual.html "arXiv API User's Manual"
[4]: https://github.com/QuantConnect/Research "QuantConnect Research repository"
[5]: https://github.com/QuantConnect/Lean "QuantConnect LEAN repository"
[6]: https://www.aqr.com/Insights/Research "AQR Research index"
[7]: https://www.man.com/insights "Man Insights hub"
