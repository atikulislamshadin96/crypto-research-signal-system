"""Persistent, analysis-only lifecycle tracking for independent research candidates.

This module deliberately does not start or execute any research phase.  It stores
candidate identity, independent Phase 2--8 state, candidate-specific OOS freezes,
and append-only provenance history.  Historical records are not migrated here.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "candidate_lifecycle_v1"
PHASES = tuple(range(2, 9))
NOT_STARTED = "NOT_STARTED"
IN_PROGRESS = "IN_PROGRESS"
PASSED = "PASSED"
FAILED = "FAILED"
BLOCKED = "BLOCKED"
PHASE_STATUSES = frozenset({NOT_STARTED, IN_PROGRESS, PASSED, FAILED, BLOCKED})
TERMINAL_STATUSES = frozenset({PASSED, FAILED, BLOCKED})
ALLOWED_TRANSITIONS = {
    NOT_STARTED: frozenset({IN_PROGRESS}),
    IN_PROGRESS: frozenset({PASSED, FAILED, BLOCKED}),
    PASSED: frozenset(),
    FAILED: frozenset(),
    BLOCKED: frozenset(),
}


class LifecycleError(ValueError):
    """Raised when a lifecycle invariant or immutable record is violated."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _load_json(value: str) -> Any:
    return json.loads(value)


