from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from crypto_signal_system.microstructure_collector import VenueStream, bybit_stream


SCHEMA_VERSION = "historical_l2_jsonl_v1"
PROTOCOL_VERSION = "l2_integrity_protocol_v1"


@dataclass(frozen=True)
class DownloadRecord:
    url: str
    path: str
    downloaded_at: str
    sha256: str
    byte_count: int
    content_type: str | None
    expected_sha256: str | None
    checksum_match: bool | None


@dataclass(frozen=True)
class L2Event:
    venue: str
    symbol: str
    source_ts_ms: int | None
    receive_ts_ms: int | None
    sequence: int | None
    previous_sequence: int | None
    cross_sequence: int | None
    action: str | None
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]
    raw_hash: str
    connection_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "symbol": self.symbol,
            "source_ts_ms": self.source_ts_ms,
            "receive_ts_ms": self.receive_ts_ms,
            "sequence": self.sequence,
            "previous_sequence": self.previous_sequence,
            "cross_sequence": self.cross_sequence,
            "action": self.action,
            "bids": [[p, q] for p, q in self.bids],
            "asks": [[p, q] for p, q in self.asks],
            "raw_hash": self.raw_hash,
            "connection_id": self.connection_id,
        }


@dataclass
class L2Validation:
    status: str
    research_usable: bool
    schema_version: str
    protocol_version: str
    input_files: list[dict[str, Any]]
    output_file: str | None
    output_sha256: str | None
    output_byte_count: int | None
    event_count: int
    venue_symbol_counts: dict[str, int]
    snapshot_count: int
    update_count: int
    pre_snapshot_update_count: int
    duplicate_count: int
    missing_source_timestamp_count: int
    missing_receive_timestamp_count: int
    sequence_gap_count: int
    out_of_order_count: int
    stale_count: int
    non_monotonic_receive_count: int
    first_source_ts_ms: int | None
    last_source_ts_ms: int | None
    max_source_receive_lag_ms: int | None
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def okx_l2_stream(symbols: list[str], channel: str = "books") -> VenueStream:
    inst_ids = [f"{symbol[:-4]}-USDT-SWAP" if symbol.endswith("USDT") else symbol for symbol in symbols]
    args = [{"channel": channel, "instId": inst_id} for inst_id in inst_ids]
    return VenueStream("okx", "wss://ws.okx.com:8443/ws/v5/public", {"op": "subscribe", "args": args}, tuple(f"{channel}:{inst_id}" for inst_id in inst_ids))


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: str | Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            total += len(chunk)
    return digest.hexdigest(), total


def _as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _as_levels(value: Any) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    if not isinstance(value, list):
        return ()
    for level in value:
        if not isinstance(level, (list, tuple)) or len(level) < 2:
            continue
        price, size = level[0], level[1]
        if price is None or size is None:
            continue
        result.append((str(price), str(size)))
    return tuple(result)


def _message_hash(message: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(message)).hexdigest()


def _extract_payload(entry: dict[str, Any]) -> tuple[str | None, dict[str, Any], int | None, str | None]:
    """Return venue, provider message, receive timestamp, and connection id."""
    if isinstance(entry.get("message"), dict):
        return str(entry.get("venue") or "").lower() or None, entry["message"], _as_int(entry.get("received_at_ms")), entry.get("connection_id")
    return str(entry.get("venue") or "").lower() or None, entry, _as_int(entry.get("receive_ts_ms")), entry.get("connection_id")


def normalize_message(entry: dict[str, Any], symbol_filter: set[str] | None = None) -> L2Event | None:
    venue, message, receive_ts_ms, connection_id = _extract_payload(entry)
    if venue not in {"okx", "bybit"}:
        return None
    data = message.get("data")
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        return None

    if venue == "okx":
        arg = message.get("arg") or {}
        symbol = str(arg.get("instId") or data.get("instId") or "")
        if not symbol:
            return None
        source_ts_ms = _as_int(data.get("ts") or data.get("uTime"))
        sequence = _as_int(data.get("seqId"))
        previous_sequence = _as_int(data.get("prevSeqId"))
        cross_sequence = None
        action = str(data.get("action") or message.get("action") or "update")
        bids = _as_levels(data.get("bids"))
        asks = _as_levels(data.get("asks"))
    else:
        topic = str(message.get("topic") or "")
        symbol = str(data.get("s") or (topic.rsplit(".", 1)[-1] if "." in topic else ""))
        if not symbol:
            return None
        source_ts_ms = _as_int(message.get("cts") or data.get("cts") or message.get("ts") or data.get("ts"))
        sequence = _as_int(data.get("u"))
        previous_sequence = _as_int(data.get("pu"))
        cross_sequence = _as_int(data.get("seq"))
        action = str(message.get("type") or data.get("type") or "update")
        bids = _as_levels(data.get("b"))
        asks = _as_levels(data.get("a"))

    if symbol_filter and symbol not in symbol_filter:
        return None
    if not bids and not asks:
        return None
    return L2Event(
        venue=venue,
        symbol=symbol,
        source_ts_ms=source_ts_ms,
        receive_ts_ms=receive_ts_ms,
        sequence=sequence,
        previous_sequence=previous_sequence,
        cross_sequence=cross_sequence,
        action=action,
        bids=bids,
        asks=asks,
        raw_hash=_message_hash(message),
        connection_id=str(connection_id) if connection_id is not None else None,
    )


