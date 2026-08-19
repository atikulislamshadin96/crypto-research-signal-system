# Historical Timestamp-Safe L2 Acquisition Design

**Status:** Implemented as a research-only acquisition path on 2026-08-19.

## Executive decision

Historical order-book state cannot be reconstructed honestly from OHLCV or aggregate trades. The repository therefore uses two separate paths. The first is an explicit archive-ingestion path for an official or authorized file whose URL, date range, schema, and usage terms are known. The second is a bounded forward collector that records public OKX and Bybit WebSocket messages with both exchange timestamps and local receive timestamps.

The strongest public exchange-native archive lead found is the official OKX historical-market-data page, which states that high-resolution L2 data is available from March 2023 onward [1]. The exact downloadable file endpoint and schema are rendered by the site after the user selects instrument, symbols, depth, and dates. Because the endpoint was not exposed as a stable documented API during inspection, the repository does not guess or scrape an undocumented URL. A downloaded file can be passed through `download-verified-l2` and `validate-historical-l2` only after its provenance and terms are recorded.

> **No historical L2 result is research-usable until source timestamps, receive timestamps or an equivalent clock field, snapshot/delta semantics, sequence integrity, symbol and venue coverage, and normalized-file checksums are present.**

## Source selection

| Source | Historical L2 | Free/public status | Timestamp and sequence quality | Repository decision |
|---|---:|---|---|---|
| OKX official historical-data page | Documented from March 2023; exact file schema pending | Public download UI; terms and endpoint must be verified per file | Potentially suitable; verify snapshot/delta and timestamps | Primary archive candidate, not yet ingested |
| OKX public WebSocket | No retroactive history; forward only | Public market-data stream | Exchange timestamp plus local receive timestamp; sequence fields available | Primary forward collector |
| Bybit public WebSocket | No retroactive history; forward only | Public market-data stream | `cts`, `ts`, `u`, `pu`, and `seq` are documented for order-book updates [2] | Secondary forward collector |
| Binance Futures public WebSocket | No retroactive history; forward only | Public market-data stream | Suitable for local-book reconstruction when snapshot and diff streams are kept together [3] | Optional future collector |
| Bybit historical-data page | OrderBook product is listed; exact file access and coverage pending | Not assumed free until a real file and terms are verified | Unknown before file inspection | Candidate archive source; fail closed |
| Tardis | Full historical L2 product | Paid/API-key product; redistribution restricted by terms | Strong event-level schema and timestamp fields [4] | Paid fallback only |
| Kaggle Coinbase fixture | About 12 days of aggregated snapshots | Public dataset states CC0 | Useful for parser tests, not venue-specific OOS | Development fixture only |
| CoinAPI | Full order-book products | Account/credits required [5] | Strong product description | Paid fallback only |

Public accessibility is not the same as a blanket right to redistribute raw market data. The repository stores source URLs, retrieval times, file hashes, and a usage note. Raw third-party files are ignored by Git and should remain in the exchange-approved download location, workflow artifact store, or an authorized private object store.

## What can be collected for free

The practical free path is **prospective collection** from public exchange WebSockets. It does not recover the past, but it creates a timestamp-safe archive from the collection start date onward. The implementation subscribes to the OKX `books` channel and Bybit public order-book channel, writes append-only raw JSONL, and then writes a canonical normalized JSONL plus a manifest. The raw record preserves provider payload, venue, connection identifier, and local receive time; the normalized record preserves source time, receive time, sequence fields, action, levels, and a canonical raw-message hash.

The official OKX page provides a possible historical backfill from March 2023, but the exact archive response must be downloaded and inspected manually or through a separately validated explicit URL. The code includes an explicit checksum-verifying downloader rather than an undocumented endpoint crawler. If a downloaded archive is CSV, ZIP, or another schema, it must first be converted to the normalized event shape without dropping source timestamps or sequence fields. If it cannot be converted without inference, it remains `BLOCKED_INTEGRITY`.

## Required collection horizon

The horizon is deliberately staged rather than presented as a guarantee. The first **30 days** are an engineering and data-quality burn-in period: reconnect rate, sequence gaps, symbol coverage, stale intervals, and storage volume are measured. A minimum **90 continuous calendar days** is required before a first descriptive L2 state/event report. A minimum **180 days** is required for a preliminary development-only event study spanning more than one volatility regime. The preferred target is **365 days** for chronological development/OOS separation and regime coverage. A shorter archive may be useful for testing parsers, but it cannot support the repository’s claim of a durable edge.

