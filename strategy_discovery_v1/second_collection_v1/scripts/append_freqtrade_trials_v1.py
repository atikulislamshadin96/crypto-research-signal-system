#!/usr/bin/env python3
"""Append the first measured Freqtrade trials to the cumulative ledger."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "strategy_discovery_v1" / "data" / "global_trial_ledger.json"
MEASURED = ROOT / "strategy_discovery_v1" / "second_collection_v1" / "data" / "freqtrade_batch_001_measured_backtest_v1.json"
PROTOCOL = ROOT / "strategy_discovery_v1" / "protocols" / "dsr_pbo_cpcv_v1.json"
ROUNDTRIP = ROOT / "strategy_discovery_v1" / "data" / "bybit_ohlcv_drive_roundtrip_manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(obj: object) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


def main() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    measured = json.loads(MEASURED.read_text(encoding="utf-8"))
    if ledger["last_sequence"] != 893 or ledger["n_trials"] != 893:
        raise SystemExit("ledger is not at required N=893 starting state")
    if measured["ledger_start_n"] != 893 or measured["measured_count"] != 5:
        raise SystemExit("measured batch does not match the authorized five-trial run")
    if measured["manifest_sha256"] != "041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97":
        raise SystemExit("unexpected execution manifest")
    existing_ids = {trial["trial_id"] for trial in ledger["trials"]}
    protocol_hash = sha256_bytes(PROTOCOL.read_bytes())
    data_hash = sha256_bytes(ROUNDTRIP.read_bytes())
    counted_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    new_trials = []
    for offset, result in enumerate(measured["results"], start=1):
        if result["trial_id"] in existing_ids:
            raise SystemExit(f"duplicate trial id: {result['trial_id']}")
        new_trials.append({
            "analysis_only": False,
            "batch_id": measured["batch_id"],
            "candidate_id": result["candidate_id"],
            "canonical_rule_hash": result["canonical_rule_hash"],
            "counted_at": counted_at,
            "data_manifest_hash": data_hash,
            "data_manifest_id": "bybit_linear_ohlcv_drive_roundtrip_v1",
            "execution_manifest_hash": result["execution_manifest_sha256"],
            "harness_profile_hash": result["harness_profile_sha256"],
            "harness_code_hash": result["harness_code_sha256"],
            "measurement": {
                "source_path": result["source_path"],
                "source_commit": measured["source_commit"],
                "source_snapshot_sha256": result["source_snapshot_sha256"],
                "timeframe": result["timeframe"],
                "pair_universe": result["pair_universe"],
                "trade_count_by_pair": result["trade_count_by_pair"],
                "return_series_sha256": result["return_series_sha256"],
                "return_series_observations": result["metrics"]["observations"],
                "statistical_outputs": {"dsr_calculated": False, "pbo_calculated": False, "cpcv_calculated": False, "reason": "statistical_outputs_are_appended_in_a_separate_versioned_artifact"},
                "source_rule_status": "source_rule_complete",
                "research_contract_status": "execution_contract_complete",
            },
            "metrics": {
                **result["metrics"],
                "backtest_run": True,
                "cpcv_calculated": False,
                "dsr_calculated": False,
                "measured": True,
                "normalized": False,
                "pbo_calculated": False,
                "selection_exposed": True,
            },
            "protocol_hash": protocol_hash,
            "protocol_id": measured["protocol_id"],
            "sequence": 893 + offset,
            "source": {
                "document_id": result["candidate_id"],
                "document_version": measured["source_commit"],
                "source_class": "freqtrade_strategy_repository",
                "source_id": "freqtrade_strategies",
                "source_refs": [f"{measured['source_repo']}/blob/{measured['source_commit']}/{result['source_path']}"],
                "source_snapshot": result["source_snapshot_sha256"],
            },
            "status": "measured_research_trial",
            "trial_id": result["trial_id"],
        })
    ledger["n_trials"] = 893 + len(new_trials)
    ledger["last_sequence"] = 893 + len(new_trials)
    ledger["analysis_only"] = False
    ledger["backtest_run"] = True
    ledger["market_data_downloaded"] = False
    ledger["trial_created"] = True
    ledger["status"] = "measured_research_trials_appended_statistical_gates_pending"
    ledger["latest_measured_batch"] = {
        "batch_id": measured["batch_id"],
        "append_count": len(new_trials),
        "candidate_universe_authorized": measured["candidate_universe_authorized"],
        "measured_count": measured["measured_count"],
        "predeclared_exclusion_count": measured["exclusion_count"],
        "measured_backtest_artifact_sha256": sha256_bytes(MEASURED.read_bytes()),
        "protocol_hash": protocol_hash,
        "data_manifest_hash": data_hash,
        "execution_manifest_hash": measured["manifest_sha256"],
        "harness_profile_hash": measured["harness_profile_sha256"],
        "statistical_gates_pending": True,
        "appended_at": counted_at,
    }
    ledger["trials"].extend(new_trials)
    ledger["global_ledger_hash"] = canonical_hash({k: v for k, v in ledger.items() if k != "global_ledger_hash"})
    LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"appended": len(new_trials), "n_trials": ledger["n_trials"], "last_sequence": ledger["last_sequence"], "global_ledger_hash": ledger["global_ledger_hash"], "trial_ids": [t["trial_id"] for t in new_trials]}, sort_keys=True))


if __name__ == "__main__":
    main()
