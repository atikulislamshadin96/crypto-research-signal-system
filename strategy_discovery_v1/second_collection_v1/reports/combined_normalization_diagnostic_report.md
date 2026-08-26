# Strategy Discovery v1 — Second Collection and Combined Normalization Diagnostic

**Run:** `sdv1-second-collection-20260826`  
**Scope:** `strategy_discovery_v1/second_collection_v1/` only  
**Mode:** Collection and deterministic-normalization diagnostic only

## Executive conclusion

The second collection expanded the source universe beyond the first run's arXiv-only distribution and produced **1,000 new raw source leads**. After applying the existing frozen collection-time rejection filter unchanged, **787 new leads remained**. The historical first-run universe remains immutable at **893 collection-filter-passed leads and 0 normalized candidates**.

The combined diagnostic universe therefore contains **1,680 collection-filter-passed leads**, of which **0 normalized deterministically**. The observed normalization pass rate is **0.0%** for Universe A, Universe B, and Universe C. The evidence supports diagnosis **D: a combination of source-universe mismatch and normalization-pipeline observability limits, with a possible schema/protocol fit issue that cannot be resolved by this metadata-only run**. It does **not** establish that the underlying full text or source code lacks executable strategies, because the current normalizer fails closed before full-text/code extraction and requires a verified structured rule payload.

No schema, protocol, reconstruction experiment, backtest, statistical trial, OOS/WFO test, stress test, trading action, or candidate promotion was performed.

## A. New collection

The new source universe was deliberately diversified across the allowed source families. It used official arXiv q-fin API slices for market microstructure and systematic-trading research, stable QuantConnect Research/LEAN repository revisions and paths, and stable AQR and Man Insights research URLs. The attempted SSRN search endpoint returned a page-not-found response, so no SSRN records were fabricated or substituted silently.

| Source family | Source class | New raw leads | New filtered leads |
| --- | --- | ---: | ---: |
| `microstructure_research` | `order_flow_microstructure` | 434 | 292 |
| `academic_systematic_research` | `academic_preprint` | 276 | 276 |
| `quantconnect_research` | `open_quant_archive` | 70 | 69 |
| `aqr_public_research` | `published_quant_research` | 75 | 75 |
| `man_institute_research` | `published_quant_research` | 75 | 75 |
| **Total** |  | **1,000** | **787** |

The raw records preserve source ID, source class, canonical URL, stable rule/code locator, source revision or document version, retrieval timestamp, snapshot hash, admissibility decision, and rejection provenance fields. Deduplication was performed within each source slice using stable source identifiers and locators; no first-run records were reprocessed or overwritten.

### Batch funnel and commits

Each batch was committed and pushed before the next batch began. Every commit was verified from a fresh clone.

