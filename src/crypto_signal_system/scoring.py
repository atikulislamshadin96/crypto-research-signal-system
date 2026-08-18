from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from crypto_signal_system.models import Candidate, RiskState, Signal
from crypto_signal_system.risk import calculate_position_size, candidate_costs, reward_risk


_CATEGORY_WEIGHTS = {
    "regime": 20.0,
    "structure": 20.0,
    "momentum": 15.0,
    "volume": 10.0,
    "volatility": 10.0,
    "derivatives": 10.0,
    "liquidity": 5.0,
    "news": 10.0,
}


def score_candidate(candidate: Candidate, risk_state: RiskState, config: dict[str, Any], derivatives_fresh: bool = True) -> tuple[float, list[str]]:
    score = 0.0
    failures: list[str] = list(candidate.failure_reasons)
    seen_categories: set[str] = set()
    for evidence in candidate.evidence:
        seen_categories.add(evidence.category)
        weight = _CATEGORY_WEIGHTS.get(evidence.category, 0.0)
        if evidence.quality == "confirmed":
            score += weight
        elif evidence.quality == "inferred":
            score += weight * 0.75
        elif evidence.quality == "conflicted":
            score -= weight * 0.50
    if "regime" not in seen_categories:
        failures.append("missing higher-timeframe regime evidence")
    if "structure" not in seen_categories:
        failures.append("missing objective structure evidence")
    if not derivatives_fresh and config["data"].get("derivatives_enabled", True):
        failures.append("derivatives data stale or unavailable")
    rr = reward_risk(candidate)
    if rr is None:
        failures.append("reward-to-risk cannot be computed")
    elif rr < float(config["risk"]["minimum_reward_risk"]):
        failures.append(f"reward-to-risk {rr:.2f} below minimum {config['risk']['minimum_reward_risk']:.2f}")
    if not risk_state.new_trades_allowed:
        failures.extend(risk_state.warnings)
    if candidate.conflicts:
        score -= min(20.0, 5.0 * len(candidate.conflicts))
        failures.append("material evidence conflict")
    return max(0.0, min(100.0, score)), sorted(set(failures))


def confidence_label(score: float, config: dict[str, Any]) -> str | None:
    thresholds = config["signal"]["confidence_labels"]
    if score >= float(thresholds["high"]):
        return "high"
    if score >= float(thresholds["medium"]):
        return "medium"
    if score >= float(thresholds["low"]):
        return "low"
    return None


def build_signal(candidate: Candidate, risk_state: RiskState, config: dict[str, Any], derivatives_fresh: bool = True) -> Signal:
    score, failures = score_candidate(candidate, risk_state, config, derivatives_fresh)
    rr = reward_risk(candidate)
    label = confidence_label(score, config)
    position, risk_values, size_warnings = calculate_position_size(candidate, config)
    costs = candidate_costs(candidate, config)
    candidate.warnings.extend(size_warnings)
    status = "CONFIRMED" if not failures and label else "NO TRADE"
    all_assumptions = list(candidate.assumptions)
    all_assumptions.append("Confidence is an evidence score, not a calibrated probability of profit.")
    all_assumptions.append("Live execution is disabled; this is a research/paper-trading output only.")
    return Signal(
        symbol=candidate.symbol,
        status=status,
        direction=candidate.direction if status == "CONFIRMED" else None,
        strategy=candidate.strategy,
        generated_at=candidate.generated_at,
        entry_zone={"low": candidate.entry_low, "high": candidate.entry_high} if candidate.entry_low is not None and candidate.entry_high is not None else None,
        stop_loss=candidate.stop_loss,
        take_profit=candidate.take_profit,
        rr=rr,
        risk_percent=float(config["risk"]["risk_per_trade_percent"]) if status == "CONFIRMED" else None,
        evidence_score=score,
        confidence_label=label,
        calibration_status="insufficient data",
        invalidation=candidate.invalidation,
        expiry=candidate.expiry,
        sources=[e.to_dict() for e in candidate.evidence],
        assumptions=all_assumptions,
        failure_reasons=sorted(set(failures)),
        why_may_fail=[
            "The regime inference may be wrong or may change before entry.",
            "Fees, funding, spread, slippage, and latency may exceed configured estimates.",
            "The setup has not earned a calibrated probability without untouched out-of-sample evidence.",
        ],
        cost_estimate=costs,
        position_size=position | risk_values,
        risk_controls={
            "daily_loss_guardrail_status": "blocked" if not risk_state.new_trades_allowed else "within limits",
            "daily_loss_percent": risk_state.daily_loss_percent,
            "total_drawdown_percent": risk_state.total_drawdown_percent,
            "total_correlated_exposure_percent": risk_state.correlated_risk_percent,
            "derivatives_fresh": derivatives_fresh,
            "sizing_warnings": list(size_warnings),
            "news_risk_status": "not configured" if not config["data"].get("news_enabled", False) else "configured",
        },
    )
