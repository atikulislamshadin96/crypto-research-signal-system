from __future__ import annotations

import json

from crypto_signal_system.microstructure_collector import AuditEvent, JsonlArchive, SequenceGapTracker, bybit_stream, okx_stream


def test_stream_subscriptions_are_public_and_analysis_only():
    okx = okx_stream(["BTCUSDT", "ETHUSDT"])
    bybit = bybit_stream(["BTCUSDT", "ETHUSDT"])
    assert okx.url.startswith("wss://")
    assert okx.subscribe_message["op"] == "subscribe"
    assert any(arg["channel"] == "books5" for arg in okx.subscribe_message["args"])
    assert any(topic.startswith("orderbook.50.") for topic in bybit.subscribe_message["args"])


def test_sequence_gap_tracker_reports_previous_mismatch():
    tracker = SequenceGapTracker()
    assert tracker.observe("books:BTC", 10) is None
    assert tracker.observe("books:BTC", 11, previous=10) is None
    gap = tracker.observe("books:BTC", 13, previous=12)
    assert gap["reason"] == "previous_sequence_mismatch"
    assert gap["expected_previous"] == 11


def test_archive_writes_raw_and_audit_jsonl(tmp_path):
    archive = JsonlArchive(tmp_path)
    archive.raw("okx", "connection", {"event": "subscribe"})
    archive.audit(AuditEvent("2025-01-01T00:00:00+00:00", "test", "okx", "connection"))
    events = list(tmp_path.glob("events-*.jsonl"))
    assert events
    assert json.loads(events[0].read_text())["venue"] == "okx"
