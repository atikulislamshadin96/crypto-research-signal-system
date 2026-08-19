# Web research source notes

## Source 1 — Easley et al., *Microstructure and Market Dynamics in Crypto Markets*
URL: https://stoye.economics.cornell.edu/docs/Easley_ssrn-4814346.pdf
Accessed: 2026-08-19

The paper studies five major cryptocurrencies and asks whether market-microstructure measures explain or predict price dynamics. The visible abstract states that microstructure measures of liquidity and price discovery have predictive power for price dynamics; it highlights implications for electronic market making, dynamic hedging, and volatility estimation, with particular attention to BTC and ETH roll measures and VPINs. It also states that the results change little during crypto winter, suggesting some stability across market conditions. This is evidence for testing measurable liquidity/order-flow variables, not proof that a retail SMC pattern is profitable after fees.

Evidence classification: academic/empirical, but the exact tradable specification, turnover, fee model, and untouched-out-of-sample performance must be checked before implementation.

## Source 2 — Cont, Kukanov & Stoikov, *The Price Impact of Order Book Events*
URL: https://arxiv.org/html/1011.6402v3
Accessed: 2026-08-19

Using NYSE TAQ data for 50 U.S. stocks, the paper reports that short-horizon price changes are mainly driven by order-flow imbalance (OFI) at the best bid/ask, with a roughly linear relation whose slope is inversely related to market depth. The study reports an average R-squared around 65% for its contemporaneous short-interval model and says the relationship is robust across stocks and time scales. It also argues that raw traded volume is noisier and less robust than OFI once order-flow imbalance is accounted for. This is a foundational microstructure relationship, not crypto-specific profitability evidence; a crypto implementation must test venue, horizon, latency, queue definition, and costs.

## Source 3 — Angerer, Gramlich & Hanke, *Order Book Liquidity on Crypto Exchanges*
URL: https://www.mdpi.com/1911-8074/18/3/124
Accessed: 2026-08-19

The article analyzes intraday liquidity for multiple cryptocurrencies across exchanges. Its summary says order-book variation is linked to liquidity measures and that liquidity patterns can help traders reduce liquidity-dependent trading costs by timing trades. It emphasizes fragmentation across exchanges and trading pairs, and questions whether uninterrupted 24/7 trading is always optimal for lower-liquidity pairs. Implication for this project: liquidity state and execution cost should be modeled as state variables and should be part of signal gating and cost stress, not treated as a generic directional pattern.

## Source 4 — Reddit r/Daytrading SMC discussion
URL: https://www.reddit.com/r/Daytrading/comments/1i92ni2/i_just_learned_about_smart_money_and_im_genuinely/
Accessed: 2026-08-19

The thread is a useful sentiment sample, not performance evidence. The original poster says that after about a week of experimentation and paper trading, liquidity sweeps/fair-value gaps appeared to work and that SMC improved their results. Replies dispute the idea that institutions specifically target individual retail traders and emphasize that retail flow is small. The post contains no controlled sample, timestamped trade ledger, cost model, or out-of-sample validation. It supports the conclusion that SMC terminology is widely discussed and vulnerable to narrative/conspiracy framing, not that the pattern is profitable.

## Source 5 — Reddit r/algotrading order-book imbalance discussion
URL: https://www.reddit.com/r/algotrading/comments/1pgsphr/algo_only_based_on_orderbook_imbalance_could_it/
Accessed: 2026-08-19

The discussion describes an order-book strategy using OBI/OFI, queue dynamics, depth shifts, and short-horizon execution. The strongest caution in the thread is that the order book can be least reliable when imbalance is strongest: liquidity withdrawal, adverse selection, liquidation cascades, funding reflexivity, and regime shifts can invalidate book-derived signals. The discussion also notes that latency, estimator choices, hidden assumptions, inventory control, volatility kill-switches, and execution costs remain central. One commenter frames the apparent edge as passive spread capture plus adverse-selection control in favorable conditions, rather than robust directional forecasting. These are practitioner observations without audited performance.

