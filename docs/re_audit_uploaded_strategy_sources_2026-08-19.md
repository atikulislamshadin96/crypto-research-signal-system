# Re-Audit of Newly Uploaded Strategy Sources

**Date:** 2026-08-19  
**Mode:** Research-only; no signal implementation, Telegram, paper trading, deployment, or live execution.  
**Decision rule:** A claimed win rate, profit factor, reward-to-risk ratio, or profitability statement is not evidence without reproducible data, timestamp rules, realistic costs, untouched OOS, uncertainty, and an auditable trade/event ledger.

## Source provenance

| Source | Local path | SHA-256 | Size | Role |
|---|---|---|---:|---|
| Source document A | `/home/ubuntu/upload/pasted_content.txt` | `bd7d001000c43c9e7031c5ae97f736e9f7f4f8403bf21f74a1fb65c0efcb9d2e` | 5,373 bytes | Focused L2 state-transition protocol |
| Source document B | `/home/ubuntu/upload/pasted_content_2.txt` | `19b56a5ff693211855c3521ff9792efd7ac96bf175025e9855fea1a0448f645d` | 9,827 bytes | Autonomous architecture and four-candidate queue |

The two documents are internally consistent with the repository’s existing research-first policy. They contain almost no independent profitability evidence; their main value is protocol design and explicit rejection of data mining.

## Claim and rule audit

| Source claim or rule | Audit result | Treatment |
|---|---|---|
| State-dependent L2 liquidity transition plus flow overlay is the primary research objective | Mechanistically plausible and materially testable, but not a validated strategy | Retain as frozen candidate `liquidity-state-transition-eth-btc-v1` |
| Historical Binance Futures L2, trades, timestamps, spread, top-20 depth and signed flow are required | Correct. OHLCV cannot reconstruct L2; no synthetic approximation is allowed | Preserve `BLOCKED_MISSING_HISTORICAL_L2` gate |
| Liquidity states may include normal, thinning, stressed, replenishing, asymmetric and post-shock recovery | A state grammar is a protocol choice, not empirical evidence | Use the existing frozen 3-bin state candidate; any alternative state grammar must be a new version |
| Event horizons from 1 second through 5 minutes, with spread/depth changes, excursions and event-clustered inference | Appropriate event-study design; adjacent snapshots must not be treated as independent trades | Retain as future protocol fields; no directional signal added |
| Order flow must be tested only after the L2-only effect | Strong anti-data-mining and incremental-information rule | Retain staged evaluation: L2-only, flow-only, L2+flow, matched control |
| BTC, ETH and SOL must be evaluated separately before pooling | Correct sample and heterogeneity control | Current candidate starts with BTC/ETH; SOL remains later extension |
| Directional candidate gates: positive net expectancy, PF >1.20, WR >45%, RR >1.5, multi-window and multi-asset stability | Acceptable research gates, not guarantees; RR is not evidence by itself | Keep as frozen promotion gates only after event study passes |
| Prop-firm simulation with 0.25% risk, 3% daily breaker and 7% total DD | A downstream risk diagnostic, not evidence of edge or readiness | Remains blocked until all prior gates pass |
| Four candidates should be separate versioned modules | Architecture requirement, not proof of profitability | Retain four immutable v1 candidates |
| Deterministic promotion state machine DATA → EVENT STUDY → ROBUSTNESS → FLOW → DIRECTIONAL → OOS → COST → RISK | Compatible with existing evaluation ladder | Preserve; no automatic promotion is enabled |
| Binance/OKX/Bybit/Hyperliquid data should be collected where legally and technically available | Data-source plan; availability and synchronization still need to be demonstrated | Treat unavailable history as blocked, not as a negative result |
| Failed candidates must be archived with ID, version, metrics, dataset hash, protocol and feature versions | Essential audit rule | Already supported by the fingerprint registry; queue now records provenance |
| Research and signal engines must remain separate | Required safety boundary | No signal-engine changes made |
| Only PAPER_ELIGIBLE/PAPER_ACTIVE may enter a paper signal engine | Safe architecture, but paper engine is not enabled | Preserve disabled status |
| “NO_VALIDATED_EDGE_FOUND” is an acceptable outcome | Correct | Retain as final system principle |

## Deduplication against the four frozen candidates

| New-source concept | Relationship to existing candidate | Result |
|---|---|---|
| L2 state + depth imbalance + spread + signed flow + transition | Exact conceptual match to Priority 1 | **Duplicate / same candidate; retained unchanged** |
| Depletion → recovery/replenishment → displacement | Exact conceptual match to Priority 2 | **Duplicate / same candidate; retained unchanged** |
| OI + funding + liquidation flow + L2 deterioration + spread/recovery | Exact conceptual match to Priority 3 | **Duplicate / same candidate; retained unchanged** |
| Synchronized Binance/OKX/Bybit venue flow/depth/lead-lag/cost | Exact conceptual match to Priority 4 | **Duplicate / same candidate; retained unchanged** |
| Six-state liquidity grammar instead of the frozen three-bin grammar | Parameter/protocol variant, not independent mechanism | Not added; would require a new version only after a preregistered reason |
| 1s/5s/10s/30s/1m/5m horizon set | Horizon expansion of Priority 1 | Not added; recorded as protocol detail, not a new hypothesis |
| Directional conversion after event study passes | Promotion stage, not a new mechanism | Not added; remains downstream and frozen only after evidence |
| Autonomous state machine, registry, reports and schedules | Infrastructure requirements, not hypotheses | Retained as architecture; no new strategy candidate |

