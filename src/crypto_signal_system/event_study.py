from __future__ import annotations

from dataclasses import asdict, dataclass
from random import Random
from typing import Any

import pandas as pd

from crypto_signal_system.features import add_features
from crypto_signal_system.models import Candle


@dataclass(frozen=True)
class SweepEvent:
    index: int
    direction: str
    event_time: str
    close: float
    atr: float
    structure_bias: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _bootstrap_mean(values: list[float], iterations: int = 5000, seed: int = 20260819) -> dict[str, float | int | None]:
    if not values:
        return {"mean": None, "p05": None, "p50": None, "p95": None, "iterations": 0}
    rng = Random(seed)
    means: list[float] = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    return {"mean": sum(values) / len(values), "p05": _quantile(means, 0.05), "p50": _quantile(means, 0.50), "p95": _quantile(means, 0.95), "iterations": iterations}


def _bootstrap_difference(event_values: list[float], control_values: list[float], iterations: int = 5000, seed: int = 20260819) -> dict[str, float | int | None]:
    if not event_values or not control_values:
        return {"mean_difference": None, "p05": None, "p50": None, "p95": None, "iterations": 0}
    rng = Random(seed)
    differences: list[float] = []
    for _ in range(iterations):
        event_sample = [event_values[rng.randrange(len(event_values))] for _ in event_values]
        control_sample = [control_values[rng.randrange(len(control_values))] for _ in control_values]
        differences.append((sum(event_sample) / len(event_sample)) - (sum(control_sample) / len(control_sample)))
    observed = (sum(event_values) / len(event_values)) - (sum(control_values) / len(control_values))
    return {"mean_difference": observed, "p05": _quantile(differences, 0.05), "p50": _quantile(differences, 0.50), "p95": _quantile(differences, 0.95), "iterations": iterations}


def _strict_events(frame: pd.DataFrame, config: dict[str, Any]) -> list[SweepEvent]:
    sweep_cfg = config.get("strategies", {}).get("liquidity_sweep_reclaim", {})
    displacement_min = float(sweep_cfg.get("minimum_displacement_atr", 1.25))
    volume_min = float(sweep_cfg.get("minimum_volume_ratio", 1.25))
    close = frame["close"]
    open_ = frame["open"]
    volume_ratio = frame["volume_ratio"]
    prior = frame.shift(1)
    prior_low = frame["prior_swing_low"].shift(1)
    prior_high = frame["prior_swing_high"].shift(1)
    bull = prior["bullish_liquidity_sweep"] & (frame["structure_bias"] >= 0) & (frame["displacement"] >= displacement_min) & (close > open_) & (close > close.shift(1)) & (close > prior_low) & (volume_ratio >= volume_min)
    bear = prior["bearish_liquidity_sweep"] & (frame["structure_bias"] <= 0) & (frame["displacement"] >= displacement_min) & (close < open_) & (close < close.shift(1)) & (close < prior_high) & (volume_ratio >= volume_min)
    events: list[SweepEvent] = []
    for index in frame.index[bull.fillna(False) | bear.fillna(False)]:
        index = int(index)
        direction = "LONG" if bool(bull.loc[index]) else "SHORT"
        row = frame.loc[index]
        if index < 80 or pd.isna(row["atr"]):
            continue
        events.append(SweepEvent(index, direction, pd.Timestamp(row["close_time"]).isoformat(), float(row["close"]), float(row["atr"]), int(row["structure_bias"])))
    return events


def _directed_forward_return(frame: pd.DataFrame, index: int, horizon: int, direction: str) -> tuple[float | None, float | None]:
    target = index + horizon
    if target >= len(frame):
        return None, None
    start = float(frame.iloc[index]["close"])
    end = float(frame.iloc[target]["close"])
    raw = (end / start - 1.0) * (1.0 if direction == "LONG" else -1.0)
    atr_fraction = float(frame.iloc[index]["atr"]) / start if start > 0 and not pd.isna(frame.iloc[index]["atr"]) else None
    normalized = raw / (atr_fraction * (horizon ** 0.5)) if atr_fraction and atr_fraction > 0 else None
    return raw, normalized


def _control_indices(frame: pd.DataFrame, events: list[SweepEvent]) -> list[int]:
    event_indices = {event.index for event in events}
    eligible: list[int] = []
    for index in range(80, len(frame)):
        if index in event_indices:
            continue
        row = frame.iloc[index]
        if pd.isna(row["atr"]) or int(row["structure_bias"]) == 0:
            continue
        eligible.append(index)
    return eligible


