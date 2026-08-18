from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    trades: int
    source: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["open_time"] = self.open_time.isoformat()
        result["close_time"] = self.close_time.isoformat()
        return result


@dataclass(frozen=True)
class DerivativesSnapshot:
    symbol: str
    observed_at: datetime
    open_interest: float | None
    funding_rate: float | None
    source: str
    fresh: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["observed_at"] = self.observed_at.isoformat()
        result["warnings"] = list(self.warnings)
        return result


@dataclass(frozen=True)
class Evidence:
    category: str
    statement: str
    value: float | str | bool | None
    source: str
    observed_at: datetime | None
    quality: Literal["confirmed", "inferred", "missing", "conflicted"]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["observed_at"] = self.observed_at.isoformat() if self.observed_at else None
        return result


@dataclass(frozen=True)
class RiskState:
    account_equity: float
    reference_equity: float
    realized_pnl: float
    unrealized_pnl: float
    fees: float
    funding: float
    estimated_slippage: float
    daily_loss_percent: float
    total_drawdown_percent: float
    open_positions: int
    correlated_risk_percent: float
    consecutive_losses: int
    new_trades_allowed: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["warnings"] = list(self.warnings)
        return result


@dataclass
class Candidate:
    symbol: str
    direction: Literal["LONG", "SHORT"]
    strategy: str
    generated_at: datetime
    entry_low: float | None
    entry_high: float | None
    stop_loss: float | None
    take_profit: list[float]
    invalidation: str
    expiry: datetime | None
    thesis: str
    regime: str
    structure: str
    trigger: str
    evidence: list[Evidence] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    failure_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class Signal:
    symbol: str
    status: Literal["CONFIRMED", "WATCHLIST", "NO TRADE", "INVALIDATED", "EXPIRED"]
    direction: Literal["LONG", "SHORT"] | None
    strategy: str | None
    generated_at: datetime
    entry_zone: dict[str, float] | None
    stop_loss: float | None
    take_profit: list[float]
    rr: float | None
    risk_percent: float | None
    evidence_score: float | None
    confidence_label: Literal["high", "medium", "low"] | None
    calibration_status: Literal["calibrated", "not calibrated", "insufficient data"]
    invalidation: str | None
    expiry: datetime | None
    sources: list[dict[str, Any]]
    assumptions: list[str]
    failure_reasons: list[str]
    why_may_fail: list[str]
    cost_estimate: dict[str, float | None]
    position_size: dict[str, float | None]
    risk_controls: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["generated_at"] = self.generated_at.isoformat()
        result["expiry"] = self.expiry.isoformat() if self.expiry else None
        return result


@dataclass
class RunResult:
    run_id: str
    generated_at: datetime
    data_as_of: datetime | None
    system_version: str
    market_regime: str
    signals: list[Signal]
    rejected_candidates: list[dict[str, Any]]
    risk_state: RiskState
    warnings: list[str]
    provider_status: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at.isoformat(),
            "data_as_of": self.data_as_of.isoformat() if self.data_as_of else None,
            "system_version": self.system_version,
            "market_regime": self.market_regime,
            "signals": [signal.to_dict() for signal in self.signals],
            "rejected_candidates": self.rejected_candidates,
            "risk_state": self.risk_state.to_dict(),
            "warnings": self.warnings,
            "provider_status": self.provider_status,
        }
