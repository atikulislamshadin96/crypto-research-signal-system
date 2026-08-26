from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from crypto_signal_system.candidate_lifecycle import (
    BLOCKED,
    IN_PROGRESS,
    NOT_STARTED,
    PASSED,
    CandidateLifecycleRegistry,
    LifecycleError,
    PHASES,
)


FIXED = {
    "candidate_id": "candidate-a",
    "hypothesis_id": "liquidity-state-transition-eth-btc-v2",
    "candidate_version": "v2",
    "candidate_type": "primary_l2_event_study",
    "source": "authorized_restart_baseline",
    "market_type": "Bybit Linear/Perpetual",
    "universe": ("BTCUSDT", "ETHUSDT"),
    "protocol_versions": ("candidate_lifecycle_v1",),
    "protocol_fingerprints": ("candidate-protocol-a",),
    "provenance_refs": ("phase1-manifest:/tmp/phase1_l2_work/phase1_l2_drive_manifest.json",),
    "created_at": "2026-08-26T00:00:00Z",
}


def register(registry: CandidateLifecycleRegistry, candidate_id: str, hypothesis_id: str) -> None:
    values = dict(FIXED)
    values.update(candidate_id=candidate_id, hypothesis_id=hypothesis_id)
    registry.register_candidate(**values)


def start(registry: CandidateLifecycleRegistry, candidate_id: str, phase: int) -> None:
    registry.start_phase(
        candidate_id=candidate_id,
        phase_number=phase,
        protocol_version=f"protocol-{candidate_id}-{phase}",
        protocol_fingerprint=f"fingerprint-{candidate_id}-{phase}",
        input_data_manifest_hash=f"manifest-{candidate_id}-{phase}",
        commit_ref=f"commit-{candidate_id}-{phase}",
        event_at=f"2026-08-26T00:{phase:02d}:00Z",
    )


def pass_phase(registry: CandidateLifecycleRegistry, candidate_id: str, phase: int) -> None:
    registry.complete_phase(
        candidate_id=candidate_id,
        phase_number=phase,
        status=PASSED,
        result_hash=f"result-{candidate_id}-{phase}",
        event_at=f"2026-08-26T01:{phase:02d}:00Z",
    )


def test_two_candidates_progress_independently_and_no_global_pointer(tmp_path: Path) -> None:
    with CandidateLifecycleRegistry(tmp_path / "lifecycle.sqlite3") as registry:
        register(registry, "candidate-a", "hypothesis-a")
        register(registry, "candidate-b", "hypothesis-b")
        start(registry, "candidate-a", 2)
        pass_phase(registry, "candidate-a", 2)
        start(registry, "candidate-a", 3)
        start(registry, "candidate-b", 2)

        assert registry.get_phase("candidate-a", 3).status == IN_PROGRESS
        assert registry.get_phase("candidate-b", 2).status == IN_PROGRESS
        assert registry.get_phase("candidate-a", 4).status == NOT_STARTED
        assert registry.phase_statuses("candidate-a")[3] == IN_PROGRESS
        assert registry.phase_statuses("candidate-b")[2] == IN_PROGRESS
        assert not any("current_phase" in name for name in registry.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall())


def test_phase_skipping_requires_explicit_previous_pass(tmp_path: Path) -> None:
    with CandidateLifecycleRegistry(tmp_path / "lifecycle.sqlite3") as registry:
        register(registry, "candidate-a", "hypothesis-a")
        with pytest.raises(LifecycleError, match="phase 2"):
            start(registry, "candidate-a", 3)
        assert registry.get_phase("candidate-a", 3).status == NOT_STARTED


def test_invalid_state_transitions_and_duplicate_candidate_rejected(tmp_path: Path) -> None:
    with CandidateLifecycleRegistry(tmp_path / "lifecycle.sqlite3") as registry:
        register(registry, "candidate-a", "hypothesis-a")
        with pytest.raises(LifecycleError, match="already exists"):
            register(registry, "candidate-a", "hypothesis-a-duplicate")
        with pytest.raises(LifecycleError, match="invalid transition"):
            registry.complete_phase(candidate_id="candidate-a", phase_number=2, status=PASSED)
        start(registry, "candidate-a", 2)
        with pytest.raises(LifecycleError, match="invalid transition"):
            registry.start_phase(
                candidate_id="candidate-a",
                phase_number=2,
                protocol_version="protocol-a-2",
                protocol_fingerprint="fingerprint-a-2",
            )
        registry.complete_phase(candidate_id="candidate-a", phase_number=2, status=BLOCKED, reason="missing criterion")
        with pytest.raises(LifecycleError, match="invalid transition"):
            registry.complete_phase(candidate_id="candidate-a", phase_number=2, status=PASSED)


