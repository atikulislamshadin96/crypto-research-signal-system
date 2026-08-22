# Phase 1 Bybit Historical L2 Validation v3

## Permanent solution

Bybit historical order-book archives are partitioned by UTC calendar date, but each record carries two different timestamps. Bybit documents `ts` as the system-generated timestamp and `cts` as the matching-engine production timestamp. The first snapshot can therefore straddle the UTC partition by a small amount: the archive observed for 2025-09-19 BTCUSDT has `ts=+43 ms` and `cts=-57 ms` relative to the target-day start.

The permanent solution is **not** to widen the date window generally and not to discard the record. It is a separately versioned, narrowly scoped rule:

> Permit a pre-start `cts` only when it belongs to the first non-empty record, that record is a snapshot, its `ts` is at or after the target-day start, and `cts` is no more than 2,000 ms before the start. Every later record must have both `ts` and `cts` at or after the start.

The 2,000 ms bound is deterministic and matches the existing Phase 1 boundary-grace convention. It is not tuned using forward returns or research outcomes.

## Required validation sequence

1. Download only from the official Bybit archive URL and verify the ZIP opens and CRC/inflate checks pass.
2. Require exactly one JSONL ZIP member, valid JSON records, the expected `orderbook.200.{SYMBOL}` topic, and the expected symbol.
3. Require integer `ts`, `cts`, `u`, and `seq` values and valid two-string bid/ask level pairs.
4. Apply the first-record boundary exception exactly as defined above. Reject any other pre-start timestamp.
5. Enforce the exclusive end boundary with the existing 2,000 ms post-midnight grace. Reject any larger overrun.
6. Enforce non-decreasing `ts` and `cts`; reject any later timestamp reversal.
7. Apply the approved Bybit snapshot-reset rule: exactly one mid-stream `snapshot` with `u=1` may occur, its `seq` must strictly increase, and the immediate next update must be `u=2`. All other `u` and `seq` order/duplicate failures remain fatal except the pre-existing terminal snapshot duplicate convention.
8. Compute the source SHA-256 and byte count before upload.
9. Upload to the symbol-specific Google Drive raw folder, restore by immutable file ID, and require exact byte-count and SHA-256 equality.
10. Record the rule version, boundary exception details, reset events, source URL, Drive file ID, source hash, restored hash, and validation report in the manifest.

## Fail-closed rules

Do not modify the original validator in place. Do not create a wider exception after seeing a new failure. Do not skip or reconstruct records, substitute another exchange, or accept an archive with unexplained timestamp/sequence/duplicate/integrity errors. A failure remains `VALIDATION_FAILED` and stops the sequential worker until a separately versioned, evidence-based rule is reviewed and authorized.

## Implementation

- Rule artifact: `protocols/phase1_bybit_l2_historical_validation_v3.json`
- Validator: `scripts/validate_bybit_l2_archive_historical_v3.py`
- Official references:
  - https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
  - https://bybit-exchange.github.io/docs/v5/market/orderbook

## Test result

`2025-09-19_BTCUSDT_ob200.data.zip` passes v3 with exactly one first-record pre-start `cts` boundary event (`-57 ms`) and no other validation errors. The archive remains pending the user's explicit instruction to update the Phase 1 manifest and resume the worker.
