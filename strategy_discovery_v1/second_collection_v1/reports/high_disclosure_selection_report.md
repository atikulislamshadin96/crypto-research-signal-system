# High-Disclosure Paper Selection Report

**Version:** `high_disclosure_paper_selection_v1`  
**Population:** immutable original 893 collection-filter-passed records  
**Purpose:** mechanically identify papers with visible implementation/rule structure before any control-group comparison  
**Criteria commit:** [`41d54ff`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/41d54ff49e734549b6f781b209546cb1e7d88b28)

## Executive result

The exact frozen selector was applied to all **893** original records. It found **62 passing papers**, **831 failures**, and then drew a **30-paper random sample** from the 62 passers using `random.Random(seed=20260827)` over sorted `document_id` values, without replacement. No paper was manually added or removed based on apparent promise.

| Result | Count | Rate of 893 |
| --- | ---: | ---: |
| Mechanical high-disclosure pass | 62 | 6.94% |
| Mechanical fail | 831 | 93.06% |
| Random sample from passers | 30 | 3.36% of population; 48.39% of passers |

The 62-pass result is a **selection result**, not a deterministic-strategy result. A pass means that the full PDF contained a mechanically detected high-disclosure heading/block. It does not mean that the paper contains a complete executable entry, exit, risk, cost, and execution contract.

## Frozen mechanical criteria

The selector was frozen and committed before it was applied. It uses only the cited PDF, not abstract or title metadata. PDF acquisition and text extraction must succeed. A record passes if and only if at least one complete-line pattern matches and at least three subsequent non-empty lines occur within the next 25 lines.

| Pattern family | Exact rule |
| --- | --- |
| Numbered algorithm/pseudocode block | Complete line matching `^\\s*(?:Algorithm|Pseudocode)\\s+(?:No\\.?\\s*)?\\d+(?:\\s*[:.-].*)?$`, case-insensitive. |
| Explicit implementation section | Complete line matching `^\\s*(?:\\d+(?:\\.\\d+)*\\s+)?Implementation(?:\\s+Details)?\\s*[:.]?\\s*$`, case-insensitive. |
| Appendix: Trading Rules section | Complete line matching `^\\s*Appendix(?:\\s+[A-Z])?\\s*[:.-]\\s*Trading\\s+Rules\\s*[:.]?\\s*$`, case-insensitive. |
| Look-ahead requirement | At least 3 non-empty lines within the next 25 lines after the matching heading. |
| Sampling | Sorted passing IDs, `random.Random(20260827)`, sample size 30, no replacement. |

The selector does not match sentence-level mentions of “algorithm,” “implementation,” “pseudocode,” or “trading rules” unless they satisfy the complete-line heading rule. It does not infer any trading rule from a match, and acquisition or text-extraction failure is a mechanical fail.

## Full-population funnel

| Funnel step | Count |
| --- | ---: |
| Original filtered population | 893 |
| PDF acquisition and text extraction succeeded | 890 |
| PDF acquisition failed after bounded retries | 3 |
| No qualifying frozen heading/block | 828 |
| Mechanical high-disclosure pass | 62 |
| Random sample drawn from passers | 30 |

The 3 acquisition failures are retained in the result file with their exact URLs and error reasons. They were not silently treated as passers and were not eligible for random sampling. The two positive pattern counts sum to 63 while there are 62 passers because one paper matched more than one positive pattern family.

| Matched pattern family | Match count among passers |
| --- | ---: |
| Numbered algorithm/pseudocode block | 45 |
| Explicit implementation section | 18 |
| Appendix: Trading Rules section | 0 |

Every original record has `source_class=academic_preprint`; there is no source-class diversity inside the original 893. The selector therefore measures high-disclosure structure within an academic-only population. The result is not a cross-source-class comparison.

## Reproducible random sample

The sample is stored in `data/high_disclosure_random_sample.json`. It contains the criteria hash, seed, sampling method, population count, pass count, sample count, selected document IDs, and full provenance records. Re-running the sampler from the same sorted passing-ID list and seed reproduces the same 30 IDs exactly.

The sample was drawn only after the full 893-record filter completed. It was not selected by looking at paper titles, reported Sharpe ratios, abstracts, authors, or apparent strategy quality.

## Interpretation before the control group

A 6.94% high-disclosure rate is materially better than the earlier 0% complete-normalization rate, but it is not evidence that 6.94% are executable strategies. The mechanical filter detects structural disclosure signals, while the existing normalizer still requires a fully explicit schema covering clock, universe, signal, entry, exit, risk, costs, constraints, and provenance.

The result supports a two-stage interpretation. First, the academic-only universe is not entirely devoid of implementation-oriented papers: 62 records pass a strict structural disclosure screen. Second, most academic records still do not present their method in a format immediately usable as an execution specification. The 62 records are therefore appropriate for a targeted semantic extraction review, not automatic normalization or backtesting.

The next comparison should use this fixed 30-paper academic high-disclosure sample as the academic arm and a separately defined, pre-registered control-group selector for stable executable-code/notebook sources. The control group must be selected mechanically before inspection, and its inclusion criteria must not be changed after seeing the academic results. The comparison should measure field-level completeness—not just heading presence—across clock, universe, signal, entry, exit, risk, costs, and constraints.

A complete academic-paper candidate should still require explicit evidence for every field. A paper that contains an algorithm block but omits fill rule, latency, fees, or risk sizing remains `needs_review`. No default, framework convention, or common trading practice may fill the gap.

## Execution boundary and integrity

| Item | Result |
| --- | ---: |
| Research trials created | 0 |
| Global trial ledger | `N=0` |
| Backtests | 0 |
| Market data downloaded | false |
| DSR/PBO/CPCV | 0 |
| OOS/WFO/stress | 0 |
| Candidate promotion | 0 |
| Original records overwritten | false |
| Frozen normalized schema/protocol modified | false |

The selector stores source PDFs under content SHA-256 filenames and checks the stored byte size and hash. All changes are confined to `strategy_discovery_v1/second_collection_v1/`. The original 893 records remain untouched.

## Artifacts

The authoritative artifacts are:

| Artifact | Purpose |
| --- | --- |
| `high_disclosure_criteria_v1.json` | Frozen criteria, regexes, look-ahead, exclusions, seed, and execution boundary. |
| `scripts/apply_high_disclosure_filter.py` | Full-population mechanical selector and random sampler. |
| `data/high_disclosure_filter_results.json` | All 893 pass/fail decisions, hashes, matches, and failure reasons. |
| `data/high_disclosure_random_sample.json` | Reproducible 30-record sample from passers only. |
| `high_disclosure_snapshots/` | Exact acquired PDF snapshots addressed by content hash. |
| `scripts/validate_high_disclosure_filter.py` | Reproducibility, provenance, and protected-state checks. |

This is research and analysis only, not personalized financial advice.
