from pathlib import Path

import pandas as pd

from crypto_signal_system.microstructure_snapshot import SnapshotState, _book_levels, _trades, collect_snapshot


def test_okx_book_and_trade_parsers():
    book = {"data": [{"bids": [["100", "2", "0", "1"]], "asks": [["101", "3", "0", "1"]]}]}
    assert _book_levels("okx", book) == ([(100.0, 2.0)], [(101.0, 3.0)])
    trades = {"data": [{"px": "100.5", "sz": "4", "side": "buy"}, {"px": "100.4", "sz": "1", "side": "sell"}]}
    assert _trades("okx", trades) == [("buy", 100.5, 4.0), ("sell", 100.4, 1.0)]


def test_bybit_parsers_and_snapshot_metrics():
    book = {"data": {"b": [["100", "2"]], "a": [["101", "3"]]}}
    assert _book_levels("bybit", book) == ([(100.0, 2.0)], [(101.0, 3.0)])
    trades = {"data": [{"p": "100.5", "v": "4", "S": "Buy"}, {"p": "100.4", "v": "1", "S": "Sell"}]}
    assert _trades("bybit", trades) == [("buy", 100.5, 4.0), ("sell", 100.4, 1.0)]
    state = SnapshotState("okx", "BTCUSDT", "2026-08-19T00:00:00+00:00", best_bid=100, best_ask=101, bid_depth=2, ask_depth=3, trade_buy_volume=4, trade_sell_volume=1, trade_count=2, book_messages=1, trade_messages=1)
    row = state.row()
    assert row["spread_bps"] > 0
    assert row["depth_imbalance"] == -0.2
    assert row["trade_signed_volume"] == 3
    assert row["trade_imbalance"] == 0.6


def test_collect_snapshot_writes_parquet(monkeypatch, tmp_path: Path):
    async def fake_collect(self):
        return [SnapshotState("okx", "BTCUSDT", "2026-08-19T00:00:00+00:00", book_messages=1).row()]

    monkeypatch.setattr("crypto_signal_system.microstructure_snapshot.SnapshotCollector.collect", fake_collect)
    output = collect_snapshot(["BTCUSDT"], tmp_path / "snapshot.parquet", duration_seconds=5)
    frame = pd.read_parquet(output)
    assert output.exists()
    assert frame.loc[0, "venue"] == "okx"
    assert frame.loc[0, "snapshot_type"] == "bounded_websocket_snapshot"
