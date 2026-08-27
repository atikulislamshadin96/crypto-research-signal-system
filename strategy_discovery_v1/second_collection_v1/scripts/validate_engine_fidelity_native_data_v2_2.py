from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

START_MS = 1755820800000
END_EXCLUSIVE_MS = 1787356800000
MARK_STEP_MS = 15 * 60 * 1000
FUNDING_STEP_MS = 8 * 60 * 60 * 1000
EXPECTED_LEDGER_CANONICAL = "2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e"
EXPECTED_V2_PACKAGE = "2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757"
EXPECTED_V2_1_PACKAGE = "d2b8d10439c17ddd98c5c6b877ae5b6a85be0b4a1de24f6840803e86d8255216"
EXPECTED_RUNTIME = "7d3e20fadf1dcffd00dc5396a1b1dca8ea426abe28f1e5c1649dbaa80b46b15d"
EXPECTED_ACQ_CANONICAL = "81893e47e4426cb1be27685dd4bdd8d5f4825eaaa490e5c69fc4e1ffffbe695f"
EXPECTED_ACQ_FILE = "0d156005a9fb57d8c4bb8429d79b20b31eeb6b261ae1f51a742767dcc9b93ed1"
EXPECTED_ENGINE = "eb1a668ceb0f29b7d578156bfc24c45278c0c0f8"
EXPECTED_TECHNICAL = "720ff67483e346271165d49cf37265f78739c74c"
EXPECTED_STRATEGIES = "eff78d3ce3456b52c68a4e9a33cc055a56b801ff"
EXPECTED_SUPERTREND = "8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838"
EXPECTED_ENGINE_FILES = {
    "freqtrade/optimize/backtesting.py": "2420410f96451cb993a7b475e9f7a4232d89480185cc25c59da8883551be6384",
    "freqtrade/strategy/interface.py": "e372b562aabf5e39e444a222f36c7c14801b254fa42141f1431a4ba95d313bb0",
    "freqtrade/data/history/datahandlers/idatahandler.py": "50d786dca6885e880889ae50b30ca757707ceed51db9fa82bfc9d25e8a7d5446",
    "freqtrade/data/history/datahandlers/jsondatahandler.py": "5ae33c5a52438ccd354f43874e78d2d010ae30cc1885971a19ce23a4bf373e7d",
    "freqtrade/candle_columns.py": "01e153140d98545f84226ada6783010e1ab1768cc8019ff1d4e16af92309f1e4",
    "freqtrade/exchange/exchange.py": "ad96d396adb1590abf0891c2da990648c8a6ac030c6e9475c0c3713e8c1dd138",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(data: dict, field: str) -> str:
    copy = dict(data)
    copy.pop(field, None)
    copy.pop("filesystem_sha256", None)
    copy.pop("package_filesystem_sha256", None)
    raw = (json.dumps(copy, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def sha256_bytes_json(data: dict) -> str:
    return hashlib.sha256((json.dumps(data, indent=2) + "\n").encode("utf-8")).hexdigest()


def git_head(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def assert_hash(repo: Path, rel: str, expected: str) -> None:
    path = repo / rel
    assert path.is_file(), f"missing: {rel}"
    assert sha256(path) == expected, f"hash mismatch: {rel}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--engine-root", required=True)
    parser.add_argument("--technical-root", required=True)
    parser.add_argument("--strategies-root", required=True)
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    package_path = repo / args.package
    package = json.loads(package_path.read_text(encoding="utf-8"))
    assert package["status"] == "validated_request_measurement_approval"
    assert package["authorization"]["measurement_authorized"] is False
    assert package["authorization"]["trial_creation_authorized"] is False
    expected_candidates = {"user_data/strategies/CustomStoplossWithPSAR.py": "1h", "user_data/strategies/Heracles.py": "4h", "user_data/strategies/HourBasedStrategy.py": "1h", "user_data/strategies/MultiMa.py": "4h", "user_data/strategies/PatternRecognition.py": "1d", "user_data/strategies/Supertrend.py": "1h"}
    assert package["candidate_eligibility"]["status"] == "future_measurement_eligible_only"
    assert package["candidate_eligibility"]["detail_timeframe"] == "15m"
    assert {item["path"]: item["main_timeframe"] for item in package["candidate_eligibility"]["candidates"]} == expected_candidates
    excluded = {item["path"]: item["reason"] for item in package["candidate_eligibility"]["excluded"]}
    assert excluded == {"user_data/strategies/BreakEven.py": "exact_5m_data_not_in_frozen_scope", "user_data/strategies/Diamond.py": "exact_5m_data_not_in_frozen_scope", "user_data/strategies/PowerTower.py": "exact_5m_data_not_in_frozen_scope", "user_data/strategies/Strategy004.py": "exact_5m_data_not_in_frozen_scope", "user_data/strategies/GodStra.py": "exact_12h_data_not_in_frozen_scope"}
    assert package["placeholder_policy"]["id"] == "mark_price_volume_structural_placeholder_v1"
    assert package["placeholder_policy"]["mark_price_volume_value"] == 0
    assert package["placeholder_policy"]["observed_market_volume"] is False
    assert package["placeholder_policy"]["allowed_only_for"] == ["mark_price"]
    assert package["package_canonical_sha256"] == canonical_hash(package, "package_canonical_sha256")
    package_without_filesystem_hash = dict(package)
    package_without_filesystem_hash.pop("package_filesystem_sha256", None)
    assert package["package_filesystem_sha256"] == sha256_bytes_json(package_without_filesystem_hash)

    schema = json.loads((repo / args.schema).read_text(encoding="utf-8"))
    assert schema["$schema"].startswith("http://json-schema.org/draft-07")
    for key in ("package_id", "version", "status", "placeholder_policy", "native_layout", "integrity_references", "protected_artifacts", "authorization"):
        assert key in schema["required"]
    assert package["version"] == "2.2.0"

    refs = package["integrity_references"]
    for rel, expected in refs["repository_files"].items():
        assert_hash(repo, rel, expected)
    assert refs["acquisition_manifest_canonical_sha256"] == EXPECTED_ACQ_CANONICAL
    acq_rel = "strategy_discovery_v1/second_collection_v1/data/bybit_linear_derivatives_history_v2/acquisition_manifest.json"
    assert_hash(repo, acq_rel, refs["acquisition_manifest_filesystem_sha256"])
    assert refs["acquisition_manifest_filesystem_sha256"] == EXPECTED_ACQ_FILE
    assert_hash(repo, refs["runtime_lock_path"], EXPECTED_RUNTIME)
    assert_hash(repo, "strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2.json", EXPECTED_V2_PACKAGE)
    assert_hash(repo, "strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2_1.json", EXPECTED_V2_1_PACKAGE)
    assert_hash(repo, "strategy_discovery_v1/data/global_trial_ledger.json", refs["ledger_filesystem_sha256"])
    ledger = json.loads((repo / "strategy_discovery_v1/data/global_trial_ledger.json").read_text(encoding="utf-8"))
    assert ledger["n_trials"] == 898 and ledger["last_sequence"] == 898
    assert ledger["global_ledger_hash"] == EXPECTED_LEDGER_CANONICAL
    assert refs["ledger_canonical_sha256"] == EXPECTED_LEDGER_CANONICAL
    assert git_head(Path(args.engine_root)) == EXPECTED_ENGINE
    assert git_head(Path(args.technical_root)) == EXPECTED_TECHNICAL
    assert git_head(Path(args.strategies_root)) == EXPECTED_STRATEGIES
    for rel, expected in EXPECTED_ENGINE_FILES.items():
        assert sha256(Path(args.engine_root) / rel) == expected, f"engine hash mismatch: {rel}"
    assert sha256(Path(args.technical_root) / "technical/indicators/supertrend.py") == EXPECTED_SUPERTREND

    layout_rel = package["native_layout"]["manifest_path"]
    layout_path = repo / layout_rel
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    assert sha256(layout_path) == package["native_layout"]["manifest_sha256"]
    assert layout["engine_commit"] == EXPECTED_ENGINE
    assert layout["dataformat_ohlcv"] == "json"
    assert layout["trading_mode"] == "futures"
    assert layout["exchange_options"] == {"mark_ohlcv_price": "mark", "mark_ohlcv_timeframe": "15m", "funding_fee_timeframe": "8h"}
    assert layout["ft_has_params_override"] == {"mark_ohlcv_timeframe": "15m", "funding_fee_timeframe": "8h"}
    assert layout["pairlist"] == ["BTC/USDT:USDT", "ETH/USDT:USDT"]
    assert layout["placeholder_policy"]["mark_price_volume_value"] == 0
    assert layout["placeholder_policy"]["observed_market_volume"] is False
    assert layout["native_columns"] == {"mark_price": ["date", "open", "high", "low", "close", "volume"], "funding_rate": ["date", "funding_rate"]}

    source_root = repo / "strategy_discovery_v1/second_collection_v1/data/bybit_linear_derivatives_history_v2"
    checked = []
    for item in layout["files"]:
        native_path = repo / item["path"]
        source_path = repo / item["source_path"]
        assert native_path.is_file() and source_path.is_file()
        assert sha256(native_path) == item["sha256"]
        assert sha256(source_path) == item["source_sha256"]
        native_rows = json.loads(native_path.read_text(encoding="utf-8"))
        source_rows = json.loads(source_path.read_text(encoding="utf-8"))
        assert len(native_rows) == item["row_count"] == len(source_rows)
        if item["kind"] == "mark_price":
            assert item["placeholder_volume_value"] == 0
            timestamps = [int(row[0]) for row in native_rows]
            assert timestamps == list(range(START_MS, END_EXCLUSIVE_MS, MARK_STEP_MS))
            for native, source in zip(native_rows, source_rows):
                assert len(native) == 6 and native[5] == 0
                assert native[:5] == [int(source["start_time_ms"]), source["open"], source["high"], source["low"], source["close"]]
        else:
            assert item["placeholder_volume_value"] is None
            timestamps = [int(row[0]) for row in native_rows]
            assert len(native_rows) == 1095 and timestamps == sorted(set(timestamps))
            assert min(b - a for a, b in zip(timestamps, timestamps[1:])) == max(b - a for a, b in zip(timestamps, timestamps[1:])) == FUNDING_STEP_MS
            for native, source in zip(native_rows, source_rows):
                assert len(native) == 2
                assert native == [int(source["funding_rate_timestamp_ms"]), source["funding_rate"]]
        checked.append({"kind": item["kind"], "symbol": item["symbol"], "rows": len(native_rows), "sha256": item["sha256"]})

    # Pinned engine source resolution: mark volume is loader-structural only.
    exchange_source = (Path(args.engine_root) / "freqtrade/exchange/exchange.py").read_text(encoding="utf-8")
    assert 'relevant_cols = ["date", "open_mark", "open_fund"]' in exchange_source
    assert 'mark_rates = mark_rates.rename(columns={"open": "open_mark"})' in exchange_source
    assert '"volume"' not in exchange_source[exchange_source.index('def combine_funding_and_mark'):exchange_source.index('def calculate_funding_fees')]
    assert "if exchange_conf.get(\"_ft_has_params\")" in exchange_source
    assert "self._ft_has = deep_merge_dicts(exchange_conf.get(\"_ft_has_params\"), self._ft_has)" in exchange_source
    candle_source = (Path(args.engine_root) / "freqtrade/candle_columns.py").read_text(encoding="utf-8")
    assert 'OHLCV_COLUMNS = ["date", "open", "high", "low", "close", "volume"]' in candle_source
    strategy_root = Path(args.strategies_root) / "user_data/strategies"
    for rel in package["authorized_strategy_paths"]:
        source = (strategy_root / Path(rel).name).read_text(encoding="utf-8")
        assert "mark_price_volume_structural_placeholder" not in source
        assert "CandleType.MARK" not in source and "native_freqtrade_data" not in source

    # Non-trading loader smoke only; no strategy import or performance execution.
    from freqtrade.data.history import load_pair_history
    from freqtrade.enums import CandleType
    datadir = repo / layout["datadir"]
    for symbol, pair in (("BTCUSDT", "BTC/USDT:USDT"), ("ETHUSDT", "ETH/USDT:USDT")):
        mark = load_pair_history(pair, "15m", datadir, fill_up_missing=False, drop_incomplete=False, data_format="json", candle_type=CandleType.MARK)
        funding = load_pair_history(pair, "8h", datadir, fill_up_missing=False, drop_incomplete=False, data_format="json", candle_type=CandleType.FUNDING_RATE)
        assert len(mark) == 35040 and len(funding) == 1095
        assert list(mark.columns) == ["date", "open", "high", "low", "close", "volume"]
        assert list(funding.columns) == ["date", "funding_rate", "open"]
        assert funding["open"].equals(funding["funding_rate"])
        assert mark["volume"].eq(0).all()
        assert mark["date"].is_monotonic_increasing and funding["date"].is_monotonic_increasing

    print(json.dumps({"status": "ok", "package": package["package_id"], "package_measurement_authorized": False, "native_loader_smoke": "pass", "placeholder_volume_only": True, "checked_files": checked, "ledger_n": 898, "trial_ids_created": 0, "backtest_run": False}, indent=2))


if __name__ == "__main__":
    main()
