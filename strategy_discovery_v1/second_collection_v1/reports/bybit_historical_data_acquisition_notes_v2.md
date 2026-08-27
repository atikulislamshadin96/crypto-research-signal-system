# Bybit historical derivatives-data acquisition notes v2

## Official sources reviewed

1. [Get Funding Rate History | Bybit API Documentation](https://bybit-exchange.github.io/docs/v5/market/history-fund-rate)
2. [Get Mark Price Kline | Bybit API Documentation](https://bybit-exchange.github.io/docs/v5/market/mark-kline)

## Verified API facts

The funding endpoint is `GET /v5/market/funding/history`. It covers USDT/USDC perpetual and inverse perpetual contracts. Required parameters are `category` and uppercase `symbol`; `startTime` and `endTime` are optional timestamps in milliseconds; `limit` is 1–200 and defaults to 200. The response contains `symbol`, `fundingRate`, and `fundingRateTimestamp`. Bybit documents that passing only `startTime` returns an error, while passing only `endTime` returns records up to that end time.

The mark-price endpoint is `GET /v5/market/mark-price-kline`. It covers linear contracts and supports intervals `1,3,5,15,30,60,120,240,360,720,D,M,W`; therefore exact 15-minute mark candles are supported with `interval=15`. The futures page limit is 1–1000 and defaults to 200. The response list is sorted in reverse order by candle start time and each record contains start time, open, high, low, and close mark prices. The close price can be the last traded price when the candle is not closed, so acquisition must enforce the frozen UTC end boundary and exclude any candle whose interval is not fully closed at that boundary.

## Acquisition constraints for this task

Use only `category=linear`, symbols `BTCUSDT` and `ETHUSDT`, exact UTC window `2025-08-22T00:00:00Z` through `2026-08-21T23:59:59.999Z`, and exact 15-minute mark candles. Funding records must be acquired at their native settlement timestamps, not resampled. Preserve raw HTTP responses and deterministic normalized records with URL, retrieval timestamp, request parameters, response hashes, and pagination evidence. Do not acquire OHLCV, funding history beyond the authorized window, or other market data. Do not synthesize or forward-fill funding or mark values.
