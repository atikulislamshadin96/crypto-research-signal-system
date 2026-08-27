#!/usr/bin/env python3
"""Freeze the v1.2 Freqtrade research harness without running measurement."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "strategy_discovery_v1" / "data"
ROUNDTRIP = DATA_ROOT / "bybit_ohlcv_drive_roundtrip_manifest.json"
OUTPUT = DATA_ROOT.parent / "second_collection_v1" / "data" / "execution_assumption_manifest_v1_2_frozen.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(obj: object) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


def load_roundtrip() -> dict:
    payload = json.loads(ROUNDTRIP.read_text(encoding="utf-8"))
    if payload.get("file_count") != 10 or payload.get("all_byte_for_byte_equal") is not True:
        raise SystemExit("Bybit round-trip manifest is not the verified 10-file byte-equal manifest")
    return payload


def data_files(roundtrip: dict) -> list[dict]:
    result = []
    for entry in sorted(roundtrip["files"], key=lambda item: item["file_name"]):
        path = REPO_ROOT / entry["local_path"]
        raw = path.read_bytes()
        if sha256_bytes(raw) != entry["local_sha256"] or sha256_bytes(raw) != entry["roundtrip_sha256"] or len(raw) != entry["local_size"]:
            raise SystemExit(f"Bybit manifest mismatch: {path}")
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        timestamps = [int(row["start_time_ms"]) for row in rows]
        result.append({
            "file_name": entry["file_name"],
            "local_path": entry["local_path"],
            "drive_file_id": entry["drive_file_id"],
            "sha256": entry["local_sha256"],
            "byte_size": entry["local_size"],
            "row_count": len(rows),
            "start_time_ms": min(timestamps),
            "end_time_ms": max(timestamps),
            "byte_for_byte_equal_to_drive": entry["byte_for_byte_equal"],
        })
    return result


def build(roundtrip: dict, files: list[dict]) -> dict:
    manifest = {
        "manifest_version": "execution_assumption_manifest_v1_2",
        "manifest_id": "freqtrade_batch_001_execution_assumptions_v1_2",
        "status": "frozen_pre_backtest",
        "frozen_at": "2026-08-27T00:00:00Z",
        "scope": {
            "batch_id": "freqtrade-strategies-001",
            "source_repo": "https://github.com/freqtrade/freqtrade-strategies",
            "source_commit": "eff78d3ce3456b52c68a4e9a33cc055a56b801ff",
            "source_license": "GPL-3.0",
            "uniformity": "one_manifest_for_the_batch",
            "candidate_specific_tuning": False,
        },
        "applicability": {
            "origin": "external_assumption",
            "venue": "bybit",
            "market_type": "linear_perpetual",
            "settlement_asset": "USDT",
            "instrument_universe": [
                {"freqtrade_pair": "BTC/USDT:USDT", "bybit_symbol": "BTCUSDT"},
                {"freqtrade_pair": "ETH/USDT:USDT", "bybit_symbol": "ETHUSDT"},
            ],
            "source_timeframe_policy": "exact_match_only_no_resampling",
            "supported_ohlcv_timeframes": ["15m", "30m", "1h", "4h", "1d"],
            "eligible_source_timeframes": ["1h", "4h", "1d"],
            "predeclared_non_tunable_exclusions": [
                {"condition": "source_timeframe not in eligible_source_timeframes", "action": "exclude_before_measurement", "reason": "no_exact_ohlcv_file_in_verified_manifest"},
                {"condition": "pair not in instrument_universe", "action": "exclude_before_measurement", "reason": "outside_uniform_research_scope"},
            ],
        },
        "field_values": {
            "instrument_universe": {"origin": "external_assumption", "value": ["BTC/USDT:USDT", "ETH/USDT:USDT"], "reference": "applicability.instrument_universe"},
            "venue": {"origin": "external_assumption", "value": "bybit", "model": "USDT_linear_perpetual"},
            "quote_currency": {"origin": "external_assumption", "value": "USDT"},
            "applicable_asset_timeframe_constraints": {"origin": "external_assumption", "value": {"eligible_source_timeframes": ["1h", "4h", "1d"], "supported_ohlcv_timeframes": ["15m", "30m", "1h", "4h", "1d"], "policy": "exact_match_only_no_resampling"}},
            "position_sizing": {"origin": "external_assumption", "model": "fixed_notional_per_position", "value": {"notional_usdt": 100.0, "max_open_positions": 2, "max_positions_per_pair": 1, "compounding": False}},
            "risk_budget": {"origin": "external_assumption", "model": "fixed_notional_cap", "value": {"max_total_open_notional_usdt": 200.0, "pyramiding": False}},
            "notional_cap": {"origin": "external_assumption", "value": {"per_position_usdt": 100.0, "portfolio_usdt": 200.0}},
            "leverage_cap": {"origin": "external_assumption", "value": 1.0, "unit": "x", "model": "isolated_margin_no_leverage_above_one"},
            "commission": {"origin": "external_assumption", "value": 0.00055, "unit": "fraction_of_notional_per_side", "model": "VIP0_taker_base_rate_proxy", "reference": "https://www.bybit.com/en/help-center/article/Trading-Fee-Structure"},
            "slippage": {"origin": "external_assumption", "value": 0.0005, "unit": "fraction_of_notional_per_side", "model": "fixed_adverse_price_slippage"},
            "spread": {"origin": "external_assumption", "value": 0.0, "unit": "fraction_of_notional_per_side", "model": "not_observable_in_OHLCV;not_double_counted"},
            "fill_rule": {"origin": "external_assumption", "value": "next_bar_open_market_equivalent", "model": "signal_on_closed_bar_then_fill_at_next_bar_open", "same_bar_fill": False},
            "latency": {"origin": "external_assumption", "value": 1, "unit": "source_timeframe_bars", "model": "one_full_bar_between_signal_and_fill"},
            "funding_or_borrow": {"origin": "external_assumption", "value": 0.0, "unit": "fraction_of_position_value_per_funding_event", "model": "zero_funding_proxy_due_to_absent_historical_funding_dataset", "limitation": "not_a_claim_that_actual_Bybit_funding_was_zero", "reference": "https://www.bybit.com/en/help-center/article/Funding-Fee-Calculation"},
            "rounding_rule": {"origin": "external_assumption", "value": {"mode": "floor", "base_asset_decimal_places": 6, "zero_quantity_action": "skip_order"}},
            "insufficient_margin_behavior": {"origin": "external_assumption", "value": "reject_new_order_no_forced_liquidation_model", "margin_mode": "isolated"},
            "external_config": {"origin": "external_assumption", "value": {"trading_mode": "futures", "margin_mode": "isolated", "stake_currency": "USDT", "dry_run_wallet_usdt": 1000.0, "max_open_trades": 2, "candidate_specific_overrides": False}},
            "missing_data_behavior": {"origin": "external_assumption", "value": "fail_closed_skip_signal_and_do_not_carry_forward_missing_bars"},
            "invalid_bar_behavior": {"origin": "external_assumption", "value": "fail_closed_exclude_invalid_bar_and_abort_candidate_if_required_series_is_invalid"},
            "ohlcv_manifest_refs": {"origin": "external_assumption", "value": [entry["local_path"] for entry in files], "reference_manifest": "strategy_discovery_v1/data/bybit_ohlcv_drive_roundtrip_manifest.json", "reference_manifest_sha256": sha256_bytes(ROUNDTRIP.read_bytes())},
        },
        "data_window": {"start_date": "2025-08-22", "end_date": "2026-08-21", "end_date_inclusive": True, "timezone": "UTC", "source": "verified_local_files_and_drive_roundtrip_manifest"},
        "trial_identity_requirements": ["manifest_id", "manifest_sha256", "source_commit", "source_snapshot_sha256", "ohlcv_manifest_refs", "strategy_code_version", "protocol_version"],
        "limitations": ["This is a research harness, not production or live-trading configuration.", "The zero-funding proxy must be treated as a material limitation until historical funding data is separately acquired and linked.", "Only exact source timeframes with verified OHLCV files are eligible; 5m and 12h source strategies are predeclared exclusions for this batch."],
        "authorization": {"status": "frozen_pre_backtest", "backtest_authorized": False, "trial_creation_authorized": False, "paper_trading_authorized": False, "live_trading_authorized": False},
        "data_manifest": {"roundtrip_manifest_path": str(ROUNDTRIP.relative_to(REPO_ROOT)), "roundtrip_manifest_sha256": sha256_bytes(ROUNDTRIP.read_bytes()), "file_count": len(files), "files": files},
    }
    manifest["manifest_sha256"] = canonical_hash(manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()
    roundtrip = load_roundtrip()
    files = data_files(roundtrip)
    manifest = build(roundtrip, files)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "manifest_id": manifest["manifest_id"], "manifest_sha256": manifest["manifest_sha256"], "file_count": manifest["data_manifest"]["file_count"], "total_candles": sum(f["row_count"] for f in files), "backtest_authorized": manifest["authorization"]["backtest_authorized"]}, sort_keys=True))


if __name__ == "__main__":
    main()
