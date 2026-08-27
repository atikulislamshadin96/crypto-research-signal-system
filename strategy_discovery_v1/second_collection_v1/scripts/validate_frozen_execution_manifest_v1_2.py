#!/usr/bin/env python3
"""Validate the frozen v1.2 Freqtrade execution-assumption manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "strategy_discovery_v1" / "second_collection_v1" / "data" / "execution_assumption_manifest_v1_2_frozen.json"
REQUIRED_FIELDS = [
    "instrument_universe", "venue", "quote_currency", "applicable_asset_timeframe_constraints",
    "position_sizing", "risk_budget", "notional_cap", "leverage_cap", "commission", "slippage",
    "spread", "fill_rule", "latency", "funding_or_borrow", "rounding_rule",
    "insufficient_margin_behavior", "external_config", "missing_data_behavior",
    "invalid_bar_behavior", "ohlcv_manifest_refs",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash_without_self(manifest: dict) -> str:
    copy = dict(manifest)
    copy.pop("manifest_sha256", None)
    return sha256(json.dumps(copy, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == "execution_assumption_manifest_v1_2"
    assert manifest["status"] == "frozen_pre_backtest"
    assert manifest["manifest_sha256"] == canonical_hash_without_self(manifest)
    values = manifest["field_values"]
    assert set(values) == set(REQUIRED_FIELDS)
    assert all(value["origin"] == "external_assumption" for value in values.values())
    assert manifest["applicability"]["venue"] == "bybit"
    assert manifest["applicability"]["market_type"] == "linear_perpetual"
    assert manifest["applicability"]["settlement_asset"] == "USDT"
    assert manifest["applicability"]["instrument_universe"] == [{"freqtrade_pair": "BTC/USDT:USDT", "bybit_symbol": "BTCUSDT"}, {"freqtrade_pair": "ETH/USDT:USDT", "bybit_symbol": "ETHUSDT"}]
    assert manifest["applicability"]["eligible_source_timeframes"] == ["1h", "4h", "1d"]
    assert manifest["data_manifest"]["file_count"] == 10
    assert sum(entry["row_count"] for entry in manifest["data_manifest"]["files"]) == 127750
    assert manifest["authorization"] == {"status": "frozen_pre_backtest", "backtest_authorized": False, "trial_creation_authorized": False, "paper_trading_authorized": False, "live_trading_authorized": False}
    print(json.dumps({"status": "ok", "manifest_id": manifest["manifest_id"], "manifest_sha256": manifest["manifest_sha256"], "required_field_count": len(values), "file_count": manifest["data_manifest"]["file_count"], "total_candles": 127750, "backtest_authorized": manifest["authorization"]["backtest_authorized"]}, sort_keys=True))


if __name__ == "__main__":
    main()
