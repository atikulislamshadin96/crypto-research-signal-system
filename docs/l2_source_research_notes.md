# Historical L2 Source Research Notes

**Research date:** 2026-08-19

## Official sources reviewed

### OKX historical market data
URL: https://www.okx.com/en-us/historical-data

The official OKX historical-data page states:

- Tick-level trade history is available from September 2021 onward.
- Historical perpetual funding rates are available from March 2022 onward.
- High-resolution L2 order-book data is available from March 2023 onward.

This is currently the strongest publicly documented exchange-native historical L2 source found for the repository’s research. The page does not yet expose all file-format and exact sampling details in the extracted text; those must be verified from the download endpoint before ingestion is treated as validated.

### OKX API documentation
URL: https://www.okx.com/docs-v5/en/

The official API documentation recommends WebSocket for market data and order-book depth. It documents public WebSocket collection, connection/request constraints, ping/pong stability requirements, and source/server timestamps. The API agreement link is https://www.okx.com/help/okx-api-agreement and must be reviewed before production-scale collection. The correct regional API domain may differ by user registration region.

### Binance Futures WebSocket documentation
URL: https://developers.binance.com/en/docs/derivatives/usds-margined-futures/market-data/websocket-api/market-data-requests

The official Binance documentation is the reference for maintaining a local order book from depth data and WebSocket streams. Binance historical Futures OHLCV/aggTrades archives do not by themselves provide historical L2 order-book states. The repository must not reconstruct L2 from OHLCV or trades.

### Bybit public order-book WebSocket documentation
URL: https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook

Bybit documents snapshot-plus-delta order-book streams. Linear/inverse level-50 updates are documented at 20 ms, level-200 at 100 ms, and level-1000 at 200 ms. The stream provides an update ID (`u`), cross sequence (`seq`), source/matching-engine timestamp (`cts`), and message timestamp (`ts`). A new snapshot resets the local book; zero-size levels are deleted; existing levels are updated. These fields are suitable for sequence-gap, restart, stale-message, and timestamp-quality validation.

## Preliminary source decision

- **Usable historical archive candidate:** OKX official high-resolution L2 from March 2023 onward, subject to confirming downloadable files, exact granularity, symbol coverage, and terms.
- **Usable forward collection:** OKX public WebSocket and Bybit public order-book WebSocket. These can create timestamp-safe prospective archives but cannot retroactively produce historical OOS.
- **Binance:** official public WebSocket is usable for forward local-book reconstruction; official Futures archive data currently known in this project covers klines/aggTrades, not historical L2.
- **Third-party archives:** may be useful only if licensing, source timestamps, full message history, sequence integrity, and chain of custody are documented. They should not be treated as free or legally redistributable without explicit terms.

## Non-negotiable quality gates

Historical L2 is accepted only when the manifest records source URL, download timestamp, legal/usage note, symbol, venue, date range, message count, source timestamps, receive timestamps where available, sampling/granularity, snapshot/delta counts, sequence gaps, duplicate messages, stale intervals, parser version, normalized-file SHA-256, and byte count. Missing history must result in `BLOCKED_MISSING_HISTORICAL_L2`; no OHLCV reconstruction or synthetic order book is allowed.

## Download-link inspection

The OKX historical-data page renders five `Download` controls as JavaScript buttons without static `href` attributes in the initial DOM. The official page confirms the existence and start date of high-resolution L2 data, but the exact downloadable endpoint and file schema require either button interaction or discovery from page/API network metadata. The collector must not guess a URL; endpoint discovery will be implemented only after validating the response content type, date/symbol metadata, and terms.

## Browser evidence URL

The page was inspected directly at https://www.okx.com/en-us/historical-data on 2026-08-19.

## Public and third-party archive findings

### Tardis.dev
URL: https://tardis.dev/

