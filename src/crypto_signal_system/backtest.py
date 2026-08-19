from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_signal_system.features import add_features, add_trade_flow_features
from crypto_signal_system.context import attach_context, infer_frame_regime
from crypto_signal_system.models import Candle
from crypto_signal_system.strategies import generate_candidates
from crypto_signal_system.risk import build_risk_state, reward_risk
from crypto_signal_system.scoring import build_signal


@dataclass(frozen=True)
class Trade:
    symbol: str
    strategy: str
    direction: str
    entry_time: str
    entry: float
    stop: float
    target: float
    exit_time: str
    exit: float
    r_multiple: float
    gross_pnl: float
    fees: float
    slippage: float
    funding: float
    exit_reason: str


@dataclass(frozen=True)
class BacktestSummary:
    trades: int
    wins: int
    win_rate: float | None
    average_r: float | None
    expectancy_r: float | None
    profit_factor: float | None
    maximum_drawdown_percent: float | None
    longest_losing_streak: int
    fees_total: float
    funding_total: float
    slippage_total: float
    period_start: str | None
    period_end: str | None
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_ohlcv_csv(path: str | Path, symbol: str, timeframe: str, source: str = "user_csv") -> list[Candle]:
    frame = pd.read_csv(path)
    required = {"open_time", "close_time", "open", "high", "low", "close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")
    candles: list[Candle] = []
    for _, row in frame.iterrows():
        open_time = pd.to_datetime(row["open_time"], utc=True).to_pydatetime()
        close_time = pd.to_datetime(row["close_time"], utc=True).to_pydatetime()
        candles.append(Candle(symbol, timeframe, open_time, close_time, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row["volume"]), float(row.get("quote_volume", 0.0)), int(row.get("trades", 0)), source))
    return candles


def _simulate_candidate(candidate: Any, future: pd.DataFrame, config: dict[str, Any]) -> Trade | None:
    if candidate.entry_low is None or candidate.entry_high is None or candidate.stop_loss is None or not candidate.take_profit:
        return None
    entry = (candidate.entry_low + candidate.entry_high) / 2
    stop = candidate.stop_loss
    target = candidate.take_profit[0]
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    for _, bar in future.iterrows():
        hit_stop = float(bar["low"]) <= stop if candidate.direction == "LONG" else float(bar["high"]) >= stop
        hit_target = float(bar["high"]) >= target if candidate.direction == "LONG" else float(bar["low"]) <= target
        if hit_stop and hit_target:
            exit_price = stop
            reason = "stop_first_ambiguous_bar"
        elif hit_stop:
            exit_price = stop
            reason = "stop"
        elif hit_target:
            exit_price = target
            reason = "target"
        else:
            continue
        direction_sign = 1 if candidate.direction == "LONG" else -1
        gross = direction_sign * (exit_price - entry)
        notional = entry
        explicit_cost_bps = config["backtest"].get("execution_cost_bps")
        if explicit_cost_bps is not None:
            fee = 0.0
            slippage = notional * float(explicit_cost_bps) / 10_000.0
        else:
            fee = notional * float(config["backtest"]["taker_fee_rate"]) * 2
            slippage = notional * float(config["backtest"]["slippage_rate"])
        bar_close_time = pd.Timestamp(bar["close_time"]).to_pydatetime()
        holding_hours = max(0.0, (bar_close_time - candidate.generated_at).total_seconds() / 3600)
        funding = notional * float(config["backtest"]["funding_rate_per_8h"]) * (holding_hours / 8)
        net = gross - fee - slippage - funding
        return Trade(candidate.symbol, candidate.strategy, candidate.direction, candidate.generated_at.isoformat(), entry, stop, target, bar_close_time.isoformat(), exit_price, net / risk, gross, fee, slippage, funding, reason)
    return None


def summarize_trades(trades: list[Trade], starting_equity: float = 10_000.0) -> BacktestSummary:
    if not trades:
        return BacktestSummary(0, 0, None, None, None, None, 0.0, 0, 0.0, 0.0, 0.0, None, None, ("No trades were produced; no performance claim is made.",))
    rs = [trade.r_multiple for trade in trades]
    wins = [value for value in rs if value > 0]
    losses = [value for value in rs if value < 0]
    equity = starting_equity
    peak = equity
    max_dd = 0.0
    losing_streak = 0
    longest = 0
    for trade in trades:
        equity *= 1 + trade.r_multiple * 0.0025
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak * 100)
        if trade.r_multiple < 0:
            losing_streak += 1
            longest = max(longest, losing_streak)
        else:
            losing_streak = 0
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    return BacktestSummary(
        trades=len(trades),
        wins=len(wins),
        win_rate=len(wins) / len(trades),
        average_r=sum(rs) / len(rs),
        expectancy_r=sum(rs) / len(rs),
        profit_factor=(gross_profit / gross_loss) if gross_loss else None,
        maximum_drawdown_percent=max_dd,
        longest_losing_streak=longest,
        fees_total=sum(t.fees for t in trades),
        funding_total=sum(t.funding for t in trades),
        slippage_total=sum(t.slippage for t in trades),
        period_start=trades[0].entry_time,
        period_end=trades[-1].exit_time,
        notes=("Backtest is event-driven and uses closed-bar information only.", "Ambiguous bars are resolved stop-first; this is conservative but not a guarantee of real fills."),
    )


