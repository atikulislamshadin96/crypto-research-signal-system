"""Autonomous, analysis-only hypothesis research primitives.

This module intentionally contains no order-submission code.  Hypotheses are
structured data, fingerprints are immutable, and missing or stale data blocks
execution rather than producing a synthetic result.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ENGINE_VERSION = "0.1.0"
PROTOCOL_VERSION = "research-ladder-v1"
FORBIDDEN_RETAIL_TERMS = ("ema", "rsi", "macd", "bollinger", "generic_breakout")
ALLOWED_FAMILIES = {
    "funding_divergence",
    "spot_perp_flow_divergence",
    "depth_normalized_ofi",
    "liquidity_adverse_selection_gate",
    "liquidation_regime_event",
    "liquidity_sweep_event",
    "liquidity_state_transition",
    "liquidity_depletion_replenishment",
    "liquidation_crowding_exhaustion",
    "cross_venue_price_discovery",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def contains_forbidden_retail_term(value: Any) -> str | None:
    haystack = canonical_json(value).lower()
    for term in FORBIDDEN_RETAIL_TERMS:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", haystack):
            return term
    return None


@dataclass(frozen=True)
class HypothesisSpec:
    hypothesis_id: str
    family: str
    title: str
    objective: str
    universe: tuple[str, ...]
    timeframes: tuple[str, ...]
    features: tuple[str, ...]
    parameters: dict[str, Any]
    outcome: dict[str, Any]
    parent_id: str | None = None
    source_refs: tuple[str, ...] = ()
    analysis_only: bool = True
    version: str = ENGINE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.hypothesis_id or not self.title:
            errors.append("hypothesis_id and title are required")
        if self.family not in ALLOWED_FAMILIES:
            errors.append(f"unsupported family: {self.family}")
        if not self.universe or not self.timeframes or not self.features:
            errors.append("universe, timeframes, and features must be non-empty")
        if not self.analysis_only:
            errors.append("analysis_only must remain true")
        forbidden = contains_forbidden_retail_term(self.to_dict())
        if forbidden:
            errors.append(f"forbidden retail term present: {forbidden}")
        if "order" in canonical_json(self.to_dict()).lower() and "order_flow" not in canonical_json(self.to_dict()).lower():
            errors.append("hypothesis may not contain order-submission instructions")
        return errors


@dataclass(frozen=True)
class ExperimentFingerprint:
    fingerprint: str
    hypothesis_hash: str
    dataset_hash: str
    protocol_version: str
    feature_version: str


def make_fingerprint(
    spec: HypothesisSpec,
    dataset_hash: str,
    protocol_version: str = PROTOCOL_VERSION,
    feature_version: str = ENGINE_VERSION,
) -> ExperimentFingerprint:
    errors = spec.validate()
    if errors:
        raise ValueError("invalid hypothesis: " + "; ".join(errors))
    hypothesis_hash = sha256_text(canonical_json(spec.to_dict()))
    payload = {
        "hypothesis_hash": hypothesis_hash,
        "dataset_hash": dataset_hash,
        "protocol_version": protocol_version,
        "feature_version": feature_version,
    }
    return ExperimentFingerprint(
        fingerprint=sha256_text(canonical_json(payload)),
        hypothesis_hash=hypothesis_hash,
        dataset_hash=dataset_hash,
        protocol_version=protocol_version,
        feature_version=feature_version,
    )


class HypothesisRegistry:
    """SQLite registry whose primary key permanently suppresses repeats."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                fingerprint TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL,
                hypothesis_json TEXT NOT NULL,
                hypothesis_hash TEXT NOT NULL,
                dataset_hash TEXT NOT NULL,
                protocol_version TEXT NOT NULL,
                feature_version TEXT NOT NULL,
                parent_id TEXT,
                status TEXT NOT NULL,
                rejection_reason TEXT,
                result_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_experiments_hypothesis_id ON experiments(hypothesis_id);
            CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
            CREATE TABLE IF NOT EXISTS learning_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT NOT NULL,
                category TEXT NOT NULL,
                value_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(fingerprint) REFERENCES experiments(fingerprint)
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def register(self, spec: HypothesisSpec, identity: ExperimentFingerprint) -> bool:
        """Insert once; return False for an exact prior experiment."""
        now = utc_now()
        try:
            self.connection.execute(
                """
                INSERT INTO experiments
                (fingerprint, hypothesis_id, hypothesis_json, hypothesis_hash,
                 dataset_hash, protocol_version, feature_version, parent_id,
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'registered', ?, ?)
                """,
                (
                    identity.fingerprint,
                    spec.hypothesis_id,
                    canonical_json(spec.to_dict()),
                    identity.hypothesis_hash,
                    identity.dataset_hash,
                    identity.protocol_version,
                    identity.feature_version,
                    spec.parent_id,
                    now,
                    now,
                ),
            )
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            self.connection.rollback()
            return False

    def update_result(
        self,
        fingerprint: str,
        status: str,
        result: dict[str, Any] | None = None,
        rejection_reason: str | None = None,
    ) -> None:
        if status not in {
            "registered", "schema_pass", "blocked_missing_data", "blocked_stale_data",
            "development_pass", "development_rejected", "cost_rejected", "validation_rejected",
            "shadow_only", "human_review_required", "failed",
        }:
            raise ValueError(f"unsupported experiment status: {status}")
        self.connection.execute(
            "UPDATE experiments SET status=?, rejection_reason=?, result_json=?, updated_at=? WHERE fingerprint=?",
            (status, rejection_reason, canonical_json(result) if result is not None else None, utc_now(), fingerprint),
        )
        self.connection.commit()

    def add_learning_observation(self, fingerprint: str, category: str, value: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO learning_observations(fingerprint, category, value_json, created_at) VALUES (?, ?, ?, ?)",
            (fingerprint, category, canonical_json(value), utc_now()),
        )
        self.connection.commit()

    def get(self, fingerprint: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM experiments WHERE fingerprint=?", (fingerprint,)).fetchone()
        return dict(row) if row else None

    def list_experiments(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?", (int(limit),)
        ).fetchall()
        return [dict(row) for row in rows]

    def export_json(self, output: str | Path, limit: int = 1000) -> Path:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "engine_version": ENGINE_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "analysis_only": True,
            "live_execution": False,
            "experiments": self.list_experiments(limit),
        }
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return destination