| Batch | Source slice | Raw | Passed filter | Collection rejection counts | Verified commit |
| --- | --- | ---: | ---: | --- | --- |
| 001 | arXiv microstructure, start 0 | 150 | 105 | `lagging_indicator_primary=45` | [`99f2bb7`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/99f2bb7020a4c42f891d3008ae3f927f4bf18f40) |
| 002 | QuantConnect open code/notebooks | 70 | 69 | `lagging_indicator_primary=1` | [`e4b6c54`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/e4b6c541a3a007a51a975ffa4234223a970af41b) |
| 003 | AQR and Man public research | 150 | 150 | none | [`6e6343d`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/6e6343d8f0d40137f5b4883dbdeae2449753262f) |
| 004 | arXiv systematic research, start 0 | 150 | 119 | `lagging_indicator_primary=28`; `retail_marketing_source=3` | [`deca8dc`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/deca8dc87d0e32d80020011099c8976b1afab047) |
| 005 | arXiv systematic research, start 150 | 150 | 121 | `lagging_indicator_primary=28`; `retail_marketing_source=1` | [`494c48d`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/494c48dd4302b821d8cdf865926216252194d2c1) |
| 006 | arXiv microstructure, start 150 | 150 | 100 | `lagging_indicator_primary=48`; `generic_price_pattern_primary=1`; `retail_marketing_source=1` | [`fc174d1`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/fc174d1aae52b3b2f5e6d378692732a9018e9841) |
| 007 | arXiv microstructure, start 300 | 134 | 87 | `lagging_indicator_primary=47` | [`87346b8`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/87346b86e155602d34a7ec57b8ed5850b85cfe2b) |
| 008 | arXiv systematic research, start 300 | 46 | 36 | `lagging_indicator_primary=8`; `generic_price_pattern_primary=1`; `retail_marketing_source=1` | [`ab2e5ac`](https://github.com/atikulislamshadin96/crypto-research-signal-system/commit/ab2e5aca90b54bf6c52e51604769a705576ba090) |
| **Total** |  | **1,000** | **787** | `lagging_indicator_primary=205`; `generic_price_pattern_primary=2`; `retail_marketing_source=6` |  |

The collection filter was applied through the existing `strategy_discovery_rejection_filter_v1` implementation. No new rejection category was introduced and no taxonomy rule was relaxed.

## B. Existing first run

The historical first run is unchanged and was used as an immutable diagnostic input.

| Measure | Historical result |
| --- | ---: |
| Raw academic leads | 1,050 |
| Collection-filter-passed leads | 893 |
| Normalized candidates | 0 |
| Historical normalization rejection | `incomplete_disclosure=893` |
| Backtests | 0 |
| DSR/PBO/CPCV calculations | 0 |
| OOS/WFO/stress tests | 0 |
| Global trial ledger | `N=0` |

No historical raw or filtered record was copied into a new mutable representation, re-filtered, or overwritten. Universe A references the historical filtered records and historical normalization review directly.

## C. Combined universe

Universe A is the immutable first-run filtered set, Universe B is the new second-run filtered set, and Universe C is their diagnostic union. Counts reconcile exactly.

| Universe | Total candidates | `subjective_rule` | `incomplete_disclosure` | `non_deterministic` | Other collection rejection categories | Normalized | Pass rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A — existing first run | 893 | 0 | 893 | 0 | 0 | 0 | 0.0% |
| B — new second run | 787 | 0 | 787 | 0 | 0 | 0 | 0.0% |
| C — A + B | 1,680 | 0 | 1,680 | 0 | 0 | 0 | 0.0% |

The collection-time rejection counts are reported separately because rejected raw records do not enter Universes A–C. Across the new raw collection, collection-time rejections were `lagging_indicator_primary=205`, `generic_price_pattern_primary=2`, and `retail_marketing_source=6`, totaling 213 and reconciling with 1,000 raw minus 787 filtered.

The current normalizer requires both `rule_disclosure_status == verified_deterministic_rule` and a `deterministic_rule_payload`. All 787 new filtered records intentionally carried metadata, page, notebook, or code locators but no verified structured rule payload. The normalizer therefore rejected all 787 as `incomplete_disclosure` without guessing missing rules. The combined result is `893 + 787 = 1,680` candidates and `893 + 787 = 1,680` normalization rejections.

## D. Representative failure analysis

The combined universe has one major normalization rejection category: `incomplete_disclosure`. The examples below represent the diversified source classes and retain the exact source locator and snapshot provenance. The relevant disclosed rule is reported conservatively: the collection record retained a source lead, not an extracted executable rule. No author intent or missing parameter is inferred.

### 1. arXiv microstructure lead

**Identifier:** `2608.13340v1` — *Fee Implied Volatility on Uniswap v3: A DEX Native Proxy and Its Limits*. **Source:** `microstructure_research`, `order_flow_microstructure`. **Locator:** [arXiv abstract](https://arxiv.org/abs/2608.13340v1) and [PDF rule locator](https://arxiv.org/pdf/2608.13340v1). **Disclosed rule:** None was recorded in the collection record; the record is explicitly a metadata lead pending full-text review. **Failure:** the current normalizer found neither `verified_deterministic_rule` status nor `deterministic_rule_payload`. **Blocking schema requirements:** a deterministic representation would need complete `clock`, `signal`, `entry`, `exit`, `risk`, `costs`, `constraints`, and `provenance` objects, including entry direction/trigger/order/fill/latency, exit rules/precedence/missing-exit behavior, and risk sizing/budget/caps/rounding.

### 2. QuantConnect open-code lead

**Identifier:** `QuantConnect/Lean@b36534d870db9c64655017f8de8af55b35cb1c37:Algorithm.CSharp/AddRiskManagementAlgorithm.cs` — *AddRiskManagementAlgorithm*. **Source:** `quantconnect_research`, `open_quant_archive`. **Locator:** [stable GitHub path](https://github.com/QuantConnect/Lean/blob/master/Algorithm.CSharp/AddRiskManagementAlgorithm.cs) and [raw code locator](https://raw.githubusercontent.com/QuantConnect/Lean/master/Algorithm.CSharp/AddRiskManagementAlgorithm.cs). **Disclosed rule:** The source file was retained as the rule/code locator; no deterministic rule payload was extracted at collection time. **Failure:** the current normalizer failed closed for the missing verified payload. **Blocking schema requirements:** the normalized record must contain the required top-level hypothesis, universe, clock, signal, entry, exit, risk, costs, constraints, provenance, and `analysis_only` fields, with fully specified timing, execution, exits, sizing, costs, and missing-data behavior.

### 3. AQR public research lead

**Identifier:** `https://www.aqr.com/Insights/Research/Alternative-Thinking` — *Alternative Thinking*. **Source:** `aqr_public_research`, `published_quant_research`. **Locator:** [AQR page](https://www.aqr.com/Insights/Research/Alternative-Thinking), snapshot hash `3a555c8cbdbd1fd67f0a601741ef35c89ad70b850921925f6e76ceaba4a1d601`. **Disclosed rule:** The collection record retained the official research page as a lead and did not assert an executable trading rule. **Failure:** no verified deterministic payload was available to the current normalizer. **Blocking schema requirements:** the schema requires explicit signal conditions, entry and exit mechanics, risk sizing and budgets, cost references, timing/cutoff rules, and constraints; these cannot be filled from the collection record without interpretation.

### 4. Man Insights lead

**Identifier:** `https://www.man.com/insights/100-dollar-oil-emerging-markets` — *What Does $100 Oil Mean for Emerging Markets?*. **Source:** `man_institute_research`, `published_quant_research`. **Locator:** [Man Insights page](https://www.man.com/insights/100-dollar-oil-emerging-markets), snapshot hash `1d136a4959d564364693bd54863b012b8c6021bd9bf63683b7b812b8e6f789da`. **Disclosed rule:** The collection record retained an official informational article lead and did not claim that the article disclosed a deterministic strategy. **Failure:** no verified deterministic payload; normalization rejected it as `incomplete_disclosure`. **Blocking schema requirements:** the current schema requires explicit executable signal, clock, entry, exit, risk, cost, and constraint objects, including missing-data and invalid-bar behavior.

### 5. Systematic academic lead

**Identifier:** `2608.24786v1` — *Harvesting the Volatility Risk Premium: A Learning-to-Rank Approach*. **Source:** `academic_systematic_research`, `academic_preprint`. **Locator:** [arXiv abstract](https://arxiv.org/abs/2608.24786v1) and [PDF rule locator](https://arxiv.org/pdf/2608.24786v1). **Disclosed rule:** The collection record preserved the paper lead and its PDF locator but did not extract or assert a complete executable rule payload. **Failure:** normalization required `verified_deterministic_rule` plus structured payload and rejected the record before rule reconstruction. **Blocking schema requirements:** the normalized schema requires all required fields for clock, signal, entry, exit, risk, costs, constraints, provenance, and analysis-only status; the metadata record does not supply those fields deterministically.

## E. Diagnosis

The best-supported classification is **D — a combination of A/B/C, with an additional pipeline-observability limitation**.

The evidence against a pure **A** conclusion is that the second collection is materially broader than the first: it adds open code/notebooks, AQR public research, Man Insights, systematic-trading academic records, and a distinct market-microstructure slice. Yet the collection records intentionally stop at provenance-preserving leads. Because the current normalizer rejects any record without a structured `deterministic_rule_payload`, the run cannot distinguish “the source lacks executable rules” from “the executable rules exist in the linked full text/code but were not extracted.” Therefore the data does not prove that the broader source universe fundamentally lacks deterministic strategies.

There is evidence consistent with **C**: public research pages and metadata-only academic records are poorly matched to a schema that demands complete executable timing, entry, exit, risk, cost, and constraint rules. The QuantConnect slice is closer to the desired source type, but the current collection stage still records stable code locators rather than parsing code into the required structured payload. This explains why diversification changed source composition but did not change the normalization result.

There is also a possible **B** issue, but it is not established. The schema is intentionally strict about execution and risk completeness, and that strictness is appropriate for preventing guessed backtests. This run provides no evidence that the schema itself is excessively restrictive because it never performed a full-text/code extraction attempt. A future authorization may add a provenance-preserving review adapter that populates `deterministic_rule_payload` only when every required field is explicitly disclosed. That is a recommendation only; no schema or protocol change is made here.

## F. Integrity and statistical boundary

The global trial ledger remains exactly **N=0**. No `trial_id` was created. All raw and filtered second-run files carry analysis-only flags and `trial_ledger_n=0`; the combined diagnostic also records zero research execution.

| Boundary item | Result |
| --- | ---: |
| Backtests | 0 |
| DSR calculations | 0 |
| PBO calculations | 0 |
| CPCV | 0 |
| OOS | 0 |
| WFO | 0 |
| Cost stress | 0 |
| Regime testing | 0 |
| Parameter perturbation | 0 |
| Survivor promotions | 0 |
| Live/paper trading | 0 |
| Candidate 1/v2 execution | 0 |
| Phase 2/3/4 execution | 0 |

The repository delta from the pre-second-run baseline `b703ef1bf3d1a4f7a4a5012763430110cce77c35` was restricted to `strategy_discovery_v1/second_collection_v1/`. The historical first-run data, normalization review, report, schemas, protocols, global ledger, Bybit OHLCV files and manifests, Drive files, lifecycle infrastructure, and Candidate 1/v2 artifacts were not modified. The combined diagnostic contains explicit checks for these protections and for exact A+B=C reconciliation.

## G. References

[1]: https://info.arxiv.org/help/api/user-manual.html "arXiv API User's Manual"
[2]: https://github.com/QuantConnect/Research "QuantConnect Research repository"
[3]: https://github.com/QuantConnect/Lean "QuantConnect LEAN repository"
[4]: https://www.aqr.com/Insights/Research "AQR Research index"
[5]: https://www.man.com/insights "Man Insights hub"
[6]: ../schemas/normalized_strategy.schema.json "Frozen normalized strategy schema"

The source registry, collection plan, raw and filtered batch records, second-run normalization review, combined diagnostic JSON, and validation scripts are stored under `strategy_discovery_v1/second_collection_v1/`.
