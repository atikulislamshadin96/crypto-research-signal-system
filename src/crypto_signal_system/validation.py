from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from itertools import combinations
from random import Random
from typing import Any

import pandas as pd

from crypto_signal_system.backtest import BacktestSummary, Trade, run_backtest
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


def _empty_summary(note: str = "No data in window.") -> dict[str, Any]:
    return BacktestSummary(0, 0, None, None, None, None, 0.0, 0, 0, 0, 0, None, None, (note,)).to_dict()


def _window(
    name: str,
    candles: list[Candle],
    config: dict[str, Any],
    minimum_trades: int,
    flow_frame: pd.DataFrame | None = None,
    evaluation_windows: list[tuple[int, int]] | None = None,
) -> ValidationWindow:
    if not candles:
        return ValidationWindow(name, None, None, _empty_summary(), ("empty window",))
    _, summary = run_backtest(candles, config, flow_frame=flow_frame, evaluation_windows=evaluation_windows)
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
        for index, start in enumerate(range(0, len(candles) - window + 1, max(1, window // 2))):
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


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def bootstrap_expectancy(trades: list[Trade], iterations: int = 5000, seed: int = 20260819) -> dict[str, Any]:
    values = [float(trade.r_multiple) for trade in trades]
    if not values:
        return {"trades": 0, "iterations": 0, "mean_r": None, "p05_r": None, "p50_r": None, "p95_r": None}
    rng = Random(seed)
    means: list[float] = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    return {
        "trades": len(values),
        "iterations": iterations,
        "mean_r": sum(values) / len(values),
        "p05_r": _quantile(means, 0.05),
        "p50_r": _quantile(means, 0.50),
        "p95_r": _quantile(means, 0.95),
        "method": "iid bootstrap of observed trade R multiples; not a substitute for independent market data",
    }


def prop_firm_drawdown_simulation(
    trades: list[Trade],
    config: dict[str, Any],
) -> dict[str, Any]:
    settings = config.get("backtest", {}).get("prop_firm", {})
    starting_equity = float(settings.get("starting_equity", 100_000.0))
    risk_rate = float(settings.get("risk_per_trade_percent", 0.25)) / 100.0
    daily_limit = float(settings.get("daily_loss_limit_percent", 5.0)) / 100.0
    total_limit = float(settings.get("total_drawdown_limit_percent", 10.0)) / 100.0
    max_daily_trades = int(settings.get("max_daily_trades", 3))
    cooldown_losses = int(settings.get("max_consecutive_losses", 3))
    cooldown_minutes = int(settings.get("cooldown_minutes", 720))
    equity = starting_equity
    peak = starting_equity
    max_dd = 0.0
    applied = 0
    skipped = 0
    consecutive_losses = 0
    cooldown_until = None
    current_day = None
    day_start = starting_equity
    day_pnl = 0.0
    day_count = 0
    breach: dict[str, Any] | None = None
    for trade in sorted(trades, key=lambda item: item.entry_time):
        entry_time = pd.Timestamp(trade.entry_time).to_pydatetime()
        day = entry_time.date().isoformat()
        if day != current_day:
            current_day = day
            day_start = equity
            day_pnl = 0.0
            day_count = 0
        if breach is not None:
            skipped += 1
            continue
        if day_count >= max_daily_trades or (cooldown_until is not None and entry_time < cooldown_until):
            skipped += 1
            continue
        pnl = equity * risk_rate * float(trade.r_multiple)
        equity += pnl
        day_pnl += pnl
        day_count += 1
        applied += 1
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak else 0.0
        max_dd = max(max_dd, dd)
        if trade.r_multiple < 0:
            consecutive_losses += 1
        else:
            consecutive_losses = 0
        if consecutive_losses >= cooldown_losses:
            cooldown_until = entry_time + pd.Timedelta(minutes=cooldown_minutes).to_pytimedelta()
            consecutive_losses = 0
        if day_pnl <= -day_start * daily_limit:
            breach = {"type": "daily_loss_limit", "time": trade.entry_time, "drawdown_percent": abs(day_pnl) / day_start * 100}
        elif dd >= total_limit:
            breach = {"type": "total_drawdown_limit", "time": trade.entry_time, "drawdown_percent": dd * 100}
    return {
        "starting_equity": starting_equity,
        "ending_equity": equity,
        "return_percent": (equity / starting_equity - 1) * 100,
        "applied_trades": applied,
        "skipped_trades": skipped,
        "maximum_drawdown_percent": max_dd * 100,
        "breach": breach,
        "survived_full_ledger": breach is None,
        "rules": {
            "risk_per_trade_percent": risk_rate * 100,
            "daily_loss_limit_percent": daily_limit * 100,
            "total_drawdown_limit_percent": total_limit * 100,
            "max_daily_trades": max_daily_trades,
            "cooldown_losses": cooldown_losses,
            "cooldown_minutes": cooldown_minutes,
        },
    }


def _cost_config(config: dict[str, Any], cost_bps: float | None) -> dict[str, Any]:
    altered = deepcopy(config)
    if cost_bps is None:
        altered["backtest"].pop("execution_cost_bps", None)
    else:
        altered["backtest"]["execution_cost_bps"] = float(cost_bps)
    return altered


def _index_windows(n: int, count: int, warmup: int = 80) -> list[tuple[int, int]]:
    if n <= warmup or count <= 0:
        return []
    usable = n - warmup
    windows: list[tuple[int, int]] = []
    for i in range(count):
        start = warmup + (usable * i) // count
        end = warmup + (usable * (i + 1)) // count
        if end > start:
            windows.append((start, end))
    return windows


def _summary_payload(trades: list[Trade], summary: BacktestSummary, config: dict[str, Any]) -> dict[str, Any]:
    risk_rate = float(config.get("risk", {}).get("risk_per_trade_percent", 0.25)) / 100.0
    uncertainty = bootstrap_expectancy(trades)
    return {
        "summary": summary.to_dict(),
        "trade_count": len(trades),
        "uncertainty": uncertainty,
        "expectancy_equity_return_percent": (summary.average_r * risk_rate * 100) if summary.average_r is not None else None,
        "prop_firm": prop_firm_drawdown_simulation(trades, config),
    }


def _perturbation_configs(config: dict[str, Any]) -> list[tuple[str, Any, dict[str, Any]]]:
    protocol = config.get("backtest", {}).get("validation_protocol", {})
    values = protocol.get("perturbations", {})
    base = config["strategies"]["bos_retest_continuation"]
    variants: list[tuple[str, Any, dict[str, Any]]] = []
    for parameter, candidates in values.items():
        for value in candidates:
            altered = deepcopy(config)
            altered["strategies"]["bos_retest_continuation"][parameter] = value
            variants.append((parameter, value, altered))
    return variants


def _purged_cpcv(
    candles: list[Candle],
    config: dict[str, Any],
    groups: int,
    test_groups: int,
    purge_bars: int,
    embargo_bars: int,
) -> dict[str, Any]:
    boundaries = [int(len(candles) * i / groups) for i in range(groups + 1)]
    group_ranges = [(boundaries[i], boundaries[i + 1]) for i in range(groups)]
    paths: list[dict[str, Any]] = []
    for path_index, selected in enumerate(combinations(range(groups), test_groups), start=1):
        test_ranges = [group_ranges[index] for index in selected]
        test_indices = {index for start, end in test_ranges for index in range(start, end)}
        excluded_train = set(test_indices)
        for start, end in test_ranges:
            excluded_train.update(range(max(0, start - purge_bars), min(len(candles), end + embargo_bars)))
        train_count = len(candles) - len(excluded_train)
        run_config = _cost_config(config, None)
        trades, summary = run_backtest(candles, run_config, evaluation_windows=test_ranges)
        paths.append({
            "path": path_index,
            "test_groups": list(selected),
            "test_ranges": [list(item) for item in test_ranges],
            "purge_bars": purge_bars,
            "embargo_bars": embargo_bars,
            "train_observations_after_purge": train_count,
            **_summary_payload(trades, summary, run_config),
        })
    expectancy = [item["summary"]["average_r"] for item in paths if item["summary"]["average_r"] is not None]
    return {
        "groups": groups,
        "test_groups_per_path": test_groups,
        "path_count": len(paths),
        "paths_with_trades": len(expectancy),
        "purge_bars": purge_bars,
        "embargo_bars": embargo_bars,
        "expectancy_r_quantiles": {"p05": _quantile(expectancy, 0.05), "p50": _quantile(expectancy, 0.50), "p95": _quantile(expectancy, 0.95)},
        "positive_path_fraction": (sum(value > 0 for value in expectancy) / len(expectancy)) if expectancy else None,
        "paths": paths,
    }


def run_focused_validation(candles: list[Candle], config: dict[str, Any]) -> dict[str, Any]:
    """Run the frozen BOS validation protocol without selecting a winning variant."""
    ordered = sorted(candles, key=lambda item: item.open_time)
    protocol = config.get("backtest", {}).get("validation_protocol", {})
    cost_values = [float(value) for value in protocol.get("costs_bps", [5, 10, 15])]
    windows = _index_windows(len(ordered), int(protocol.get("oos_windows", 8)))
    if not windows:
        return {"status": "insufficient_data", "observations": len(ordered), "message": "Not enough observations for the frozen protocol."}
    baseline_config = _cost_config(config, None)
    full_trades, full_summary = run_backtest(ordered, baseline_config)
    test_start = int(len(ordered) * (float(config["backtest"].get("train_fraction", 0.50)) + float(config["backtest"].get("validation_fraction", 0.25))))
    final_oos_range = (test_start, len(ordered))
    cost_stress: dict[str, Any] = {}
    for cost in cost_values:
        cost_config = _cost_config(config, cost)
        trades, summary = run_backtest(ordered, cost_config, evaluation_windows=[final_oos_range])
        cost_stress[str(int(cost)) + "bps"] = _summary_payload(trades, summary, cost_config)
    walk_forward: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(windows, start=1):
        trades, summary = run_backtest(ordered, baseline_config, evaluation_windows=[(start, end)])
        walk_forward.append({"window": index, "start_index": start, "end_index": end, **_summary_payload(trades, summary, baseline_config)})
    final_start, final_end = windows[-1]
    terminal_trades, terminal_summary = run_backtest(ordered, baseline_config, evaluation_windows=[(final_start, final_end)])
    final_trades, final_summary = run_backtest(ordered, baseline_config, evaluation_windows=[final_oos_range])
    cpcv = _purged_cpcv(
        ordered,
        baseline_config,
        int(protocol.get("cpcv_groups", 8)),
        int(protocol.get("cpcv_test_groups", 2)),
        int(protocol.get("purge_bars", 8)),
        int(protocol.get("embargo_bars", 1)),
    )
    perturbations: list[dict[str, Any]] = []
    for parameter, value, altered in _perturbation_configs(config):
        trades, summary = run_backtest(ordered, _cost_config(altered, None), evaluation_windows=[(final_start, final_end)])
        perturbations.append({"parameter": parameter, "value": value, **_summary_payload(trades, summary, _cost_config(altered, None))})
    risk_rate = float(config.get("risk", {}).get("risk_per_trade_percent", 0.25)) / 100.0
    cpcv_p50_equity_return = (cpcv["expectancy_r_quantiles"]["p50"] * risk_rate) if cpcv["expectancy_r_quantiles"]["p50"] is not None else None
    negative_windows = sum((item["summary"]["average_r"] is not None and item["summary"]["average_r"] < 0) for item in walk_forward)
    reasons: list[str] = []
    min_equity_return = 0.0005
    if cpcv_p50_equity_return is None or cpcv_p50_equity_return < min_equity_return:
        reasons.append("purged CPCV P50 expectancy is below +0.05% of equity at the frozen risk rate")
    if negative_windows >= 4:
        reasons.append(f"{negative_windows} of {len(walk_forward)} walk-forward windows have negative expectancy")
    minimum_oos_trades = int(config["backtest"].get("minimum_trades_for_review", 30))
    if final_summary.trades < minimum_oos_trades:
        reasons.append(f"final untouched OOS trade count {final_summary.trades} is below the review threshold {minimum_oos_trades}")
    if final_summary.win_rate is None or final_summary.win_rate < 0.45:
        reasons.append("final untouched OOS win rate is below 45%")
    if final_summary.profit_factor is None or final_summary.profit_factor < 1.20:
        reasons.append("final untouched OOS profit factor is below 1.20")
    if final_oos_payload := _summary_payload(final_trades, final_summary, baseline_config):
        if final_oos_payload["uncertainty"]["p05_r"] is None or final_oos_payload["uncertainty"]["p05_r"] <= 0:
            reasons.append("final untouched OOS bootstrap 5th-percentile expectancy is non-positive")
    if not all(item["prop_firm"]["survived_full_ledger"] for item in [cost_stress[key] for key in cost_stress]):
        reasons.append("at least one cost-stress ledger breaches the frozen prop-firm drawdown limits")
    return {
        "status": "completed",
        "observations": len(ordered),
        "period_start": ordered[0].open_time.isoformat(),
        "period_end": ordered[-1].close_time.isoformat(),
        "baseline": _summary_payload(full_trades, full_summary, baseline_config),
        "cost_stress": cost_stress,
        "walk_forward": walk_forward,
        "walk_forward_negative_windows": negative_windows,
        "final_oos": {"start_index": test_start, "end_index": len(ordered), **_summary_payload(final_trades, final_summary, baseline_config)},
        "terminal_walk_forward_oos": {"start_index": final_start, "end_index": final_end, **_summary_payload(terminal_trades, terminal_summary, baseline_config)},
        "purged_cpcv": cpcv,
        "parameter_perturbation": perturbations,
        "acceptance_thresholds": {
            "cpcv_p50_min_equity_return_per_trade": min_equity_return,
            "walk_forward_negative_window_limit": 3,
            "minimum_oos_trades_for_review": minimum_oos_trades,
            "minimum_win_rate": 0.45,
            "minimum_profit_factor": 1.20,
            "bootstrap_p05_expectancy_minimum": 0.0,
        },
        "rejected": bool(reasons),
        "rejection_reasons": reasons,
        "flow_filter_status": "frozen_rejected_disabled",
        "tuning_policy": "No parameter selection after final OOS; perturbations are reported, not optimized.",
    }
