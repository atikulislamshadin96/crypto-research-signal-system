# Historical L2 Sample Acceptance Report — 2026-08-19

## Historical archive access status

`HISTORICAL_ARCHIVE_ACCESS_PARTIALLY_RESOLVED`: one real official OKX historical order-book archive was downloaded through the official historical-data UI. The repository now supports manual ingestion of that archive through `validate-okx-historical-l2`. The sample is not research-usable because the archive does not contain provider sequence fields required by the acceptance gate.

## Dataset actually acquired

| Field | Value |
|---|---|
| Source | Official OKX historical-data page |
| Source URL | https://www.okx.com/en-us/historical-data |
| Archive | `BTC-USDT-L2orderbook-400lv-2026-08-16.tar.gz` |
| Venue | OKX |
| Symbol | BTC-USDT |
| Coverage | 2026-08-16 00:00:00.000 UTC through 2026-08-16 23:59:59.958 UTC |
| Format | tar.gz containing one NDJSON `.data` member |
| Depth | 400 levels |
| Archive bytes | 42,123,848 |
| Archive SHA-256 | `88e7ea48766d5a3cf3da34587288f5a52e192992d240fd9a88946b25ffb2049f` |
| Retrieved at | 2026-08-19T06:43:51Z |
| Terms note | Official OKX public historical-data download; subject to OKX Terms/API agreement; raw redistribution is not assumed. |

## Normalization and integrity result

The real archive was processed by `normalize_okx_historical_archive()` and the repository CLI command `validate-okx-historical-l2`.

| Metric | Result |
|---|---:|
| Status | `BLOCKED_INTEGRITY` |
| Research usable | `false` |
| Events | 2,017,875 |
| Snapshots | 1 |
| Updates | 2,017,779 |
| Pre-snapshot updates | 0 |
| Duplicate events | 0 |
| Missing source timestamps | 0 |
| Missing receive timestamps | 2,017,875 |
| Sequence gaps | 0, because sequence fields are absent |
| Missing sequence fields | 2,017,875 |
| Out-of-order events | 0 |
| Stale intervals | 0 measurable, because receive timestamps are absent |
| Source timestamp range | 1786838400000–1786924799958 ms |
| Normalized bytes | 768,513,814 |
| Normalized SHA-256 | `ceb36d4566e8947a8b719337fd31c1aa083b936ebb7d5fb603e22eaaf522463d` |

The source timestamp is exchange-provided and present on every event. The archive exposes `action`, `ts`, `asks`, and `bids`, with one snapshot followed by updates. It does **not** expose `seqId`, `prevSeqId`, `u`, `pu`, or another continuity identifier in the downloaded records. It also does not expose local receive timestamps; this is not itself the critical blocker under the uploaded acceptance document, but it prevents stale-lag measurement from the archive alone.

## Exact blocker

`BLOCKED_MISSING_HISTORICAL_L2`: the official OKX archive lacks sequence fields, so sequence integrity cannot be checked. The repository correctly refuses to mark it `RESEARCH_USABLE`. It does not reconstruct sequence values from line order, OHLCV, aggregate trades, or interpolated book states.

The acceptance gate therefore remains closed. This is not a parser failure: the parser recognized all 2,017,875 direct archive records, preserved source timestamps and depth levels, and reported zero duplicate or out-of-order records. The missing field is absent from the official sample itself.

## Repository capability verified

The repository now supports:

1. explicit official archive download with optional expected SHA-256;
2. safe extraction/reading of the single NDJSON `.data` member;
3. direct-record normalization into canonical JSONL;
4. source timestamp, snapshot/update, duplicate, missingness, ordering, and sequence-field accounting;
5. archive and normalized-file hashes and byte counts in the manifest;
6. a nonzero CLI exit code on a blocked sample;
7. analysis-only behavior with no signal, paper-trading, alert, or deployment path.

Verification: **49 tests passed**, CLI help succeeded, Python compilation succeeded, and `git diff --check` was clean.

## Phase 3 decision

**Phase 3 remains locked.** BTC/ETH historical L2 does not pass the acceptance gate. No historical L2 strategy event study may begin. No frozen research candidate was changed. Paper trading, Telegram alerts, and deployment remain disabled.

## Remaining path

The next valid path is to locate an officially authorized archive or data format that includes a usable continuity field, or to acquire a longer official event stream with sequence identifiers from an authorized source. A new archive must be tested with the same sample-first procedure before any large BTC/ETH ingest. No paid source will be purchased automatically.
