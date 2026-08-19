from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from crypto_signal_system.backtest import load_ohlcv_csv
from crypto_signal_system.features import add_features
from crypto_signal_system.strategies import bos_retest_continuation

CONFIG_PATH = Path("config/bos_only_strict_4h_daily.yaml")
ROOT = Path("artifacts/bos-4h-daily/advanced_bos_extension")
DATA_ROOT = Path("data/focused_ohlcv_advanced/4h")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TIMEFRAME = "4h"
HORIZONS = (1, 2, 4, 8, 12)
BOOTSTRAPS = 5000
SEED = 1337


def bootstrap_diff(event: np.ndarray, control: np.ndarray, rng: np.random.Generator) -> dict[str, float | None]:
    if len(event) == 0 or len(control) == 0:
        return {"mean_event": None, "mean_control": None, "mean_difference": None, "p05_difference": None, "p95_difference": None}
    differences = np.empty(BOOTSTRAPS, dtype=float)
    for i in range(BOOTSTRAPS):
        differences[i] = rng.choice(event, len(event), replace=True).mean() - rng.choice(control, len(control), replace=True).mean()
    return {
        "mean_event": float(np.mean(event)),
        "mean_control": float(np.mean(control)),
        "mean_difference": float(np.mean(event) - np.mean(control)),
        "p05_difference": float(np.quantile(differences, 0.05)),
        "p95_difference": float(np.quantile(differences, 0.95)),
    }


def event_study(symbol: str, frame: pd.DataFrame, start: int, end: int, strategy_cfg: dict) -> dict[str, object]:
    history_bars = 160
    events: list[dict[str, object]] = []
    event_keys: set[tuple[int, str]] = set()
    for index in range(max(80, start), min(end, len(frame) - max(HORIZONS))):
        history = frame.iloc[max(0, index + 1 - history_bars) : index + 1]
        candidate = bos_retest_continuation(symbol, history, strategy_cfg)
        if candidate is not None:
            event_keys.add((index, candidate.direction))
            events.append({"index": index, "direction": candidate.direction})

    by_horizon: dict[str, object] = {}
    rng = np.random.default_rng(SEED)
    for horizon in HORIZONS:
        event_values: list[float] = []
        control_values: list[float] = []
        for index in range(max(80, start), min(end - horizon, len(frame) - horizon)):
            row = frame.iloc[index]
            if pd.isna(row["atr"]) or float(row["atr"]) <= 0 or pd.isna(row["structure_bias"]):
                continue
            directions = [direction for event_index, direction in event_keys if event_index == index]
            if directions:
                direction = directions[0]
                value = (1 if direction == "LONG" else -1) * (float(frame.iloc[index + horizon]["close"]) - float(row["close"])) / (1.25 * float(row["atr"]))
                event_values.append(value)
            else:
                # Structure-matched non-event control: use the current causal structure bias.
                bias = int(row["structure_bias"])
                if bias == 0:
                    continue
                direction = "LONG" if bias > 0 else "SHORT"
                value = (1 if direction == "LONG" else -1) * (float(frame.iloc[index + horizon]["close"]) - float(row["close"])) / (1.25 * float(row["atr"]))
                control_values.append(value)
        event_array = np.asarray(event_values, dtype=float)
        control_array = np.asarray(control_values, dtype=float)
        result = bootstrap_diff(event_array, control_array, rng)
        result.update({"event_count": len(event_array), "control_count": len(control_array), "effect_is_positive_lower_bound": bool(result["p05_difference"] is not None and result["p05_difference"] > 0)})
        by_horizon[str(horizon)] = result

    return {
        "symbol": symbol,
        "timeframe": TIMEFRAME,
        "oos_start_index": start,
        "oos_end_index": end,
        "event_definition": "exact strict bos_retest_continuation candidate on closed bars; no scoring, entry, exit, or strategy simulation",
        "control_definition": "non-event closed bars matched only on causal structure-bias direction",
        "horizons_bars": list(HORIZONS),
        "events": events,
        "horizon_results": by_horizon,
        "decision": "diagnostic_only_no_strategy_construction",
    }


