from __future__ import annotations

from typing import Any

import pandas as pd

from crypto_signal_system.models import Candidate, Evidence
from crypto_signal_system.microstructure import OrderBookSnapshot, TradeFlowSnapshot


def infer_frame_regime(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "indeterminate"
    row = frame.iloc[-1]
    values = [row.get("close"), row.get("ema_fast"), row.get("ema_slow"), row.get("atr_percent")]
    if any(pd.isna(value) for value in values):
        return "indeterminate"
    if float(row["atr_percent"]) >= 8.0:
        return "transition"
    if float(row["close"]) > float(row["ema_slow"]) and float(row["ema_fast"]) > float(row["ema_slow"]):
        return "bullish"
    if float(row["close"]) < float(row["ema_slow"]) and float(row["ema_fast"]) < float(row["ema_slow"]):
        return "bearish"
    return "range"


def attach_microstructure(
    candidate: Candidate,
    order_book: OrderBookSnapshot | None,
    trade_flow: TradeFlowSnapshot | None,
    use_for_confirmation: bool = False,
) -> None:
    """Attach public microstructure evidence; never infer missing values."""
    quality = "confirmed" if use_for_confirmation else "inferred"
    evidence_category = "microstructure" if use_for_confirmation else "microstructure_observation"
    if order_book is not None:
        if not order_book.fresh:
            candidate.conflicts.append("order-book snapshot stale")
        elif order_book.depth_imbalance is not None:
            direction_agrees = (candidate.direction == "LONG" and order_book.depth_imbalance > 0) or (candidate.direction == "SHORT" and order_book.depth_imbalance < 0)
            statement = "Fresh top-of-book depth imbalance agrees with candidate direction" if direction_agrees else "Fresh top-of-book depth imbalance conflicts with candidate direction"
            if direction_agrees:
                candidate.evidence.append(Evidence(evidence_category, statement, order_book.depth_imbalance, order_book.source, order_book.observed_at, quality))
            else:
                candidate.conflicts.append(statement)
        if order_book.spread_bps is not None:
            candidate.evidence.append(Evidence("execution", "Observed top-of-book spread is available for cost audit", order_book.spread_bps, order_book.source, order_book.observed_at, quality))
    if trade_flow is not None:
        if not trade_flow.fresh:
            candidate.conflicts.append("recent trade flow stale")
        elif trade_flow.signed_volume_imbalance is not None:
            direction_agrees = (candidate.direction == "LONG" and trade_flow.signed_volume_imbalance > 0) or (candidate.direction == "SHORT" and trade_flow.signed_volume_imbalance < 0)
            statement = "Fresh signed public-trade flow agrees with candidate direction" if direction_agrees else "Fresh signed public-trade flow conflicts with candidate direction"
            if direction_agrees:
                candidate.evidence.append(Evidence(evidence_category, statement, trade_flow.signed_volume_imbalance, trade_flow.source, trade_flow.observed_at, quality))
            else:
                candidate.conflicts.append(statement)


def attach_context(candidate: Candidate, frame: pd.DataFrame, market_regime: str | None = None, derivatives: Any | None = None) -> None:
    row = frame.iloc[-1]
    observed_at = row["close_time"]
    regime = market_regime or infer_frame_regime(frame)
    direction_regime_match = (candidate.direction == "LONG" and regime == "bullish") or (candidate.direction == "SHORT" and regime == "bearish")
    if direction_regime_match:
        candidate.evidence.append(Evidence("regime", "Closed-bar trend regime agrees with candidate direction", regime, "computed:EMA_regime", observed_at, "inferred"))
    elif regime == "range" and candidate.strategy == "range_mean_reversion":
        candidate.evidence.append(Evidence("regime", "Closed-bar regime is range-bound for mean reversion", regime, "computed:EMA_regime", observed_at, "inferred"))
    elif regime != "indeterminate":
        candidate.conflicts.append(f"candidate direction conflicts with {regime} regime")
    atr_percent = row.get("atr_percent")
    if pd.notna(atr_percent):
        candidate.evidence.append(Evidence("volatility", "ATR percentage is available from closed candles", float(atr_percent), "computed:ATR", observed_at, "inferred"))
    return_n = row.get("return_n")
    if pd.notna(return_n) and ((candidate.direction == "LONG" and float(return_n) > 0) or (candidate.direction == "SHORT" and float(return_n) < 0)):
        candidate.evidence.append(Evidence("momentum", "Recent multi-bar return agrees with candidate direction", float(return_n), "computed:return_n", observed_at, "inferred"))
    volume_ratio = row.get("volume_ratio")
    if pd.notna(volume_ratio) and float(volume_ratio) >= 1.0:
        candidate.evidence.append(Evidence("volume", "Volume is at or above its rolling baseline", float(volume_ratio), "computed:volume_ratio", observed_at, "inferred"))
    if derivatives is not None:
        if not derivatives.fresh:
            candidate.conflicts.append("derivatives snapshot stale")
        else:
            candidate.evidence.append(Evidence("derivatives", "Funding and open interest snapshot is fresh", True, derivatives.source, derivatives.observed_at, "confirmed"))
            if derivatives.funding_rate is not None:
                candidate.evidence.append(Evidence("liquidity", "Funding rate is recorded for audit", derivatives.funding_rate, derivatives.source, derivatives.observed_at, "confirmed"))
