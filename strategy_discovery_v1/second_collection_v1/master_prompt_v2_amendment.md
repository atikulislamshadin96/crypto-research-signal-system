# Master Prompt v2 Amendment — Two-Level Completeness for Code Sources

**Status:** additive policy amendment  
**Applies to:** `strategy_discovery_v1/second_collection_v1/` and future code-repository source pivots  
**Does not rewrite:** the attached `master_prompt.pdf`, frozen DSR/PBO/CPCV protocol, normalized strategy schema, Phase 1 artifacts, Candidate 1/v2, or archived academic collection

## Purpose

The first Freqtrade batch exposed a distinction that must be made explicit. A source can fully disclose its trading logic while leaving execution-environment assumptions to a batch-level test harness. The absence of source-declared sizing, fees, slippage, fill, latency, or external configuration must not erase the evidence that entry/exit/TP/SL logic is explicit. Conversely, those missing execution assumptions must never be silently guessed or represented as source facts.

## Required completeness states

| State | Meaning | Allowed next action |
| --- | --- | --- |
| `source_rule_complete` | Source text/code explicitly determines the strategy hypothesis, instrument universe or applicability, clock/frequency, signal, entry direction/condition, and exit/SL/TP or time-exit logic. | Create a reviewable draft; may proceed to an execution-assumption gate, never directly to live use. |
| `execution_assumption_required` | The source-rule layer is complete, but one or more execution-environment fields—sizing, risk budget, fees, slippage, spread, fill, latency, funding/borrow, rounding, invalid-data behavior, or external config—are not explicit in the source. | Apply one separately frozen batch execution-assumption manifest, or remain review-only. No per-candidate defaults. |
| `execution_contract_complete` | Source rules plus a separately committed execution-assumption manifest produce a complete reproducible research contract. | Eligible for the existing pre-backtest gates if all other invariants pass. |
| `needs_review` | A source rule field is absent, ambiguous, contradictory, or not deterministically mapped. | Human review only; no trial. |
| `rejected_incomplete` | Required source-rule facts cannot be established from explicit evidence. | No normalization or trial. |

`source_rule_complete` is not equivalent to `candidate_complete` in the existing normalized schema. `execution_assumption_required` is a controlled intermediate state, not permission to invent values. The existing `normalized_strategy_v1` object remains the final complete contract.

## Explicit-only rule

A source-code literal, AST assignment, or control-flow branch is explicit only when the code directly determines the field. A hardcoded `stoploss = -0.10` is explicit. A fee, sizing, fill, or stop value that exists only in an unfetched config file or framework default is `not_found` in the source evidence bundle. A batch manifest may supply a research assumption, but the field must be marked `external_assumption`, linked to the manifest hash, and excluded from the source-rule evidence claim.

No strategy-specific assumption may be chosen after observing results. The same frozen manifest applies to every candidate in a batch. Changing any assumption that can affect selection creates a new trial identity and increments the global ledger.

## Code-source rejection clarification

The existing rejection taxonomy remains unchanged, but its application to code sources is semantic rather than token-only. `lagging_indicator_primary` applies when a lagging indicator is the primary signal or entry condition. A mere import, auxiliary feature, secondary filter, documentation mention, or indicator used outside the primary trigger is not sufficient by itself. The adapter must record the exact code span supporting the classification. No code candidate is exempt from the rejection taxonomy.

## Freqtrade-specific source-rule gate

For `freqtrade_strategy_v1`, a source may reach `source_rule_complete` only if exact code evidence establishes instrument applicability or pair scope, strategy timing, an explicit entry direction and condition (`populate_entry_trend` or legacy `populate_buy_trend`), an explicit exit condition (`populate_exit_trend`, legacy `populate_sell_trend`, or an explicit custom-exit path), and explicit hardcoded stop/target or time-exit behavior where claimed. Framework defaults do not fill missing rule fields. `minimal_roi`, `stoploss`, `trailing_stop`, and `timeframe` are extracted as source facts only when literal assignments are present.

A Freqtrade source normally reaches `execution_assumption_required` because position sizing, fees, slippage, fill, latency, funding, and external configuration are often outside the strategy file. It can reach `execution_contract_complete` only after a single batch-level execution-assumption manifest is committed and hashed.

## Trial and DSR boundary

The post-fix ledger count is never reset. DSR calculations use the ledger N at the selection event. A source-rule draft that has not been measured does not enter N. Once a complete execution contract is actually backtested, that distinct trial is added to the ledger before selection statistics are reported. A change in strategy code, execution assumptions, data manifest, feature version, or protocol version creates a new trial.

## Required artifacts for a re-evaluation

A code-source re-evaluation must produce a versioned evidence bundle, source-rule classification, execution-assumption manifest or an explicit `execution_assumption_required` status, primary-signal rejection evidence, and a no-promotion report. It must not vendor third-party source or change the frozen normalization schema in place.

This amendment authorizes design and re-evaluation preparation only. It does not authorize a backtest, DSR/PBO/CPCV run, OOS test, trading action, or candidate promotion by itself.
