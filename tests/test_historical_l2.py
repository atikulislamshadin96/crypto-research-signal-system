import io
import json
import tarfile
from pathlib import Path

from crypto_signal_system.historical_l2 import normalize_l2_jsonl, normalize_okx_historical_archive, okx_l2_stream, write_manifest


def _okx_row(action: str, seq: int, prev: int | None, ts: int, received: int) -> dict:
    message = {
        "arg": {"channel": "books", "instId": "BTC-USDT-SWAP"},
        "action": action,
        "data": [
            {
                "asks": [["100.5", "2"]],
                "bids": [["100.0", "3"]],
                "ts": str(ts),
                "seqId": str(seq),
                "prevSeqId": str(prev) if prev is not None else "0",
            }
        ],
    }
    return {"venue": "okx", "connection_id": "test", "received_at_ms": received, "message": message}


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_okx_l2_stream_uses_books_channel() -> None:
    stream = okx_l2_stream(["BTCUSDT", "ETHUSDT"])
    assert stream.venue == "okx"
    assert all(arg["channel"] == "books" for arg in stream.subscribe_message["args"])
    assert stream.subscribe_message["args"][0]["instId"] == "BTC-USDT-SWAP"


def test_clean_snapshot_delta_passes(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    output = tmp_path / "normalized.jsonl"
    _write(source, [_okx_row("snapshot", 1, None, 1_000, 1_010), _okx_row("update", 2, 1, 2_000, 2_010)])
    result = normalize_l2_jsonl([source], output)
    assert result.status == "PASS"
    assert result.research_usable is True
    assert result.event_count == 2
    assert result.sequence_gap_count == 0
    assert result.snapshot_count == 1
    assert output.exists()
    manifest = write_manifest(result, tmp_path / "manifest.json")
    assert manifest.exists()


def test_sequence_gap_blocks_research_use(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    output = tmp_path / "normalized.jsonl"
    _write(source, [_okx_row("snapshot", 1, None, 1_000, 1_010), _okx_row("update", 3, 99, 2_000, 2_010)])
    result = normalize_l2_jsonl([source], output)
    assert result.status == "BLOCKED_INTEGRITY"
    assert result.research_usable is False
    assert result.sequence_gap_count == 1


def test_okx_noncontiguous_sequence_with_matching_previous_is_allowed(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    output = tmp_path / "normalized.jsonl"
    _write(source, [_okx_row("snapshot", 1, None, 1_000, 1_010), _okx_row("update", 300, 1, 2_000, 2_010)])
    result = normalize_l2_jsonl([source], output)
    assert result.status == "PASS"
    assert result.research_usable is True
    assert result.sequence_gap_count == 0


def test_exact_duplicate_is_deduplicated_but_warned(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    output = tmp_path / "normalized.jsonl"
    row = _okx_row("snapshot", 1, None, 1_000, 1_010)
    _write(source, [row, row])
    result = normalize_l2_jsonl([source], output)
    assert result.status == "PASS_WITH_DEDUP_WARNINGS"
    assert result.research_usable is True
    assert result.duplicate_count == 1
    assert result.event_count == 1


def test_missing_input_fails_closed(tmp_path: Path) -> None:
    result = normalize_l2_jsonl([tmp_path / "missing.jsonl"], tmp_path / "normalized.jsonl")
    assert result.status == "BLOCKED_INTEGRITY"
    assert result.research_usable is False
    assert any(item.startswith("missing_input:") for item in result.errors)


def test_delta_before_snapshot_blocks_research_use(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    output = tmp_path / "normalized.jsonl"
    _write(source, [_okx_row("update", 2, 1, 1_000, 1_010)])
    result = normalize_l2_jsonl([source], output)
    assert result.status == "BLOCKED_INTEGRITY"
    assert result.research_usable is False
    assert result.pre_snapshot_update_count == 1


def test_collector_error_blocks_research_use(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    output = tmp_path / "normalized.jsonl"
    _write(source, [{"venue": "okx", "collector_error": {"type": "TimeoutError"}}])
    result = normalize_l2_jsonl([source], output)
    assert result.status == "BLOCKED_INTEGRITY"
    assert result.research_usable is False
    assert any(item.startswith("collector_error:") for item in result.errors)


def test_reconnect_snapshot_resets_sequence_continuity(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    output = tmp_path / "normalized.jsonl"
    first = _okx_row("snapshot", 1_000, None, 1_000, 1_010)
    first["connection_id"] = "old"
    second = _okx_row("snapshot", 10, None, 2_000, 2_010)
    second["connection_id"] = "new"
    third = _okx_row("update", 30, 10, 3_000, 3_010)
    third["connection_id"] = "new"
    _write(source, [first, second, third])
    result = normalize_l2_jsonl([source], output)
    assert result.status == "PASS"
    assert result.sequence_gap_count == 0


def test_official_okx_archive_without_sequences_blocks_research_use(tmp_path: Path) -> None:
    archive_path = tmp_path / "BTC-USDT-L2orderbook-400lv-2026-08-16.tar.gz"
    member_name = "BTC-USDT-L2orderbook-400lv-2026-08-16.data"
    rows = [
        {"instId": "BTC-USDT", "action": "snapshot", "ts": "1786838400000", "asks": [["100.5", "2", "1"]], "bids": [["100.0", "3", "1"]]},
        {"instId": "BTC-USDT", "action": "update", "ts": "1786838400020", "asks": [["100.5", "0", "0"]], "bids": []},
    ]
    payload = ("\n".join(json.dumps(row) for row in rows) + "\n").encode("utf-8")
    with tarfile.open(archive_path, "w:gz") as archive:
        info = tarfile.TarInfo(member_name)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    result = normalize_okx_historical_archive(
        archive_path,
        tmp_path / "normalized.jsonl",
        source_url="https://www.okx.com/en-us/historical-data",
        retrieved_at="2026-08-19T00:00:00Z",
        usage_terms_note="Official public archive; subject to OKX terms.",
        symbol="BTC-USDT",
        date_start="2026-08-16",
        date_end="2026-08-16",
        depth_levels=400,
    )
    assert result.status == "BLOCKED_INTEGRITY"
    assert result.research_usable is False
    assert result.event_count == 2
    assert result.snapshot_count == 1
    assert result.missing_sequence_count == 2
    assert any(item.startswith("missing_sequence_fields:") for item in result.errors)
    assert result.metadata["archive_format"] == "tar.gz containing NDJSON .data"
