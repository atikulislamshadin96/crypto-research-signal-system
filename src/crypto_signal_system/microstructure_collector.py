from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VenueStream:
    venue: str
    url: str
    subscribe_message: dict[str, Any]
    stream_names: tuple[str, ...]


@dataclass(frozen=True)
class AuditEvent:
    timestamp: str
    event: str
    venue: str
    connection_id: str
    stream: str | None = None
    detail: dict[str, Any] | None = None


class JsonlArchive:
    """Append-only raw-event and audit archive; no signal or order side effects."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.root / f"{name}-{datetime.now(timezone.utc):%Y%m%d}.jsonl"

    def append(self, name: str, payload: dict[str, Any]) -> None:
        path = self._path(name)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")

    def raw(self, venue: str, connection_id: str, message: dict[str, Any]) -> None:
        self.append("events", {"received_at": datetime.now(timezone.utc).isoformat(), "venue": venue, "connection_id": connection_id, "message": message})

    def audit(self, event: AuditEvent) -> None:
        self.append("audit", asdict(event))


class SequenceGapTracker:
    """Track monotonic update identifiers and report gaps without mutating the event."""

    def __init__(self):
        self.last: dict[str, int] = {}

    def observe(self, stream: str, sequence: int | None, previous: int | None = None) -> dict[str, Any] | None:
        if sequence is None:
            return None
        prior = self.last.get(stream)
        gap: dict[str, Any] | None = None
        if previous is not None and prior is not None and previous != prior:
            gap = {"reason": "previous_sequence_mismatch", "expected_previous": prior, "reported_previous": previous, "sequence": sequence}
        elif previous is None and prior is not None and sequence > prior + 1:
            gap = {"reason": "sequence_jump", "expected_sequence": prior + 1, "reported_sequence": sequence}
        self.last[stream] = sequence
        return gap


def okx_stream(symbols: list[str]) -> VenueStream:
    inst_ids = [f"{symbol[:-4]}-USDT-SWAP" if symbol.endswith("USDT") else symbol for symbol in symbols]
    args = [{"channel": channel, "instId": inst_id} for channel in ("books5", "trades") for inst_id in inst_ids]
    return VenueStream("okx", "wss://ws.okx.com:8443/ws/v5/public", {"op": "subscribe", "args": args}, tuple(f"{arg['channel']}:{arg['instId']}" for arg in args))


def bybit_stream(symbols: list[str]) -> VenueStream:
    topics = [topic for symbol in symbols for topic in (f"orderbook.50.{symbol}", f"publicTrade.{symbol}")]
    return VenueStream("bybit", "wss://stream.bybit.com/v5/public/linear", {"op": "subscribe", "args": topics}, tuple(topics))


def _message_stream(venue: str, message: dict[str, Any]) -> str | None:
    if venue == "okx":
        arg = message.get("arg") or {}
        channel = arg.get("channel")
        inst_id = arg.get("instId")
        return f"{channel}:{inst_id}" if channel and inst_id else None
    return message.get("topic")


def _sequence_fields(venue: str, message: dict[str, Any]) -> tuple[int | None, int | None]:
    data = message.get("data") or {}
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        return None, None
    if venue == "okx":
        sequence = data.get("seqId")
        previous = data.get("prevSeqId")
    else:
        sequence = data.get("u")
        previous = data.get("pu")
    try:
        return (int(sequence) if sequence is not None else None, int(previous) if previous is not None else None)
    except (TypeError, ValueError):
        return None, None


class WebSocketCollector:
    """Persistent public-event collector; it never computes or emits trading signals."""

    def __init__(self, streams: list[VenueStream], archive_dir: str | Path, reconnect_max_seconds: int = 60):
        self.streams = streams
        self.archive = JsonlArchive(archive_dir)
        self.reconnect_max_seconds = reconnect_max_seconds
        self.gaps = {stream.venue: SequenceGapTracker() for stream in streams}

    async def _run_stream(self, stream: VenueStream) -> None:
        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError("WebSocket collection requires the optional 'websockets' dependency") from exc
        backoff = 1
        while True:
            connection_id = uuid.uuid4().hex
            self.archive.audit(AuditEvent(datetime.now(timezone.utc).isoformat(), "connect_attempt", stream.venue, connection_id, detail={"url": stream.url}))
            try:
                async with websockets.connect(stream.url, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=8 * 1024 * 1024) as socket:
                    await socket.send(json.dumps(stream.subscribe_message))
                    self.archive.audit(AuditEvent(datetime.now(timezone.utc).isoformat(), "subscribed", stream.venue, connection_id, detail={"streams": list(stream.stream_names)}))
                    backoff = 1
                    async for raw in socket:
                        received_at = datetime.now(timezone.utc).isoformat()
                        try:
                            message = json.loads(raw)
                        except (TypeError, ValueError):
                            self.archive.audit(AuditEvent(received_at, "malformed_message", stream.venue, connection_id, detail={"raw_type": type(raw).__name__}))
                            continue
                        self.archive.raw(stream.venue, connection_id, message)
                        stream_name = _message_stream(stream.venue, message)
                        sequence, previous = _sequence_fields(stream.venue, message)
                        gap = self.gaps[stream.venue].observe(stream_name or "unknown", sequence, previous)
                        if gap is not None:
                            self.archive.audit(AuditEvent(received_at, "sequence_gap", stream.venue, connection_id, stream_name, gap))
            except asyncio.CancelledError:
                self.archive.audit(AuditEvent(datetime.now(timezone.utc).isoformat(), "cancelled", stream.venue, connection_id))
                raise
            except Exception as exc:
                self.archive.audit(AuditEvent(datetime.now(timezone.utc).isoformat(), "connection_error", stream.venue, connection_id, detail={"error_type": type(exc).__name__, "error": str(exc)}))
                await asyncio.sleep(backoff)
                backoff = min(self.reconnect_max_seconds, backoff * 2)

    async def run_forever(self) -> None:
        await asyncio.gather(*(self._run_stream(stream) for stream in self.streams))


def run_collector(symbols: list[str], archive_dir: str | Path = "artifacts/microstructure_events") -> None:
    collector = WebSocketCollector([okx_stream(symbols), bybit_stream(symbols)], archive_dir)
    asyncio.run(collector.run_forever())