## Source 6 — X/Twitter post on liquidity sweep + bearish CHOCH
URL: https://x.com/MhagamaFau31375/status/2052758333958852942
Accessed: 2026-08-19

The public post presents a standard SMC short sequence: a liquidity sweep above a recent high/low followed by bearish CHOCH, framed as a high-probability setup. The accessible page did not provide a sample, cost model, out-of-sample ledger, or reproducible parameter definitions. It can be converted into a testable event hypothesis only after fixing lookback, sweep distance, CHOCH definition, entry timing, invalidation, and horizon.

## Source 7 — X/Twitter post on spot/perpetual flow divergence and order fingerprinting
URL: https://x.com/karlbooklover/status/2082818048692543931
Accessed: 2026-08-19

The post claims a contemporaneous divergence in BTC spot versus perpetual flow and links to an article about order fingerprinting, including the warning that CVD can be misleading. The post is technically more concrete than generic SMC marketing because it points to cross-venue flow and order-pattern classification, but it still is a single observation and does not establish a repeatable edge. This is a promising research family for event studies if the repository can define venue coverage, synchronized timestamps, flow classification, persistence windows, and costs before looking at results.

## Source 8 — BitcoinTalk funding-rate arbitrage thread
URL: https://bitcointalk.org/index.php?topic=5584224.0
Accessed: 2026-08-19

This user-generated thread describes funding-rate arbitrage across Binance, Bybit, dYdX, Hyperliquid, and another venue, including claimed 30-day funding comparisons and discussion of negative-rate windows. The post presents numerical tables but is not an audited source: the author is a low-activity forum account, the raw API extracts and timestamped trade ledger are not attached, and venue-specific fees, borrow/transfer risk, basis moves, liquidation, and execution are not fully demonstrated. Treat the thread as a hypothesis lead for the already drafted HL↔dYdX funding-divergence event study, not as evidence of profit.

## Source 9 — Bieganowski & Slepczak, *Explainable Patterns in Cryptocurrency Microstructure*
URL: https://arxiv.org/html/2602.00776v1
Accessed: 2026-08-19

The paper studies Binance Futures perpetual order books and trades at one-second frequency from 2022 through October 2025. It uses interpretable features including spread, top-of-book volumes, signed order flow/trade imbalance, and VWAP-to-mid deviations, with time-series cross-validation, and reports stable cross-asset feature importance and dependence structures. It explicitly validates tradability using conservative top-of-book taker and fixed-depth maker backtests. Its flash-crash analysis highlights that maker and taker strategies can diverge because of adverse selection and systemic risk. Implication: the most credible advanced candidates are measurable microstructure states and execution-aware rules—not chart labels alone—and any maker-style backtest must include fill uncertainty, adverse selection, inventory, and crash kill-switches.

## Source 10 — GitHub order-flow topic page
URL: https://github.com/topics/order-flow?l=python&o=asc&s=updated
Accessed: 2026-08-19

The topic page lists public projects covering OFI, market-impact simulation, crypto order-book imbalance, low-latency WebSocket feeds, Hawkes processes, and order-flow backtesting. The page includes at least one repository description explicitly stating that a public 1-minute BTC research attempt found no tradable edge, which is a useful negative-result signal. The breadth of public implementations indicates that basic OBI/OFI ideas are not genuinely undiscovered; novelty must come from robust measurement, cross-venue synchronization, regime-aware gating, and honest execution modeling. Repository listings themselves are not audited performance evidence.

## Source 11 — TradingView open-source SMC liquidity-sweep script
URL: https://www.tradingview.com/script/DJgoI4Ha-Smart-Money-Concept-Liquidity-Sweep-MarkitTick/
Accessed: 2026-08-19

The open-source script combines BOS/CHoCH labels, order blocks, fair-value gaps, premium/discount zones, inducement labels, session kill zones, and a 0–5 confluence score. This confirms that the standard SMC feature bundle is already highly packaged and widely accessible. The page describes visualization and rule components but does not present a verified, cost-aware, untouched-OOS performance ledger. Therefore, these components should be treated as crowded candidate primitives, not as an unexploited strategy.

