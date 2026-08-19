"""Pre-registered HL↔dYdX funding-divergence event study.

This module measures events only. It never constructs positions or emits orders.
The primary threshold is fixed from the training segment and the economic gate
is deliberately stringent; underpowered samples remain inconclusive.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

import pandas as pd

REQUIRED_FUNDING_COLUMNS = {"timestamp", "asset", "venue", "funding_rate"}
REQUIRED_PRICE_COLUMNS = {"timestamp", "asset", "close"}
VENUES = {"hyperliquid", "dydx"}
PRIMARY_HORIZON_HOURS = 8
FORWARD_HORIZONS_HOURS = (4, 8, 24)
COST_STRESS_BPS = (5, 10, 15)
MIN_EVENTS_PER_TAIL = 50


@dataclass(frozen=True)
class FundingProtocol:
    universe: tuple[str, ...] = ("BTC", "ETH")
    primary_horizon_hours: int = PRIMARY_HORIZON_HOURS
    train_fraction: float = 0.60
    tail_quantile: float = 0.05
    min_separation_hours: int = 24
    required_events_per_tail: int = MIN_EVENTS_PER_TAIL
    cost_stress_bps: tuple[int, ...] = COST_STRESS_BPS


class FundingStudyError(ValueError):
    pass


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise FundingStudyError(f"{name} missing required columns: {missing}")


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        raise FundingStudyError("training segment has no usable divergence observations")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round(probability * (len(ordered) - 1)))))
    return float(ordered[index])


def _bootstrap_ci(values: list[float], seed: int = 20260819, draws: int = 2000) -> tuple[float | None, float | None]:
    if len(values) < 2:
        return None, None
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(draws):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    return means[int(0.025 * (len(means) - 1))], means[int(0.975 * (len(means) - 1))]


def _non_overlapping_events(index: pd.DatetimeIndex, separation_hours: int) -> list[int]:
    selected: list[int] = []
    last: pd.Timestamp | None = None
    for position, timestamp in enumerate(index):
        if last is None or (timestamp - last).total_seconds() >= separation_hours * 3600:
            selected.append(position)
            last = timestamp
    return selected


def _forward_return(prices: pd.Series, timestamp: pd.Timestamp, horizon_hours: int) -> float | None:
    target = timestamp + pd.to_timedelta(int(horizon_hours), unit="h")
    future = prices[prices.index >= target]
    if future.empty:
        return None
    current = prices[prices.index <= timestamp]
    if current.empty or current.iloc[-1] == 0:
        return None
    return float(future.iloc[0] / current.iloc[-1] - 1.0)


def _asset_study(funding: pd.DataFrame, prices: pd.DataFrame, asset: str, protocol: FundingProtocol) -> dict[str, Any]:
    asset_funding = funding[funding["asset"] == asset].copy()
    asset_prices = prices[prices["asset"] == asset].copy()
    if asset_funding.empty or asset_prices.empty:
        return {"asset": asset, "status": "inconclusive", "reason": "missing common-history funding or price data"}
    pivot = asset_funding.pivot_table(index="timestamp", columns="venue", values="funding_rate", aggfunc="last").sort_index()
    if not VENUES.issubset(set(pivot.columns)):
        return {"asset": asset, "status": "inconclusive", "reason": "both Hyperliquid and dYdX are required"}
    pivot = pivot.dropna(subset=["hyperliquid", "dydx"])
    pivot["d4h"] = pivot["hyperliquid"].rolling(4, min_periods=4).sum() - pivot["dydx"].rolling(4, min_periods=4).sum()
    pivot["d8h"] = pivot["hyperliquid"].rolling(8, min_periods=8).sum() - pivot["dydx"].rolling(8, min_periods=8).sum()
    pivot = pivot.dropna(subset=["d4h", "d8h"])
    if len(pivot) < 20:
        return {"asset": asset, "status": "inconclusive", "reason": "fewer than 20 aligned hourly observations", "aligned_observations": int(len(pivot))}

    split = max(1, min(len(pivot) - 1, int(len(pivot) * protocol.train_fraction)))
    train = pivot.iloc[:split]
    validation = pivot.iloc[split:]
    upper = _quantile(train["d8h"].tolist(), 1.0 - protocol.tail_quantile)
    lower = _quantile(train["d8h"].tolist(), protocol.tail_quantile)
    price_series = asset_prices.set_index("timestamp")["close"].sort_index()
    rows: list[dict[str, Any]] = []
    for label, mask in (("positive", validation["d8h"] >= upper), ("negative", validation["d8h"] <= lower)):
        selected = validation[mask]
        selected_positions = _non_overlapping_events(selected.index, protocol.min_separation_hours)
        selected = selected.iloc[selected_positions]
        for timestamp in selected.index:
            outcomes = {f"forward_return_{hours}h": _forward_return(price_series, timestamp, hours) for hours in FORWARD_HORIZONS_HOURS}
            row = {"asset": asset, "event": label, "timestamp": timestamp.isoformat(), "d8h": float(validation.loc[timestamp, "d8h"]), **outcomes}
            rows.append(row)

    event_frame = pd.DataFrame(rows)
    result: dict[str, Any] = {
        "asset": asset,
        "status": "inconclusive",
        "aligned_observations": int(len(pivot)),
        "train_observations": int(len(train)),
        "validation_observations": int(len(validation)),
        "upper_threshold": upper,
        "lower_threshold": lower,
        "event_count_positive": int((event_frame["event"] == "positive").sum()) if not event_frame.empty else 0,
        "event_count_negative": int((event_frame["event"] == "negative").sum()) if not event_frame.empty else 0,
        "required_events_per_tail": protocol.required_events_per_tail,
        "primary_horizon_hours": protocol.primary_horizon_hours,
        "cost_stress_bps": list(protocol.cost_stress_bps),
        "strategy_constructed": False,
    }
    if event_frame.empty:
        result["reason"] = "no non-overlapping tail events in untouched validation segment"
        return result

    primary = f"forward_return_{protocol.primary_horizon_hours}h"
    positive = event_frame.loc[event_frame["event"] == "positive", primary].dropna().tolist()
    negative = event_frame.loc[event_frame["event"] == "negative", primary].dropna().tolist()
    result["positive_primary_mean"] = sum(positive) / len(positive) if positive else None
    result["negative_primary_mean"] = sum(negative) / len(negative) if negative else None
    result["positive_bootstrap_ci"] = _bootstrap_ci(positive)
    result["negative_bootstrap_ci"] = _bootstrap_ci(negative)
    result["cost_stress_net_positive_mean"] = {
        str(bps): (sum(positive) / len(positive) - 2.0 * bps / 10000.0) if positive else None for bps in protocol.cost_stress_bps
    }
    if len(positive) < protocol.required_events_per_tail or len(negative) < protocol.required_events_per_tail:
        result["reason"] = "underpowered: minimum positive and negative non-overlapping event counts not met"
        return result
    gross = result["positive_primary_mean"]
    lower_ci = result["positive_bootstrap_ci"][0] if result["positive_bootstrap_ci"] else None
    economically_positive = gross is not None and lower_ci is not None and gross - 2.0 * 15 / 10000.0 > 0.0005 and lower_ci > 0
    result["status"] = "passed_event_gate" if economically_positive else "rejected_event_gate"
    result["reason"] = "event gate evaluated under frozen protocol; no strategy construction"
    return result


def run_funding_divergence_event_study(
    funding: pd.DataFrame,
    prices: pd.DataFrame,
    protocol: FundingProtocol | None = None,
) -> dict[str, Any]:
    protocol = protocol or FundingProtocol()
    _require_columns(funding, REQUIRED_FUNDING_COLUMNS, "funding")
    _require_columns(prices, REQUIRED_PRICE_COLUMNS, "prices")
    funding = funding.copy()
    prices = prices.copy()
    funding["timestamp"] = pd.to_datetime(funding["timestamp"], utc=True, errors="coerce")
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True, errors="coerce")
    funding["venue"] = funding["venue"].str.lower()
    funding["funding_rate"] = pd.to_numeric(funding["funding_rate"], errors="coerce")
    prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
    if funding["timestamp"].isna().any() or prices["timestamp"].isna().any() or funding["funding_rate"].isna().any() or prices["close"].isna().any():
        raise FundingStudyError("invalid timestamps or numeric values; fail closed")
    funding = funding[funding["venue"].isin(VENUES)].copy()
    results = [_asset_study(funding, prices, asset, protocol) for asset in protocol.universe]
    return {
        "protocol": {
            "universe": list(protocol.universe),
            "primary_horizon_hours": protocol.primary_horizon_hours,
            "train_fraction": protocol.train_fraction,
            "tail_quantile": protocol.tail_quantile,
            "min_separation_hours": protocol.min_separation_hours,
            "required_events_per_tail": protocol.required_events_per_tail,
            "cost_stress_bps": list(protocol.cost_stress_bps),
        },
        "analysis_only": True,
        "strategy_constructed": False,
        "results": results,
    }
