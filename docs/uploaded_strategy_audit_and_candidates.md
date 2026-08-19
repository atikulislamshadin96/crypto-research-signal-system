# Uploaded Strategy Audit and Frozen Research Candidates

**As-of date:** 2026-08-19  
**Scope:** BTC/ETH/SOL-focused, analysis-only, no live execution, no automatic paper promotion.

## Executive verdict

দুটি uploaded document-এর মধ্যে সবচেয়ে গুরুত্বপূর্ণ এবং repository-তে ব্যবহারযোগ্য ধারণা হলো **SMC label নয়, state-first market microstructure**: আগে order-book liquidity state কী অবস্থায় ছিল, তারপর aggressive flow কী করল, spread/depth কীভাবে বদলাল, এবং শেষে price বা execution quality কী হলো। এই framing সাম্প্রতিক research-এর সঙ্গে সামঞ্জস্যপূর্ণ। তবে এটিকে এখনও profitable strategy বলা যাবে না।

প্রথম document-এ 2,600-trade backtest, 61.2% average win rate, 2.17 profit factor, 55–65% win rate এবং 1.8–2.5 profit factor-এর মতো সংখ্যা আছে। কিন্তু pasted file-এ primary URL, raw trade ledger, timestamp rules, cost model, asset/time split, untouched OOS, bootstrap uncertainty বা protocol version নেই। তাই এই সংখ্যাগুলো **unverified practitioner claims** এবং কোনো hypothesis pass করার evidence নয়।

দ্বিতীয় document তুলনামূলকভাবে বেশি disciplined। এটি pure BOS/FVG/Order Block/CHoCH-কে validated edge হিসেবে প্রত্যাখ্যান করে এবং L2 state + flow interaction, liquidity depletion/replenishment, liquidation/crowding state, cross-venue microstructure এবং options positioning-কে research candidates হিসেবে আলাদা করে। এই classification-ই repository-র পরবর্তী research direction-এর জন্য গ্রহণ করা হলো।

## Strategy-by-strategy classification

| Uploaded concept | Mechanism | Required data | Main risk | Evidence status | Repository decision |
|---|---|---|---|---|---|
| Liquidity sweep + FVG + order block | Chart-defined sweep, displacement and retest | OHLCV; historical L2 for confirmation | Subjective labels, look-ahead, crowding, multiple confirmation tuning | Social/marketing claims only; repository BOS family rejected or underpowered | Keep closed as a standalone strategy; allow only a pre-registered event label/control |
| ICT kill zones / Silver Bullet | Time-of-day conditional setup | Timestamped bars, session timezone, volume/depth | Session definitions and selection bias; no causal institutional-flow proof | Practitioner claims, no audited OOS ledger | Do not add as alpha; may be a stratification variable in an event study |
| Order blocks / breaker blocks / mitigation blocks | Last opposing candle or failed block | OHLCV and causal structure rules | Discretionary definitions, survivorship and hindsight | No independent cost-aware evidence | Do not add as standalone family |
| FVG / Power of Three / premium-discount | Visual imbalance or narrative daily phase | OHLCV | Ambiguous definitions and confirmation overfitting | Unverified | Do not add as standalone family |
| State-dependent L2 liquidity + order flow | Pre-event spread/depth/imbalance state followed by flow overlay | Top-N L2, trades, timestamps, spread, depth | Historical L2 availability, venue differences, short-horizon costs | Recent 2026 study supports state prediction; ETH flow overlay established in that study, BTC not established [1] | **Priority 1: add as state-transition event study** |
| Liquidity depletion/replenishment + displacement | Depth/spread deterioration, aggressive flow, then recovery or price displacement | L2, trades, spread, depth, volatility, optional OI | “Displacement” can become a disguised chart pattern; sequence leakage | Plausible mechanism, not validated directional edge | **Priority 2: add as event study with non-SMC displacement definition** |
| Liquidation/crowding + liquidity exhaustion | Crowding and forced-flow context followed by depletion/exhaustion/replenishment | Liquidations, OI, funding, L2, trades | Few independent cascades; event heterogeneity; false alarms | Recent cascade research finds no event-invariant alarm [2] | **Priority 3: risk-state/event study, not a short/long rule** |
| Cross-venue price-discovery migration | Venue A state/flow changes followed by venue B response | Synchronized venue trades/L2, basis, latency | Timestamp misalignment, fees, transfer/venue risk | Researchable but data-intensive | **Priority 4: lead-lag event study** |
| Queue-aware adverse selection | Queue position, fill probability, post-fill return and adverse selection | Full depth/events, queue proxy, fills or conservative simulation | Impossible fill assumptions and latency | Recent research supports a fill-versus-adverse-selection trade-off [3] | Later execution-quality study; no live maker module |
| Options positioning + microstructure | Options skew/OI/depth as regime context | Options surface, OI, funding, L2, timestamps | Low-frequency context may not improve short-horizon execution | Contextually plausible, no standalone alpha evidence | Later regime filter only |

