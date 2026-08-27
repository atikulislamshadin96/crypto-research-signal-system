# Original 893 — Larger Deterministic-Rule Extraction Sample

**Run:** `original_893_extraction_sample_v1`  
**Population:** the immutable original 893 collection-filter-passed leads  
**Sample:** 40 leads  
**Mode:** source acquisition and evidence extraction only; no normalization promotion, backtest, or trial creation

## Executive result

The extraction layer was run on a fixed **40-lead sample** from the original 893 leads. The original population has only one `source_class`: `academic_preprint` for all 893 records. Therefore it was not possible to stratify this sample across multiple source-class values without adding a new source universe. Instead, the sample was stratified across eight relevant q-fin subcategories, with five leads per category.

| Outcome | Count | Rate |
| --- | ---: | ---: |
| `candidate_complete` | 0 | 0.0% |
| `needs_review` | 40 | 100.0% |
| `rejected_incomplete` | 0 | 0.0% |
| **Total processed** | **40** | **100.0%** |

The result is clearly **near-zero candidate completeness** at the larger sample size. However, every lead produced a review bundle rather than an immediate incomplete rejection, which means the extractor found source text worth reviewing but did not safely map it into the complete executable schema.

## Sampling frame

The sample was created without changing the original records. Because `source_class` is homogeneous, the internal stratification dimension was the first relevant q-fin category in each record. The allocation was deterministic and balanced.

| q-fin category | Sampled leads |
| --- | ---: |
| `q-fin.CP` | 5 |
| `q-fin.GN` | 5 |
| `q-fin.MF` | 5 |
| `q-fin.PM` | 5 |
| `q-fin.PR` | 5 |
| `q-fin.RM` | 5 |
| `q-fin.ST` | 5 |
| `q-fin.TR` | 5 |
| **Total** | **40** |

The complete sampling frame is stored in `data/original_893_stratified_sample.json`. Its metadata records `population_count=893`, `sample_count=40`, `source_class_counts={academic_preprint:893}`, and the q-fin category allocation.

## What the extractor actually did

For each sample lead, the POC acquired the cited PDF and converted it into page/line-addressable text. It then searched for possible hypothesis, clock, signal, entry, exit, risk, cost, and constraint fragments. Each hit was retained with the source URL, snapshot SHA-256, locator, and verbatim excerpt. The extractor did not convert a keyword or sentence into a normalized expression, did not fill a missing default, and did not infer an execution convention.

All 40 bundles were classified `needs_review`. This is important: `needs_review` means evidence or a source snapshot exists but the evidence is not yet a complete, unambiguous normalized field. It is not equivalent to “the paper contains no strategy.” The output is stored in `data/original_893_extraction_poc_results.json`, and all acquired snapshots are stored under `original_893_poc_snapshots/`.

## Does this prove that academic-only sources are too sparse?

The result is a strong warning, but it is **not yet a clean causal test of academic-source sparsity**. There are two simultaneous explanations for the 0/40 complete rate.

| Hypothesis | Evidence from this run | Assessment |
| --- | --- | --- |
| Academic papers often describe a research hypothesis or empirical result without a fully executable execution contract. | All 40 were academic preprints, and none reached complete representation across timing, signal, entry, exit, risk, cost, and constraints. | Supported. |
| The current extraction stage remains intentionally shallow and pattern-based. | Every bundle is `needs_review`; evidence is explicitly flagged `pattern_hit_not_semantic_parse` and `value_not_mapped_to_normalized_schema`. | Also supported. |
| The academic-only universe fundamentally contains no deterministic strategies. | The POC did not perform full semantic extraction or human verification of every candidate. | **Not established.** |

The correct conclusion is therefore: **academic-only collection is poorly matched to immediate executable normalization, and its practical yield is currently near zero, but the run cannot distinguish source sparsity from insufficient semantic extraction.** Scaling the current pattern-only extractor across all 893 would not solve that problem; it would mostly produce a larger review queue.

## Recommended decision before scaling

Do not scale the current POC blindly. First add a targeted, provenance-preserving semantic review adapter for papers that advertise an algorithm, pseudocode, implementation appendix, explicit trading rules, or a public code companion. The adapter should extract field-by-field evidence into the existing evidence bundle and leave missing fields as `not_found`. It should promote only when the full clock, signal, universe, entry, exit, risk, costs, and constraints contract is explicit.

The next diagnostic should compare a targeted academic high-disclosure sample against a small non-academic executable-source control group, such as stable QuantConnect Alpha code or a reproducible public notebook. This comparison is required to identify whether the bottleneck is primarily source class or extraction capability. Until that comparison passes, no strategy should enter the global ledger or backtest pipeline.

## Safety boundary

| Item | Result |
| --- | ---: |
| Research trial IDs created | 0 |
| Global trial ledger | `N=0` |
| Backtests | 0 |
| DSR/PBO/CPCV | 0 |
| OOS/WFO/stress tests | 0 |
| Candidate promotions | 0 |
| Market data downloaded | false |
| Rule reconstruction | false |
| Frozen first-run records modified | false |
| Frozen schema/protocol modified | false |

All changes made for this sample are confined to `strategy_discovery_v1/second_collection_v1/`. The original 893 records were read as an immutable population and copied only into a separately versioned sample file for diagnostic use.

## Evidence and references

The exact result distribution and per-lead evidence are in `data/original_893_extraction_poc_results.json`. The extraction contract is in `deterministic_rule_extraction_design.md`, and the machine-readable evidence contract is in `schemas/extraction_evidence_bundle.schema.json`. The source population was originally collected through the allowed academic preprint pathway using the official arXiv API [1].

[1]: https://info.arxiv.org/help/api/user-manual.html "arXiv API User's Manual"
[2]: ../schemas/normalized_strategy.schema.json "Existing normalized strategy schema"
[3]: ../data/normalization_review.json "Historical normalization review"

This is research and analysis only, not personalized financial advice.
