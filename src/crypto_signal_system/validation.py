from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

import pandas as pd

from crypto_signal_system.backtest import BacktestSummary, run_backtest
from crypto_signal_system.models import Candle


@dataclass(frozen=True)
class ValidationWindow:
    name: str
    start: str | None
    end: str | None
    summary: dict[str, Any]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    splits: tuple[ValidationWindow, ...]
    walk_forward: tuple[ValidationWindow, ...]
    sensitivity: tuple[dict[str, Any], ...]
    acceptance_thresholds: dict[str, Any]
    rejected: bool
    rejection_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "splits": [item.to_dict() for item in self.splits],
            "walk_forward": [item.to_dict() for item in self.walk_forward],
            "sensitivity": list(self.sensitivity),
            "acceptance_thresholds": self.acceptance_thresholds,
            "rejected": self.rejected,
            "rejection_reasons": list(self.rejection_reasons),
        }


def _window(name: str, candles: list[Candle], config: dict[str, Any], minimum_trades: int, flow_frame: pd.DataFrame | None = None) -> ValidationWindow:
    if not candles:
        return ValidationWindow(name, None, None, BacktestSummary(0, 0, None, None, None, None, None, 0, 0, 0, 0, None, None, ("No data in window.",)).to_dict(), ("empty window",))
    _, summary = run_backtest(candles, config, flow_frame=flow_frame)
    warnings = list(summary.notes)
    if summary.trades < minimum_trades:
        warnings.append(f"trade count {summary.trades} below minimum review threshold {minimum_trades}")
    return ValidationWindow(name, candles[0].open_time.isoformat(), candles[-1].close_time.isoformat(), summary.to_dict(), tuple(warnings))


def split_candles(candles: list[Candle], train_fraction: float, validation_fraction: float) -> tuple[list[Candle], list[Candle], list[Candle]]:
    ordered = sorted(candles, key=lambda item: item.open_time)
    n = len(ordered)
    train_end = int(n * train_fraction)
    validation_end = train_end + int(n * validation_fraction)
    return ordered[:train_end], ordered[train_end:validation_end], ordered[validation_end:]


def run_validation(candles: list[Candle], config: dict[str, Any], flow_frame: pd.DataFrame | None = None) -> ValidationReport:
    train, validation, test = split_candles(candles, float(config["backtest"]["train_fraction"]), float(config["backtest"]["validation_fraction"]))
    minimum = int(config["backtest"]["minimum_trades_for_review"])
    splits = (
        _window("research_train", train, config, minimum, flow_frame),
        _window("validation", validation, config, minimum, flow_frame),
        _window("untouched_out_of_sample_test", test, config, minimum, flow_frame),
    )
    walk_forward: list[ValidationWindow] = []
    if len(candles) >= 200:
        window = max(100, len(candles) // 4)
        for index, start in enumerate(range(0, len(candles) - window + 1, window // 2)):
            walk_forward.append(_window(f"walk_forward_{index + 1}", candles[start : start + window], config, minimum, flow_frame))
    sensitivity: list[dict[str, Any]] = []
    baseline = config["strategies"]["trend_pullback"].get("pullback_tolerance_atr", 0.75)
    for tolerance in (max(0.25, baseline - 0.25), baseline, baseline + 0.25):
        altered = {**config, "strategies": {**config["strategies"], "trend_pullback": {**config["strategies"]["trend_pullback"], "pullback_tolerance_atr": tolerance}}}
        _, summary = run_backtest(test, altered, flow_frame=flow_frame)
        sensitivity.append({"parameter": "trend_pullback.pullback_tolerance_atr", "value": tolerance, "out_of_sample_summary": summary.to_dict()})
    rejection_reasons: list[str] = []
    oos = splits[-1].summary
    if oos["trades"] < minimum:
        rejection_reasons.append("untouched out-of-sample trade count is below the review threshold")
    if oos["average_r"] is not None and oos["average_r"] <= 0:
        rejection_reasons.append("untouched out-of-sample average R is non-positive")
    return ValidationReport(tuple(splits), tuple(walk_forward), tuple(sensitivity), {"minimum_out_of_sample_trades": minimum, "minimum_average_r": 0.0}, bool(rejection_reasons), tuple(rejection_reasons))
