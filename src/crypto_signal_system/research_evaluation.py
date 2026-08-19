"""Fail-closed evaluation ladder for autonomous research experiments."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from crypto_signal_system.research_engine import (
    HypothesisRegistry,
    HypothesisSpec,
    make_fingerprint,
    utc_now,
)


@dataclass(frozen=True)
class LadderResult:
    fingerprint: str
    hypothesis_id: str
    status: str
    completed_stages: tuple[str, ...]
    blocked_stage: str | None
    rejection_reason: str | None
    analysis_only: bool = True
    live_execution_enabled: bool = False
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchEvaluator:
    """Run deterministic gates before any optional data-specific evaluator.

    A data-specific evaluator must be supplied by the repository maintainer and
    may only return measurements; it cannot alter the hypothesis or promotion
    rules.  With no evaluator, the ladder stops at schema/causality gates.
    """

    def __init__(self, registry: HypothesisRegistry, stale_after_seconds: int = 36 * 3600):
        self.registry = registry
        self.stale_after_seconds = stale_after_seconds

    def evaluate(
        self,
        spec: HypothesisSpec,
        identity,
        dataset_available: bool,
        dataset_fresh: bool,
        evaluator: Callable[[HypothesisSpec], dict[str, Any]] | None = None,
    ) -> LadderResult:
        errors = spec.validate()
        if errors:
            reason = "; ".join(errors)
            self.registry.update_result(identity.fingerprint, "failed", rejection_reason=reason)
            return LadderResult(identity.fingerprint, spec.hypothesis_id, "failed", (), "schema", reason)

        stages = ["schema", "causality"]
        self.registry.update_result(identity.fingerprint, "schema_pass", result={"stages": stages})
        if not dataset_available:
            reason = "required dataset manifest or files unavailable; fail closed"
            self.registry.update_result(identity.fingerprint, "blocked_missing_data", rejection_reason=reason, result={"stages": stages})
            return LadderResult(identity.fingerprint, spec.hypothesis_id, "blocked_missing_data", tuple(stages), "data_availability", reason)
        if not dataset_fresh:
            reason = "dataset is stale under the configured freshness policy; fail closed"
            self.registry.update_result(identity.fingerprint, "blocked_stale_data", rejection_reason=reason, result={"stages": stages})
            return LadderResult(identity.fingerprint, spec.hypothesis_id, "blocked_stale_data", tuple(stages), "data_freshness", reason)

        if evaluator is None:
            reason = "no deterministic data-specific evaluator registered; no performance claim permitted"
            self.registry.update_result(identity.fingerprint, "blocked_missing_data", rejection_reason=reason, result={"stages": stages})
            return LadderResult(identity.fingerprint, spec.hypothesis_id, "blocked_missing_data", tuple(stages), "development_backtest", reason)

        measured = evaluator(spec)
        stages.extend(("development_backtest", "cost_stress", "chronological_validation", "walk_forward_cpcv", "perturbation", "uncertainty"))
        # Promotion is deliberately never automatic.  The evaluator may return
        # a diagnostic result, but the registry stops at human_review_required.
        self.registry.update_result(
            identity.fingerprint,
            "human_review_required",
            result={"stages": stages, "measurements": measured, "generated_at": utc_now()},
        )
        self.registry.add_learning_observation(identity.fingerprint, "evaluation_measurements", measured)
        return LadderResult(
            identity.fingerprint,
            spec.hypothesis_id,
            "human_review_required",
            tuple(stages),
            "human_promotion_gate",
            "automatic promotion is disabled",
            result=measured,
        )


def write_ladder_report(path: str | Path, result: LadderResult) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return destination
