#!/usr/bin/env python3
"""Read-only validator for engine_fidelity_harness_v2 pre-measurement freeze.

This validator must not load candidate strategies, create trial IDs, produce
returns/trades, download data, or update the ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_REL = Path("strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2.json")
SCHEMA_REL = Path("strategy_discovery_v1/second_collection_v1/schemas/engine_fidelity_measurement_freeze_package_v2.schema.json")
LEDGER_REL = Path("strategy_discovery_v1/data/global_trial_ledger.json")


def read_json(rel: str | Path):
    return json.loads((ROOT / rel).read_text())


def digest(rel: str | Path) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def validate_schema(package: dict) -> None:
    schema = read_json(SCHEMA_REL)
    errors = sorted(Draft202012Validator(schema).iter_errors(package), key=lambda e: list(e.path))
    if errors:
        joined = "\n".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise AssertionError(f"package schema validation failed:\n{joined}")


def validate_integrity(package: dict) -> None:
    assert_equal(digest(package["runtime"]["lock_path"]), package["runtime"]["lock_sha256"], "full runtime lock hash")
    assert_equal(digest(package["runtime"]["direct_lock_path"]), package["runtime"]["direct_lock_sha256"], "direct runtime lock hash")
    execution = package["execution_manifest"]
    assert_equal(digest(execution["path"]), execution["file_sha256"], "execution manifest filesystem hash")
    manifest = read_json(execution["path"])
    assert_equal(manifest.get("manifest_sha256"), execution["canonical_sha256"], "execution manifest canonical hash")

    data = package["data"]
    assert_equal(digest(data["main_manifest_path"]), data["main_manifest_sha256"], "main data manifest hash")
    assert_equal(digest(data["detail_manifest_path"]), data["detail_manifest_sha256"], "detail data manifest hash")
    source_manifest = read_json(data["main_manifest_path"])
    declared = {item["local_path"]: item for item in data["exact_csv_files"]}
    manifest_files = {item["local_path"]: item for item in source_manifest["files"]}
    assert_equal(set(declared), set(manifest_files), "exact CSV path set")
    for rel, item in declared.items():
        path = ROOT / rel
        if not path.is_file():
            raise AssertionError(f"missing declared CSV: {rel}")
        assert_equal(path.stat().st_size, item["byte_size"], f"CSV byte size {rel}")
        assert_equal(digest(rel), item["sha256"], f"CSV hash {rel}")
        assert_equal(item["sha256"], manifest_files[rel]["local_sha256"], f"manifest CSV hash {rel}")

    for ref_key, path_key, hash_key in [
        ("protocol_path", "protocol_path", "protocol_sha256"),
        ("dependency_pin_manifest_path", "dependency_pin_manifest_path", "dependency_pin_manifest_sha256"),
        ("source_evidence_path", "source_evidence_path", "source_evidence_sha256"),
        ("reassessment_path", "reassessment_path", "reassessment_sha256"),
        ("exclusion_resolution_path", "exclusion_resolution_path", "exclusion_resolution_sha256"),
    ]:
        refs = package["integrity_references"]
        rel = refs[path_key]
        assert_equal(digest(rel), refs[hash_key], f"integrity reference hash {ref_key}")

    assert_equal(package["engine"]["commit"], "eb1a668ceb0f29b7d578156bfc24c45278c0c0f8", "engine commit")
    assert_equal(package["technical_dependency"]["commit"], "720ff67483e346271165d49cf37265f78739c74c", "technical commit")
    assert_equal(package["strategy_source"]["commit"], "eff78d3ce3456b52c68a4e9a33cc055a56b801ff", "strategy source commit")


def validate_policy(package: dict) -> None:
    assert_equal(package["measurement_authorized"], False, "measurement authorization")
    assert_equal(package["new_trial_ids_authorized"], False, "trial authorization")
    for key, value in package["authorization"].items():
        assert_equal(value, False, f"authorization.{key}")
    assert_equal(package["pairlist_venue"]["dynamic_pairlist_allowed"], False, "dynamic pairlist")
    assert_equal(package["data"]["detail_scope"]["no_resampling"], True, "no resampling")
    assert_equal(package["data"]["detail_scope"]["timeframe"], "15m", "detail timeframe")
    assert_equal(package["execution_policy"]["precision_limits_policy"]["status"], "unresolved_external_exchange_metadata", "precision/limits status")
    assert_equal(package["execution_policy"]["precision_limits_policy"]["required_before_measurement"], True, "precision/limits gate")
    assert_equal(package["execution_policy"]["precision_limits_policy"]["missing_metadata_action"], "fail_closed", "missing precision/limits behavior")
    assert_equal(package["candidate_eligibility"]["final_status"], "conditional_not_measurement_ready", "candidate final status")
    assert_equal(package["candidate_eligibility"]["measurement_eligible_count"], 0, "measurement eligible count")
    assert_equal(package["candidate_eligibility"]["conditional_count"], 6, "conditional count")
    eligible = package["candidate_eligibility"]["conditional"]
    allowed = {"1h", "4h", "1d"}
    for item in eligible:
        if item["timeframe"] not in allowed or item["detail_timeframe"] != "15m" or item["status"] != "conditional_pending_engine_native_validation":
            raise AssertionError(f"invalid candidate timeframe/status mapping: {item}")
    excluded_paths = {item.get("source_path") for item in package["candidate_eligibility"]["remain_excluded"]}
    required_excluded = {
        "user_data/strategies/BreakEven.py",
        "user_data/strategies/Diamond.py",
        "user_data/strategies/PowerTower.py",
        "user_data/strategies/Strategy004.py",
        "user_data/strategies/GodStra.py",
    }
    if not required_excluded.issubset(excluded_paths):
        raise AssertionError(f"required historical exclusions missing: {sorted(required_excluded - excluded_paths)}")


def validate_ledger_immutable(package: dict) -> None:
    ledger = read_json(LEDGER_REL)
    assert_equal(len(ledger["trials"]), 898, "ledger trial count")
    assert_equal(ledger["last_sequence"], 898, "ledger last sequence")
    assert_equal(digest(LEDGER_REL), "9642d0daa824d2ab49d7f4018d72f9b5e2e29cdea13bdcb73cd8af69653722eb", "ledger filesystem hash")
    assert_equal(package["ledger"]["global_ledger_hash"], "2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e", "historical ledger canonical hash")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, help="optional common temporary audit clone root")
    parser.add_argument("--engine-root", type=Path, help="temporary Freqtrade engine audit clone root")
    parser.add_argument("--technical-root", type=Path, help="temporary technical dependency audit clone root")
    args = parser.parse_args()
    package = read_json(PACKAGE_REL)
    validate_schema(package)
    validate_integrity(package)
    validate_policy(package)
    validate_ledger_immutable(package)
    engine_root = args.engine_root or args.source_root
    technical_root = args.technical_root or args.source_root
    if engine_root and technical_root:
        for rel, expected in package["engine"]["file_hashes"].items():
            path = engine_root / rel
            if not path.is_file():
                raise AssertionError(f"missing pinned engine file in supplied source root: {path}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            assert_equal(actual, expected, f"pinned engine source hash {rel}")
        for rel, expected in package["technical_dependency"]["file_hashes"].items():
            path = technical_root / rel
            if not path.is_file():
                raise AssertionError(f"missing pinned technical file in supplied source root: {path}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            assert_equal(actual, expected, f"pinned technical source hash {rel}")
        source_notice = "source_clone_hashes=PASS"
    else:
        source_notice = "source_clone_hashes=DEFERRED(engine/technical clone roots not supplied)"
    print("FREEZE_VALIDATION=PASS")
    print("SCHEMA=PASS")
    print("INTEGRITY=PASS")
    print("POLICY=PASS")
    print("LEDGER_IMMUTABILITY=PASS")
    print(source_notice)
    print("MEASUREMENT=NOT_RUN")
    print("TRIAL_IDS_CREATED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
