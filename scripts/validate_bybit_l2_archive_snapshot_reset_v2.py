#!/usr/bin/env python3
"""Validate a Bybit historical L2 archive with one documented u=1 snapshot reset.

This is a separately versioned historical-data rule. It does not modify or replace
validate_bybit_l2_archive.py. The only additional sequence behavior allowed here is
one mid-stream snapshot with u=1 followed immediately by u=2; seq must remain
strictly increasing across that reset. The pre-existing terminal snapshot duplicate
convention remains the sole permitted duplicate exception.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path

VALIDATION_RULE_VERSION = "bybit_l2_historical_snapshot_reset_v2"
BOUNDARY_GRACE_MS = 2_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(path: Path, symbol: str, day: str) -> dict:
    errors: list[str] = []
    records = snapshots = deltas = 0
    first_ts = last_ts = first_cts = last_cts = None
    previous_u = previous_seq = None
    previous_pair = None
    previous_type = None
    out_of_order_ts = out_of_order_cts = 0
    invalid_levels = 0
    boundary_records = 0
    max_boundary_overrun_ms = 0
    terminal_snapshot_duplicates = 0
    invalid_duplicate_ids = 0
    seen_u: set[int] = set()
    seen_seq: set[int] = set()
    member_names: list[str] = []
    reset_events: list[dict] = []
    reset_followup_pending = False
    reset_event_line: int | None = None

    start_ms = int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    end_ms = start_ms + 86_400_000

    try:
        with zipfile.ZipFile(path, "r") as archive:
            member_names = archive.namelist()
            if len(member_names) != 1:
                errors.append(f"zip_member_count:{len(member_names)}")
            if not member_names:
                errors.append("zip_empty")
            else:
                with archive.open(member_names[0], "r") as raw:
                    for line_no, line in enumerate(raw, 1):
                        if not line.strip():
                            continue
                        records += 1
                        try:
                            row = json.loads(line)
                        except Exception as exc:
                            errors.append(f"json_parse:{line_no}:{type(exc).__name__}")
                            continue
                        if not isinstance(row, dict):
                            errors.append(f"row_not_object:{line_no}")
                            continue

                        expected_topic = f"orderbook.200.{symbol}"
                        if row.get("topic") != expected_topic:
                            errors.append(f"topic_mismatch:{line_no}:{row.get('topic')}")
                        data = row.get("data")
                        if not isinstance(data, dict):
                            errors.append(f"data_invalid:{line_no}")
                            data = {}
                        if data.get("s") != symbol:
                            errors.append(f"symbol_mismatch:{line_no}")

                        typ = row.get("type")
                        if typ == "snapshot":
                            snapshots += 1
                        elif typ == "delta":
                            deltas += 1
                        else:
                            errors.append(f"unknown_type:{line_no}:{typ}")

                        ts = row.get("ts")
                        cts = row.get("cts")
                        if not isinstance(ts, int) or not isinstance(cts, int):
                            errors.append(f"timestamp_invalid:{line_no}")
                            continue
                        if ts < start_ms or cts < start_ms:
                            errors.append(f"timestamp_before_day:{line_no}:{ts}:{cts}")
                        overrun = max(ts, cts) - end_ms
                        if overrun >= 0:
                            boundary_records += 1
                            max_boundary_overrun_ms = max(max_boundary_overrun_ms, overrun)
                            if overrun > BOUNDARY_GRACE_MS:
                                errors.append(f"boundary_overrun:{line_no}:{overrun}")
                        if first_ts is None:
                            first_ts = ts
                        if first_cts is None:
                            first_cts = cts
                        if last_ts is not None and ts < last_ts:
                            out_of_order_ts += 1
                        if last_cts is not None and cts < last_cts:
                            out_of_order_cts += 1
                        last_ts = ts
                        last_cts = cts

                        u = data.get("u")
                        seq = data.get("seq")
                        if not isinstance(u, int):
                            errors.append(f"u_missing_or_invalid:{line_no}")
                        if not isinstance(seq, int):
                            errors.append(f"seq_missing_or_invalid:{line_no}")

                        pair = (u, seq)
                        terminal_dup = (
                            pair == previous_pair
                            and typ == "snapshot"
                            and previous_type in ("delta", "snapshot")
                        )
                        if terminal_dup:
                            terminal_snapshot_duplicates += 1
                        is_reset = (
                            typ == "snapshot"
                            and u == 1
                            and previous_u is not None
                            and previous_u > 1
                        )
                        if isinstance(u, int):
                            if u in seen_u and not terminal_dup and not is_reset:
                                invalid_duplicate_ids += 1
                            seen_u.add(u)
                        if isinstance(seq, int):
                            if seq in seen_seq and not terminal_dup:
                                invalid_duplicate_ids += 1
                            seen_seq.add(seq)

                        # The documented exception: exactly one mid-stream snapshot
                        # with u=1, followed by a new sequence beginning at u=2.
                        if is_reset:
                            if reset_events:
                                errors.append(f"multiple_u1_snapshot_resets:{line_no}")
                            if not isinstance(seq, int) or previous_seq is None or seq <= previous_seq:
                                errors.append(f"reset_seq_not_strictly_increasing:{line_no}")
                            reset_events.append({
                                "line_no": line_no,
                                "type": typ,
                                "u": u,
                                "seq": seq,
                                "previous_u": previous_u,
                                "previous_seq": previous_seq,
                            })
                            reset_followup_pending = True
                            reset_event_line = line_no
                        elif isinstance(u, int) and previous_u is not None:
                            if reset_followup_pending:
                                if u != 2:
                                    errors.append(
                                        f"reset_followup_u_expected_2:{reset_event_line}:{line_no}:{u}"
                                    )
                                reset_followup_pending = False
                            elif not terminal_dup and u <= previous_u:
                                errors.append(f"u_out_of_order:{line_no}")

                        if isinstance(seq, int) and previous_seq is not None:
                            if not terminal_dup and seq <= previous_seq:
                                errors.append(f"seq_not_strictly_increasing:{line_no}")

                        for side in ("b", "a"):
                            levels = data.get(side)
                            if not isinstance(levels, list):
                                errors.append(f"levels_invalid:{line_no}:{side}")
                                continue
                            for level in levels:
                                if (
                                    not isinstance(level, list)
                                    or len(level) != 2
                                    or not all(isinstance(value, str) for value in level)
                                ):
                                    invalid_levels += 1

                        previous_u = u if isinstance(u, int) else previous_u
                        previous_seq = seq if isinstance(seq, int) else previous_seq
                        previous_pair = pair
                        previous_type = typ
    except (zipfile.BadZipFile, OSError) as exc:
        errors.append(f"archive_open_failed:{type(exc).__name__}:{exc}")

    if reset_followup_pending:
        errors.append(f"reset_missing_followup_u2:{reset_event_line}")
    if not reset_events:
        errors.append("required_u1_snapshot_reset_not_found")
    if out_of_order_ts:
        errors.append(f"ts_out_of_order_count:{out_of_order_ts}")
    if out_of_order_cts:
        errors.append(f"cts_out_of_order_count:{out_of_order_cts}")
    if invalid_duplicate_ids:
        errors.append(f"invalid_duplicate_id_count:{invalid_duplicate_ids}")
    if invalid_levels:
        errors.append(f"invalid_level_count:{invalid_levels}")

    result = {
        "status": "PASS" if records > 0 and not errors else "FAIL",
        "validation_rule_version": VALIDATION_RULE_VERSION,
        "symbol": symbol,
        "date": day,
        "source_file": str(path),
        "archive_sha256": sha256(path) if path.exists() else None,
        "archive_byte_count": path.stat().st_size if path.exists() else 0,
        "zip_members": member_names,
        "record_count": records,
        "snapshot_count": snapshots,
        "delta_count": deltas,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "first_cts": first_cts,
        "last_cts": last_cts,
        "unique_u_count": len(seen_u),
        "unique_seq_count": len(seen_seq),
        "boundary_record_count": boundary_records,
        "max_boundary_overrun_ms": max_boundary_overrun_ms,
        "terminal_snapshot_duplicate_count": terminal_snapshot_duplicates,
        "u1_snapshot_reset_count": len(reset_events),
        "u1_snapshot_resets": reset_events,
        "errors": errors[:100],
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("symbol")
    parser.add_argument("day")
    args = parser.parse_args()
    raise SystemExit(0 if validate(args.path, args.symbol, args.day)["status"] == "PASS" else 1)