def _required_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LifecycleError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_text(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    return _required_text(name, value)


def _validate_phase(phase_number: int) -> int:
    if phase_number not in PHASES:
        raise LifecycleError(f"phase_number must be one of {PHASES}")
    return phase_number


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    hypothesis_id: str | None
    candidate_version: str
    candidate_type: str
    source: str
    market_type: str
    universe: tuple[str, ...]
    created_at: str
    protocol_versions: tuple[str, ...]
    protocol_fingerprints: tuple[str, ...]
    provenance_refs: tuple[str, ...]


@dataclass(frozen=True)
class PhaseRecord:
    candidate_id: str
    phase_number: int
    status: str
    started_at: str | None
    completed_at: str | None
    protocol_version: str | None
    protocol_fingerprint: str | None
    input_data_manifest_hash: str | None
    result_hash: str | None
    commit_ref: str | None
    reason: str | None


@dataclass(frozen=True)
class OOSFreeze:
    candidate_id: str
    protocol_version: str
    oos_start: str
    oos_end: str
    data_manifest_hash: str
    freeze_timestamp: str
    freeze_commit_ref: str


@dataclass(frozen=True)
class HistoryEvent:
    event_id: int
    candidate_id: str
    phase_number: int | None
    event_type: str
    from_status: str | None
    to_status: str | None
    event_at: str
    protocol_version: str | None
    protocol_fingerprint: str | None
    input_data_manifest_hash: str | None
    result_hash: str | None
    commit_ref: str | None
    reason: str | None
    payload: dict[str, Any]


class CandidateLifecycleRegistry:
    """SQLite-backed registry with no global current-phase pointer.

    Phase status is stored per ``(candidate_id, phase_number)``.  The registry
    never stores or derives a single global phase that controls all candidates.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "CandidateLifecycleRegistry":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS lifecycle_candidates (
                candidate_id TEXT PRIMARY KEY,
                hypothesis_id TEXT,
                candidate_version TEXT NOT NULL,
                candidate_type TEXT NOT NULL,
                source TEXT NOT NULL,
                market_type TEXT NOT NULL,
                universe_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                protocol_versions_json TEXT NOT NULL,
                protocol_fingerprints_json TEXT NOT NULL,
                provenance_refs_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lifecycle_phases (
                candidate_id TEXT NOT NULL,
                phase_number INTEGER NOT NULL CHECK (phase_number BETWEEN 2 AND 8),
                status TEXT NOT NULL CHECK (status IN ('NOT_STARTED','IN_PROGRESS','PASSED','FAILED','BLOCKED')),
                started_at TEXT,
                completed_at TEXT,
                protocol_version TEXT,
                protocol_fingerprint TEXT,
                input_data_manifest_hash TEXT,
                result_hash TEXT,
                commit_ref TEXT,
                reason TEXT,
                PRIMARY KEY (candidate_id, phase_number),
                FOREIGN KEY (candidate_id) REFERENCES lifecycle_candidates(candidate_id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS lifecycle_oos_freezes (
                candidate_id TEXT PRIMARY KEY,
                protocol_version TEXT NOT NULL,
                oos_start TEXT NOT NULL,
                oos_end TEXT NOT NULL,
                data_manifest_hash TEXT NOT NULL,
                freeze_timestamp TEXT NOT NULL,
                freeze_commit_ref TEXT NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES lifecycle_candidates(candidate_id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS lifecycle_history (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT NOT NULL,
                phase_number INTEGER CHECK (phase_number IS NULL OR phase_number BETWEEN 2 AND 8),
                event_type TEXT NOT NULL,
                from_status TEXT,
                to_status TEXT,
                event_at TEXT NOT NULL,
                protocol_version TEXT,
                protocol_fingerprint TEXT,
                input_data_manifest_hash TEXT,
                result_hash TEXT,
                commit_ref TEXT,
                reason TEXT,
                payload_json TEXT NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES lifecycle_candidates(candidate_id) ON DELETE RESTRICT
            );

            CREATE TRIGGER IF NOT EXISTS lifecycle_history_no_update
            BEFORE UPDATE ON lifecycle_history
            BEGIN
                SELECT RAISE(ABORT, 'lifecycle history is append-only');
            END;

            CREATE TRIGGER IF NOT EXISTS lifecycle_history_no_delete
            BEFORE DELETE ON lifecycle_history
            BEGIN
                SELECT RAISE(ABORT, 'lifecycle history is append-only');
            END;

            CREATE TRIGGER IF NOT EXISTS lifecycle_candidate_no_update
            BEFORE UPDATE ON lifecycle_candidates
            BEGIN
                SELECT RAISE(ABORT, 'candidate identity is immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS lifecycle_candidate_no_delete
            BEFORE DELETE ON lifecycle_candidates
            BEGIN
                SELECT RAISE(ABORT, 'candidate identity is immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS lifecycle_oos_no_update
            BEFORE UPDATE ON lifecycle_oos_freezes
            BEGIN
                SELECT RAISE(ABORT, 'frozen OOS definition is immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS lifecycle_oos_no_delete
            BEFORE DELETE ON lifecycle_oos_freezes
            BEGIN
                SELECT RAISE(ABORT, 'frozen OOS definition is immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS lifecycle_terminal_phase_no_update
            BEFORE UPDATE ON lifecycle_phases
            WHEN OLD.status IN ('PASSED','FAILED','BLOCKED')
            BEGIN
                SELECT RAISE(ABORT, 'completed phase is immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS lifecycle_phase_protocol_version_no_change
            BEFORE UPDATE ON lifecycle_phases
            WHEN OLD.protocol_version IS NOT NULL
                 AND (NEW.protocol_version IS NULL OR NEW.protocol_version <> OLD.protocol_version)
            BEGIN
                SELECT RAISE(ABORT, 'phase protocol version is immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS lifecycle_phase_protocol_fingerprint_no_change
            BEFORE UPDATE ON lifecycle_phases
            WHEN OLD.protocol_fingerprint IS NOT NULL
                 AND (NEW.protocol_fingerprint IS NULL OR NEW.protocol_fingerprint <> OLD.protocol_fingerprint)
            BEGIN
                SELECT RAISE(ABORT, 'phase protocol fingerprint is immutable');
            END;
            """
        )
        self.connection.commit()

    def register_candidate(
        self,
        *,
        candidate_id: str,
        hypothesis_id: str | None,
        candidate_version: str,
        candidate_type: str,
        source: str,
        market_type: str,
        universe: Iterable[str],
        protocol_versions: Iterable[str] = (),
        protocol_fingerprints: Iterable[str] = (),
        provenance_refs: Iterable[str] = (),
        created_at: str | None = None,
    ) -> Candidate:
        candidate_id = _required_text("candidate_id", candidate_id)
        candidate_version = _required_text("candidate_version", candidate_version)
        candidate_type = _required_text("candidate_type", candidate_type)
        source = _required_text("source", source)
        market_type = _required_text("market_type", market_type)
        hypothesis_id = _optional_text("hypothesis_id", hypothesis_id)
        universe_values = tuple(_required_text("universe item", item) for item in universe)
        if not universe_values or len(set(universe_values)) != len(universe_values):
            raise LifecycleError("universe must be non-empty and unique")
        protocol_values = tuple(_required_text("protocol version", item) for item in protocol_versions)
        fingerprint_values = tuple(_required_text("protocol fingerprint", item) for item in protocol_fingerprints)
        provenance_values = tuple(_required_text("provenance reference", item) for item in provenance_refs)
        created_at = created_at or utc_now()
        try:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO lifecycle_candidates
                    (candidate_id, hypothesis_id, candidate_version, candidate_type, source,
                     market_type, universe_json, created_at, protocol_versions_json,
                     protocol_fingerprints_json, provenance_refs_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate_id,
                        hypothesis_id,
                        candidate_version,
                        candidate_type,
                        source,
                        market_type,
                        _json(universe_values),
                        created_at,
                        _json(protocol_values),
                        _json(fingerprint_values),
                        _json(provenance_values),
                    ),
                )
                for phase_number in PHASES:
                    self.connection.execute(
                        "INSERT INTO lifecycle_phases (candidate_id, phase_number, status) VALUES (?, ?, ?)",
                        (candidate_id, phase_number, NOT_STARTED),
                    )
                self._append_history(
                    candidate_id=candidate_id,
                    event_type="candidate_created",
                    reason="candidate identity registered; no research phase started",
                    payload={"schema_version": SCHEMA_VERSION},
                )
                for phase_number in PHASES:
                    self._append_history(
                        candidate_id=candidate_id,
                        phase_number=phase_number,
                        event_type="phase_initialized",
                        from_status=None,
                        to_status=NOT_STARTED,
                        payload={"schema_version": SCHEMA_VERSION},
                    )
        except sqlite3.IntegrityError as exc:
            raise LifecycleError(f"candidate_id already exists: {candidate_id}") from exc
        return self.get_candidate(candidate_id)

    def get_candidate(self, candidate_id: str) -> Candidate:
        row = self.connection.execute(
            "SELECT * FROM lifecycle_candidates WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
        if row is None:
            raise LifecycleError(f"unknown candidate_id: {candidate_id}")
        return Candidate(
            candidate_id=row["candidate_id"],
            hypothesis_id=row["hypothesis_id"],
            candidate_version=row["candidate_version"],
            candidate_type=row["candidate_type"],
            source=row["source"],
            market_type=row["market_type"],
            universe=tuple(_load_json(row["universe_json"])),
            created_at=row["created_at"],
            protocol_versions=tuple(_load_json(row["protocol_versions_json"])),
            protocol_fingerprints=tuple(_load_json(row["protocol_fingerprints_json"])),
            provenance_refs=tuple(_load_json(row["provenance_refs_json"])),
        )

    def get_phase(self, candidate_id: str, phase_number: int) -> PhaseRecord:
        _validate_phase(phase_number)
        row = self.connection.execute(
            "SELECT * FROM lifecycle_phases WHERE candidate_id = ? AND phase_number = ?",
            (candidate_id, phase_number),
        ).fetchone()
        if row is None:
            raise LifecycleError(f"unknown candidate or phase: {candidate_id}, {phase_number}")
        return PhaseRecord(
            candidate_id=row["candidate_id"],
            phase_number=row["phase_number"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            protocol_version=row["protocol_version"],
            protocol_fingerprint=row["protocol_fingerprint"],
            input_data_manifest_hash=row["input_data_manifest_hash"],
            result_hash=row["result_hash"],
            commit_ref=row["commit_ref"],
            reason=row["reason"],
        )

    def transition_phase(
        self,
        *,
        candidate_id: str,
        phase_number: int,
        to_status: str,
        protocol_version: str | None = None,
        protocol_fingerprint: str | None = None,
        input_data_manifest_hash: str | None = None,
        result_hash: str | None = None,
        commit_ref: str | None = None,
        reason: str | None = None,
        event_at: str | None = None,
    ) -> PhaseRecord:
        _validate_phase(phase_number)
        if to_status not in PHASE_STATUSES or to_status == NOT_STARTED:
            raise LifecycleError(f"to_status must be one of {IN_PROGRESS, PASSED, FAILED, BLOCKED}")
        if protocol_version is not None:
            protocol_version = _required_text("protocol_version", protocol_version)
        if protocol_fingerprint is not None:
            protocol_fingerprint = _required_text("protocol_fingerprint", protocol_fingerprint)
        if input_data_manifest_hash is not None:
            input_data_manifest_hash = _required_text("input_data_manifest_hash", input_data_manifest_hash)
        if result_hash is not None:
            result_hash = _required_text("result_hash", result_hash)
        if commit_ref is not None:
            commit_ref = _required_text("commit_ref", commit_ref)
        if reason is not None:
            reason = _required_text("reason", reason)
        current = self.get_phase(candidate_id, phase_number)
        if to_status not in ALLOWED_TRANSITIONS[current.status]:
            raise LifecycleError(f"invalid transition {current.status} -> {to_status}")
        if to_status == IN_PROGRESS:
            if protocol_version is None or protocol_fingerprint is None:
                raise LifecycleError("starting a phase requires protocol_version and protocol_fingerprint")
        if to_status == IN_PROGRESS and phase_number > 2:
            previous = self.get_phase(candidate_id, phase_number - 1)
            if previous.status != PASSED:
                raise LifecycleError(
                    f"phase {phase_number} is blocked until phase {phase_number - 1} has an explicit PASS"
                )
        if to_status == BLOCKED and reason is None:
            reason = "blocked: promotion criterion or required evidence is not available"
        timestamp = event_at or utc_now()
        protocol_version = protocol_version if protocol_version is not None else current.protocol_version
        protocol_fingerprint = protocol_fingerprint if protocol_fingerprint is not None else current.protocol_fingerprint
        input_data_manifest_hash = (
            input_data_manifest_hash if input_data_manifest_hash is not None else current.input_data_manifest_hash
        )
        commit_ref = commit_ref if commit_ref is not None else current.commit_ref
        reason = reason if reason is not None else current.reason
        started_at = timestamp if to_status == IN_PROGRESS else current.started_at
        completed_at = timestamp if to_status in TERMINAL_STATUSES else current.completed_at
        with self.connection:
            self.connection.execute(
                """
                UPDATE lifecycle_phases
                SET status=?, started_at=?, completed_at=?, protocol_version=?,
                    protocol_fingerprint=?, input_data_manifest_hash=?, result_hash=?,
                    commit_ref=?, reason=?
                WHERE candidate_id=? AND phase_number=? AND status=?
                """,
                (
                    to_status,
                    started_at,
                    completed_at,
                    protocol_version,
                    protocol_fingerprint,
                    input_data_manifest_hash,
                    result_hash,
                    commit_ref,
                    reason,
                    candidate_id,
                    phase_number,
                    current.status,
                ),
            )
            self._append_history(
                candidate_id=candidate_id,
                phase_number=phase_number,
                event_type="phase_transition",
                from_status=current.status,
                to_status=to_status,
                event_at=timestamp,
                protocol_version=protocol_version,
                protocol_fingerprint=protocol_fingerprint,
                input_data_manifest_hash=input_data_manifest_hash,
                result_hash=result_hash,
                commit_ref=commit_ref,
                reason=reason,
                payload={"schema_version": SCHEMA_VERSION},
            )
        return self.get_phase(candidate_id, phase_number)

    def start_phase(self, **kwargs: Any) -> PhaseRecord:
        kwargs["to_status"] = IN_PROGRESS
        return self.transition_phase(**kwargs)

    def complete_phase(self, **kwargs: Any) -> PhaseRecord:
        to_status = kwargs.pop("status", None)
        if to_status not in TERMINAL_STATUSES:
            raise LifecycleError("complete_phase status must be PASSED, FAILED, or BLOCKED")
        kwargs["to_status"] = to_status
        return self.transition_phase(**kwargs)

    def freeze_oos(
        self,
        *,
        candidate_id: str,
        protocol_version: str,
        oos_start: str,
        oos_end: str,
        data_manifest_hash: str,
        freeze_commit_ref: str,
        freeze_timestamp: str | None = None,
    ) -> OOSFreeze:
        self.get_candidate(candidate_id)
        values = (
            _required_text("protocol_version", protocol_version),
            _required_text("oos_start", oos_start),
            _required_text("oos_end", oos_end),
            _required_text("data_manifest_hash", data_manifest_hash),
            _required_text("freeze_timestamp", freeze_timestamp) if freeze_timestamp is not None else utc_now(),
            _required_text("freeze_commit_ref", freeze_commit_ref),
        )
        existing = self.connection.execute(
            "SELECT * FROM lifecycle_oos_freezes WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
        if existing is not None:
            existing_values = tuple(existing[key] for key in (
                "protocol_version", "oos_start", "oos_end", "data_manifest_hash",
                "freeze_timestamp", "freeze_commit_ref",
            ))
            if existing_values != values:
                raise LifecycleError("frozen OOS definition cannot be mutated")
            return self.get_oos_freeze(candidate_id)
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO lifecycle_oos_freezes
                (candidate_id, protocol_version, oos_start, oos_end, data_manifest_hash,
                 freeze_timestamp, freeze_commit_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (candidate_id, *values),
            )
            self._append_history(
                candidate_id=candidate_id,
                event_type="oos_frozen",
                protocol_version=values[0],
                input_data_manifest_hash=values[3],
                commit_ref=values[5],
                reason="candidate-specific final-OOS definition frozen; no result-driven split selection performed",
                payload={"oos_start": values[1], "oos_end": values[2], "schema_version": SCHEMA_VERSION},
            )
        return self.get_oos_freeze(candidate_id)

    def get_oos_freeze(self, candidate_id: str) -> OOSFreeze:
        row = self.connection.execute(
            "SELECT * FROM lifecycle_oos_freezes WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
        if row is None:
            raise LifecycleError(f"no OOS freeze for candidate_id: {candidate_id}")
        return OOSFreeze(
            candidate_id=row["candidate_id"],
            protocol_version=row["protocol_version"],
            oos_start=row["oos_start"],
            oos_end=row["oos_end"],
            data_manifest_hash=row["data_manifest_hash"],
            freeze_timestamp=row["freeze_timestamp"],
            freeze_commit_ref=row["freeze_commit_ref"],
        )

    def get_history(self, candidate_id: str) -> list[HistoryEvent]:
        self.get_candidate(candidate_id)
        rows = self.connection.execute(
            "SELECT * FROM lifecycle_history WHERE candidate_id = ? ORDER BY event_id", (candidate_id,)
        ).fetchall()
        return [
            HistoryEvent(
                event_id=row["event_id"],
                candidate_id=row["candidate_id"],
                phase_number=row["phase_number"],
                event_type=row["event_type"],
                from_status=row["from_status"],
                to_status=row["to_status"],
                event_at=row["event_at"],
                protocol_version=row["protocol_version"],
                protocol_fingerprint=row["protocol_fingerprint"],
                input_data_manifest_hash=row["input_data_manifest_hash"],
                result_hash=row["result_hash"],
                commit_ref=row["commit_ref"],
                reason=row["reason"],
                payload=_load_json(row["payload_json"]),
            )
            for row in rows
        ]

    def phase_statuses(self, candidate_id: str) -> dict[int, str]:
        self.get_candidate(candidate_id)
        rows = self.connection.execute(
            "SELECT phase_number, status FROM lifecycle_phases WHERE candidate_id = ? ORDER BY phase_number",
            (candidate_id,),
        ).fetchall()
        return {int(row["phase_number"]): row["status"] for row in rows}

    def _append_history(
        self,
        *,
        candidate_id: str,
        event_type: str,
        phase_number: int | None = None,
        from_status: str | None = None,
        to_status: str | None = None,
        event_at: str | None = None,
        protocol_version: str | None = None,
        protocol_fingerprint: str | None = None,
        input_data_manifest_hash: str | None = None,
        result_hash: str | None = None,
        commit_ref: str | None = None,
        reason: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO lifecycle_history
            (candidate_id, phase_number, event_type, from_status, to_status, event_at,
             protocol_version, protocol_fingerprint, input_data_manifest_hash, result_hash,
             commit_ref, reason, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                phase_number,
                event_type,
                from_status,
                to_status,
                event_at or utc_now(),
                protocol_version,
                protocol_fingerprint,
                input_data_manifest_hash,
                result_hash,
                commit_ref,
                reason,
                _json(payload or {}),
            ),
        )


__all__ = [
    "ALLOWED_TRANSITIONS",
    "BLOCKED",
    "Candidate",
    "CandidateLifecycleRegistry",
    "FAILED",
    "HistoryEvent",
    "IN_PROGRESS",
    "LifecycleError",
    "NOT_STARTED",
    "OOSFreeze",
    "PASSED",
    "PHASES",
    "PhaseRecord",
    "SCHEMA_VERSION",
]