def _spec(
    hypothesis_id: str,
    family: str,
    title: str,
    objective: str,
    parameters: dict[str, Any],
    features: tuple[str, ...],
    outcome: dict[str, Any],
    parent_id: str | None = None,
) -> HypothesisSpec:
    return HypothesisSpec(
        hypothesis_id=hypothesis_id,
        family=family,
        title=title,
        objective=objective,
        universe=("BTCUSDT", "ETHUSDT", "SOLUSDT"),
        timeframes=("4h", "1h"),
        features=features,
        parameters=parameters,
        outcome=outcome,
        parent_id=parent_id,
        source_refs=(),
    )


def frozen_candidate_grid() -> list[HypothesisSpec]:
    """Return a small, deterministic, pre-registered candidate grid.

    The grid is intentionally bounded.  It is a research queue, not an
    optimizer, and changing it requires a protocol/version change.
    """
    candidates: list[HypothesisSpec] = []
    for threshold in (0.0005, 0.001, 0.002):
        for persistence in (2, 4):
            candidates.append(_spec(
                f"funding-divergence-{threshold:.4f}-{persistence}h",
                "funding_divergence",
                "Cross-venue funding divergence persistence event",
                "Measure whether persistent HL/dYdX funding differences precede basis or spread reversal after costs.",
                {"divergence_abs_min": threshold, "min_persistence_hours": persistence, "max_horizon_hours": 24},
                ("funding_rate_hl", "funding_rate_dydx", "basis", "venue_spread", "venue_depth"),
                {"type": "event_study", "horizons_hours": [1, 4, 8, 24], "net_of_costs": True},
            ))
    for z in (1.5, 2.0):
        for window in (5, 15):
            candidates.append(_spec(
                f"spot-perp-flow-divergence-z{z:g}-{window}m",
                "spot_perp_flow_divergence",
                "Synchronized spot/perpetual flow divergence event",
                "Test whether persistent spot-versus-perpetual signed-flow divergence predicts short-horizon basis or return changes.",
                {"flow_z_threshold": z, "window_minutes": window, "persistence_bars": 2},
                ("spot_signed_flow", "perp_signed_flow", "basis", "spread", "depth"),
                {"type": "event_study", "horizons_minutes": [1, 5, 15, 60], "net_of_costs": True},
            ))
    for levels in (5, 10):
        for z in (1.5, 2.0):
            candidates.append(_spec(
                f"depth-normalized-ofi-l{levels}-z{z:g}",
                "depth_normalized_ofi",
                "Depth-normalized order-flow imbalance event",
                "Test whether OFI scaled by available depth is conditionally associated with short-horizon returns or impact.",
                {"depth_levels": levels, "ofi_z_threshold": z, "horizon_seconds": 60},
                ("order_flow_imbalance", "available_depth", "spread", "mid_price", "trade_sign"),
                {"type": "event_study", "horizons_seconds": [1, 5, 30, 60], "net_of_costs": True},
            ))
    for spread_q, depth_q in ((0.8, 0.2), (0.9, 0.1)):
        candidates.append(_spec(
            f"liquidity-gate-spread{spread_q:.1f}-depth{depth_q:.1f}",
            "liquidity_adverse_selection_gate",
            "Liquidity and adverse-selection regime gate",
            "Identify market states where execution cost or adverse selection is unusually high.",
            {"spread_quantile": spread_q, "depth_quantile": depth_q, "lookback_bars": 500},
            ("spread", "available_depth", "order_flow_variance", "realized_volatility"),
            {"type": "risk_gate", "directional_claim": False, "net_of_costs": True},
        ))
    candidates.append(_spec(
        "liquidity-state-transition-eth-btc-v1",
        "liquidity_state_transition",
        "State-dependent L2 liquidity transition with flow overlay",
        "Test whether pre-event L2 state predicts post-event liquidity transitions and whether signed flow adds incremental value without making a directional claim.",
        {"depth_levels": 20, "state_bins": 3, "event_horizon_minutes": 5, "flow_overlay": True},
        ("relative_spread", "top_n_depth", "top_n_imbalance", "signed_flow", "event_cluster"),
        {"type": "event_study", "target": "liquidity_state_transition", "assets": ["ETHUSDT", "BTCUSDT"], "horizons_minutes": [1, 5], "net_of_costs": False},
    ))
    candidates.append(_spec(
        "liquidity-depletion-replenishment-displacement-v1",
        "liquidity_depletion_replenishment",
        "Liquidity depletion and replenishment before displacement",
        "Measure whether causal depth or spread deterioration followed by replenishment changes post-event mid-price displacement and execution cost.",
        {"depth_levels": 10, "depletion_window_minutes": 5, "replenishment_window_minutes": 5, "displacement_horizon_minutes": 15},
        ("relative_spread", "available_depth", "depth_change", "signed_flow", "mid_return"),
        {"type": "event_study", "target": "displacement_and_execution_cost", "horizons_minutes": [1, 5, 15], "matched_controls": True, "net_of_costs": True},
    ))
    candidates.append(_spec(
        "liquidation-crowding-exhaustion-risk-v1",
        "liquidation_crowding_exhaustion",
        "Crowding and liquidation pressure to liquidity-exhaustion state",
        "Classify whether joint crowding, forced-flow and L2 depletion precede stressed or exhausted liquidity without issuing an automatic directional signal.",
        {"crowding_quantile": 0.9, "liquidation_window_minutes": 5, "depth_quantile": 0.1, "replenishment_window_minutes": 15},
        ("open_interest", "funding_rate", "liquidation_flow", "signed_flow_variance", "relative_spread", "available_depth"),
        {"type": "risk_gate", "target": "liquidity_exhaustion_state", "leave_one_event_out": True, "directional_claim": False, "net_of_costs": True},
    ))
    candidates.append(_spec(
        "cross-venue-price-discovery-migration-v1",
        "cross_venue_price_discovery",
        "Cross-venue liquidity and flow price-discovery migration",
        "Test whether a synchronized change in venue-A liquidity or flow precedes a venue-B response after latency, spread and cost controls.",
        {"venues": ["OKX", "Bybit"], "timestamp_tolerance_ms": 250, "flow_window_seconds": 30, "lead_lag_horizons_seconds": [1, 5, 30]},
        ("venue_a_signed_flow", "venue_b_signed_flow", "venue_a_depth", "venue_b_depth", "basis", "timestamp_quality"),
        {"type": "event_study", "target": "lead_lag_and_price_discovery", "horizons_seconds": [1, 5, 30], "net_of_costs": True, "missing_sync_blocks": True},
    ))
    candidates.append(_spec(
        "liquidity-sweep-event-fixed-v1",
        "liquidity_sweep_event",
        "Strict liquidity sweep reclaim event study",
        "Measure event-level forward returns versus structure-matched controls without constructing a tradable strategy.",
        {"lookback_bars": 20, "reclaim_bars": 3, "displacement_atr_multiple": 1.5},
        ("swing_high_low", "sweep_distance", "reclaim", "displacement", "structure_bias"),
        {"type": "event_study", "directional_strategy": False, "net_of_costs": False},
    ))
    return candidates


def dataset_manifest_hash(paths: Iterable[str | Path]) -> str:
    """Hash file names, sizes, and bytes; missing files are explicit."""
    digest = hashlib.sha256()
    for raw_path in sorted((str(Path(item)) for item in paths)):
        path = Path(raw_path)
        digest.update(raw_path.encode("utf-8"))
        if not path.exists():
            digest.update(b"<MISSING>")
            continue
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(path.read_bytes())
    return digest.hexdigest()
