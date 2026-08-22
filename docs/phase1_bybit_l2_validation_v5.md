# Phase 1 Bybit Historical L2 Validation v5

## Purpose

This instruction governs unaccepted official Bybit `orderbook.200` daily archives for the Phase 1 BTCUSDT and ETHUSDT dataset. It is a new version and does not modify the original validator or the v2, v3, or v4 rules.

## UTC partition

Each archive represents one inclusive-start, exclusive-end UTC calendar day:

```text
[target_day_start_ms, target_day_end_ms)
```

The ordinary terminal grace remains 2,000 ms.

## First-record rule

The first non-empty record may be a `snapshot` whose `ts` and/or `cts` is slightly before the target-day start, but neither may be earlier than 2,000 ms before the start. Every later record must have both timestamps at or after the target-day start. The event must be recorded in the validation result and manifest. Any wider or later pre-start record is a failure.

## Documented snapshot reset rule

The existing approved reset rule remains unchanged. Exactly one mid-stream `snapshot` with `u=1` may occur when its `seq` is strictly greater than the prior `seq` and the immediately following update has `u=2`. All other `u` and `seq` ordering and duplicate rules remain strict.

## v5 terminal duplicate rule

A record over the ordinary 2,000 ms end grace may be accepted only when all of the following are true:

1. It is the final non-empty archive record.
2. It is a `snapshot`.
3. Its `(u, seq)` pair exactly equals the immediately preceding record's pair.
4. The immediately preceding record is a `delta` or `snapshot`.
5. `max(ts, cts) - target_day_end_ms` is exactly within the v5 cap of 2,001 ms.
6. No other record exceeds the ordinary 2,000 ms grace.
7. ZIP CRC/inflate, JSON parsing, topic, symbol, record type, timestamps, level shapes, sequence ordering, duplicate rules, and all other checks pass.

The accepted event must be recorded with line number, overrun milliseconds, `u`, `seq`, and the fact that it was an exact terminal duplicate. A non-final overrun, a non-snapshot final record, an inexact duplicate, or an overrun greater than 2,001 ms fails closed.

This is not a general relaxation of the archive time window. It is a narrowly versioned representation of the observed Bybit terminal delta-plus-snapshot boundary convention.

## Required acceptance chain

```text
official Bybit URL
→ resumable byte-range download
→ byte count
→ v5 validation
→ source SHA-256
→ symbol-specific Google Drive upload
→ immutable-ID restore
→ restored byte count and SHA-256 equality
→ DRIVE_RESTORED_HASH_MATCH
```

No archive may be accepted based only on local validation. No data may be substituted, reconstructed, skipped, or synthesized.

## Failure response

On any validation failure, source hash mismatch, Drive upload failure, restore failure, or restored-hash mismatch, record the exact error and stop the worker. Do not widen the v5 boundary, create an unversioned exception, overwrite accepted files, or reprocess accepted archives.

## Provenance

Official references:

- <https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook>
- <https://bybit-exchange.github.io/docs/v5/market/orderbook>

Protocol artifact: `protocols/phase1_bybit_l2_historical_validation_v5.json`

Validator: `scripts/validate_bybit_l2_archive_historical_v5.py`

Test fixture: `2025-10-01_ETHUSDT_ob200.data.zip`

Fixture result: PASS under `bybit_l2_historical_integrity_v5`; one exact terminal duplicate with 2,001 ms overrun; no other errors.