## Source 12 — Garcia Seuma, *Where does the criticality live? Early-warning signals are event-heterogeneous across seven crypto-perpetual liquidation cascades*
URL: https://arxiv.org/html/2607.27070v1
Accessed: 2026-08-19

The paper studies seven major BTC perpetual liquidation cascades from 2022–2025 using minute-level price and five-minute leverage/order-flow data. It finds no event-invariant early-warning variable: price showed a critical-slowing-down signature in five of seven events but failed in sudden-news shocks. The one population-level regularity surviving all events was compression of taker-order-flow variance, which passed a placebo test but is explicitly described as a population-level precursor rather than a reliable per-event alarm. This is strong caution against single-event “liquidation sweep” narratives; liquidation/order-flow variables are better suited to regime-risk monitoring and event studies than automatic directional entries until replicated.

## Source 13 — Barone & Lillo, *Trading in the Sunshine or in the Shade: Market Impact and Adverse Selection on Hyperliquid*
URL: https://arxiv.org/abs/2606.15715
Accessed: 2026-08-19

Using address-level Hyperliquid data, the paper reconstructs 4.3 million hidden metaorders and compares them with 465,000 visible protocol-native TWAP executions. It reports that visible TWAPs have lower execution costs and smaller permanent price impact than comparable hidden metaorders; visible programs attract liquidity and tilt displayed depth toward the absorbing side, while hidden metaorders executed alongside visible same-direction flow incur higher permanent costs. This supports a research direction around order disclosure, flow visibility, adverse selection, and passive-versus-aggressive execution, but it is not a retail directional strategy. For this repository, an analysis-only event study could test whether large visible-flow imbalance plus spread/depth state predicts short-horizon impact after conservative costs.

## Source 14 — Zhivkov, *The Two-Tiered Structure of Cryptocurrency Funding Rate Markets*
URL: https://www.mdpi.com/2227-7390/14/2/346
Accessed: 2026-08-19

This 2026 open-access study constructs 35.7 million one-minute funding observations across 26 exchanges and 749 symbols over eight consecutive days. It reports that centralized venues dominate price discovery, while 17% of observations show spreads of at least 20 bps; only 40% of top opportunities remain profitable after transaction costs and spread reversals, with forced exits in 95% of opportunities. The key implication is not that funding arbitrage is easy, but that persistence/duration and execution risk determine whether an apparent spread is tradable. This strongly supports a pre-registered HL↔dYdX event study with time-to-reversal, net-cost, forced-exit, and venue-risk fields, while rejecting naive “highest funding wins” logic.


## Follow-up research: uploaded strategy claims and state-dependent L2 evidence

### Uploaded document claims audited
- Document 1 claims a 2,600-trade SMC backtest with 61.2% win rate and PF 2.17, plus 55–65% win rates for liquidity sweep, kill zones, order blocks, and a 4H BTC/ETH model. The pasted material does not provide an accessible primary URL, trade ledger, cost model, asset/time split, OOS protocol, or uncertainty intervals; these figures are unverified practitioner claims and must not enter the engine as evidence.
- Document 2 proposes state-dependent L2 liquidity transitions plus order flow as the strongest candidate, followed by liquidity depletion/replenishment plus displacement, liquidation/crowding plus liquidity-state exhaustion, cross-venue microstructure, and options positioning as a regime filter. It explicitly rejects pure BOS/FVG/OB/CHoCH as validated standalone strategies and warns that historical L2 data is required.