## Verified evidence boundary

Recent L2 research on Binance BTCUSDT and ETHUSDT futures from 2023–2026 defines a post-event liquidity-state transition target rather than directly predicting price direction. It reports that a coarse pre-event L2 state is informative, nonlinear L2 shape adds value, and order flow adds value only as an overlay; the overlay is established for ETH and not established for BTC in the reported tests [1]. This is a strong reason to reproduce the **state transition** first, not to copy the paper into an immediate trading system.

Additional work reports stable feature families involving OFI, spread, depth and VWAP-to-mid relationships across several crypto assets, but its tradability findings still require independent replication with conservative fills and crash testing [4]. Cross-exchange liquidity research supports timing execution around liquidity conditions, not a generic directional signal [5]. A 2026 liquidation-cascade study reports event heterogeneity and no event-invariant early-warning variable, so liquidation features should initially reduce exposure or classify risk rather than produce automatic shorts or longs [2].

> **Rule:** A mechanism can be research-worthy without being profitable. The repository will only call an edge validated after causal data checks, realistic costs, chronological OOS, walk-forward/CPCV where possible, perturbation, uncertainty, and independent replication.

## Frozen candidates for the repository

### Candidate A — State-dependent L2 liquidity transition with flow overlay

The target is a discrete liquidity-state transition such as calm, mixed or stressed, constructed from relative spread, top-N depth and top-N imbalance. The first baseline uses only pre-event state. The second layer adds local signed flow. A directional return result is secondary and cannot be used to bypass the state-transition gate.

The required data are timestamped L2 snapshots or event streams, public trades, spread, depth and a data-quality manifest. The first evaluation must use rolling chronological folds, event-clustered bootstrap, blocked flow-shuffle nulls and separate ETH/BTC results. SOL is a later extension only after the BTC/ETH protocol is frozen.

### Candidate B — Liquidity depletion/replenishment plus displacement

Define depletion causally as a deterioration in normalized depth and/or spread over a fixed window, replenishment as a subsequent recovery under the same fixed measurements, and displacement as a future signed mid-price move exceeding a pre-registered depth-scaled threshold. Do not use BOS, FVG, order-block or candle-name labels in the primary specification.

The first output is an event study reporting post-event return, spread, depth and execution-cost changes. It must include matched non-event controls and report whether displacement occurs before or after replenishment. No directional strategy is constructed unless the event effect survives costs, controls and untouched OOS.

### Candidate C — Liquidation/crowding to liquidity-exhaustion risk state

The event is a joint state of elevated OI/funding/crowding proxy, abnormal liquidation or forced-flow activity, and L2 depth deterioration. The initial outcome is a risk-state label: normal, stressed or exhausted/replenishing. The module may mark a market as untradeable or increase a research risk penalty; it may not issue a short or long signal.

The protocol requires independent cascade episodes, event-level leave-one-event-out checks, placebo windows and explicit news-shock stratification. A single historic crash cannot establish a general alarm.

### Candidate D — Cross-venue price-discovery migration

The event is a causal, synchronized change in liquidity or signed flow on venue A followed by a measurable response on venue B. Venue order is estimated only inside the training/development sample and then frozen. The study reports lead-lag, basis response, spread/depth response and net execution cost.

A simple “venue A moved first” rule is forbidden. Venue coverage, timestamp tolerance, dropped packets, outages, fees and transfer constraints must be recorded. Missing synchronization blocks the experiment.

## Implementation contract

The autonomous engine may propose only JSON hypothesis specifications. Deterministic Python code validates family, features, parameters, causality, data availability and analysis-only status. Every candidate receives a permanent fingerprint containing canonical hypothesis JSON, dataset manifest hash, protocol version and feature version. A failure is never silently retried; a changed dataset or protocol creates a new immutable experiment.

The engine will generate a bounded queue for the four candidates above. It will not add the unverified 2,600-trade SMC claims, claimed 55–65% win rates, 1:3 reward-to-risk assumptions, kill-zone win rates, or prop-firm pass probabilities to the repository as facts.

## References

[1]: https://arxiv.org/html/2607.09230v1 "Jeon, When Does Order Flow Matter? State-Dependent L2 Liquidity-State Transitions in Crypto Futures"
[2]: https://arxiv.org/html/2607.27070v1 "Garcia Seuma, Where does the criticality live?"
[3]: https://arxiv.org/html/2502.18625v2 "Albers et al., The Market Maker's Dilemma"
[4]: https://arxiv.org/html/2602.00776v1 "Bieganowski and Ślepaczuk, Explainable Patterns in Cryptocurrency Microstructure"
[5]: https://www.mdpi.com/1911-8074/18/3/124 "Angerer, Gramlich and Hanke, Order Book Liquidity on Crypto Exchanges"
