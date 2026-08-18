from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from crypto_signal_system.models import Candle


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    completeness: float
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


def validate_candles(
    candles: list[Candle],
    expected_limit: int,
    freshness_seconds: int,
    now: datetime | None = None,
) -> ValidationResult:
    now = now or datetime.now(timezone.utc)
    warnings: list[str] = []
    errors: list[str] = []
    if not candles:
        return ValidationResult(False, 0.0, (), ("no candles returned",))
    ordered = sorted(candles, key=lambda c: c.open_time)
    completeness = min(1.0, len(ordered) / max(1, expected_limit))
    if len({c.open_time for c in ordered}) != len(ordered):
        errors.append("duplicate candle open times")
    for candle in ordered:
        if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close):
            errors.append(f"impossible OHLC values at {candle.open_time.isoformat()}")
        if min(candle.open, candle.high, candle.low, candle.close, candle.volume) < 0:
            errors.append(f"negative OHLCV value at {candle.open_time.isoformat()}")
    if len(ordered) >= 2:
        interval = ordered[1].open_time - ordered[0].open_time
        for previous, current in zip(ordered, ordered[1:]):
            if current.open_time - previous.open_time != interval:
                errors.append(f"missing or irregular candle between {previous.open_time} and {current.open_time}")
                break
    age = now - ordered[-1].close_time
    observed_interval = ordered[-1].close_time - ordered[-2].close_time if len(ordered) >= 2 else timedelta(0)
    effective_freshness = max(timedelta(seconds=freshness_seconds), observed_interval * 1.5)
    if age > effective_freshness:
        errors.append(f"latest candle stale by {age.total_seconds():.0f}s; effective threshold {effective_freshness.total_seconds():.0f}s")
    elif age.total_seconds() < 0:
        errors.append("latest candle is in the future")
    if completeness < 1.0:
        warnings.append(f"candle completeness {completeness:.2%} below requested limit")
    return ValidationResult(not errors, completeness, tuple(warnings), tuple(errors))
