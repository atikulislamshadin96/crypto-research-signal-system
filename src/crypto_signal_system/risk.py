from __future__ import annotations

from dataclasses import replace
from typing import Any

from crypto_signal_system.models import Candidate, RiskState


def build_risk_state(config: dict[str, Any], realized_pnl: float = 0.0, unrealized_pnl: float = 0.0, fees: float = 0.0, funding: float = 0.0, estimated_slippage: float = 0.0, open_positions: int = 0, correlated_risk_percent: float = 0.0, consecutive_losses: int = 0) -> RiskState:
    risk = config["risk"]
    equity = float(risk["account_equity"]) + realized_pnl + unrealized_pnl - fees - funding - estimated_slippage
    reference = float(risk["reference_equity"])
    daily_loss_percent = max(0.0, -(realized_pnl + unrealized_pnl - fees - funding - estimated_slippage) / float(risk["account_equity"]) * 100)
    total_drawdown_percent = max(0.0, (reference - equity) / reference * 100)
    warnings: list[str] = []
    allowed = True
    if daily_loss_percent >= float(risk["soft_daily_loss_percent"]):
        warnings.append("soft daily-loss warning reached")
    if daily_loss_percent >= float(risk["hard_daily_loss_percent"]):
        allowed = False
        warnings.append("hard daily-loss stop reached")
    if total_drawdown_percent >= float(risk["hard_total_drawdown_percent"]):
        allowed = False
        warnings.append("hard total-drawdown stop reached")
    if open_positions >= int(risk["max_simultaneous_positions"]):
        allowed = False
        warnings.append("maximum simultaneous positions reached")
    if correlated_risk_percent >= float(risk["max_correlated_risk_percent"]):
        allowed = False
        warnings.append("correlation-adjusted risk cap reached")
    if consecutive_losses >= int(risk["max_consecutive_losses"]):
        allowed = False
        warnings.append("loss-streak cooldown active")
    return RiskState(
        account_equity=equity,
        reference_equity=reference,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        fees=fees,
        funding=funding,
        estimated_slippage=estimated_slippage,
        daily_loss_percent=daily_loss_percent,
        total_drawdown_percent=total_drawdown_percent,
        open_positions=open_positions,
        correlated_risk_percent=correlated_risk_percent,
        consecutive_losses=consecutive_losses,
        new_trades_allowed=allowed,
        warnings=tuple(warnings),
    )


def calculate_position_size(candidate: Candidate, config: dict[str, Any]) -> tuple[dict[str, float | None], dict[str, float | None], list[str]]:
    risk_cfg = config["risk"]
    if candidate.entry_low is None or candidate.entry_high is None or candidate.stop_loss is None:
        return {"contracts": None, "notional_usd": None}, {"risk_usd": None, "maximum_planned_loss_usd": None}, ["entry or stop unavailable"]
    entry = (candidate.entry_low + candidate.entry_high) / 2
    stop_distance = abs(entry - candidate.stop_loss)
    if entry <= 0 or stop_distance <= 0:
        return {"contracts": None, "notional_usd": None}, {"risk_usd": None, "maximum_planned_loss_usd": None}, ["invalid entry or stop distance"]
    equity = float(risk_cfg["account_equity"])
    risk_usd = equity * float(risk_cfg["risk_per_trade_percent"]) / 100
    round_trip_cost_rate = float(risk_cfg["estimated_fee_rate_round_trip"]) + float(risk_cfg["estimated_slippage_rate_round_trip"])
    cost_per_unit = entry * round_trip_cost_rate
    funding_per_unit = entry * float(risk_cfg["estimated_funding_rate_per_8h"])
    risk_per_unit = stop_distance + cost_per_unit + funding_per_unit
    contracts = risk_usd / risk_per_unit
    notional = contracts * entry
    warnings: list[str] = []
    max_notional = float(risk_cfg["max_notional_usd"])
    if notional > max_notional:
        contracts = max_notional / entry
        notional = max_notional
        warnings.append("position clipped to maximum notional")
    leverage = notional / equity
    if leverage > float(risk_cfg["max_leverage"]):
        contracts = equity * float(risk_cfg["max_leverage"]) / entry
        notional = contracts * entry
        warnings.append("position clipped to maximum leverage ceiling")
    planned_loss = contracts * risk_per_unit
    return {"contracts": contracts, "notional_usd": notional}, {"risk_usd": risk_usd, "maximum_planned_loss_usd": planned_loss}, warnings


def candidate_costs(candidate: Candidate, config: dict[str, Any]) -> dict[str, float | None]:
    if candidate.entry_low is None or candidate.entry_high is None:
        return {"entry_reference": None, "fee_usd": None, "slippage_usd": None, "funding_usd_per_8h": None}
    entry = (candidate.entry_low + candidate.entry_high) / 2
    position, _, _ = calculate_position_size(candidate, config)
    notional = position["notional_usd"]
    if notional is None:
        return {"entry_reference": entry, "fee_usd": None, "slippage_usd": None, "funding_usd_per_8h": None}
    return {
        "entry_reference": entry,
        "fee_usd": notional * float(config["risk"]["estimated_fee_rate_round_trip"]),
        "slippage_usd": notional * float(config["risk"]["estimated_slippage_rate_round_trip"]),
        "funding_usd_per_8h": notional * float(config["risk"]["estimated_funding_rate_per_8h"]),
    }


def reward_risk(candidate: Candidate) -> float | None:
    if candidate.entry_low is None or candidate.entry_high is None or candidate.stop_loss is None or not candidate.take_profit:
        return None
    entry = (candidate.entry_low + candidate.entry_high) / 2
    risk = abs(entry - candidate.stop_loss)
    if risk <= 0:
        return None
    reward = abs(candidate.take_profit[0] - entry)
    return reward / risk