def _event_indices(frame: pd.DataFrame, strategies: dict[str, Any]) -> list[int]:
    """Return causal bars that can possibly emit an enabled strategy candidate."""
    masks: list[pd.Series] = []
    close = frame["close"]
    open_ = frame["open"]
    high = frame["high"]
    low = frame["low"]
    atr = frame["atr"]
    volume_ratio = frame["volume_ratio"]
    if strategies.get("trend_pullback", {}).get("enabled", False):
        cfg = strategies["trend_pullback"]
        tol = float(cfg.get("pullback_tolerance_atr", 0.75))
        up = (close > frame["ema_slow"]) & (frame["ema_fast"] > frame["ema_slow"]) & ((close - frame["ema_fast"]).abs() <= tol * atr) & (close > open_)
        down = (close < frame["ema_slow"]) & (frame["ema_fast"] < frame["ema_slow"]) & ((close - frame["ema_fast"]).abs() <= tol * atr) & (close < open_)
        masks.append(up | down)
    if strategies.get("volatility_breakout", {}).get("enabled", False):
        cfg = strategies["volatility_breakout"]
        lookback = int(cfg.get("lookback", 20))
        buffer = float(cfg.get("breakout_buffer_atr", 0.10)) * atr
        prior_high = high.shift(1).rolling(lookback, min_periods=lookback).max()
        prior_low = low.shift(1).rolling(lookback, min_periods=lookback).min()
        masks.append(((close > prior_high + buffer) | (close < prior_low - buffer)) & (volume_ratio >= 1.2))
    if strategies.get("range_mean_reversion", {}).get("enabled", False):
        cfg = strategies["range_mean_reversion"]
        lookback = int(cfg.get("lookback", 40))
        window_high = high.rolling(lookback, min_periods=lookback).max()
        window_low = low.rolling(lookback, min_periods=lookback).min()
        width = window_high - window_low
        position = (close - window_low) / width
        boundary = float(cfg.get("boundary_percentile", 0.15))
        masks.append((width > 0) & (width <= 8 * atr) & (((position <= boundary) & (close > open_)) | ((position >= 1 - boundary) & (close < open_))))
    if strategies.get("liquidity_sweep_reclaim", {}).get("enabled", False):
        cfg = strategies["liquidity_sweep_reclaim"]
        displacement_min = float(cfg.get("minimum_displacement_atr", 0.50))
        volume_min = float(cfg.get("minimum_volume_ratio", 1.0))
        prior = frame.shift(1)
        prior_low = frame["prior_swing_low"].shift(1)
        prior_high = frame["prior_swing_high"].shift(1)
        bull = prior["bullish_liquidity_sweep"] & (frame["structure_bias"] >= 0) & (frame["displacement"] >= displacement_min) & (close > open_) & (close > frame["close"].shift(1)) & (close > prior_low) & (volume_ratio >= volume_min)
        bear = prior["bearish_liquidity_sweep"] & (frame["structure_bias"] <= 0) & (frame["displacement"] >= displacement_min) & (close < open_) & (close < frame["close"].shift(1)) & (close < prior_high) & (volume_ratio >= volume_min)
        masks.append(bull | bear)
    if strategies.get("bos_retest_continuation", {}).get("enabled", False):
        cfg = strategies["bos_retest_continuation"]
        lookback = int(cfg.get("structure_lookback", 20))
        displacement_min = float(cfg.get("minimum_displacement_atr", 0.65))
        volume_min = float(cfg.get("minimum_volume_ratio", 1.1))
        prior_high = high.shift(2).rolling(lookback, min_periods=lookback).max()
        prior_low = low.shift(2).rolling(lookback, min_periods=lookback).min()
        prior_bull_bos = (close.shift(1) > prior_high) & (frame["displacement"].shift(1) >= displacement_min)
        prior_bear_bos = (close.shift(1) < prior_low) & (frame["displacement"].shift(1) >= displacement_min)
        tol = float(cfg.get("retest_tolerance_atr", 0.25)) * atr
        bull = prior_bull_bos & (low <= close.shift(1) + tol) & (close > close.shift(1)) & (close > open_) & (frame["structure_bias"] >= 0) & (volume_ratio >= volume_min)
        bear = prior_bear_bos & (high >= close.shift(1) - tol) & (close < close.shift(1)) & (close < open_) & (frame["structure_bias"] <= 0) & (volume_ratio >= volume_min)
        masks.append(bull | bear)
    if strategies.get("momentum_continuation", {}).get("enabled", False):
        cfg = strategies["momentum_continuation"]
        minimum_return = float(cfg.get("minimum_return", 0.01))
        masks.append((frame["return_n"].abs() >= minimum_return) & (volume_ratio >= 1.3))
    if not masks:
        return []
    combined = masks[0].fillna(False)
    for mask in masks[1:]:
        combined = combined | mask.fillna(False)
    return [int(index) for index in combined[combined].index if int(index) >= 80]