def hierarchical_trade_diagnostic() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    trade_arrays: dict[str, np.ndarray] = {}
    for symbol in SYMBOLS:
        path = ROOT / f"{symbol}-{TIMEFRAME}-advanced-oos-ledger.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = np.asarray([float(t["r_multiple"]) for t in payload["trades"]], dtype=float)
        trade_arrays[symbol] = values
        rows.append({"asset": symbol, "n": int(len(values)), "mean_r": float(values.mean()) if len(values) else None, "sd_r": float(values.std(ddof=1)) if len(values) > 1 else None})

    means = np.asarray([row["mean_r"] for row in rows if row["mean_r"] is not None], dtype=float)
    ses = np.asarray([row["sd_r"] / np.sqrt(row["n"]) for row in rows if row["mean_r"] is not None], dtype=float)
    grand = float(np.average(means, weights=1 / np.maximum(ses**2, 1e-12))) if len(means) else None
    between = max(0.0, float(np.var(means, ddof=1) - np.mean(ses**2))) if len(means) > 1 else 0.0
    pooled_rows: list[dict[str, object]] = []
    for row, mean, se in zip(rows, means, ses):
        weight = between / (between + se**2) if between + se**2 > 0 else 0.0
        pooled_rows.append({**row, "standard_error": float(se), "empirical_bayes_shrinkage_weight": float(weight), "partial_pooled_mean_r": float(weight * mean + (1 - weight) * grand) if grand is not None else None})

    all_values = np.concatenate(list(trade_arrays.values())) if trade_arrays else np.asarray([], dtype=float)
    rng = np.random.default_rng(SEED)
    pooled_bootstrap = []
    for _ in range(BOOTSTRAPS):
        sampled = []
        for symbol in SYMBOLS:
            values = trade_arrays[symbol]
            if len(values):
                sampled.append(rng.choice(values, len(values), replace=True).mean())
        if sampled:
            pooled_bootstrap.append(float(np.mean(sampled)))
    loo = {}
    for excluded in SYMBOLS:
        kept = [values for symbol, values in trade_arrays.items() if symbol != excluded and len(values)]
        combined = np.concatenate(kept) if kept else np.asarray([], dtype=float)
        loo[excluded] = {"trades": int(len(combined)), "mean_r": float(combined.mean()) if len(combined) else None}
    return {
        "diagnostic_status": "not_a_validation_gate; no executable strategy change",
        "method": "empirical-Bayes normal-normal partial pooling of final untouched-OOS trade means; within-asset bootstrap; leave-one-asset-out sensitivity",
        "asset_trade_summaries": pooled_rows,
        "grand_inverse_variance_weighted_mean_r": grand,
        "estimated_between_asset_variance": between,
        "pooled_trade_count": int(len(all_values)),
        "pooled_within_asset_bootstrap_p05_mean_r": float(np.quantile(pooled_bootstrap, 0.05)) if pooled_bootstrap else None,
        "pooled_within_asset_bootstrap_p50_mean_r": float(np.quantile(pooled_bootstrap, 0.50)) if pooled_bootstrap else None,
        "pooled_within_asset_bootstrap_p95_mean_r": float(np.quantile(pooled_bootstrap, 0.95)) if pooled_bootstrap else None,
        "leave_one_asset_out": loo,
        "interpretation": "Pooling may describe a shared family-level signal, but it cannot promote an asset-specific strategy when that asset fails its pre-registered OOS gates.",
    }


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    strategy_cfg = config["strategies"]["bos_retest_continuation"]
    out_dir = ROOT / "advanced-diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    event_index: dict[str, object] = {}
    for symbol in SYMBOLS:
        report = json.loads((ROOT / f"{symbol}-{TIMEFRAME}-advanced-validation.json").read_text(encoding="utf-8"))
        candles = load_ohlcv_csv(DATA_ROOT / symbol / f"{symbol}-{TIMEFRAME}-2020-2026-08-17.csv", symbol, TIMEFRAME, source="binance_vision_official")
        frame = add_features(pd.DataFrame([c.to_dict() for c in candles]))
        frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
        frame["close_time"] = pd.to_datetime(frame["close_time"], utc=True)
        result = event_study(symbol, frame, int(report["final_oos"]["start_index"]), int(report["final_oos"]["end_index"]), strategy_cfg)
        path = out_dir / f"{symbol}-{TIMEFRAME}-event-study.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        event_index[symbol] = str(path)
    pooling = hierarchical_trade_diagnostic()
    (out_dir / "hierarchical-trade-diagnostic.json").write_text(json.dumps(pooling, indent=2), encoding="utf-8")
    (out_dir / "index.json").write_text(json.dumps({"event_studies": event_index, "hierarchical_trade_diagnostic": str(out_dir / "hierarchical-trade-diagnostic.json")}, indent=2), encoding="utf-8")
    print(json.dumps({"event_studies": event_index, "hierarchical": str(out_dir / "hierarchical-trade-diagnostic.json")}, indent=2))


if __name__ == "__main__":
    main()
