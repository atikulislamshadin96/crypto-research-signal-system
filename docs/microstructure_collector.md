# Prospective Microstructure Event Collector

The collector is a separate, analysis-only process. It archives public OKX and Bybit WebSocket events; it does not calculate a live signal, submit an order, access private credentials, or enable execution.

## Run command

After installing the package dependencies, run:

```bash
crypto-signal --config config/default.yaml collect-microstructure \
  --symbols BTCUSDT ETHUSDT \
  --archive-dir artifacts/microstructure_events
```

The process is intentionally persistent. It should be supervised outside the scheduled four-hour scan, with filesystem rotation and an operational stop policy appropriate for the host. The repository does not enable it in GitHub Actions by default because a scheduled runner is not a persistent event recorder.

## Streams

| Venue | Public endpoint | Streams |
|---|---|---|
| OKX | `wss://ws.okx.com:8443/ws/v5/public` | `books5` and `trades` for `*-USDT-SWAP` instruments |
| Bybit linear | `wss://stream.bybit.com/v5/public/linear` | `orderbook.50.*` and `publicTrade.*` topics |

The collector writes raw messages to daily `events-YYYYMMDD.jsonl` files. Every line contains a local receipt timestamp, venue, connection identifier, and the untouched decoded message. Daily `audit-YYYYMMDD.jsonl` files contain connection attempts, successful subscriptions, malformed messages, cancellations, connection errors, and detected sequence anomalies.

## Gap policy

The collector tracks venue-specific update identifiers. A previous-sequence mismatch or unexpected jump is recorded as `sequence_gap`; the collector does not silently reconstruct an order book or fill missing events. Downstream replay must exclude or explicitly repair intervals with gaps. Exchange timestamps and local receipt timestamps must both be preserved for latency and clock-skew analysis.

## Research gate

A prospective dataset is not evidence of a profitable strategy. Before any claim, the replay pipeline must perform timestamp alignment, exclude gap-affected intervals, define event-to-bar aggregation without look-ahead, freeze thresholds using training observations only, model fees/slippage/funding and latency, and score a separate untouched evaluation period. The current project remains analysis-only throughout.

## Bounded five-minute snapshot workflow

For a lower-cost prospective sampling path, the repository also exposes a bounded command:

```bash
crypto-signal --config config/default.yaml collect-microstructure-snapshot \
  --symbols BTCUSDT ETHUSDT SOLUSDT \
  --duration-seconds 45 \
  --output artifacts/microstructure_snapshots/snapshot.parquet
```

The dedicated workflow `.github/workflows/microstructure-snapshot.yml` requests this command on a best-effort `*/5` schedule and uploads one Parquet artifact per run with 90-day retention. Each row is a venue-symbol snapshot containing best bid/ask, spread, configured depth totals, trade count, signed trade volume, and data-quality status. It is a bounded sample, not a lossless order-book event archive: GitHub Actions may delay or queue schedules, jobs can fail, and snapshots cannot reconstruct intervals between runs. The workflow therefore must not be used as proof of continuous coverage or historical edge.

For timestamp-safe microstructure replay, the persistent JSONL collector remains the authoritative prospective recorder. The five-minute workflow is only a supplementary snapshot stream intended to measure coverage and develop data-quality diagnostics. Parquet artifacts must be downloaded and merged with their GitHub run timestamps, retaining missing-run and invalid-row metadata rather than silently forward-filling observations.