Tardis documents tick-by-tick order-book snapshots and incremental L2 updates, trades, funding, open interest, and liquidations across many exchanges. Its sample download is publicly accessible and the sample schema includes exchange, symbol, exchange timestamp, local/receive timestamp, snapshot flag, side, price, and amount. The full historical replay/download product requires an API key; therefore it is **not a free full-history source**. It is a viable paid or institutionally licensed fallback and a useful schema/reference source. Any use in a public repository must respect its terms and must not redistribute downloaded files unless explicitly permitted.

### Kaggle Coinbase LOB dataset
URL: https://www.kaggle.com/datasets/martinsn/high-frequency-crypto-limit-order-book-data

This public dataset states that it contains approximately 12 days of Coinbase BTC, ETH, and ADA order-book snapshots, aggregated at 1-second, 1-minute, and 5-minute frequencies, with 15 best levels. The page states a CC0/public-domain license. It is legally reusable as a small development/format-validation fixture, but it is not sufficient for the repository’s multi-year, venue-specific, timestamp-safe OOS research: it is short, snapshot-aggregated, and not the target OKX/Binance/Bybit venue history.

### Bybit historical data page
URL: https://www.bybit.com/en-GB/derivative-activity/history-data/

The official Bybit page lists public trading history and an OrderBook data product for spot, contract, and option markets. Exact downloadable coverage and terms must be checked at the download endpoint. This is a promising official source for historical data, but no collector should assume its files are free, complete, or sequence-replayable until a real file is downloaded and its schema/terms are verified.

### CoinAPI Flat Files
URL: https://www.coinapi.io/products/flat-files/docs

CoinAPI documents full limit-book updates, periodic 50-level snapshots, depth summaries, trades, and quotes. Its documentation states that access requires an account and usage credits, so it is not a free source. It can be considered a paid fallback, not the default Phase 1 solution.

## Source classification

| Source | Official/primary | Full historical L2 | Free | Timestamp/sequence suitability | Repository decision |
|---|---:|---:|---:|---|---|
| OKX historical data | Yes | Documented from Mar 2023; exact files pending endpoint inspection | Public download appears available; verify terms | Potentially high; must inspect schema | Primary archive candidate |
| OKX WebSocket | Yes | Forward only | Yes, public market data | High if receive/source timestamps and gaps are recorded | Primary forward collector |
| Bybit WebSocket | Yes | Forward only | Yes, public market data | High: ts, cts, u, seq documented | Secondary forward collector |
| Bybit historical page | Yes | Listed, exact coverage pending | Unknown | Unknown until file inspection | Candidate archive source; fail closed pending verification |
| Binance depth WebSocket | Yes | Forward only | Yes | High if local book is built from snapshots/deltas | Optional secondary forward collector |
| Tardis | Third-party licensed | Yes | No for full history | Strong schema and timestamp support | Paid fallback; no redistribution by default |
| Kaggle Coinbase fixture | Public dataset | About 12 days, aggregated snapshots | Yes, CC0 stated | Useful for parser tests, not OOS | Dev/test fixture only |
| CoinAPI | Third-party licensed | Yes | No; credits required | Strong product description | Paid fallback; no redistribution by default |

No source is accepted as a substitute for official/authorized data solely because it is downloadable. License, provenance, message-level timestamps, sequence integrity, and venue/symbol coverage are required.

## Dynamic endpoint inspection

The OKX historical-data page loads a JavaScript application and several `/priapi` resources, but the initial performance-resource list did not expose a direct static order-book archive URL. The exact download endpoint remains unverified. The implementation must use an explicit configured endpoint or a separately validated discovery step; it must never infer a file URL from the page text alone.

## OKX order-book download dialog

The official OKX order-book dialog opens without login and exposes:

- Instrument selector; default Spot.
- Symbol selector supporting up to four symbols.
- Depth field; default shown as 400.
- Start and end date fields.
- A results/download table after query.

The initial network resources include public instrument and coin endpoints under `/priapi/v5/broker/public/trade-data/`, but the archive query/download request is triggered only after symbol/date submission. This confirms a public UI path but not yet a stable API contract. The collector implementation will treat the downloaded file as an external input and validate its content/schema before ingestion; it will not scrape undocumented endpoints in the first version.