def test_completed_phase_and_protocol_fingerprint_are_immutable(tmp_path: Path) -> None:
    db = tmp_path / "lifecycle.sqlite3"
    with CandidateLifecycleRegistry(db) as registry:
        register(registry, "candidate-a", "hypothesis-a")
        start(registry, "candidate-a", 2)
        pass_phase(registry, "candidate-a", 2)
        with pytest.raises(sqlite3.IntegrityError, match="completed phase is immutable"):
            registry.connection.execute(
                "UPDATE lifecycle_phases SET result_hash='tampered' WHERE candidate_id='candidate-a' AND phase_number=2"
            )
        with pytest.raises(sqlite3.IntegrityError, match="phase protocol fingerprint is immutable"):
            registry.connection.execute(
                "UPDATE lifecycle_phases SET protocol_fingerprint='tampered' WHERE candidate_id='candidate-a' AND phase_number=2"
            )
        assert registry.get_phase("candidate-a", 2).result_hash == "result-candidate-a-2"


def test_frozen_oos_definition_is_immutable(tmp_path: Path) -> None:
    with CandidateLifecycleRegistry(tmp_path / "lifecycle.sqlite3") as registry:
        register(registry, "candidate-a", "hypothesis-a")
        kwargs = {
            "candidate_id": "candidate-a",
            "protocol_version": "oos-v1",
            "oos_start": "2025-01-01",
            "oos_end": "2025-03-31",
            "data_manifest_hash": "manifest-oos",
            "freeze_commit_ref": "commit-oos",
            "freeze_timestamp": "2026-08-26T02:00:00Z",
        }
        registry.freeze_oos(**kwargs)
        assert registry.freeze_oos(**kwargs).data_manifest_hash == "manifest-oos"
        changed = dict(kwargs, oos_end="2025-04-01")
        with pytest.raises(LifecycleError, match="cannot be mutated"):
            registry.freeze_oos(**changed)
        with pytest.raises(sqlite3.IntegrityError, match="frozen OOS definition is immutable"):
            registry.connection.execute(
                "UPDATE lifecycle_oos_freezes SET data_manifest_hash='tampered' WHERE candidate_id='candidate-a'"
            )


def test_history_reconstruction_and_fresh_restart_preserve_state(tmp_path: Path) -> None:
    db = tmp_path / "lifecycle.sqlite3"
    with CandidateLifecycleRegistry(db) as registry:
        register(registry, "candidate-a", "hypothesis-a")
        start(registry, "candidate-a", 2)
        pass_phase(registry, "candidate-a", 2)
        start(registry, "candidate-a", 3)
        history = registry.get_history("candidate-a")
        assert history[0].event_type == "candidate_created"
        assert history[-1].event_type == "phase_transition"
        assert [(item.from_status, item.to_status) for item in history if item.event_type == "phase_transition"] == [
            (NOT_STARTED, IN_PROGRESS),
            (IN_PROGRESS, PASSED),
            (NOT_STARTED, IN_PROGRESS),
        ]

    with CandidateLifecycleRegistry(db) as reopened:
        assert reopened.get_candidate("candidate-a").candidate_id == "candidate-a"
        assert reopened.get_phase("candidate-a", 2).status == PASSED
        assert reopened.get_phase("candidate-a", 3).status == IN_PROGRESS
        assert len(reopened.get_history("candidate-a")) == 11


def test_schema_is_versioned_and_has_seven_phases() -> None:
    schema_path = Path(__file__).parents[1] / "schemas" / "candidate_lifecycle_v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["$id"].endswith("candidate_lifecycle_v1.schema.json")
    assert schema["properties"]["schema_version"]["const"] == "candidate_lifecycle_v1"
    assert schema["properties"]["phases"]["minItems"] == len(PHASES)
    assert schema["properties"]["phases"]["maxItems"] == len(PHASES)
