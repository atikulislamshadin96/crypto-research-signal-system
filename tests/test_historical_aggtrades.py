from __future__ import annotations

import csv
import io
import zipfile

import pandas as pd

from crypto_signal_system.features import add_trade_flow_features
from crypto_signal_system.historical import _aggregate_aggtrades_archive


def _archive(tmp_path):
    raw = io.StringIO()
    writer = csv.writer(raw)
    writer.writerow(["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "transact_time", "is_buyer_maker", "is_best_match"])
    writer.writerow([1, "100", "2", 1, 1, 1_000, "false", "true"])
    writer.writerow([2, "101", "1", 2, 2, 60_000, "true", "true"])
    writer.writerow([3, "102", "3", 3, 3, 900_000, "false", "true"])
    path = tmp_path / "agg.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("BTCUSDT-aggTrades-2025-01.csv", raw.getvalue())
    return path


def test_aggregate_trades_are_signed_and_bucketed(tmp_path):
    rows = _aggregate_aggtrades_archive(_archive(tmp_path), "BTCUSDT", "15m")
    assert len(rows) == 2
    assert rows[0]["flow_buy_volume"] == 2.0
    assert rows[0]["flow_sell_volume"] == 1.0
    assert rows[0]["flow_signed_volume"] == 1.0
    assert rows[0]["flow_taker_buy_ratio"] == 2 / 3
    assert rows[1]["flow_buy_volume"] == 3.0


def test_flow_features_are_shifted_one_bar():
    candles = pd.DataFrame({
        "open_time": pd.to_datetime(["1970-01-01T00:00:00Z", "1970-01-01T00:15:00Z"]),
        "close": [100.0, 101.0],
    })
    flow = pd.DataFrame({
        "open_time": pd.to_datetime(["1970-01-01T00:00:00Z", "1970-01-01T00:15:00Z"]),
        "flow_imbalance": [0.5, -0.5],
        "flow_taker_buy_ratio": [0.75, 0.25],
    })
    result = add_trade_flow_features(candles, flow)
    assert pd.isna(result.loc[0, "flow_imbalance_prior"])
    assert result.loc[1, "flow_imbalance_prior"] == 0.5
    assert result.loc[1, "flow_taker_buy_ratio_prior"] == 0.75
