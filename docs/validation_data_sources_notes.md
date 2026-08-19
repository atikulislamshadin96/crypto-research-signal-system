# Validation data-source notes

External source checks performed on 2026-08-19.

| Data need | Source | URL | Finding |
|---|---|---|---|
| Binance USD-M Futures klines | Binance Data Collection | https://data.binance.vision/ | Official public archive is available; futures/um/monthly/klines is the preferred historical OHLCV source. |
| Binance public-data implementation details | Binance public-data repository | https://github.com/binance/binance-public-data | Documents Binance public archive conventions. |
| Hyperliquid historical archives | Hyperliquid historical-data documentation | https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data | Historical data is uploaded approximately monthly; API can be used to record additional history. Availability and symbol-specific coverage must be checked before using it as a filter. |
| Hyperliquid funding history | Hyperliquid perpetuals/API documentation | https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals | Public info endpoint documentation includes historical funding-rate retrieval. |
| Deribit historical volatility / DVOL-related data | Deribit API documentation | https://docs.deribit.com/api-reference/market-data/public-get-historical-volatility | Public API documents historical volatility data. DVOL coverage and exact endpoint fields must be verified before including it as a context variable. |
| Deribit API entry point | Deribit API documentation | https://docs.deribit.com/ | Public market-data API documentation. |

Research discipline: external source availability is not evidence of predictive value. Hyperliquid funding and Deribit volatility remain context variables unless an independent event study demonstrates predictive value without tuning on final OOS data.

## Funding-divergence source checks (2026-08-19)

| Provider | Verified public behavior | Research implication | Source |
|---|---|---|---|
| Hyperliquid | Funding is paid hourly; the documented formula uses an 8-hour-style rate computed from premium but charges one eighth each hour. The public `POST https://api.hyperliquid.xyz/info` interface exposes perpetual metadata/contexts and historical-funding-related methods. | Normalize Hyperliquid funding to an hourly rate and retain the raw reported value, timestamp, symbol, and API response. Do not compare it directly with an 8-hour CEX rate without normalization. | https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding ; https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals |
| dYdX v4 | Funding is calculated and charged hourly. The documented rate uses hourly premium sampling and market-specific parameters; the Indexer client exposes `getPerpetualMarketHistoricalFunding(ticker)`. | Normalize to the documented hourly rate and preserve the market ticker, indexer timestamp, funding rate, and response metadata. Governance/configuration changes must be tracked as regime breaks. | https://docs.dydx.xyz/concepts/trading/funding ; https://docs.dydx.exchange/api_integration-clients/indexer_client |

These sources establish data availability and cadence, not predictive value. Any HL↔dYdX divergence study must use common timestamps, explicit symbol mapping, hourly-to-4H/8H aggregation, and a pre-registered event definition before outcomes are viewed.
