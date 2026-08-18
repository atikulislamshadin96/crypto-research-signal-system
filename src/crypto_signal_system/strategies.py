from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from crypto_signal_system.models import Candidate, Evidence


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _last(frame: pd.DataFrame) -> pd.Series:
    return frame.iloc[-1]


def _candidate_base(symbol: str, strategy: str, direction: str, frame: pd.DataFrame, thesis: str, regime: str, structure: str, trigger: str, assumptions: list[str]) -> Candidate:
    row = _last(frame)
    generated_at = row["close_time"]
    if hasattr(generated_at, "to_pydatetime"):
        generated_at = generated_at.to_pydatetime()
    atr = float(row["atr"])
    close = float(row["close"])
    if direction == "LONG":
        stop = close - 1.5 * atr
        targets = [close + 2.25 * atr, close + 3.0 * atr]
    else:
        stop = close + 1.5 * atr
        targets = [close - 2.25 * atr, close - 3.0 * atr]
    return Candidate(
        symbol=symbol,
        direction=direction,
        strategy=strategy,
        generated_at=generated_at,
        entry_low=close - 0.10 * atr,
        entry_high=close + 0.10 * atr,
        stop_loss=stop,
        take_profit=targets,
        invalidation=f"A closed candle beyond the {1.5:.1f} ATR protective stop invalidates the setup.",
        expiry=generated_at + timedelta(hours=12),
        thesis=thesis,
        regime=regime,
        structure=structure,
        trigger=trigger,
        assumptions=assumptions,
    )


def trend_pullback(symbol: str, frame: pd.DataFrame, config: dict[str, Any]) -> Candidate | None:
    if len(frame) < 60:
        return None
    row = _last(frame)
    if pd.isna(row["ema_fast"]) or pd.isna(row["ema_slow"]) or pd.isna(row["atr"]):
        return None
    close = float(row["close"])
    atr = float(row["atr"])
    trend_up = close > float(row["ema_slow"]) and float(row["ema_fast"]) > float(row["ema_slow"])
    trend_down = close < float(row["ema_slow"]) and float(row["ema_fast"]) < float(row["ema_slow"])
    near_fast = abs(close - float(row["ema_fast"])) <= config.get("pullback_tolerance_atr", 0.75) * atr
    if not near_fast:
        return None
    if trend_up and close > float(row["open"]):
        candidate = _candidate_base(symbol, "trend_pullback", "LONG", frame, "Price is above the slow trend filter and the latest candle reclaimed the fast trend average after a pullback.", "bullish", "fast EMA above slow EMA; pullback near fast EMA", "closed bullish reclaim candle", ["ATR stop multiplier is configured, not empirically calibrated."])
    elif trend_down and close < float(row["open"]):
        candidate = _candidate_base(symbol, "trend_pullback", "SHORT", frame, "Price is below the slow trend filter and the latest candle rejected the fast trend average after a pullback.", "bearish", "fast EMA below slow EMA; pullback near fast EMA", "closed bearish rejection candle", ["ATR stop multiplier is configured, not empirically calibrated."])
    else:
        return None
    candidate.evidence.extend([
        Evidence("regime", "EMA fast/slow alignment supports direction", True, "computed:EMA", row["close_time"], "inferred"),
        Evidence("structure", "Close is within configured ATR tolerance of fast EMA", True, "computed:EMA_ATR", row["close_time"], "inferred"),
    ])
    return candidate


def volatility_breakout(symbol: str, frame: pd.DataFrame, config: dict[str, Any]) -> Candidate | None:
    lookback = int(config.get("lookback", 20))
    if len(frame) < lookback + 20:
        return None
    row = _last(frame)
    prior = frame.iloc[-2]
    prior_high = float(frame["high"].iloc[-lookback-1:-1].max())
    prior_low = float(frame["low"].iloc[-lookback-1:-1].min())
    atr = float(row["atr"])
    close = float(row["close"])
    buffer = float(config.get("breakout_buffer_atr", 0.10)) * atr
    volume_confirmed = float(row["volume_ratio"]) >= 1.2
    if close > prior_high + buffer and volume_confirmed:
        candidate = _candidate_base(symbol, "volatility_breakout", "LONG", frame, "The latest closed candle broke above the prior rolling range with above-average volume.", "breakout", f"close above {lookback}-bar high", "range breakout with volume confirmation", ["Breakout persistence is not yet statistically calibrated."])
    elif close < prior_low - buffer and volume_confirmed:
        candidate = _candidate_base(symbol, "volatility_breakout", "SHORT", frame, "The latest closed candle broke below the prior rolling range with above-average volume.", "breakout", f"close below {lookback}-bar low", "range breakdown with volume confirmation", ["Breakout persistence is not yet statistically calibrated."])
    else:
        return None
    candidate.evidence.extend([
        Evidence("structure", "Closed price exceeded prior rolling boundary", close, "computed:rolling_range", row["close_time"], "inferred"),
        Evidence("volume", "Volume ratio exceeds 1.2", float(row["volume_ratio"]), "computed:volume_ratio", row["close_time"], "inferred"),
    ])
    return candidate


