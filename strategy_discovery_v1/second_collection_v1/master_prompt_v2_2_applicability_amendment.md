# Master Prompt v2.2 Applicability Amendment

**Status:** additive, versioned policy amendment
**Scope:** `freqtrade_strategy_v1` Batch 001 reassessment only
**Supersedes:** the v2.1 Freqtrade applicability gate only; it does not rewrite historical artifacts, the normalized strategy schema, or the frozen DSR/PBO/CPCV protocol.

## Decision

For a Freqtrade strategy source, the configured pairlist, venue/exchange, quote currency, and research timeframe scope may satisfy the **applicability environment** through one uniformly frozen batch-level research harness. They are **external assumptions**, not source facts. This is allowed because Freqtrade strategy classes commonly define signal and trade-management logic while the configured pairlist and exchange are supplied outside the strategy file.

This decision does not allow a framework default to silently become a candidate fact. The harness must explicitly declare the exact pair universe, venue, quote currency, and applicable timeframe rule before any measured trial. The same values must apply to every candidate, except for a predeclared, non-tunable exclusion rule that is applied without observing results.

## Completeness semantics

`source_rule_complete` means that the source explicitly and deterministically defines the strategy logic required for the research hypothesis: entry direction and condition, exit or custom-exit condition, stop-loss/take-profit or time-exit behavior, timing where required, and any source-specific pair restriction or dependency. If the source contains no conflicting pair restriction, the common research harness may provide the applicability environment under the `uniform_external_research_scope` resolution.

`execution_assumption_required` means that the source-rule layer is complete under this applicability policy, but the research contract still requires external assumptions. These include the pair universe, venue, quote currency, timeframe scope, position sizing, risk budget, notional and leverage caps, commission, slippage, spread, fill rule, latency, funding/borrow, rounding, margin behavior, external configuration, missing/invalid-data behavior, and OHLCV manifest references.

`execution_contract_complete` remains unavailable until the v1.2 manifest is fully populated, frozen, hashed, uniformly applied, and linked to the candidate identity. It still authorizes research measurement only; it is not production or live-trading readiness.

## Applicability resolution

| Resolution | Meaning | Outcome |
| --- | --- | --- |
| `source_explicit` | The strategy source declares a pair/universe restriction or explicit applicability rule. | Validate that rule against the common harness; conflicts remain review-only. |
| `uniform_external_research_scope` | No conflicting source restriction exists; the common pairlist/venue scope is an external research environment. | May satisfy applicability for `source_rule_complete`; all scope fields remain external assumptions. |
| `conflict_review` | Non-empty or non-literal informative-pair scope, pair-dependent restriction, or unresolved applicability conflict exists. | `needs_review`; no auto-pass. |
| `not_resolved` | Applicability cannot be established from source or the approved common scope. | `needs_review`. |

A runtime reference such as `metadata['pair']` used for logging or pair-keyed state is not itself a pairlist declaration. An empty `informative_pairs()` return is not a trade universe declaration. Non-empty informative-pair declarations require review unless their relationship to the trade universe is explicitly and deterministically resolved.

## Non-negotiable controls

No candidate-specific pairlist, venue, timeframe, sizing, cost, fill, latency, or risk choice is allowed. No values may be tuned after observing performance. Every external field must carry `origin=external_assumption` and a deterministic value, model, or reference. A changed manifest or scope creates a new trial identity if a backtest later occurs.

This amendment does not authorize a backtest. Before measurement, the v1.2 manifest must be populated and frozen, exact Bybit OHLCV manifest references must be reconfirmed, the global ledger must start at `N=893`, and a separate explicit measured-backtest authorization must be recorded. No live, paper, deployment, or promotion claim may be made from this evidence-stage decision.
