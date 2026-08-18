from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_signal_system.features import add_features
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


def run_backtest(candles: list[Candle], config: dict[str, Any]) -> tuple[list[Trade], BacktestSummary]:
    frame = add_features(pd.DataFrame([c.to_dict() for c in candles]))
    historical_config = deepcopy(config)
    historical_config.setdefault("data", {})["derivatives_enabled"] = False
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    frame["close_time"] = pd.to_datetime(frame["close_time"], utc=True)
    trades: list[Trade] = []
    latency = int(config["backtest"].get("latency_bars", 1))
    expiry_bars = int(config.get("signal", {}).get("expiry_bars", 8))
    for index in range(80, len(frame) - latency - 1):
        history = frame.iloc[: index + 1]
        candidates = generate_candidates(candles[0].symbol, history, config["strategies"])
        risk_state = build_risk_state(historical_config)
        for candidate in candidates:
            attach_context(candidate, history, infer_frame_regime(history), None)
            signal = build_signal(candidate, risk_state, historical_config, derivatives_fresh=True)
            if signal.status != "CONFIRMED":
                continue
            future_start = index + latency + 1
            future = frame.iloc[future_start : future_start + expiry_bars]
            trade = _simulate_candidate(candidate, future, config)
            if trade:
                trades.append(trade)
                break
    return trades, summarize_trades(trades, float(config["risk"]["account_equity"]))
