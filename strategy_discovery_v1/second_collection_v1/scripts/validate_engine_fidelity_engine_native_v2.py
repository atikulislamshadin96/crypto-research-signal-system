#!/usr/bin/env python3
"""Non-trading smoke checks for the pinned engine-fidelity v2 environment.

This script imports the pinned engine and loads six strategy modules only. It
never reads OHLCV, invokes backtesting, creates trades/returns/trial IDs, or
writes research artifacts.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path

EXPECTED_ENGINE_COMMIT = "eb1a668ceb0f29b7d578156bfc24c45278c0c0f8"
EXPECTED_TECHNICAL_COMMIT = "720ff67483e346271165d49cf37265f78739c74c"
EXPECTED_SUPERTREND_SHA256 = "8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838"
CANDIDATES = {
    "user_data/strategies/CustomStoplossWithPSAR.py": "1h",
    "user_data/strategies/Heracles.py": "4h",
    "user_data/strategies/HourBasedStrategy.py": "1h",
    "user_data/strategies/MultiMa.py": "4h",
    "user_data/strategies/PatternRecognition.py": "1d",
    "user_data/strategies/Supertrend.py": "1h",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def class_timeframe(module, base_class):
    matches = []
    for obj in module.__dict__.values():
        if isinstance(obj, type) and issubclass(obj, base_class) and obj is not base_class:
            matches.append(obj)
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one IStrategy subclass, got {len(matches)}")
    cls = matches[0]
    timeframe = getattr(cls, "timeframe", None)
    if timeframe is None:
        raise AssertionError(f"{cls.__name__} has no timeframe")
    return cls, timeframe


def check_ordering_source(engine_root: Path) -> None:
    backtesting = (engine_root / "freqtrade/optimize/backtesting.py").read_text()
    for token in ("ExitType.EXIT_SIGNAL", "ExitType.STOP_LOSS", "ExitType.ROI", "ExitType.TRAILING_STOP_LOSS"):
        if token not in backtesting:
            raise AssertionError(f"pinned backtesting source lacks expected semantic token: {token}")
    interface = (engine_root / "freqtrade/strategy/interface.py").read_text()
    for token in ("startup_candle_count", "custom_stoploss"):
        if token not in interface:
            raise AssertionError(f"pinned interface source lacks expected semantic token: {token}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-root", type=Path, required=True)
    parser.add_argument("--technical-root", type=Path, required=True)
    parser.add_argument("--strategies-root", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()

    package = json.loads(args.package.read_text())
    if package["measurement_authorized"] or any(package["authorization"].values()):
        raise AssertionError("package unexpectedly authorizes measurement or trading")
    if package["pairlist_venue"]["dynamic_pairlist_allowed"]:
        raise AssertionError("dynamic pairlist is prohibited")
    if package["data"]["detail_scope"]["no_resampling"] is not True:
        raise AssertionError("resampling must be prohibited")

    sys.path.insert(0, str(args.engine_root))
    sys.path.insert(0, str(args.technical_root))
    freqtrade = importlib.import_module("freqtrade")
    interface = importlib.import_module("freqtrade.strategy.interface")
    base_class = interface.IStrategy
    if not freqtrade:
        raise AssertionError("freqtrade import returned no module")
    check_ordering_source(args.engine_root)

    technical_source = args.technical_root / "technical/indicators/supertrend.py"
    if sha(technical_source) != EXPECTED_SUPERTREND_SHA256:
        raise AssertionError("Supertrend source hash mismatch")

    results = []
    for rel, expected_timeframe in sorted(CANDIDATES.items()):
        path = args.strategies_root / rel
        if not path.is_file():
            raise AssertionError(f"missing candidate source: {path}")
        module = load_module(path, "v2_smoke_" + path.stem)
        cls, timeframe = class_timeframe(module, base_class)
        if timeframe != expected_timeframe:
            raise AssertionError(f"{rel}: expected timeframe {expected_timeframe}, got {timeframe}")
        startup = getattr(cls, "startup_candle_count", 0)
        if not isinstance(startup, int) or startup < 0:
            raise AssertionError(f"{rel}: invalid startup_candle_count={startup!r}")
        results.append({"source_path": rel, "strategy_class": cls.__name__, "timeframe": timeframe, "startup_candle_count": startup, "detail_timeframe": "15m"})

    print(json.dumps({
        "status": "ok",
        "engine_import": "pass",
        "engine_commit": EXPECTED_ENGINE_COMMIT,
        "technical_commit": EXPECTED_TECHNICAL_COMMIT,
        "supertrend_source_sha256": EXPECTED_SUPERTREND_SHA256,
        "candidate_loads": results,
        "static_pairlist": True,
        "no_resampling": True,
        "market_data_read": False,
        "performance_metrics_created": False,
        "trial_ids_created": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
