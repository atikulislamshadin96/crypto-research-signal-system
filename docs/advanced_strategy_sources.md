# Advanced Strategy Research Sources

## OKX public API documentation

Source: https://www.okx.com/docs-v5/en/

The official OKX documentation states that OKX provides REST and WebSocket APIs and recommends WebSocket for market data and order-book depth. The public-data section is the relevant source for candles, order books, trades, funding, and open-interest style derivatives data. The documentation also notes regional API-domain requirements and distinguishes public market-data access from authenticated account/trading permissions. This supports a research design that uses public market data only and keeps trading permissions disabled.

## Research direction

Candidate low-crowding hypotheses to investigate with real data are: order-flow imbalance and price impact, cross-venue lead-lag and liquidity fragmentation, perp basis/funding dislocations, liquidation/impact shocks, and options-implied positioning where public data is available. No claim is made that any candidate is unused or unexploited; each must be treated as a falsifiable research hypothesis.

## Bybit public order-book documentation

Source: https://bybit-exchange.github.io/docs/v5/market/orderbook

Bybit documents a public order-book endpoint covering spot, USDT/USDC/inverse contracts, and options. Contract and spot responses can provide up to 1000 levels. The response includes bid/ask prices and sizes, a system timestamp, update ID, cross-sequence, and matching-engine timestamp (`cts`) that can be correlated with the public trade channel. This makes snapshot-level microstructure features such as spread, depth imbalance, queue concentration, and event-time alignment measurable, but it does not by itself provide a full historical order-book replay; such replay would require archived snapshots/deltas or a vendor dataset.

The same official documentation navigation lists public endpoints for funding-rate history, recent public trades, open interest, historical volatility, and long/short ratio. These are candidate inputs, subject to availability, timestamp alignment, and survivorship/data-quality checks.

## Academic evidence: Easley, O'Hara, Yang, Zhang (April 2024)

Source: https://stoye.economics.cornell.edu/docs/Easley_ssrn-4814346.pdf
SSRN copy: https://ssrn.com/abstract=4814346

The paper studies five major cryptocurrencies using high-frequency Binance data from January 2021 through July 2023. It evaluates standard microstructure variables including Amihud liquidity, Kyle lambda, VPIN, Roll measure, and Roll Impact, and uses machine learning to predict changes in realized volatility, autocorrelation, skewness, kurtosis, and Jarque-Bera statistics.

Reported findings include relatively high Roll and VPIN values in crypto, predictive power for future market-dynamics labels, average AUC above 0.55 across currencies and variables, individual-feature AUC roughly 0.54–0.61 except skewness, and important cross-asset effects from BTC and ETH Roll/VPIN. The paper reports that results changed little during the crypto-winter regime. These are predictive findings about market dynamics and execution-relevant labels, not a guaranteed directional trading strategy or profit claim.

Research implication for this repository: prioritize toxicity/liquidity-state and cross-asset features, and test them as regime/entry filters or volatility/holding-period selectors rather than assuming they directly predict next-bar direction. Require purged chronological validation, cost-aware execution, and a separate untouched period because the cited paper does not establish profitability for this implementation.

## Perpetual-futures and basis research leads

Sources:
- https://arxiv.org/html/2212.06888v5
- https://ideas.repec.org/p/arx/papers/2212.06888.html
- https://www.nber.org/system/files/working_papers/w32936/w32936.pdf

The search results identify empirical/theoretical work on perpetual futures showing that deviations from no-arbitrage prices can be material, may co-move across currencies, and tend to diminish over time. This motivates testing basis/funding dislocations as conditional state variables or convergence hypotheses. It does not establish a standalone directional edge. Any implementation must model funding timing, borrow/short constraints, execution legs, index/mark-price differences, and cross-venue transfer or hedging costs.

## Liquidation research lead

Source: https://arxiv.org/abs/2607.27070

A recent research lead studies early-warning signals around crypto-perpetual liquidation cascades across major BTC events. This is not yet treated as validated evidence for the repository; it motivates an event-risk classifier based on volatility acceleration, open-interest changes, funding extremes, spread/depth deterioration, and liquidation proxies. Such a module should initially be used as a risk-off filter or event-state label, not as an unvalidated entry signal.

## OKX API implementation constraints

Source: https://www.okx.com/docs-v5/en/

OKX states that it provides REST and WebSocket APIs and recommends WebSocket for market data and order-book depth. Public market data can be collected without account-trading permissions, while authenticated permissions are separate. The documentation warns that API domains are region-dependent (for example, US/AU and EU users may need different domains), so the provider adapter must make the API base URL configurable and record it in run metadata. WebSocket connections require heartbeat/reconnect handling and subscription limits; a historical microstructure collector therefore needs persistent storage and a gap/reconnect audit log rather than simply polling a REST snapshot.

## Historical microstructure data availability

Search findings:
- Binance Vision: https://data.binance.vision/
- Binance public-data repository: https://github.com/binance/binance-public-data
- OKX historical market data: https://www.okx.com/historical-data
- CoinAPI historical order-book article: https://www.coinapi.io/blog/full-order-book-data-in-crypto
- CoinDesk Data order-book product: https://data.coindesk.com/order-book

Binance Vision appears to provide official futures monthly trade archives in addition to klines, and the Binance public-data repository documents aggregate-trade files. OKX advertises downloadable historical market data including candlesticks, aggregate trades, and order-book data, but the exact public availability, coverage, licensing, and format must be verified before use. Commercial vendors advertise deeper Level-2/L3 history; they should not be silently assumed available or free.

Research constraint: OHLCV-only 2025 data cannot validate order-book imbalance, VPIN, queue dynamics, or cross-venue lead-lag claims. Those features require timestamped trades/order-book snapshots or event streams. If unavailable for the same period, the backtest must mark them unavailable and exclude the strategy from performance claims rather than fabricate proxies.

## Academic research leads

Relevant research leads include Easley et al., *Microstructure and Market Dynamics in Crypto Markets* (2024): https://stoye.economics.cornell.edu/docs/Easley_ssrn-4814346.pdf; *Order flow analysis of cryptocurrency markets* (Springer): https://link.springer.com/article/10.1007/s42521-019-00007-w; *Order-Flow Imbalance and Short-Horizon Return Predictability in Cryptocurrency Markets* (SSRN): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6938742; *Fundamentals of Perpetual Futures* (arXiv/RePEc): https://ideas.repec.org/p/arx/papers/2212.06888.html; *Cryptocurrency exchanges and comovements of cryptocurrency returns* (SSRN): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3604322; and a lead-lag study of emerging crypto assets: https://link.springer.com/chapter/10.1007/978-981-96-6839-7_14.

These sources support testing order-flow imbalance, price impact/liquidity state, funding/basis, and cross-venue lead-lag as hypotheses. They do not establish that any specific public rule is currently profitable after fees, slippage, latency, adverse selection, or crowding. The implementation should therefore register each hypothesis before testing and preserve failed variants.
