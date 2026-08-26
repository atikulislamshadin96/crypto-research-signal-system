# Deterministic Rule Extraction POC Report

**Version:** `deterministic_rule_extraction_v1_poc`  
**Run date:** 2026-08-26 UTC  
**Scope:** `strategy_discovery_v1/second_collection_v1/` only  
**Author:** Manus AI

## Executive summary

A new extraction stage was designed and implemented as an intermediate evidence layer between source collection and the existing normalized-strategy schema. The stage acquires a real source snapshot, records its content hash, segments it into addressable lines or pages, captures exact text/code spans for candidate rule facts, and assigns ambiguity flags. It does not invent thresholds, timing, execution, exits, costs, or sizing. It does not weaken the existing normalized schema and it cannot create a trial.

The proof of concept processed **five real collected leads**, one from each major source family represented in the diversified second collection. All five acquired successfully, produced immutable local snapshots and evidence spans, and were placed in `needs_review`. **Zero candidates were promoted**, `reconstruction_performed=false`, `backtest_run=false`, `market_data_downloaded=false`, and `trial_ledger_n=0`.

This is the intended safe result for a first extraction POC: the method demonstrates that source evidence can be acquired and addressed without confusing keyword hits with executable rules. It also confirms that the next engineering step is a source-aware semantic mapping/review stage, not a relaxation of the fail-closed gate.

## Why the new stage is needed

The prior collection records were provenance-preserving leads: papers, pages, notebooks, or code locators. The existing normalizer correctly requires `rule_disclosure_status=verified_deterministic_rule` and a structured `deterministic_rule_payload`, but there was no intermediate component that acquired the cited content and recorded field-level evidence. This created a format mismatch: a source could contain useful text or code while the collection record still lacked the structure required by `normalized_strategy_v1`.

The new design separates **evidence extraction** from **strategy normalization**. A pattern hit is only a review signal. A normalized candidate is permitted only when all required fields have explicit evidence, all values map to the existing schema, and cross-field causal and execution checks pass.

## POC architecture

| Component | POC behavior | Safety property |
| --- | --- | --- |
| Source acquisition | Downloads the exact rule/code locator from the collected record. | Content is stored under a SHA-256 filename and its byte size/hash are verified. |
| Source adapter | Uses PDF, HTML, or code-aware handling based on source class and locator. | Generic parsing is not treated as semantic understanding. |
| Segmentation | Records PDF page/line or source line locators. | Every evidence item is addressable and reproducible. |
| Pattern scan | Finds possible hypothesis, signal, entry, exit, risk, cost, and constraint fragments. | Pattern hits are labeled `explicit_but_ambiguous`, never executable values. |
| Evidence bundle | Stores URL, snapshot hash, locator, verbatim text, adapter, and flags. | No claim exists without exact source evidence. |
| Completeness gate | Requires explicit mapped values for every normalized field. | Missing/ambiguous fields lead to review, never promotion. |
| Trial boundary | Emits analysis-only JSON. | No trial IDs, backtests, market-data use, or ledger writes. |

The implementation is `scripts/extract_rules_poc.py`. The machine-readable evidence contract is `schemas/extraction_evidence_bundle.schema.json`, and the complete design is `deterministic_rule_extraction_design.md`.

## Sample and results

The sample was selected from the collected filtered universe with one lead per source ID. The QuantConnect selection was intentionally changed to an Alpha file rather than a framework risk-management file so that the POC exercised an actual disclosed source-code lead.

| Source family | Identifier | Adapter | Snapshot bytes | Content SHA-256 | Evidence outcome | Promotion |
| --- | --- | --- | ---: | --- | ---: | --- |
| Academic systematic research | `2608.24786v1` | `arxiv_pdf_v1` | 1,056,862 | `7ddf3853c5757f2273c40ed3c24b10aad048b4e9cf13b51b627790e8c480bd08` | 7 field groups with pattern evidence | `needs_review` |
| AQR | `https://www.aqr.com/Insights/Research/Alternative-Thinking` | `published_html_v1` | 64,703 | `98ac1753c81f97f25344af3e27da6bdbc4ec5133ea9191c3cd3ad97e76e7dc30` | 4 field groups with pattern evidence | `needs_review` |
| Man Insights | `https://www.man.com/insights/100-dollar-oil-emerging-markets` | `published_html_v1` | 155,937 | `a8ca4061477c6e61ea0480bc977a26d67a74bdc260f3067a3598ff44cfee01c4` | 4 field groups with pattern evidence | `needs_review` |
| Academic microstructure research | `2608.13340v1` | `arxiv_pdf_v1` | 844,076 | `dfc232c4cfd01a85cab2c3005b06fa27e79af74b1c580221092cb90ca24f469e` | 7 field groups with pattern evidence | `needs_review` |
| QuantConnect LEAN Alpha | `QuantConnect/Lean@660306a2fa4e4933e7c2f9e57a4ca3ef71096ca2:Algorithm.CSharp/Alphas/GasAndCrudeOilEnergyCorrelationAlpha.cs` | `quantconnect_code_v1` | 14,279 | `1afe9fcabb7439ea6274bd5b4dc7b4c73403784b6f501afde6dc1a9756b8de4c` | 1 field group with pattern evidence | `needs_review` |
| **Total** | 5 real leads | 3 adapters | **2,135,857** | 5 verified snapshots | 5 review bundles | **0 complete** |

