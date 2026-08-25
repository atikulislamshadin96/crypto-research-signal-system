# Strategy Discovery v1 Architecture

**Status:** Frozen architecture design only. No strategy collection, market-data download, backtest, trading, paper trading, or deployment is permitted by this artifact.

**Version:** `strategy_discovery_v1`

**Scope:** Generate future deterministic candidates (`Candidate 5+`) for entry into the existing frozen Phase 0–8 ladder. This track is additive and must not replace, modify, shortcut, or reinterpret the existing ladder or its artifacts.

## 1. Non-negotiable boundaries

This research track is intentionally separated from the existing validation state. It must not touch Phase 1 L2 acquisition, the frozen Candidate 1 state grammar or thresholds, the Phase 3 result, the Phase 4 protocol/fingerprint, existing manifests, hashes, or research history. In particular, the current Phase 1 acquisition state (`560/730`) must continue uninterrupted.

This version defines architecture and protocol only. It does not collect real strategies, download market data, instantiate a candidate, run a backtest, or create a trading or paper-trading path. Any future implementation must refuse execution when a required frozen artifact is absent or when a requested operation is outside the allowed stage.

## 2. Design principles

The discovery funnel is a **research-control system**, not a strategy marketplace. Every candidate must be traceable to an allowed source class, transformed into a deterministic rule representation, assigned a stable identity, and recorded whether it was rejected before any performance test. The system must preserve negative results and must count all tested alternatives, not only the winner.

The primary signal must be economically or microstructurally defined and computable from timestamped data. A candidate is not admissible merely because it uses quant language or reports a high win rate. A rule that requires visual judgment, discretionary chart interpretation, or an undefined pattern description is rejected rather than translated by assumption.

The statistical significance bar is frozen before any candidate is backtested. The protocol uses the Deflated Sharpe Ratio (DSR) to correct Sharpe-ratio inference for multiple testing and non-normal returns, and Combinatorial Purged Cross-Validation (CPCV) to estimate Probability of Backtest Overfitting (PBO), following Bailey and López de Prado and the methodology described in *Advances in Financial Machine Learning* [1][2]. No ad hoc substitute may be silently introduced.

## 3. Source registry and admissibility policy

The source registry is defined in [`source_registry.json`](source_registry.json). It is a registry of **source classes and admissibility rules**, not a collection of real strategies. During a future collection run, each source record must contain provenance, access date, document identifier, version or revision, and a locator for the exact rule disclosure.

Allowed primary source classes are:

| Source class | Minimum admissibility condition | Typical evidence retained |
| --- | --- | --- |
| Academic or preprint research | The paper states an operational signal and all required decision variables, timing, exits, and constraints, or links to a complete reproducible supplement. | DOI/SSRN/arXiv identifier, version, pages or sections, supplement hash |
| Published quantitative research | The publication provides a complete rule disclosure or a reproducible implementation with unambiguous timing and cost assumptions. | Publication metadata, code/revision hash, rule-extraction notes |
| Open quantitative research archives | QuantConnect-, Quantopian-style, or equivalent archive material is admissible only when the full rule set and execution assumptions are available. | Repository or notebook URL, commit/version, extracted rule hash |
| Order-flow and market-microstructure research | The signal is defined using observable order book, trade, funding, liquidation, queue, or cross-venue variables with timestamp and sampling rules. | Paper/source identifier, variable definitions, event-time rules, data requirements |

Generic TradingView scripts, “90% win rate” pages, anonymous signal sellers, and retail technical-analysis blogs are excluded as primary sources. Such material may be used only as a pointer to a fully disclosed, independently verifiable rule set; the pointer itself is never the candidate source.

No source is promoted to collection merely because it is popular, profitable in a screenshot, or described as “institutional.” A future collector must prove that the source satisfies the registry policy before normalization.

## 4. Collection-time rejection filter

The filter runs before normalization and before any backtest. It rejects candidates whose **primary signal** is a lagging or smoothed technical indicator or a generic chart pattern. The frozen rejection taxonomy is:

| Code | Rejection category | Examples |
| --- | --- | --- |
| `lagging_indicator_primary` | Primary signal is a lagging or smoothed indicator | RSI, EMA/SMA crossover, MACD, Stochastic, Bollinger Bands |
| `generic_price_pattern_primary` | Primary signal is generic and not independently operationalized | Generic support/resistance, generic breakout |
| `standalone_smc_ict_primary` | An SMC/ICT-labeled pattern is used as standalone alpha | FVG, Order Block, BOS/CHoCH |
| `retail_marketing_source` | Source is retail marketing content without a complete disclosed rule set | Win-rate pages, anonymous signal sellers, undisclosed scripts |
| `subjective_rule` | Rule depends on a human visual or discretionary judgment | “Looks strong,” “clean structure,” “obvious rejection” |
| `incomplete_disclosure` | Required timing, exit, sizing, or data definition is absent | Missing stop, holding horizon, or signal timestamp |
| `non_deterministic` | The rule cannot be represented by the normalization schema without guessing | Undefined adaptive or discretionary behavior |
| `prohibited_scope` | Candidate requires a forbidden action or unavailable state | Trading, deployment, or mutation of frozen artifacts |

