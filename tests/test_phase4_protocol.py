from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_signal_system.phase4_protocol import (
    DEFAULT_PROTOCOL_PATH,
    EXPECTED_PHASE4_FLOW_FINGERPRINT,
    PROTOCOL_VERSION,
    compute_protocol_fingerprint,
    load_verified_phase4_protocol,
)


def test_frozen_phase4_protocol_has_expected_version_and_fingerprint() -> None:
    protocol = load_verified_phase4_protocol(
        DEFAULT_PROTOCOL_PATH,
        expected_version=PROTOCOL_VERSION,
        expected_fingerprint=EXPECTED_PHASE4_FLOW_FINGERPRINT,
    )
    assert protocol["protocol_version"] == "v1"
    assert protocol["protocol_fingerprint_sha256"] == EXPECTED_PHASE4_FLOW_FINGERPRINT
    assert compute_protocol_fingerprint(protocol) == EXPECTED_PHASE4_FLOW_FINGERPRINT


def test_tampered_phase4_protocol_is_rejected(tmp_path: Path) -> None:
    protocol = json.loads(DEFAULT_PROTOCOL_PATH.read_text(encoding="utf-8"))
    protocol["flow_measure"]["aggregation_window_ms"] = 5000
    tampered = tmp_path / "phase4_flow_construction_v1.json"
    tampered.write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(RuntimeError, match="fingerprint mismatch"):
        load_verified_phase4_protocol(tampered, expected_fingerprint=EXPECTED_PHASE4_FLOW_FINGERPRINT)


def test_wrong_protocol_version_is_rejected(tmp_path: Path) -> None:
    protocol = json.loads(DEFAULT_PROTOCOL_PATH.read_text(encoding="utf-8"))
    protocol["protocol_version"] = "v2"
    tampered = tmp_path / "phase4_flow_construction_v2.json"
    tampered.write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(RuntimeError, match="version mismatch"):
        load_verified_phase4_protocol(tampered, expected_version="v1")