def range_mean_reversion(symbol: str, frame: pd.DataFrame, config: dict[str, Any]) -> Candidate | None:
    lookback = int(config.get("lookback", 40))
    if len(frame) < lookback + 20:
        return None
    window = frame.iloc[-lookback:]
    row = _last(frame)
    high = float(window["high"].max())
    low = float(window["low"].min())
    width = high - low
    atr = float(row["atr"])
    close = float(row["close"])
    if width <= 0 or width > 8 * atr:
        return None
    position = (close - low) / width
    boundary = float(config.get("boundary_percentile", 0.15))
    if position <= boundary and close > float(row["open"]):
        candidate = _candidate_base(symbol, "range_mean_reversion", "LONG", frame, "Price is near the lower boundary of a comparatively compact range and the latest candle rejected the boundary upward.", "range", "compact rolling range; lower boundary", "bullish rejection from range low", ["Range identity is a heuristic and not yet validated across regimes."])
    elif position >= 1 - boundary and close < float(row["open"]):
        candidate = _candidate_base(symbol, "range_mean_reversion", "SHORT", frame, "Price is near the upper boundary of a comparatively compact range and the latest candle rejected the boundary downward.", "range", "compact rolling range; upper boundary", "bearish rejection from range high", ["Range identity is a heuristic and not yet validated across regimes."])
    else:
        return None
    candidate.evidence.append(Evidence("structure", "Price is near an objectively computed range boundary", position, "computed:rolling_range", row["close_time"], "inferred"))
    return candidate


def liquidity_sweep_reclaim(symbol: str, frame: pd.DataFrame, config: dict[str, Any]) -> Candidate | None:
    if len(frame) < 60:
        return None
    row = _last(frame)
    atr = float(row["atr"])
    if pd.isna(row["structure_bias"]) or pd.isna(row["displacement"]):
        return None
    displacement_min = float(config.get("minimum_displacement_atr", 0.50))
    direction: str | None = None
    if bool(row["bullish_liquidity_sweep"]) and int(row["structure_bias"]) >= 0 and float(row["displacement"]) >= displacement_min and float(row["close"]) > float(row["open"]):
        direction = "LONG"
    elif bool(row["bearish_liquidity_sweep"]) and int(row["structure_bias"]) <= 0 and float(row["displacement"]) >= displacement_min and float(row["close"]) < float(row["open"]):
        direction = "SHORT"
    if direction is None:
        return None
    candidate = _candidate_base(symbol, "liquidity_sweep_reclaim", direction, frame, "The closed candle swept a prior liquidity boundary and reclaimed it with directional displacement.", "structure", "prior liquidity sweep with structure bias", "closed-bar sweep reclaim", ["Sweep and displacement thresholds are research defaults and require out-of-sample validation."])
    candidate.evidence.extend([
        Evidence("structure", "Prior liquidity boundary was swept and reclaimed", True, "computed:liquidity_sweep", row["close_time"], "inferred"),
        Evidence("momentum", "Displacement exceeds the configured ATR threshold", float(row["displacement"]), "computed:displacement_atr", row["close_time"], "inferred"),
    ])
    return candidate


def momentum_continuation(symbol: str, frame: pd.DataFrame, config: dict[str, Any]) -> Candidate | None:
    lookback = int(config.get("lookback", 12))
    if len(frame) < lookback + 20:
        return None
    row = _last(frame)
    return_n = float(row["return_n"])
    volume_ratio = float(row["volume_ratio"])
    if pd.isna(return_n) or pd.isna(volume_ratio) or volume_ratio < 1.3 or abs(return_n) < 0.01:
        return None
    direction = "LONG" if return_n > 0 else "SHORT"
    candidate = _candidate_base(symbol, "momentum_continuation", direction, frame, "Recent multi-bar price momentum is aligned with an above-average volume impulse.", "momentum", "directional multi-bar move", "momentum and volume continuation", ["Momentum threshold is a research default, not a profit probability."])
    candidate.evidence.extend([
        Evidence("momentum", f"{lookback}-bar return supports direction", return_n, "computed:return_n", row["close_time"], "inferred"),
        Evidence("volume", "Volume ratio exceeds 1.3", volume_ratio, "computed:volume_ratio", row["close_time"], "inferred"),
    ])
    return candidate


def generate_candidates(symbol: str, frame: pd.DataFrame, strategy_config: dict[str, Any]) -> list[Candidate]:
    candidates: list[Candidate] = []
    modules = [
        ("trend_pullback", trend_pullback),
        ("volatility_breakout", volatility_breakout),
        ("range_mean_reversion", range_mean_reversion),
        ("liquidity_sweep_reclaim", liquidity_sweep_reclaim),
        ("momentum_continuation", momentum_continuation),
    ]
    for name, module in modules:
        cfg = strategy_config.get(name, {})
        if not cfg.get("enabled", False):
            continue
        candidate = module(symbol, frame, cfg)
        if candidate:
            candidates.append(candidate)
    return candidates