def run_liquidity_sweep_event_study(candles: list[Candle], config: dict[str, Any], horizons: tuple[int, ...] = (1, 3, 6, 12)) -> dict[str, Any]:
    ordered = sorted(candles, key=lambda item: item.open_time)
    frame = add_features(pd.DataFrame([c.to_dict() for c in ordered]))
    if frame.empty:
        return {"status": "insufficient_data", "events": 0, "controls": 0}
    events = _strict_events(frame, config)
    controls = _control_indices(frame, events)
    rows: list[dict[str, Any]] = []
    for event in events:
        row: dict[str, Any] = {"index": event.index, "direction": event.direction, "event_time": event.event_time}
        for horizon in horizons:
            raw, normalized = _directed_forward_return(frame, event.index, horizon, event.direction)
            row[f"h{horizon}_return"] = raw
            row[f"h{horizon}_normalized"] = normalized
        rows.append(row)
    control_rows: list[dict[str, Any]] = []
    for index in controls:
        direction = "LONG" if int(frame.iloc[index]["structure_bias"]) > 0 else "SHORT"
        row = {"index": index, "direction": direction}
        for horizon in horizons:
            raw, normalized = _directed_forward_return(frame, index, horizon, direction)
            row[f"h{horizon}_return"] = raw
            row[f"h{horizon}_normalized"] = normalized
        control_rows.append(row)
    horizon_results: dict[str, Any] = {}
    for horizon in horizons:
        event_returns = [float(row[f"h{horizon}_return"]) for row in rows if row.get(f"h{horizon}_return") is not None]
        event_normalized = [float(row[f"h{horizon}_normalized"]) for row in rows if row.get(f"h{horizon}_normalized") is not None]
        control_returns = [float(row[f"h{horizon}_return"]) for row in control_rows if row.get(f"h{horizon}_return") is not None]
        control_normalized = [float(row[f"h{horizon}_normalized"]) for row in control_rows if row.get(f"h{horizon}_normalized") is not None]
        effect = ((sum(event_returns) / len(event_returns)) - (sum(control_returns) / len(control_returns))) if event_returns and control_returns else None
        difference_bootstrap = _bootstrap_difference(event_returns, control_returns)
        minimum_events = 30
        horizon_results[str(horizon)] = {
            "event_count": len(event_returns),
            "control_count": len(control_returns),
            "event_mean_return_bps": (sum(event_returns) / len(event_returns) * 10_000) if event_returns else None,
            "control_mean_return_bps": (sum(control_returns) / len(control_returns) * 10_000) if control_returns else None,
            "event_minus_control_bps": effect * 10_000 if effect is not None else None,
            "event_hit_rate": (sum(value > 0 for value in event_returns) / len(event_returns)) if event_returns else None,
            "control_hit_rate": (sum(value > 0 for value in control_returns) / len(control_returns)) if control_returns else None,
            "event_return_bootstrap": _bootstrap_mean(event_returns),
            "event_normalized_bootstrap": _bootstrap_mean(event_normalized),
            "control_return_bootstrap": _bootstrap_mean(control_returns),
            "control_normalized_bootstrap": _bootstrap_mean(control_normalized),
            "event_minus_control_bootstrap": difference_bootstrap,
            "economic_threshold_bps": 5.0,
            "minimum_event_count": minimum_events,
            "minimum_control_count": minimum_events,
            "meaningful_by_preregistered_rule": bool(
                len(event_returns) >= minimum_events
                and len(control_returns) >= minimum_events
                and effect is not None
                and effect * 10_000 > 5.0
                and difference_bootstrap["p05"] is not None
                and difference_bootstrap["p05"] > 0
            ),
        }
    meaningful = any(item["meaningful_by_preregistered_rule"] for item in horizon_results.values())
    return {
        "status": "completed",
        "period_start": ordered[0].open_time.isoformat(),
        "period_end": ordered[-1].close_time.isoformat(),
        "observations": len(ordered),
        "event_definition": "Existing strict two-bar liquidity-sweep-reclaim prefilter; no trading simulation.",
        "event_count": len(events),
        "long_events": sum(event.direction == "LONG" for event in events),
        "short_events": sum(event.direction == "SHORT" for event in events),
        "control_count": len(controls),
        "horizons_bars": list(horizons),
        "horizon_results": horizon_results,
        "economically_meaningful_event_found": meaningful,
        "strategy_construction_status": "not_constructed",
        "events": [event.to_dict() for event in events],
        "event_rows": rows,
        "control_rows": control_rows,
        "interpretation_rule": "No strategy is built unless an event horizon passes the pre-registered economic and bootstrap rules; one passing horizon is still a hypothesis, not deployment evidence.",
    }