A candidate is not promoted because the horizon elapsed. It must also meet event-count, timestamp, missingness, cost-stress, chronological validation, and uncertainty gates. The four frozen state-first hypotheses remain data-blocked until their individual minimum event and quality requirements are met.

## Sampling and storage protocol

The collector uses a bounded four-minute run by default so it can execute safely in a scheduled runner. OKX uses the high-resolution `books` subscription rather than the existing five-level `books5` snapshot path. Bybit uses the existing public order-book subscription. This is a message archive, not a pre-aggregated bar dataset. No OHLCV reconstruction is performed.

Raw messages are stored as one canonical JSON object per line under `data/l2/raw/` or the workflow artifact directory. Normalized records are stored under `data/l2/normalized/`. Manifests are small JSON files under `data/l2/manifests/` and are allowed to be committed. Raw and normalized data are ignored by Git because a full L2 archive is too large and may have redistribution restrictions. The scheduled workflow uploads each bounded run as an artifact with a 90-day retention period; retention beyond that requires an authorized durable storage location or an always-on user-controlled machine.

The manifest records input-file SHA-256 and byte counts, normalized-file SHA-256 and byte count, schema/protocol version, event counts, venue-symbol counts, snapshot count, update count, duplicate count, missing source/receive timestamps, sequence gaps, out-of-order events, stale source-to-receive lag, non-monotonic receive timestamps, source time range, and validation status. A `PASS` result requires a snapshot before updates, non-empty events, source timestamps, no collector errors, no sequence gaps, no out-of-order timestamps, no stale intervals over the configured threshold, and monotonic receive time. Exact duplicates can produce `PASS_WITH_DEDUP_WARNINGS`; missing or inconsistent integrity data produces `BLOCKED_INTEGRITY`.

## Reproducible commands

The bounded forward collector is analysis-only:

```bash
python -m crypto_signal_system.cli \
  --config config/default.yaml \
  collect-historical-l2 \
  --symbols BTCUSDT ETHUSDT SOLUSDT \
  --duration-seconds 240 \
  --archive-dir artifacts/l2/raw \
  --normalized-output artifacts/l2/normalized/latest.jsonl \
  --manifest artifacts/l2/manifests/latest.json
```

An explicitly supplied official archive can be downloaded with a checksum:

```bash
python -m crypto_signal_system.cli \
  download-verified-l2 \
  --url '<official-public-file-url>' \
  --output data/l2/archives/source-file.bin \
  --sha256 '<provider-or-independent-sha256>'
```

An existing raw JSONL or JSONL.GZ file can be normalized and validated without running a network collector:

```bash
python -m crypto_signal_system.cli \
  validate-historical-l2 \
  --input data/l2/archives/source-events.jsonl.gz \
  --symbols BTC-USDT-SWAP ETH-USDT-SWAP SOL-USDT-SWAP \
  --normalized-output data/l2/normalized/source-events.jsonl \
  --manifest data/l2/manifests/source-events.json
```

The command exits nonzero when the data is not research-usable. This is intentional: a blocked dataset must not silently flow into an economic backtest.

## Hosting and retention choices

A scheduled repository runner is suitable for bounded collection and short-term artifact retention, but it is not a permanent database. The included workflow runs every 15 minutes, collects four minutes, uploads raw/normalized/manifest artifacts, and retains them for 90 days. It does not commit raw L2 into Git and it does not make trading decisions.

For a free starting path, leave the workflow artifact retention at 90 days and periodically export artifacts to a user-controlled, legally permitted archive. For a true multi-month or multi-year archive without manual export, use a continuously running user-controlled machine or a durable storage service with explicit credentials and retention policy. The repository itself records manifests and checksums but is not treated as the raw data warehouse.

## Final Phase 1 status

The forward acquisition path is implemented and tested. The OKX historical archive is a promising official candidate but remains **pending endpoint/schema/terms verification**. Binance official archives remain usable for OHLCV and aggregate trades, not historical L2. Therefore the state-first candidates remain `BLOCKED_MISSING_HISTORICAL_L2` until an authorized historical archive or a sufficiently long prospective archive passes the manifest gates.

## References

[1]: https://www.okx.com/en-us/historical-data "OKX Historical Market Data"
[2]: https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook "Bybit V5 Public Orderbook WebSocket"
[3]: https://developers.binance.com/en/docs/derivatives/usds-margined-futures/websocket-market-streams/partial-book-depth-streams "Binance USDⓈ-M Futures Partial Book Depth Streams"
[4]: https://tardis.dev/ "Tardis Market Data"
[5]: https://www.coinapi.io/products/flat-files/docs "CoinAPI Flat Files Documentation"
