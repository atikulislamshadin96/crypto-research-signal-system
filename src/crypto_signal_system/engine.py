from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from crypto_signal_system.data.binance_public import ProviderError
from crypto_signal_system.data.providers import build_public_client
from crypto_signal_system.data.validation import validate_candles
from crypto_signal_system.features import add_features, candles_to_frame, frame_is_ready
from crypto_signal_system.models import RunResult
from crypto_signal_system.context import attach_context, infer_frame_regime
from crypto_signal_system.reporting import write_artifacts
from crypto_signal_system.risk import build_risk_state
from crypto_signal_system.scoring import build_signal, score_candidate
from crypto_signal_system.strategies import generate_candidates


def _run_id(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")




def run_scan(config: dict[str, Any], now: datetime | None = None) -> RunResult:
    now = now or datetime.now(timezone.utc)
    client = build_public_client(config)
    provider_name = str(config["data"].get("provider", "unknown"))
    warnings: list[str] = []
    provider_status: list[dict[str, Any]] = []
    all_signals = []
    rejected: list[dict[str, Any]] = []
    freshest: list[datetime] = []
    regime_frames: list[Any] = []
    risk_state = build_risk_state(config)
    for symbol in config["data"]["symbols"]:
        frames: dict[str, Any] = {}
        symbol_errors: list[str] = []
        for timeframe in list(config["data"]["timeframes"]["regime"]) + [config["data"]["timeframes"]["structure"], config["data"]["timeframes"]["entry"]]:
            try:
                candles = client.get_closed_candles(symbol, timeframe, int(config["data"]["candle_limit"]), now)
                validation = validate_candles(candles, int(config["data"]["candle_limit"]), int(config["data"]["stale_after_seconds"]["candles"]), now)
                provider_status.append({"symbol": symbol, "timeframe": timeframe, "valid": validation.valid, "completeness": validation.completeness, "warnings": list(validation.warnings), "errors": list(validation.errors), "source": candles[-1].source if candles else provider_name})
                if not validation.valid:
                    symbol_errors.extend(validation.errors)
                    continue
                frame = add_features(candles_to_frame(candles))
                if not frame_is_ready(frame):
                    symbol_errors.append(f"{symbol} {timeframe}: insufficient feature history")
                    continue
                frames[timeframe] = frame
                freshest.append(candles[-1].close_time)
            except ProviderError as exc:
                symbol_errors.append(f"{symbol} {timeframe}: provider failure: {exc}")
                provider_status.append({"symbol": symbol, "timeframe": timeframe, "valid": False, "errors": [str(exc)], "source": provider_name})
        if symbol_errors:
            warnings.extend(symbol_errors)
            rejected.append({"symbol": symbol, "strategy": None, "direction": None, "evidence_score": None, "reasons": symbol_errors})
            continue
        try:
            derivatives = client.get_derivatives_snapshot(symbol, now)
        except ProviderError as exc:
            derivatives = type("Unavailable", (), {"fresh": False, "source": "unavailable", "observed_at": None, "funding_rate": None})()
            warnings.append(f"{symbol}: derivatives unavailable: {exc}")
        frame = frames[config["data"]["timeframes"]["entry"]]
        if config["data"]["timeframes"]["regime"]:
            regime_frames.append(frames[config["data"]["timeframes"]["regime"][0]])
        candidates = generate_candidates(symbol, frame, config["strategies"])
        for candidate in candidates:
            attach_context(candidate, frame, infer_frame_regime(regime_frames[0] if regime_frames else frame), derivatives)
            score, failures = score_candidate(candidate, risk_state, config, derivatives.fresh)
            signal = build_signal(candidate, risk_state, config, derivatives.fresh)
            signal.evidence_score = score
            signal.failure_reasons = sorted(set(signal.failure_reasons))
            if signal.status == "CONFIRMED":
                all_signals.append(signal)
            else:
                rejected.append({"symbol": symbol, "strategy": candidate.strategy, "direction": candidate.direction, "evidence_score": score, "reasons": signal.failure_reasons})
    deduped = []
    seen: set[str] = set()
    for signal in all_signals:
        key = hashlib.sha256(f"{signal.symbol}|{signal.direction}|{signal.strategy}|{signal.entry_zone}".encode()).hexdigest()
        if key in seen:
            rejected.append({"symbol": signal.symbol, "strategy": signal.strategy, "direction": signal.direction, "evidence_score": signal.evidence_score, "reasons": ["duplicate setup suppressed"]})
        else:
            seen.add(key)
            deduped.append(signal)
    return RunResult(
        run_id=_run_id(now),
        generated_at=now,
        data_as_of=min(freshest) if freshest else None,
        system_version=config["system"]["version"],
        market_regime=infer_frame_regime(regime_frames[0] if regime_frames else None) if regime_frames else "indeterminate",
        signals=deduped,
        rejected_candidates=rejected,
        risk_state=risk_state,
        warnings=warnings,
        provider_status=provider_status,
    )


def run_and_write(config: dict[str, Any], now: datetime | None = None) -> tuple[RunResult, tuple[Any, Any, Any]]:
    result = run_scan(config, now)
    paths = write_artifacts(result, config["system"]["output_dir"])
    return result, paths
