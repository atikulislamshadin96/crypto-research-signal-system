#!/usr/bin/env python3
"""Traceable, analysis-disabled Phase 4 runner scaffold.

This module performs only frozen-protocol and accepted-dataset preflight.  The
A/B/C/D stage functions are explicit refusal boundaries until a separate,
explicitly authorized implementation is added.  No outcome statistic is
computed here.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from crypto_signal_system.phase4_protocol import (
    DEFAULT_PROTOCOL_PATH,
    EXPECTED_PHASE4_FLOW_FINGERPRINT,
    PROTOCOL_VERSION,
    load_verified_phase4_protocol,
)

ROOT = Path(__file__).resolve().parents[1]
FLOW_MANIFEST_ROOT = ROOT / "data/flow/bybit_spot_trades/manifests"
L2_MANIFEST_ROOT = ROOT / "data/l2/manifests"
START_DATE = date(2025, 5, 1)
END_DATE_INCLUSIVE = date(2025, 7, 29)
END_EXCLUSIVE_ISO = "2025-07-30T00:00:00.000Z"
SYMBOLS = ("BTCUSDT", "ETHUSDT")


class Phase4PreflightError(RuntimeError):
    """Raised when frozen protocol or accepted-data gates fail."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_days() -> list[str]:
    return [
        (START_DATE + timedelta(days=i)).isoformat()
        for i in range((END_DATE_INCLUSIVE - START_DATE).days + 1)
    ]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive fail-closed boundary
        raise Phase4PreflightError(f"invalid_json:{path}:{exc}") from exc


def _require_pass_manifest(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise Phase4PreflightError(f"missing_{label}_manifest:{path}")
    manifest = _read_json(path)
    if manifest.get("status") != "PASS" or manifest.get("research_usable") is not True:
        raise Phase4PreflightError(f"{label}_manifest_not_pass:{path}")
    if manifest.get("errors"):
        raise Phase4PreflightError(f"{label}_manifest_errors:{path}")
    return manifest


def _verify_archive(path: Path, expected_sha256: str, label: str) -> None:
    if not path.exists():
        raise Phase4PreflightError(f"missing_{label}_archive:{path}")
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise Phase4PreflightError(
            f"{label}_archive_hash_mismatch:{path}:expected={expected_sha256}:actual={actual}"
        )


def verify_protocol() -> dict[str, Any]:
    protocol = load_verified_phase4_protocol(
        DEFAULT_PROTOCOL_PATH,
        expected_version=PROTOCOL_VERSION,
        expected_fingerprint=EXPECTED_PHASE4_FLOW_FINGERPRINT,
    )
    window = protocol.get("timestamp_alignment", {}).get("coverage_boundary", "")
    if END_EXCLUSIVE_ISO not in window:
        raise Phase4PreflightError("protocol_window_end_mismatch")
    if protocol.get("symbols") != list(SYMBOLS):
        raise Phase4PreflightError("protocol_symbol_scope_mismatch")
    if protocol.get("venue") != "Bybit":
        raise Phase4PreflightError("protocol_venue_mismatch")
    return protocol


def verify_accepted_datasets() -> dict[str, dict[str, int]]:
    days = expected_days()
    summary: dict[str, dict[str, int]] = {}
    for symbol in SYMBOLS:
        flow_days = l2_days = 0
        flow_events = l2_events = 0
        for day in days:
            flow = _require_pass_manifest(FLOW_MANIFEST_ROOT / symbol / f"{day}.json", "flow")
            flow_archive = ROOT / flow["archive_path"]
            _verify_archive(flow_archive, flow["archive_sha256"], "flow")
            flow_days += 1
            flow_events += int(flow.get("event_count", 0))

            l2 = _require_pass_manifest(L2_MANIFEST_ROOT / symbol / f"{day}.json", "l2")
            inputs = l2.get("input_files")
            if not isinstance(inputs, list) or len(inputs) != 1:
                raise Phase4PreflightError(f"l2_input_file_shape:{symbol}:{day}")
            l2_archive = ROOT / inputs[0]["path"]
            _verify_archive(l2_archive, inputs[0]["sha256"], "l2")
            l2_days += 1
            l2_events += int(l2.get("event_count", 0))
        if flow_days != 90 or l2_days != 90:
            raise Phase4PreflightError(f"incomplete_90_day_gate:{symbol}")
        summary[symbol] = {
            "flow_valid_days": flow_days,
            "l2_valid_days": l2_days,
            "flow_event_count": flow_events,
            "l2_event_count": l2_events,
        }
    return summary


def stage_a_l2_state_only(*, execute: bool = False) -> None:
    """A: frozen L2 state-only arm; statistical execution is intentionally disabled."""
    if not execute:
        raise Phase4PreflightError("phase4_analysis_disabled:A")


def stage_b_order_flow_only(*, execute: bool = False) -> None:
    """B: frozen signed-flow-only arm; statistical execution is intentionally disabled."""
    if not execute:
        raise Phase4PreflightError("phase4_analysis_disabled:B")


def stage_c_l2_plus_order_flow(*, execute: bool = False) -> None:
    """C: frozen L2-plus-flow arm; statistical execution is intentionally disabled."""
    if not execute:
        raise Phase4PreflightError("phase4_analysis_disabled:C")


def stage_d_matched_control(*, execute: bool = False) -> None:
    """D: frozen matched-control arm; statistical execution is intentionally disabled."""
    if not execute:
        raise Phase4PreflightError("phase4_analysis_disabled:D")


def build_traceable_scaffold() -> dict[str, Any]:
    """Verify prerequisites and emit a plan; never compute Phase 4 outcomes."""
    protocol = verify_protocol()
    datasets = verify_accepted_datasets()
    return {
        "runner_version": "phase4_traceable_scaffold_v1",
        "status": "READY_SCAFFOLD_ANALYSIS_DISABLED",
        "protocol_version": protocol["protocol_version"],
        "protocol_fingerprint_sha256": EXPECTED_PHASE4_FLOW_FINGERPRINT,
        "window": {
            "start_inclusive": "2025-05-01T00:00:00.000Z",
            "end_exclusive": END_EXCLUSIVE_ISO,
        },
        "symbols": list(SYMBOLS),
        "datasets": datasets,
        "stage_boundaries": {
            "A": "l2_state_only",
            "B": "order_flow_only",
            "C": "l2_state_plus_order_flow",
            "D": "matched_control",
        },
        "execution": {
            "outcome_statistics_computed": False,
            "forward_returns_computed": False,
            "bootstrap_computed": False,
            "fdr_computed": False,
            "bonferroni_computed": False,
            "analysis_enabled": False,
        },
        "frozen_scope_preserved": True,
    }


def main() -> None:
    result = build_traceable_scaffold()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
