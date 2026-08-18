# Provider Research for Fallback Ingestion

## Verified public sources

| Provider | Evidence | Use in system |
|---|---|---|
| OKX | Official API guide: https://www.okx.com/docs-v5/en/ | Public REST and WebSocket documentation; regional API-domain warning noted. |
| OKX historical data | https://www.okx.com/historical-data | Official page states candlestick history is available from July 2023 onward and funding-rate history from March 2022 onward. |
| Binance archive | https://data.binance.vision/ | Official public market-data archive exposes futures and spot directories. |

## Sandbox endpoint tests on 2026-08-18

The following public OKX endpoints returned HTTP 200 and `code: 0` from the sandbox:

- `GET https://www.okx.com/api/v5/market/candles?instId=BTC-USDT-SWAP&bar=15m&limit=5`
- `GET https://www.okx.com/api/v5/market/history-candles?instId=BTC-USDT-SWAP&bar=15m&limit=5`
- `GET https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=5`

The candle response is newest-first and contains timestamp, open, high, low, close, base volume, quote volume, and a confirmation flag. The public endpoint response did not require API credentials. The funding response includes `fundingRate`, `fundingTime`, `instId`, and `realizedRate`.

The endpoint test returned timestamps around 2026-08-18. It confirms access and response shape, not 2025 historical availability through the same live API. The official OKX historical-data page is the source for the longer downloadable history claim.

## Design decision

Implement provider selection as `okx` first for the analysis workflow, with Binance public/archive as a separate explicit provider and no silent mixing of exchange data. Every candle and funding record must retain provider, instrument, endpoint, observed-at timestamp, and retrieval status. If all providers fail or the requested historical range is incomplete, the run must stop with `NO DATA` rather than generate a signal.
