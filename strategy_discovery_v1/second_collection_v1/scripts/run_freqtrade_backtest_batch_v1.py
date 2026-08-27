#!/usr/bin/env python3
"""Run the first authorized, measured Freqtrade research batch.

Only strategies with exact verified OHLCV timeframes and available declared
indicator dependencies are measured. Unsupported candidates are recorded as
predeclared exclusions. The script never fetches data or changes the ledger.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import sys
import types
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import talib.abstract as talib_abstract

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_COMMIT = "eff78d3ce3456b52c68a4e9a33cc055a56b801ff"
SOURCE_REPO = "https://github.com/freqtrade/freqtrade-strategies"
HARNESS_PROFILE_VERSION = "freqtrade_batch_001_research_harness_v1"
SUPPORTED_STRATEGIES = {"CustomStoplossWithPSAR.py", "Heracles.py", "HourBasedStrategy.py", "MultiMa.py", "PatternRecognition.py"}
TIMEFRAME_MINUTES = {"15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
SYMBOLS = {"BTC/USDT:USDT": "BTCUSDT", "ETH/USDT:USDT": "ETHUSDT"}
SLIPPAGE = 0.0005
COMMISSION = 0.00055
STARTING_EQUITY = 1000.0
POSITION_NOTIONAL = 100.0
MAX_HOLDING_DAYS = 30


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_shims() -> None:
    """Supply only the framework interfaces used by the selected source files."""
    freqtrade = types.ModuleType("freqtrade")
    strategy = types.ModuleType("freqtrade.strategy")
    vendor = types.ModuleType("freqtrade.vendor")
    qtpylib = types.ModuleType("freqtrade.vendor.qtpylib")
    qtpylib_ind = types.ModuleType("freqtrade.vendor.qtpylib.indicators")
    persistence = types.ModuleType("freqtrade.persistence")
    pandas_ta = types.ModuleType("pandas_ta")
    technical_util = types.ModuleType("technical.util")

    class Parameter:
        def __init__(self, *args, default=None, **kwargs):
            self.value = default
            self.default = default
            self.range = range(int(args[0]), int(args[1]) + 1) if len(args) >= 2 and all(isinstance(x, (int, float)) for x in args[:2]) else []
            self.choices = args[0] if args and isinstance(args[0], (list, tuple)) else None

    class DataProvider:
        runmode = types.SimpleNamespace(value="backtest")
        def get_analyzed_dataframe(self, **kwargs):
            return pd.DataFrame(), None

    class IStrategy:
        def __init__(self):
            self.dp = DataProvider()

    def crossed_above(a, b):
        return (a > b) & (a.shift(1) <= b.shift(1))

    def crossed_below(a, b):
        return (a < b) & (a.shift(1) >= b.shift(1))

    strategy.IStrategy = IStrategy
    strategy.IntParameter = Parameter
    strategy.DecimalParameter = Parameter
    strategy.CategoricalParameter = Parameter
    strategy.BooleanParameter = Parameter
    strategy.merge_informative_pair = lambda *args, **kwargs: args[0]
    qtpylib_ind.crossed_above = crossed_above
    qtpylib_ind.crossed_below = crossed_below
    persistence.Trade = object
    technical_util.resample_to_interval = lambda dataframe, interval: dataframe
    technical_util.resampled_merge = lambda dataframe, informative, **kwargs: dataframe
    freqtrade.strategy = strategy
    freqtrade.vendor = vendor
    vendor.qtpylib = qtpylib
    qtpylib.indicators = qtpylib_ind
    freqtrade.persistence = persistence
    sys.modules.update({
        "freqtrade": freqtrade,
        "freqtrade.strategy": strategy,
        "freqtrade.vendor": vendor,
        "freqtrade.vendor.qtpylib": qtpylib,
        "freqtrade.vendor.qtpylib.indicators": qtpylib_ind,
        "freqtrade.persistence": persistence,
        "pandas_ta": pandas_ta,
        "technical.util": technical_util,
    })


def load_strategy(path: Path):
    install_shims()
    module_name = "strategy_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    classes = [x for x in module.__dict__.values() if isinstance(x, type) and x.__module__ == module_name]
    cls = next((x for x in classes if any("Strategy" in getattr(base, "__name__", str(base)) for base in getattr(x, "__bases__", []))), classes[0])
    obj = cls()
    for side in ("buy_params", "sell_params"):
        params = getattr(cls, side, {}) or {}
        for name, value in params.items():
            attr = getattr(obj, name, None)
            if hasattr(attr, "value"):
                attr.value = value
    return obj, cls


def load_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    raw["date"] = pd.to_datetime(raw["start_time_ms"], unit="ms", utc=True)
    raw = raw.rename(columns={"start_time_ms": "timestamp_ms"})
    raw = raw[["date", "open", "high", "low", "close", "volume"]].copy()
    raw = raw.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    if raw[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise RuntimeError(f"invalid OHLCV values in {path}")
    return raw


def strategy_signals(obj, df: pd.DataFrame, pair: str) -> pd.DataFrame:
    obj.custom_info = getattr(obj, "custom_info", {})
    out = df.copy()
    if obj.__class__.__name__ == "MultiMa":
        # Source-equivalent pruning: the source creates ~2,000 TEMA columns,
        # but its explicit entry/exit methods reference only these keys for the
        # fixed source-declared buy/sell parameterization. Unreferenced columns
        # cannot affect the returned signal dataframe.
        import talib
        buy_count = int(getattr(obj, "buy_ma_count").value)
        buy_gap = int(getattr(obj, "buy_ma_gap").value)
        sell_count = int(getattr(obj, "sell_ma_count").value)
        sell_gap = int(getattr(obj, "sell_ma_gap").value)
        periods = set()
        for count in range(buy_count):
            key = count * buy_gap; past = (count - 1) * buy_gap
            if past > 1: periods.update([key, past])
        for count in range(sell_count):
            key = count * sell_gap; past = (count - 1) * sell_gap
            if past > 1: periods.update([key, past])
        for period in sorted(periods):
            out[period] = talib.TEMA(out["close"].to_numpy(dtype=float), timeperiod=int(period))
        out = obj.populate_entry_trend(out, {"pair": pair})
        out = obj.populate_exit_trend(out, {"pair": pair})
    else:
        out = obj.populate_indicators(out, {"pair": pair})
        out["enter_long"] = 0
        out["exit_long"] = 0
        out = obj.populate_entry_trend(out, {"pair": pair})
        out = obj.populate_exit_trend(out, {"pair": pair})
    out["enter_long"] = out.get("enter_long", 0).fillna(0).astype(int)
    out["exit_long"] = out.get("exit_long", 0).fillna(0).astype(int)
    return out


def roi_value(roi_table: dict, elapsed_minutes: float) -> float | None:
    choices = [(int(k), float(v)) for k, v in roi_table.items() if elapsed_minutes >= int(k)]
    return min(choices, key=lambda x: x[0])[1] if choices else None


def simulate_pair(df: pd.DataFrame, obj, pair: str, timeframe: str) -> tuple[pd.Series, list[dict]]:
    stoploss = float(getattr(obj, "stoploss", -1.0))
    roi_table = getattr(obj, "minimal_roi", {}) or {}
    trailing = bool(getattr(obj, "trailing_stop", False))
    trail_positive = getattr(obj, "trailing_stop_positive", None)
    trail_offset = float(getattr(obj, "trailing_stop_positive_offset", 0.0) or 0.0)
    trail_only = bool(getattr(obj, "trailing_only_offset_is_reached", False))
    max_bars = max(1, int(MAX_HOLDING_DAYS * 1440 / TIMEFRAME_MINUTES[timeframe]))
    position = None
    pending_entry = False
    pending_exit = False
    realized = 0.0
    peak = None
    pnl = []
    trades = []
    for i, row in df.iterrows():
        if pending_exit and position is not None:
            exit_price = float(row["open"]) * (1 - SLIPPAGE)
            gross = (exit_price - position["entry_price"]) * position["qty"]
            fees = (position["entry_price"] * position["qty"] + exit_price * position["qty"]) * COMMISSION
            net = gross - fees
            realized += net
            trades.append({"pair": pair, "entry_time": position["entry_time"], "exit_time": row["date"].isoformat(), "entry_price": position["entry_price"], "exit_price": exit_price, "net_pnl": net, "exit_reason": "exit_signal"})
            position = None
            pending_exit = False
            peak = None
        if pending_entry and position is None:
            entry_price = float(row["open"]) * (1 + SLIPPAGE)
            qty = math.floor((POSITION_NOTIONAL / entry_price) * 1_000_000) / 1_000_000
            if qty > 0:
                position = {"entry_time": row["date"].isoformat(), "entry_idx": i, "entry_price": entry_price, "qty": qty, "peak": float(row["high"])}
                peak = float(row["high"])
            pending_entry = False
        if position is not None and i > position["entry_idx"]:
            peak = max(float(peak), float(row["high"]))
            base_stop = position["entry_price"] * (1 + stoploss)
            stop_price = base_stop
            if hasattr(obj, "custom_stoploss") and hasattr(obj, "custom_info"):
                sar = row.get("sar", np.nan)
                if pd.notna(sar):
                    # Source formula: result = (current_rate - sar) / current_rate - 1,
                    # so the effective stop price is current_rate - sar.
                    source_custom_stop = float(row["close"]) - float(sar)
                    stop_price = max(stop_price, source_custom_stop)
            if trailing and trail_positive is not None:
                profit_peak = peak / position["entry_price"] - 1
                if (not trail_only) or profit_peak >= trail_offset:
                    stop_price = max(stop_price, peak * (1 - float(trail_positive)))
            elapsed = (row["date"] - pd.Timestamp(position["entry_time"])) / pd.Timedelta(minutes=1)
            roi = roi_value(roi_table, float(elapsed))
            target_price = position["entry_price"] * (1 + roi) if roi is not None else None
            hit_stop = float(row["low"]) <= stop_price
            hit_target = target_price is not None and float(row["high"]) >= target_price
            force_time = i - position["entry_idx"] >= max_bars
            reason = None
            exit_price = None
            if hit_stop and hit_target:
                reason, exit_price = "stoploss_same_bar_priority", stop_price * (1 - SLIPPAGE)
            elif hit_stop:
                reason, exit_price = "custom_stoploss" if hasattr(obj, "custom_stoploss") else "stoploss", stop_price * (1 - SLIPPAGE)
            elif hit_target:
                reason, exit_price = "roi_target", target_price * (1 - SLIPPAGE)
            elif force_time:
                reason, exit_price = "max_holding_time", float(row["open"]) * (1 - SLIPPAGE)
            if reason is not None:
                gross = (exit_price - position["entry_price"]) * position["qty"]
                fees = (position["entry_price"] * position["qty"] + exit_price * position["qty"]) * COMMISSION
                net = gross - fees
                realized += net
                trades.append({"pair": pair, "entry_time": position["entry_time"], "exit_time": row["date"].isoformat(), "entry_price": position["entry_price"], "exit_price": exit_price, "net_pnl": net, "exit_reason": reason})
                position = None
                peak = None
            elif int(row.get("exit_long", 0)) == 1:
                pending_exit = True
        mark = realized
        if position is not None:
            mark += (float(row["close"]) - position["entry_price"]) * position["qty"]
        pnl.append(mark)
        if position is None and int(row.get("enter_long", 0)) == 1 and i + 1 < len(df):
            pending_entry = True
    if position is not None:
        row = df.iloc[-1]
        exit_price = float(row["close"]) * (1 - SLIPPAGE)
        gross = (exit_price - position["entry_price"]) * position["qty"]
        fees = (position["entry_price"] * position["qty"] + exit_price * position["qty"]) * COMMISSION
        net = gross - fees
        realized += net
        trades.append({"pair": pair, "entry_time": position["entry_time"], "exit_time": row["date"].isoformat(), "entry_price": position["entry_price"], "exit_price": exit_price, "net_pnl": net, "exit_reason": "end_of_data"})
        pnl[-1] = realized
    return pd.Series(pnl, index=df["date"], name=pair), trades


def metric_summary(returns: pd.Series, trades: list[dict], timeframe: str) -> dict:
    r = returns.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    ann = math.sqrt(365 * 1440 / TIMEFRAME_MINUTES[timeframe])
    mean = float(r.mean()) if len(r) else 0.0
    std = float(r.std(ddof=1)) if len(r) > 1 else 0.0
    sharpe = mean / std * ann if std > 0 else 0.0
    eq = (1 + r).cumprod()
    dd = eq / eq.cummax() - 1
    wins = sum(t["net_pnl"] > 0 for t in trades)
    return {
        "observations": int(len(r)), "annualization_factor": 365 * 1440 / TIMEFRAME_MINUTES[timeframe],
        "trade_count": len(trades), "win_rate": wins / len(trades) if trades else 0.0,
        "total_net_pnl_usdt": float(sum(t["net_pnl"] for t in trades)),
        "total_return": float(eq.iloc[-1] - 1) if len(eq) else 0.0,
        "annualized_sharpe": sharpe, "sample_skewness": float(r.skew()) if len(r) > 2 else 0.0,
        "sample_pearson_kurtosis": float(r.kurtosis() + 3) if len(r) > 3 else 3.0,
        "max_drawdown": float(dd.min()) if len(dd) else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--readiness", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--harness-profile", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source_dir = Path(args.source_dir)
    harness_code_sha256 = sha256_file(Path(__file__))
    readiness_path = Path(args.readiness)
    manifest_path = Path(args.manifest)
    profile_path = Path(args.harness_profile)
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if manifest["status"] != "frozen_pre_backtest" or manifest["manifest_sha256"] != "041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97":
        raise SystemExit("unexpected frozen manifest")
    if profile["source_execution_manifest_sha256"] != manifest["manifest_sha256"] or profile["status"] != "frozen_pre_backtest":
        raise SystemExit("harness profile does not link to frozen manifest")
    data_root = REPO_ROOT
    by_symbol_tf = {f["file_name"]: data_root / f["local_path"] for f in manifest["data_manifest"]["files"]}
    results, exclusions = [], []
    for candidate in readiness["records"]:
        if candidate["research_contract_status"] != "execution_contract_complete":
            continue
        fname = Path(candidate["source_path"]).name
        timeframe = next((c.get("value") for c in candidate["field_claims"] if c["field_path"] == "source.timeframe"), None)
        if fname not in SUPPORTED_STRATEGIES:
            exclusions.append({"document_id": candidate["document_id"], "source_path": candidate["source_path"], "reason": "unsupported_dependency_or_harness_semantics", "timeframe": timeframe, "trial_created": False})
            continue
        if timeframe not in manifest["applicability"]["eligible_source_timeframes"]:
            exclusions.append({"document_id": candidate["document_id"], "source_path": candidate["source_path"], "reason": "source_timeframe_not_in_exact_verified_ohlcv_scope", "timeframe": timeframe, "trial_created": False})
            continue
        source_path = source_dir / candidate["source_path"]
        source_hash = sha256_file(source_path)
        if source_hash != candidate["source_snapshot_sha256"]:
            raise SystemExit(f"source hash mismatch: {source_path}")
        obj, cls = load_strategy(source_path)
        pair_pnls, all_trades = [] , []
        pair_counts = {}
        for pair, symbol in SYMBOLS.items():
            file_name = f"{symbol}_{timeframe}_2025-08-22_2026-08-21.csv"
            path = by_symbol_tf.get(file_name)
            if path is None:
                raise SystemExit(f"missing exact data file: {file_name}")
            df = load_csv(path)
            sig = strategy_signals(obj, df, pair)
            pnl, trades = simulate_pair(sig, obj, pair, timeframe)
            pair_pnls.append(pnl.rename(pair)); all_trades.extend(trades); pair_counts[pair] = len(trades)
        joined = pd.concat(pair_pnls, axis=1).sort_index().ffill().fillna(0.0)
        equity = STARTING_EQUITY + joined.sum(axis=1)
        returns = equity.pct_change().fillna(0.0)
        return_records = [{"timestamp": idx.isoformat(), "return": float(value)} for idx, value in returns.items()]
        rule_hash = canonical_hash({"source_path": candidate["source_path"], "source_commit": SOURCE_COMMIT, "source_hash": source_hash, "manifest_sha256": manifest["manifest_sha256"], "harness_profile_sha256": profile["harness_profile_sha256"], "harness_code_sha256": harness_code_sha256, "timeframe": timeframe})
        trial_id = "freqtrade-001-" + rule_hash[:16]
        results.append({"trial_id": trial_id, "candidate_id": candidate["document_id"], "source_path": candidate["source_path"], "source_snapshot_sha256": source_hash, "timeframe": timeframe, "pair_universe": list(SYMBOLS), "canonical_rule_hash": rule_hash, "data_manifest_hash": manifest["data_manifest"]["roundtrip_manifest_sha256"], "execution_manifest_sha256": manifest["manifest_sha256"], "harness_profile_sha256": profile["harness_profile_sha256"], "harness_code_sha256": harness_code_sha256, "return_series_sha256": canonical_hash(return_records), "return_series": return_records, "metrics": metric_summary(returns, all_trades, timeframe), "trade_count_by_pair": pair_counts, "trades": all_trades, "measured": True, "trial_created": True, "analysis_only": False})
    output = {"batch_id": "freqtrade-strategies-001-measured-v1", "source_repo": SOURCE_REPO, "source_commit": SOURCE_COMMIT, "manifest_id": manifest["manifest_id"], "manifest_sha256": manifest["manifest_sha256"], "harness_profile_version": HARNESS_PROFILE_VERSION, "harness_profile_sha256": profile["harness_profile_sha256"], "harness_code_sha256": harness_code_sha256, "protocol_id": "dsr_pbo_cpcv_v1", "protocol_path": "strategy_discovery_v1/protocols/dsr_pbo_cpcv_v1.json", "candidate_universe_authorized": 11, "measured_count": len(results), "exclusion_count": len(exclusions), "exclusions": exclusions, "backtest_run": True, "market_data_downloaded": False, "trial_created": True, "ledger_start_n": 893, "results": results, "analysis_only": False}
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"measured_count": len(results), "exclusion_count": len(exclusions), "trades": sum(r["metrics"]["trade_count"] for r in results), "trial_ids": [r["trial_id"] for r in results], "manifest_sha256": manifest["manifest_sha256"], "harness_profile_sha256": profile["harness_profile_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