def _iter_json_records(path: Path) -> Iterator[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc
            if isinstance(record, dict):
                yield record
            elif isinstance(record, list):
                for item in record:
                    if isinstance(item, dict):
                        yield item


def _file_record(path: Path) -> dict[str, Any]:
    digest, byte_count = sha256_file(path)
    return {"path": str(path), "sha256": digest, "byte_count": byte_count}


def normalize_l2_jsonl(
    input_paths: Iterable[str | Path],
    output_path: str | Path,
    symbols: Iterable[str] | None = None,
    stale_threshold_seconds: float = 60.0,
) -> L2Validation:
    """Normalize provider JSONL messages and fail closed on causal/integrity defects."""
    paths = [Path(item) for item in input_paths]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    symbol_filter = set(symbols or ())
    seen_hashes: set[str] = set()
    last_sequence: dict[tuple[str, str], int] = {}
    last_source_ts: dict[tuple[str, str], int] = {}
    last_receive_ts: dict[tuple[str, str], int] = {}
    snapshots: set[tuple[str, str]] = set()
    counts: dict[str, int] = {}
    errors: list[str] = []
    warnings: list[str] = []
    duplicate_count = 0
    missing_source = 0
    missing_receive = 0
    sequence_gaps = 0
    out_of_order = 0
    stale_count = 0
    non_monotonic_receive = 0
    update_count = 0
    pre_snapshot_update_count = 0
    event_count = 0
    first_source: int | None = None
    last_source: int | None = None
    max_lag: int | None = None

    with output.open("w", encoding="utf-8") as destination:
        for path in paths:
            if not path.exists() or not path.is_file():
                errors.append(f"missing_input:{path}")
                continue
            try:
                records = _iter_json_records(path)
                for record in records:
                    if record.get("collector_error"):
                        errors.append(f"collector_error:{path}:{record.get('collector_error')}")
                        continue
                    event = normalize_message(record, symbol_filter)
                    if event is None:
                        continue
                    key = (event.venue, event.symbol)
                    if event.raw_hash in seen_hashes:
                        duplicate_count += 1
                        continue
                    seen_hashes.add(event.raw_hash)
                    if event.action.lower() == "snapshot":
                        snapshots.add(key)
                        if event.sequence is not None:
                            # A fresh provider snapshot establishes a new local-book
                            # continuity segment after reconnect/reset.
                            last_sequence[key] = event.sequence
                    else:
                        update_count += 1
                        if key not in snapshots:
                            pre_snapshot_update_count += 1
                    if event.source_ts_ms is None:
                        missing_source += 1
                    else:
                        first_source = event.source_ts_ms if first_source is None else min(first_source, event.source_ts_ms)
                        last_source = event.source_ts_ms if last_source is None else max(last_source, event.source_ts_ms)
                        prior_source = last_source_ts.get(key)
                        if prior_source is not None and event.source_ts_ms < prior_source:
                            out_of_order += 1
                        last_source_ts[key] = max(event.source_ts_ms, prior_source or event.source_ts_ms)
                    if event.receive_ts_ms is None:
                        missing_receive += 1
                    else:
                        prior_receive = last_receive_ts.get(key)
                        if prior_receive is not None and event.receive_ts_ms < prior_receive:
                            non_monotonic_receive += 1
                        last_receive_ts[key] = max(event.receive_ts_ms, prior_receive or event.receive_ts_ms)
                        if event.source_ts_ms is not None:
                            lag = event.receive_ts_ms - event.source_ts_ms
                            max_lag = lag if max_lag is None else max(max_lag, lag)
                            if lag > stale_threshold_seconds * 1000:
                                stale_count += 1
                    if event.action.lower() != "snapshot" and event.sequence is not None:
                        prior_sequence = last_sequence.get(key)
                        if event.previous_sequence is not None and prior_sequence is not None and event.previous_sequence != prior_sequence:
                            sequence_gaps += 1
                        elif event.previous_sequence is None and prior_sequence is not None and event.sequence > prior_sequence + 1:
                            sequence_gaps += 1
                        last_sequence[key] = max(event.sequence, prior_sequence or event.sequence)
                    destination.write(json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
                    event_count += 1
                    counts[f"{event.venue}:{event.symbol}"] = counts.get(f"{event.venue}:{event.symbol}", 0) + 1
            except (OSError, ValueError) as exc:
                errors.append(f"read_error:{path}:{exc}")

    output_sha256, output_bytes = sha256_file(output) if output.exists() else (None, None)
    if duplicate_count:
        warnings.append(f"deduplicated_exact_messages:{duplicate_count}")
    if missing_receive:
        warnings.append(f"missing_receive_timestamps:{missing_receive}")
    if max_lag is not None and max_lag > stale_threshold_seconds * 1000:
        warnings.append(f"source_receive_lag_exceeded:{max_lag}ms")
    required_ok = (
        event_count > 0
        and not errors
        and not missing_source
        and not pre_snapshot_update_count
        and not sequence_gaps
        and not out_of_order
        and not stale_count
        and not non_monotonic_receive
        and bool(snapshots)
    )
    if required_ok and duplicate_count == 0:
        status = "PASS"
    elif required_ok:
        status = "PASS_WITH_DEDUP_WARNINGS"
    else:
        status = "BLOCKED_INTEGRITY"
    return L2Validation(
        status=status,
        research_usable=required_ok,
        schema_version=SCHEMA_VERSION,
        protocol_version=PROTOCOL_VERSION,
        input_files=[_file_record(path) for path in paths if path.exists() and path.is_file()],
        output_file=str(output),
        output_sha256=output_sha256,
        output_byte_count=output_bytes,
        event_count=event_count,
        venue_symbol_counts=counts,
        snapshot_count=len(snapshots),
        update_count=update_count,
        pre_snapshot_update_count=pre_snapshot_update_count,
        duplicate_count=duplicate_count,
        missing_source_timestamp_count=missing_source,
        missing_receive_timestamp_count=missing_receive,
        sequence_gap_count=sequence_gaps,
        out_of_order_count=out_of_order,
        stale_count=stale_count,
        non_monotonic_receive_count=non_monotonic_receive,
        first_source_ts_ms=first_source,
        last_source_ts_ms=last_source,
        max_source_receive_lag_ms=max_lag,
        errors=errors,
        warnings=warnings,
    )


def write_manifest(validation: L2Validation, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(validation.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target


async def _bounded_stream(stream: VenueStream, archive_dir: Path, duration_seconds: int) -> None:
    try:
        import websockets
    except ImportError as exc:
        raise RuntimeError("Forward L2 collection requires websockets") from exc
    archive_dir.mkdir(parents=True, exist_ok=True)
    raw_path = archive_dir / f"raw-{stream.venue}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.jsonl"
    connection_id = uuid.uuid4().hex
    deadline = time.monotonic() + max(1, duration_seconds)
    backoff = 1.0
    with raw_path.open("a", encoding="utf-8") as destination:
        while time.monotonic() < deadline:
            try:
                async with websockets.connect(stream.url, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=8 * 1024 * 1024) as socket:
                    await socket.send(json.dumps(stream.subscribe_message))
                    backoff = 1.0
                    while time.monotonic() < deadline:
                        timeout = max(0.1, min(5.0, deadline - time.monotonic()))
                        try:
                            raw = await asyncio.wait_for(socket.recv(), timeout=timeout)
                        except asyncio.TimeoutError:
                            continue
                        received_ms = int(time.time() * 1000)
                        try:
                            message = json.loads(raw)
                        except (TypeError, ValueError):
                            continue
                        row = {"venue": stream.venue, "connection_id": connection_id, "received_at_ms": received_ms, "message": message}
                        destination.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                        destination.flush()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if time.monotonic() >= deadline:
                    break
                destination.write(json.dumps({"venue": stream.venue, "connection_id": connection_id, "received_at_ms": int(time.time() * 1000), "collector_error": {"type": type(exc).__name__, "message": str(exc)}}, sort_keys=True, separators=(",", ":")) + "\n")
                destination.flush()
                await asyncio.sleep(min(backoff, max(0.1, deadline - time.monotonic())))
                backoff = min(30.0, backoff * 2.0)


def run_forward_collection(symbols: list[str], archive_dir: str | Path, duration_seconds: int = 240) -> list[Path]:
    """Collect public OKX/Bybit L2 events for a bounded interval; analysis-only."""
    root = Path(archive_dir)
    before = set(root.glob("raw-*.jsonl")) if root.exists() else set()
    streams = [okx_l2_stream(symbols), bybit_stream(symbols)]

    async def _run_all() -> None:
        await asyncio.gather(*(_bounded_stream(stream, root, duration_seconds) for stream in streams))

    asyncio.run(_run_all())
    after = set(root.glob("raw-*.jsonl"))
    return sorted(after - before or after)


def download_verified_file(url: str, output_path: str | Path, expected_sha256: str | None = None, timeout_seconds: int = 120) -> DownloadRecord:
    """Download an explicitly supplied public archive URL; never guesses undocumented endpoints."""
    import requests

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    with requests.get(url, stream=True, timeout=timeout_seconds, headers={"User-Agent": "crypto-research-signal-system/1.0"}) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type")
        with partial.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    digest, byte_count = sha256_file(partial)
    checksum_match = None if expected_sha256 is None else digest.lower() == expected_sha256.lower()
    if checksum_match is False:
        partial.unlink(missing_ok=True)
        raise ValueError(f"checksum mismatch for {url}: expected {expected_sha256}, got {digest}")
    partial.replace(target)
    return DownloadRecord(url, str(target), datetime.now(timezone.utc).isoformat(), digest, byte_count, content_type, expected_sha256, checksum_match)
