import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/run_phase4_order_flow_overlay.py"
SPEC = importlib.util.spec_from_file_location("phase4_runner_scaffold", MODULE_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_runner_window_and_protocol_lock():
    assert runner.END_EXCLUSIVE_ISO == "2025-07-30T00:00:00.000Z"
    assert runner.expected_days()[0] == "2025-05-01"
    assert runner.expected_days()[-1] == "2025-07-29"
    assert len(runner.expected_days()) == 90
    protocol = runner.verify_protocol()
    assert protocol["protocol_version"] == "v1"
    assert protocol["protocol_fingerprint_sha256"] == runner.EXPECTED_PHASE4_FLOW_FINGERPRINT


def test_runner_has_explicit_nonexecuting_abcd_boundaries():
    for stage in (
        runner.stage_a_l2_state_only,
        runner.stage_b_order_flow_only,
        runner.stage_c_l2_plus_order_flow,
        runner.stage_d_matched_control,
    ):
        with pytest.raises(runner.Phase4PreflightError, match="phase4_analysis_disabled"):
            stage()


def test_runner_rejects_tampered_protocol(tmp_path):
    original = (ROOT / "protocols/phase4_flow_construction_v1.json").read_text(encoding="utf-8")
    tampered = tmp_path / "phase4_flow_construction_v1.json"
    tampered.write_text(original.replace('"venue": "Bybit"', '"venue": "NOT_BYBIT"'), encoding="utf-8")
    with pytest.raises(RuntimeError, match="fingerprint mismatch"):
        runner.load_verified_phase4_protocol(
            tampered,
            expected_version=runner.PROTOCOL_VERSION,
            expected_fingerprint=runner.EXPECTED_PHASE4_FLOW_FINGERPRINT,
        )
