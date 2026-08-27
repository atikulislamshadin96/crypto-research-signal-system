#!/usr/bin/env python3
"""Run semantic-only v2 parity fixtures.

This runner intentionally does not load candidate strategies, market data, or
return series. It creates no trial IDs and never writes research artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_TECHNICAL_COMMIT = "720ff67483e346271165d49cf37265f78739c74c"
EXPECTED_SUPERTREND_SHA256 = "8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_case(case: dict, technical_source: Path | None) -> None:
    cid = case["id"]
    if cid == "entry_next_main_open":
        assert case["expected_entry_candle_index"] == case["signal_candle_index"] + 1
    elif cid == "same_candle_exit_signal_priority":
        sequence = ["exit_signal", "stoploss", "roi", "trailing_stop"]
        active = [x for x in sequence if case.get(x)]
        assert active and active[0] == case["expected_first_exit"]
    elif cid == "stoploss_before_roi_when_no_exit_signal":
        sequence = ["exit_signal", "stoploss", "roi", "trailing_stop"]
        active = [x for x in sequence if case.get(x)]
        assert active and active[0] == case["expected_first_exit"]
    elif cid == "custom_stoploss_uses_long_high_bound":
        current_rate = case["candle_high"]
        stop_price = current_rate * (1.0 - case["returned_distance"])
        assert math.isclose(stop_price, case["expected_stop_price"], rel_tol=0, abs_tol=1e-12)
        assert case["candle_low"] <= stop_price == case["expected_stop_price"]
    elif cid == "custom_stoploss_monotonic":
        history = [case["initial_stop"]]
        for update in case["updates"]:
            history.append(max(history[-1], update))
        assert history == case["expected_stop_history"]
    elif cid == "roi_respects_candle_bound":
        target = case["entry_price"] * (1.0 + case["roi_ratio"])
        assert case["candle_high"] >= target
        exit_price = max(target, case["candle_low"])
        assert math.isclose(exit_price, case["expected_exit_price"], rel_tol=0, abs_tol=1e-12)
    elif cid == "startup_trim":
        assert case["expected_first_evaluable_index"] == case["startup_candle_count"]
    elif cid == "detail_timeframe_missing_fail_closed":
        assert not case["detail_data_available"]
        assert case["expected_status"] == "fail_closed"
    elif cid == "static_pairlist_required":
        assert case["pairlist_mode"] == "StaticPairList" and not case["dynamic_pairlist"]
        assert case["expected_status"] == "accepted"
    elif cid == "dynamic_pairlist_prohibited":
        assert case["dynamic_pairlist"]
        assert case["expected_status"] == "fail_closed"
    elif cid == "quantity_floor_precision":
        scale = 10 ** case["decimal_places"]
        quantity = math.floor(case["raw_quantity"] * scale) / scale
        assert math.isclose(quantity, case["expected_quantity"], rel_tol=0, abs_tol=1e-12)
    elif cid == "end_of_data_force_exit":
        assert case["position_open"] and case["expected_exit_reason"] == "force_exit_end_of_data"
        assert case["expected_exit_price"] == case["last_close"]
    elif cid == "supertrend_output_contract":
        assert technical_source is not None, "pinned technical source is required for Supertrend parity"
        assert technical_source.exists()
        assert sha256_file(technical_source) == EXPECTED_SUPERTREND_SHA256
        spec = importlib.util.spec_from_file_location("pinned_supertrend", technical_source)
        if spec is None or spec.loader is None:
            raise AssertionError("cannot load pinned Supertrend source")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = case["input_rows"]
        values = np.arange(rows, dtype=float)
        frame = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC"),
            "open": values + 100.0,
            "high": values + 101.0,
            "low": values + 99.0,
            "close": values + 100.5,
            "volume": np.full(rows, 10.0),
        })
        st, stx = module.supertrend(frame, period=3, multiplier=2)
        assert len(st) == rows and len(stx) == rows
        assert set(x for x in stx.tolist() if x is not None).issubset({"up", "down"})
    else:
        raise AssertionError(f"unknown fixture: {cid}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--technical-source", required=True)
    args = parser.parse_args()
    fixtures_path = Path(args.fixtures)
    technical_source = Path(args.technical_source)
    payload = json.loads(fixtures_path.read_text(encoding="utf-8"))
    assert payload["purpose"] == "semantic_only_no_performance_measurement"
    assert payload["performance_metrics_created"] is False
    assert payload["trial_ids_created"] is False
    for case in payload["cases"]:
        check_case(case, technical_source)
    print(json.dumps({
        "status": "ok",
        "fixture_id": payload["fixture_id"],
        "cases_passed": len(payload["cases"]),
        "performance_metrics_created": False,
        "trial_ids_created": False,
        "technical_commit": EXPECTED_TECHNICAL_COMMIT,
        "technical_source_sha256": sha256_file(technical_source),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