### Verified recent sources
- Jeon, arXiv:2607.09230 (2026), studies Binance BTCUSDT and ETHUSDT futures from 2023–2026 using top-20 L2 and trade flow. Its target is post-event liquidity-state transition, not price direction. A coarse pre-event state is predictive; nonlinear L2 shape adds value; order flow adds incremental value only on top of the L2 state, with the effect established for ETH and not established for BTC. This supports an event-study and risk/liquidity-state module, not a ready-made directional strategy.
- Bieganowski and Ślepaczuk, arXiv:2602.00776 (2026), studies Binance Futures perpetual LOB/trades at 1-second frequency from 2022-01-01 to 2025-10-12 across BTC, LTC, ETC, ENJ, and ROSE. It reports stable cross-asset feature importance for OFI, spreads, depth, and VWAP-to-mid features, but the paper’s tradability claims depend on conservative taker/maker backtests and still require independent replication in this repository.
- Anastasopoulos et al., Journal of Financial Markets 79 (2026), reports that international/world order flow predicts the cross-section of cryptocurrency returns out of sample. Data availability is stated as “on request”; it is a research lead rather than immediately reproducible public data for this repository.
- Angerer, Gramlich, and Hanke, JRFM 18(3), 124 (2025), finds intraday crypto order-book variation and liquidity patterns that affect trading costs. This supports execution-cost and liquidity-state gating, not a standalone alpha claim.
- Additional research leads include queue-position/fill-probability versus post-fill return trade-offs, cross-venue price discovery/lead-lag, and liquidation-cascade early-warning work. Current liquidation research is explicitly event-heterogeneous, so it should be tested as a capital-preservation/regime filter before any directional use.

### Provisional classification
1. State-dependent L2 liquidity-state transition + flow: high research priority; requires timestamped L2 snapshots/events and trades; target should be state transition or execution quality before direction.
2. Liquidity depletion/replenishment + displacement: medium-high priority; requires depth/spread/flow transitions and a frozen causal displacement definition; no SMC labels as signal.
3. Liquidation/crowding + liquidity exhaustion/replenishment: medium priority; requires liquidation/OI/funding/flow/depth and many independent cascade episodes; default output is risk-state classification.
4. Cross-venue price-discovery migration: medium priority; requires synchronized venue trades/L2, lead-lag, basis, and latency controls; not simple venue-A-up/venue-B-follows.
5. Queue-aware adverse-selection/fill-quality model: medium priority; requires full depth, queue proxy, fills or carefully bounded fill simulation; analysis-only execution-quality study.
6. Options positioning + microstructure: context/regime filter only; options data and timestamp alignment are required; not standalone directional alpha.

No uploaded performance percentage is accepted as validated until its source, raw data, timestamp rules, full trade ledger, fees/slippage, untouched OOS, and uncertainty are independently reproduced.

### Additional sources checked on 2026-08-19
- Jeon, “When Does Order Flow Matter? State-Dependent L2 Liquidity-State Transitions in Crypto Futures,” https://arxiv.org/html/2607.09230v1. The paper’s staged OOS results support state-first modeling: coarse pre-event state and nonlinear L2 shape matter; order flow adds only as an overlay, with ETH clearing the overlay null and BTC not established.
- Bieganowski and Ślepaczuk, “Explainable Patterns in Cryptocurrency Microstructure,” https://arxiv.org/html/2602.00776v1. The study reports portable feature families but its model/trading results require independent replication with repository data and strict leakage controls.
- Anastasopoulos et al., “Order flow and cryptocurrency returns,” https://www.sciencedirect.com/science/article/pii/S1386418126000029. The article reports out-of-sample information in international order flow, but its data are available on request, so it is not immediately reproducible here.
- Angerer, Gramlich, and Hanke, “Order Book Liquidity on Crypto Exchanges,” https://www.mdpi.com/1911-8074/18/3/124. The study supports liquidity-aware execution timing and cost modeling, not an automatic directional signal.

### Updated decision
The uploaded documents strengthen the case for a **state-first microstructure research program**, not for adding a 4H SMC bundle with claimed 55–65% win rates. The first implementation candidates should be: (A) L2 liquidity-state transition event study with flow overlay, (B) liquidity depletion/replenishment and displacement event study, (C) liquidation/crowding-to-liquidity-exhaustion risk-state study, and (D) cross-venue price-discovery migration study. Queue-aware adverse-selection and options-positioning modules remain later context/execution research. All remain unvalidated until timestamp-safe data, costs, chronological OOS, uncertainty, and independent replication are complete.