A candidate may have secondary descriptive indicators, but a prohibited category remains fatal when the prohibited element is the primary signal. Future collection reports must emit only summary counts by rejection category, source class, and collection batch. They must not create an annotated catalogue of excluded retail material.

## 5. Deterministic normalization contract

Normalization is a lossless translation into [`schemas/normalized_strategy.schema.json`](schemas/normalized_strategy.schema.json). The normalized representation uses a typed expression tree rather than free-form prose. Every value that affects a decision must resolve to one of the following: a typed constant, a field reference, a fixed-window statistic, a fixed-time event aggregate, an arithmetic expression, or a boolean comparison/logical expression. The schema forbids arbitrary executable code and subjective text in decision fields.

A normalized candidate must specify, at minimum:

| Area | Required deterministic content |
| --- | --- |
| Universe and clock | Instruments, venue(s), timezone, bar or event frequency, session/calendar, and data cutoffs |
| Signal | Exact fields, event aggregation, lookback windows, comparison operators, threshold units, and signal timestamp |
| Entry | Trigger, order type, fill convention, latency assumption, and whether same-bar execution is permitted |
| Exit | Time exit, signal exit, stop-loss, take-profit, and precedence when multiple exits occur |
| Risk and sizing | Risk budget, notional cap, leverage cap, sizing formula, rounding, and behavior on insufficient margin |
| Costs | Commission, spread, slippage, funding/borrow treatment, and the source of each parameter |
| Constraints | Concurrent positions, pyramiding, cooldown, missing-data behavior, and invalid-bar behavior |
| Provenance | Source references, extraction version, normalization version, and canonical rule hash |

If any required field is missing or ambiguous, the candidate is rejected with `incomplete_disclosure`, `subjective_rule`, or `non_deterministic`. The normalizer must not infer a missing rule from common practice.

## 6. Funnel and stage gates

The future pipeline is defined but not executed in v1:

```text
collection
  → collection-time rejection filter
  → deterministic normalization
  → in-sample backtest
  → DSR/PBO-corrected significance gate
  → OOS evaluation
  → walk-forward evaluation
  → cost/slippage stress
  → cross-asset and regime stability
  → parameter-perturbation check
  → survivor set
  → existing Phase 1–8 ladder from the top
```

Each stage is append-only and produces a versioned artifact. A candidate may advance only if the prior stage has a recorded pass, all required hashes are present, and the relevant protocol version is frozen. A failure remains in the registry with its rejection reason and observed metrics, if any.

The DSR/PBO gate is a joint gate. A candidate must satisfy the frozen protocol in [`protocols/dsr_pbo_cpcv_v1.json`](protocols/dsr_pbo_cpcv_v1.json), including the required DSR probability threshold, PBO limit, minimum observations, and leakage controls. Passing this gate does not authorize live use; it authorizes only the next research stage.

The survivor handoff is strict: every survivor becomes a new numbered candidate, starting at `Candidate 5` or the next unused candidate number, and enters the existing Phase 1–8 ladder at its top. No discovery-stage survivor may enter at Phase 2 or later, and no discovery artifact may mutate the frozen ladder.

## 7. Candidate identity and registry extension

The extended registry schema is [`schemas/candidate_registry.schema.json`](schemas/candidate_registry.schema.json). It preserves the existing tracking pattern—`candidate_id`, `version`, `hypothesis`, `status`, `validation_status`, `promotion_stage`, `metrics`, and `rejection_reason`—and adds discovery-specific provenance, rule, protocol, and trial-accounting fields.

A candidate identity must include the canonical normalized-rule hash, source reference set, source snapshot metadata, normalization schema version, and all applicable protocol versions. The total-trial counter used by DSR must be recorded in the candidate record or in a linked immutable batch record. It must include every candidate, parameterization, feature variant, execution variant, and failed test exposed to selection, including rejected and non-surviving trials when those trials entered the statistical search.

## 8. Freeze and change control

The protocol artifact is frozen at version `dsr_pbo_cpcv_v1`. Any change to the trial-count definition, return construction, DSR formula, CPCV partitioning, purge/embargo rules, gate thresholds, or acceptance criteria requires a new versioned protocol artifact and a new research batch. Existing results must not be silently reinterpreted under the new version.

The architecture document is itself scoped to `strategy_discovery_v1/`. Implementation work must preserve the repository's existing files, manifests, hashes, SQLite research history, Phase 1 acquisition process, Candidate 1 artifacts, and Phase 4 fingerprint/protocol.

## References

[1]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 "Bailey and López de Prado, The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality"

[2]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104847 "López de Prado, Advances in Financial Machine Learning (Chapter 1)"

[3]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4686376 "Arian, Norouzi Mobarekeh, and Seco, Backtest Overfitting in the Machine Learning Era"
