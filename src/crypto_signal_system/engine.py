from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from crypto_signal_system.data.binance_public import ProviderError
from crypto_signal_system.data.providers import build_public_client
from crypto_signal_system.data.validation import validate_candles
from crypto_signal_system.features import add_features, candles_to_frame, frame_is_ready
from crypto_signal_system.models import RunResult
from crypto_signal_system.context import (
    attach_context,
    attach_hierarchy_context,
    attach_microstructure,
    hierarchy_market_regime,
    timeframe_hierarchy,
)
from crypto_signal_system.reporting import write_artifacts
from crypto_signal_system.risk import build_risk_state
from crypto_signal_system.scoring import build_signal, score_candidate
from crypto_signal_system.strategies import generate_candidates


def _run_id(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")


def _unique_roles(config: dict[str, Any]) -> dict[str, str]:
    return timeframe_hierarchy(config)


def _signal_key(signal: Any, entry_close_time: Any) -> str:
    raw = f"{signal.symbol}|{signal.direction}|{signal.strategy}|{entry_close_time.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def run_scan(config: dict[str, Any], now: datetime | None = None) -> RunResult:
    now = now or datetime.now(timezone.utc)
    client = build_public_client(config)
    provider_name = str(config["data"].get("provider", "unknown"))
    roles = _unique_roles(config)
    warnings: list[str] = []
    provider_status: list[dict[str, Any]] = []
    all_signals = []
    rejected: list[dict[str, Any]] = []
    data_not_ready = False

    if provider_name == "bybit_public" and hasattr(client, "refresh_websocket_state"):
        ws_timeframes = list(dict.fromkeys(roles.values()))
        try:
            collection = client.refresh_websocket_state(
                list(config["data"]["symbols"]),
                ws_timeframes,
                int(config["data"].get("bybit_ws_collect_seconds", 20)),
            )
            provider_status.append({
                "data_type": "websocket_collection",
                "valid": bool(collection.get("connection") and collection.get("subscription_ack")),
                "source": "bybit_public:websocket",
                "summary": collection,
                "timeframe_roles": roles,
            })
            if not collection.get("connection") or not collection.get("subscription_ack"):
                data_not_ready = True
        except ProviderError as exc:
            data_not_ready = True
            warnings.append(f"Bybit WebSocket collection failed: {exc}")
            provider_status.append({
                "data_type": "websocket_collection",
                "valid": False,
                "source": "bybit_public:websocket",
                "errors": [str(exc)],
                "timeframe_roles": roles,
            })

    freshest: list[datetime] = []
    regime_frames: list[Any] = []
    risk_state = build_risk_state(config)
    required_roles = ("regime", "structure", "confirmation", "setup", "entry")

    for symbol in config["data"]["symbols"]:
        frames_by_role: dict[str, Any] = {}
        symbol_errors: list[str] = []
        for role in required_roles:
            timeframe = roles[role]
            try:
                candles = client.get_closed_candles(symbol, timeframe, int(config["data"]["candle_limit"]), now)
                validation = validate_candles(
                    candles,
                    int(config["data"]["candle_limit"]),
                    int(config["data"]["stale_after_seconds"]["candles"]),
                    now,
                )
                provider_status.append({
                    "symbol": symbol,
                    "role": role,
                    "timeframe": timeframe,
                    "valid": validation.valid,
                    "completeness": validation.completeness,
                    "warnings": list(validation.warnings),
                    "errors": list(validation.errors),
                    "source": candles[-1].source if candles else provider_name,
                })
                if not validation.valid:
                    symbol_errors.extend([f"{role}/{timeframe}: {error}" for error in validation.errors])
                    continue
                frame = add_features(candles_to_frame(candles))
                if not frame_is_ready(frame):
                    symbol_errors.append(f"{role}/{timeframe}: insufficient feature history")
                    continue
                frames_by_role[role] = frame
                freshest.append(candles[-1].close_time)
            except ProviderError as exc:
                symbol_errors.append(f"{role}/{timeframe}: provider failure: {exc}")
                provider_status.append({
                    "symbol": symbol,
                    "role": role,
                    "timeframe": timeframe,
                    "valid": False,
                    "errors": [str(exc)],
                    "source": provider_name,
                })

        if symbol_errors or len(frames_by_role) != len(required_roles):
            data_not_ready = True
            warnings.extend([f"{symbol}: {error}" for error in symbol_errors])
            rejected.append({
                "symbol": symbol,
                "strategy": None,
                "direction": None,
                "evidence_score": None,
                "status": "DATA_NOT_READY",
                "reasons": symbol_errors or ["required timeframe/history unavailable"],
            })
            continue

        order_book = None
        trade_flow = None
        micro_cfg = config["data"].get("microstructure", {})
        if micro_cfg.get("enabled", False) and hasattr(client, "get_order_book_snapshot"):
            try:
                order_book = client.get_order_book_snapshot(symbol, now, int(micro_cfg.get("order_book_depth_levels", 10)))
                provider_status.append({"symbol": symbol, "data_type": "order_book", "valid": order_book.fresh, "source": order_book.source, "observed_at": order_book.observed_at.isoformat(), "warnings": list(order_book.warnings)})
            except ProviderError as exc:
                warnings.append(f"{symbol}: order book unavailable: {exc}")
                provider_status.append({"symbol": symbol, "data_type": "order_book", "valid": False, "source": provider_name, "errors": [str(exc)]})
            try:
                trade_flow = client.get_recent_trade_flow(symbol, now, int(micro_cfg.get("recent_trade_limit", 100)))
                provider_status.append({"symbol": symbol, "data_type": "trade_flow", "valid": trade_flow.fresh, "source": trade_flow.source, "observed_at": trade_flow.observed_at.isoformat(), "warnings": list(trade_flow.warnings)})
            except ProviderError as exc:
                warnings.append(f"{symbol}: recent trade flow unavailable: {exc}")
                provider_status.append({"symbol": symbol, "data_type": "trade_flow", "valid": False, "source": provider_name, "errors": [str(exc)]})

        try:
            derivatives = client.get_derivatives_snapshot(symbol, now)
        except ProviderError as exc:
            derivatives = type("Unavailable", (), {"fresh": False, "source": "unavailable", "observed_at": None, "funding_rate": None})()
            warnings.append(f"{symbol}: derivatives unavailable: {exc}")

        entry_frame = frames_by_role["entry"]
        regime_frames.append(frames_by_role["regime"])
        candidates = generate_candidates(symbol, entry_frame, config["strategies"])
        for candidate in candidates:
            hierarchy_failures = attach_hierarchy_context(candidate, frames_by_role, roles)
            attach_context(candidate, entry_frame, hierarchy_market_regime(frames_by_role), derivatives, include_regime=False)
            attach_microstructure(candidate, order_book, trade_flow, use_for_confirmation=bool(micro_cfg.get("use_for_confirmation", False)))
            candidate.failure_reasons.extend(hierarchy_failures)
            score, failures = score_candidate(candidate, risk_state, config, derivatives.fresh)
            signal = build_signal(candidate, risk_state, config, derivatives.fresh)
            signal.evidence_score = score
            signal.failure_reasons = sorted(set(signal.failure_reasons + failures))
            if signal.status == "CONFIRMED":
                state = getattr(client, "_state", None)
                key = _signal_key(signal, entry_frame.iloc[-1]["close_time"])
                if state is not None and state.has_emitted_signal(key):
                    rejected.append({"symbol": symbol, "strategy": candidate.strategy, "direction": candidate.direction, "evidence_score": score, "status": "NO_VALID_SETUP", "reasons": ["duplicate setup suppressed for confirmed entry candle"]})
                else:
                    all_signals.append(signal)
                    if state is not None:
                        state.record_emitted_signal(key)
            else:
                rejected.append({"symbol": symbol, "strategy": candidate.strategy, "direction": candidate.direction, "evidence_score": score, "status": "NO_VALID_SETUP", "reasons": signal.failure_reasons})

    state = getattr(client, "_state", None)
    if state is not None:
        state.save()
    deduped = []
    seen: set[str] = set()
    for signal in all_signals:
        key = hashlib.sha256(f"{signal.symbol}|{signal.direction}|{signal.strategy}|{signal.entry_zone}".encode()).hexdigest()
        if key in seen:
            rejected.append({"symbol": signal.symbol, "strategy": signal.strategy, "direction": signal.direction, "evidence_score": signal.evidence_score, "status": "NO_VALID_SETUP", "reasons": ["duplicate setup suppressed"]})
        else:
            seen.add(key)
            deduped.append(signal)

    analysis_status = "DATA_NOT_READY" if data_not_ready else ("SIGNAL_READY" if deduped else "NO_VALID_SETUP")
    return RunResult(
        run_id=_run_id(now),
        generated_at=now,
        data_as_of=min(freshest) if freshest else None,
        system_version=config["system"]["version"],
        market_regime=hierarchy_market_regime({"regime": regime_frames[-1]}) if regime_frames else "indeterminate",
        signals=deduped,
        rejected_candidates=rejected,
        risk_state=risk_state,
        warnings=warnings,
        provider_status=provider_status,
        analysis_status=analysis_status,
    )


def run_and_write(config: dict[str, Any], now: datetime | None = None) -> tuple[RunResult, tuple[Any, Any, Any]]:
    result = run_scan(config, now)
    paths = write_artifacts(result, config["system"]["output_dir"])
    return result, paths