The five snapshots total **2,135,857 bytes**. This aggregate is descriptive only and is not used for any decision; the machine-readable output is authoritative for the exact per-file sizes and hashes. No aggregate byte total is required for promotion.

Each evidence item stores a source URL, the snapshot SHA-256, locator type, locator, and a verbatim excerpt. For example, the systematic academic sample captured explicit hypothesis text such as “Hypothesis 1 (H1): A LambdaRank ranker over a cross-section of delta-targeted SPXW,” but correctly did not convert that statement into a signal, entry order, option contract rule, exit rule, or risk policy. The QuantConnect sample stored the exact immutable raw-code snapshot and recorded only a code pattern hit; it did not assume that framework behavior supplied missing execution or risk parameters.

## Why all five remain in review

The POC deliberately assigns `explicit_but_ambiguous` to pattern hits because a keyword or sentence fragment is not yet a valid value in the normalized strategy schema. For example, a paper can explicitly mention a “static short-put rule” while still omitting exact contract selection, entry timing, fill assumptions, exit precedence, loss limits, costs, and missing-data behavior. Similarly, a code file can contain an Alpha calculation while execution, portfolio construction, brokerage costs, and latency are configured elsewhere.

The existing normalized schema requires explicit values for the full execution contract. This includes clock timezone/frequency/cutoff, signal condition, entry direction/order/fill/latency, exit rules/precedence/missing-exit behavior, risk sizing/budget/caps/rounding, costs and cost references, constraints, and provenance. A field is never filled with a default merely because a framework, exchange, paper, or common trading convention normally uses one.

## Safe path from evidence to normalized strategy

| Gate | Required condition | Failure result |
| --- | --- | --- |
| Content identity | Locator resolves and snapshot hash is stored. | Acquisition review; no rule claim. |
| Evidence locality | Every proposed field has an exact quote or code span. | `needs_review`. |
| Semantic mapping | Evidence maps directly to a permitted schema value. | `explicit_but_ambiguous`; no promotion. |
| Completeness | All required nested fields are explicit. | `rejected_incomplete` or `needs_review`. |
| Causal validity | No future information, unverified same-bar fill, or `lead` in causal signal. | `rejected_contradictory`. |
| Cross-field consistency | Timing, entry, exit, sizing, costs, and constraints do not conflict. | `rejected_contradictory`. |
| Provenance | Source refs, snapshot, extraction version, and canonical rule hash exist. | `needs_review`. |
| Research handoff | Separate authorization and frozen protocol gates are present. | No trial or backtest. |

The normalization pipeline becomes more flexible by accepting **evidence bundles and review states**, not by accepting incomplete strategies. This allows useful extraction work to proceed on partial sources while preserving a hard boundary before any statistical measurement.

## Optional social and video sources

Twitter/X posts, public handles, screenshots, and YouTube videos should be treated as low-trust discovery leads, not primary executable strategy sources. A future `social_video_lead_v1` adapter may store the URL, author/channel, timestamp, transcript availability, and cited primary sources. It must not promote a strategy from a verbal claim, chart, screenshot, or performance statement. A video can provide evidence only after a stable transcript is captured and the operational rules are corroborated against a primary paper, code repository, exchange rule, or institutional source. This preserves the higher source priority of academic papers, stable open code, institutional research, and exchange documentation.

## Boundaries and validation

| Boundary | POC result |
| --- | ---: |
| Sample processed | 5 |
| Evidence bundles | 5 |
| Complete candidates | 0 |
| Needs-review bundles | 5 |
| Reconstruction performed | false |
| Market data downloaded | false |
| Backtest run | false |
| Trial IDs created | 0 |
| Global trial ledger N | 0 |

The snapshot files' SHA-256 names were checked against their byte contents. All evidence references point to the corresponding snapshot hash. The existing first-run normalization review, normalized schema, frozen protocols, Bybit/Drive artifacts, lifecycle infrastructure, Candidate 1/v2 artifacts, and global ledger were not modified. All changes are confined to `strategy_discovery_v1/second_collection_v1/`.

## Recommended next stage

The next separately authorized implementation should add source-specific semantic mappers and a human-review queue. The mapper may create a draft normalized object only when every field is backed by explicit evidence. It should support PDF equations/tables, HTML algorithm descriptions, notebook cells, and code control flow independently. It should maintain a “not found” state rather than inventing values, preserve contradictory evidence instead of resolving it silently, and require a reviewer to approve any ambiguous field. Only after a complete candidate passes the existing normalized schema and causal checks should the existing frozen research protocol be allowed to measure it.

## References

[1]: ../schemas/normalized_strategy.schema.json "Existing deterministic normalized strategy schema"
[2]: ../schemas/extraction_evidence_bundle.schema.json "Extraction evidence bundle schema"
[3]: ../source_registry.json "Allowed source registry"
[4]: https://info.arxiv.org/help/api/user-manual.html "arXiv API User's Manual"
[5]: https://github.com/QuantConnect/Research "QuantConnect Research repository"
[6]: https://github.com/QuantConnect/Lean "QuantConnect LEAN repository"
[7]: https://www.aqr.com/Insights/Research "AQR Research index"
[8]: https://www.man.com/insights "Man Insights hub"

This document is research and analysis only, not personalized financial advice.
