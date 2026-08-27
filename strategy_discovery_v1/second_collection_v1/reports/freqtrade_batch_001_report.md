# Task 2 — Freqtrade Strategy Batch 001

**Source adapter:** `freqtrade_strategy_v1`  
**Repository:** [https://github.com/freqtrade/freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies)  
**Source commit:** `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`  
**License:** GPL-3.0  
**Batch ID:** `freqtrade-strategies-001`

## Scope and provenance

This was the first and only Task 2 code-repository batch. It used 25 named Python files under `user_data/strategies/` from the confirmed Freqtrade repository. No GitHub search results, second repository, QuantConnect source, backtrader source, vectorbt source, or unrelated framework files were pulled.

The collector parsed the temporary source clone and retained only structured metadata plus short evidence fragments tied to fields. It did not vendor full third-party files. Each record contains the repository URL, immutable source commit, file path, GPL-3.0 license, source-file SHA-256, and short snippets for explicit fields such as `minimal_roi`, `stoploss`, `trailing_stop`, `timeframe`, and entry/exit method logic. Snippets are capped and are not standalone source-file copies.

## Batch funnel

| Stage | Count |
| --- | ---: |
| Freqtrade strategy files pulled | 25 |
| Passed unchanged frozen rejection filter | 0 |
| Rejected by unchanged frozen filter | 25 |
| `candidate_complete` | 0 |
| Backtested candidates | 0 |
| DSR calculations | 0 |
| PBO/CPCV calculations | 0 |
| New trial ledger entries | 0 |
| Post-fix global ledger N | **893** |

All 25 records were rejected under `lagging_indicator_primary`. The filter was applied without modification. In this code-source batch, the collector’s deterministic summary exposed indicator tokens detected in each file, and the existing filter treated the presence of those terms as a lagging-indicator rejection. No exception was made for a strategy that appeared promising.

## Why no normalization or backtest occurred

Because the unchanged rejection filter produced zero survivors, no Freqtrade record reached the normalization stage and no record could be `candidate_complete`. Therefore there was no eligible candidate for the already-acquired Bybit OHLCV backtest, and no DSR, PBO, or CPCV calculation was performed.

The frozen global trial ledger remains at **N=893**. The post-fix ledger N was not reset and was not increased because collection-time filter rejections were not measured trials. If a later batch produces a complete candidate and a measured trial is actually run, its DSR input must begin from N=893 and increment only for newly measured distinct trials.

## DSR/PBO status

| Requirement | Status |
| --- | --- |
| Post-fix starting N | `893` |
| New measured trials in this batch | `0` |
| DSR threshold | Not invoked; no eligible candidate |
| PBO threshold | Not invoked; no eligible candidate |
| CPCV partition | Not invoked; no eligible candidate |
| IS backtest | Not invoked; no eligible candidate |
| OOS/WFO/cost stress/paper/live | Not authorized for this batch and not run |

## Integrity and boundaries

The raw batch and evidence bundle contain no complete third-party source-file reproductions. The exact repository URL, source commit, file path, license, file hash, and short field-supporting excerpts are preserved. The existing rejection filter, normalized schema, frozen DSR/PBO/CPCV protocol, post-fix ledger, historical academic collection, Bybit/Drive artifacts, Candidate 1/v2 artifacts, and lifecycle infrastructure were not modified.

The batch was collection/filter-only. No market data was downloaded, no backtest was run, no trial was created, and no candidate was promoted. Per the master prompt, this report is the stopping point: no QuantConnect, backtrader, vectorbt, larger Freqtrade pull, WFO, stress test, trading, or deployment action was started.

## Repository artifacts

| Artifact | Purpose |
| --- | --- |
| `data/freqtrade_raw_batch_001.json` | 25 structured Freqtrade records with provenance and short evidence snippets. |
| `data/freqtrade_evidence_batch_001.json` | Evidence-bundle view of the short snippets and source hashes. |
| `data/freqtrade_filtered_batch_001.json` | Unchanged-filter output and rejection summary. |
| `scripts/collect_freqtrade_batch.py` | Freqtrade AST collector with short-snippet policy. |
| `reports/freqtrade_batch_001_report.md` | This result report. |

This is research and analysis only, not personalized financial advice.
