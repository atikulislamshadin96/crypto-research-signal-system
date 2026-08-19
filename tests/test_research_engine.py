from __future__ import annotations

from pathlib import Path

from crypto_signal_system.research_engine import (
    HypothesisRegistry,
    HypothesisSpec,
    frozen_candidate_grid,
    make_fingerprint,
)
from crypto_signal_system.research_evaluation import ResearchEvaluator


def test_candidate_grid_is_bounded_and_analysis_only() -> None:
    candidates = frozen_candidate_grid()
    assert candidates
    assert len(candidates) == 17
    assert all(candidate.analysis_only for candidate in candidates)
    assert all(not candidate.validate() for candidate in candidates)


def test_forbidden_retail_terms_are_rejected() -> None:
    candidate = frozen_candidate_grid()[0]
    invalid = HypothesisSpec(
        hypothesis_id="invalid",
        family=candidate.family,
        title="invalid EMA proposal",
        objective=candidate.objective,
        universe=candidate.universe,
        timeframes=candidate.timeframes,
        features=candidate.features,
        parameters=candidate.parameters,
        outcome=candidate.outcome,
    )
    assert any("forbidden retail term" in error for error in invalid.validate())


def test_fingerprint_is_deterministic_and_dataset_sensitive() -> None:
    candidate = frozen_candidate_grid()[0]
    first = make_fingerprint(candidate, "dataset-a")
    second = make_fingerprint(candidate, "dataset-a")
    third = make_fingerprint(candidate, "dataset-b")
    assert first == second
    assert first.fingerprint != third.fingerprint


def test_registry_never_repeats_exact_failed_experiment(tmp_path: Path) -> None:
    registry = HypothesisRegistry(tmp_path / "registry.sqlite3")
    try:
        candidate = frozen_candidate_grid()[0]
        identity = make_fingerprint(candidate, "dataset-a")
        assert registry.register(candidate, identity)
        assert not registry.register(candidate, identity)
        registry.update_result(identity.fingerprint, "development_rejected", rejection_reason="negative expectancy")
        assert registry.get(identity.fingerprint)["status"] == "development_rejected"
        assert not registry.register(candidate, identity)
    finally:
        registry.close()


def test_evaluator_blocks_when_data_is_missing(tmp_path: Path) -> None:
    registry = HypothesisRegistry(tmp_path / "registry.sqlite3")
    try:
        candidate = frozen_candidate_grid()[0]
        identity = make_fingerprint(candidate, "missing")
        assert registry.register(candidate, identity)
        result = ResearchEvaluator(registry).evaluate(candidate, identity, dataset_available=False, dataset_fresh=False)
        assert result.status == "blocked_missing_data"
        assert result.blocked_stage == "data_availability"
        assert registry.get(identity.fingerprint)["rejection_reason"]
    finally:
        registry.close()