def _passes_order_flow_confirmation(candidate: Any, history: pd.DataFrame, config: dict[str, Any]) -> bool:
    flow_config = config.get("backtest", {}).get("order_flow_confirmation", {})
    if not flow_config.get("enabled", False):
        return True
    if history.empty:
        return False
    row = history.iloc[-1]
    ratio = row.get("flow_taker_buy_ratio_prior")
    imbalance = row.get("flow_imbalance_prior")
    impact = row.get("flow_price_impact_bps_prior")
    if pd.isna(ratio) or pd.isna(imbalance):
        return False
    ratio = float(ratio)
    imbalance = float(imbalance)
    if candidate.direction == "LONG":
        if ratio < float(flow_config.get("long_min_taker_buy_ratio", 0.60)):
            return False
        if imbalance < float(flow_config.get("long_min_signed_imbalance", 0.15)):
            return False
    elif candidate.direction == "SHORT":
        if ratio > float(flow_config.get("short_max_taker_buy_ratio", 0.40)):
            return False
        if imbalance > -float(flow_config.get("short_min_abs_signed_imbalance", 0.15)):
            return False
    else:
        return False
    max_abs_impact = flow_config.get("max_abs_price_impact_bps")
    if max_abs_impact is not None:
        if pd.isna(impact) or abs(float(impact)) > float(max_abs_impact):
            return False
    return True


def run_backtest(
    candles: list[Candle],
    config: dict[str, Any],
    flow_frame: pd.DataFrame | None = None,
    evaluation_windows: list[tuple[int, int]] | None = None,
) -> tuple[list[Trade], BacktestSummary]:
    frame = add_features(pd.DataFrame([c.to_dict() for c in candles]))
    if flow_frame is not None:
        frame = add_trade_flow_features(frame, flow_frame)
    historical_config = deepcopy(config)
    historical_config.setdefault("data", {})["derivatives_enabled"] = False
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    frame["close_time"] = pd.to_datetime(frame["close_time"], utc=True)
    trades: list[Trade] = []
    latency = int(config["backtest"].get("latency_bars", 1))
    expiry_bars = int(config.get("signal", {}).get("expiry_bars", 8))
    # Features are precomputed on the full closed-bar frame. Strategy modules only
    # require a bounded causal window; limiting the slice avoids O(n^2) dataframe
    # copying during year-long research runs without exposing future rows.
    history_bars = int(config.get("backtest", {}).get("strategy_history_bars", 160))
    event_indices = _event_indices(frame, config["strategies"])
    for index in event_indices:
        if index >= len(frame) - latency - 1:
            continue
        active_window_end = len(frame)
        if evaluation_windows is not None:
            matching_windows = [end for start, end in evaluation_windows if start <= index < end]
            if not matching_windows:
                continue
            active_window_end = min(matching_windows)
        history = frame.iloc[max(0, index + 1 - history_bars) : index + 1]
        candidates = generate_candidates(candles[0].symbol, history, config["strategies"])
        risk_state = build_risk_state(historical_config)
        for candidate in candidates:
            if not _passes_order_flow_confirmation(candidate, history, historical_config):
                continue
            attach_context(candidate, history, infer_frame_regime(history), None)
            signal = build_signal(candidate, risk_state, historical_config, derivatives_fresh=True)
            if signal.status != "CONFIRMED":
                continue
            future_start = index + latency + 1
            future = frame.iloc[future_start : min(active_window_end, future_start + expiry_bars)]
            trade = _simulate_candidate(candidate, future, config)
            if trade:
                trades.append(trade)
                break
    return trades, summarize_trades(trades, float(config["risk"]["account_equity"]))