## Existing candidates retained

All four existing candidates are retained with their existing IDs and versions. No existing hypothesis was overwritten or silently modified.

| Priority | Hypothesis ID | Exact measurable definition | Evidence grade | Testable with current repository data? | Status | Next research stage |
|---:|---|---|---|---|---|---|
| 1 | `liquidity-state-transition-eth-btc-v1` | Pre-event state from relative spread, top-20 depth and top-20 imbalance; test post-event state transition, then compare L2-only, signed-flow-only and L2+flow against matched controls with event clustering | **B- / mechanism-supported, not validated** | **No**: no timestamp-safe historical top-20 L2 history | `BLOCKED_DATA` | Acquire and validate BTC/ETH historical L2; run state-transition event study before any direction |
| 2 | `liquidity-depletion-replenishment-displacement-v1` | Fixed-window normalized depth/spread deterioration, subsequent depth/spread recovery, then measure signed mid-price displacement, execution cost and matched controls | **C+ / plausible and testable, no independent validation** | **No**: historical L2 and synchronized trades are missing | `QUEUED_BLOCKED_DATA` | Use the same historical L2 manifest after Priority 1 data audit; no SMC labels |
| 3 | `liquidation-crowding-exhaustion-risk-v1` | Joint high crowding proxy, liquidation/forced-flow activity and low depth or high spread; classify normal/stressed/exhausted/replenishing risk state | **C+ / risk mechanism supported, event-heterogeneous** | **No**: long liquidation history and synchronized L2/OI/funding are missing | `QUEUED_BLOCKED_DATA` | Build event-level cascade dataset; leave-one-event-out and placebo testing |
| 4 | `cross-venue-price-discovery-migration-v1` | Synchronized venue-A signed flow/depth/spread change followed by venue-B response under timestamp tolerance, basis, latency and cost controls | **C+ / research-supported, data-intensive** | **No**: no long synchronized multi-venue L2/trade archive | `QUEUED_BLOCKED_DATA` | Complete forward OKX/Bybit collection and obtain timestamp-safe venue history; estimate lead-lag only in development |

## New candidates added

**None.** The new documents do not contain a genuinely independent or superior hypothesis. Every substantive proposal is either an exact restatement of one of the four candidates, a parameter/protocol variant, or infrastructure guidance. Therefore:

> **NO NEW VALIDATED HYPOTHESIS FOUND.**

No candidate was added, removed, or modified. The four candidates remain the only approved research queue entries.

## Unsupported claims rejected

The documents do not provide a new audited performance claim with an identifiable raw dataset. Accordingly, the following are not accepted as evidence: any implied expectation that the primary L2 candidate will produce a directional edge; any assumption that the order-flow overlay must add predictive value; any assumption that one venue leads another; any assumption that liquidation events predict reversal or continuation; and any suggestion that passing the stated gates implies prop-firm readiness.

The existing uploaded high-win-rate/PF/RR claims from earlier source material also remain unverified and are not imported into the registry as metrics. The present documents’ protocol gates are preserved as gates, not as observed results.

## Data currently available

The repository currently contains verified OHLCV archives, official Binance Futures aggregate-trade material for limited coverage, OKX public live/forward collection code, Bybit/OKX WebSocket archival code, and a bounded microstructure Parquet smoke artifact. These are useful for engineering validation and future prospective collection.

They do **not** constitute a sufficient historical L2 dataset for the four candidates. The bounded Parquet smoke artifact is not a multi-year, timestamp-safe, event-complete research archive and must not be treated as economic evidence.

## Data still missing

The main missing inputs are long historical top-N L2 snapshots or order-book events for BTC/ETH, synchronized public trades with source timestamps, reliable sequence/gap metadata, complete liquidation/OI/funding history for the risk-state candidate, and a sufficiently long synchronized OKX/Bybit/Binance cross-venue archive with venue-specific fees and latency controls. Forward collection can fill the prospective portion, but it cannot be relabeled as historical OOS.

## Updated research priority

The queue remains exactly: **Priority 1 L2 state transition + flow; Priority 2 depletion → replenishment → displacement; Priority 3 liquidation/crowding → exhaustion; Priority 4 cross-venue migration.** The orchestrator must not advance merely because a candidate is inconvenient; it can advance only after `REJECTED`, `BLOCKED_DATA`, or a fully validated downstream state. No threshold relaxation or candidate rescue is permitted.

## Repository changes in this re-audit

The repository receives a machine-readable provenance registry and a machine-readable priority queue. The source files, hashes, source claim ranges, evidence grades, data requirements, current status, and next stage are recorded. Existing hypothesis code and frozen parameters remain unchanged. No alert, signal, paper, or deployment path was added.

## Final status

**NO NEW VALIDATED HYPOTHESIS FOUND.** Existing four candidates are retained unchanged. The system remains research-first, analysis-only, fail-closed on missing historical L2, and permanently prevented from treating document claims as profitability evidence.
