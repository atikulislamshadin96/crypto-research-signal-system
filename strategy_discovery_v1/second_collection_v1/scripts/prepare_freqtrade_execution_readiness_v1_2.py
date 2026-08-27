#!/usr/bin/env python3
"""Link a frozen v1.2 manifest to source-complete Freqtrade records.

This is a readiness artifact only. It does not run a backtest, create a trial,
or increment the global ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reassessment", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    reassessment_path = Path(args.reassessment)
    manifest_path = Path(args.manifest)
    reassessment = json.loads(reassessment_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "frozen_pre_backtest" or manifest.get("manifest_sha256") is None:
        raise SystemExit("manifest is not frozen_pre_backtest with a hash")
    if manifest.get("scope", {}).get("batch_id") != "freqtrade-strategies-001":
        raise SystemExit("manifest batch scope mismatch")
    records = []
    for source_record in reassessment["records"]:
        ready = dict(source_record)
        ready["execution_assumption_manifest"] = {
            "manifest_id": manifest["manifest_id"],
            "manifest_sha256": manifest["manifest_sha256"],
            "status": "frozen",
        }
        ready["manifest_linkage"] = "uniform_external_assumption_manifest_v1_2"
        ready["backtest_authorized"] = False
        ready["trial_created"] = False
        if source_record["source_rule_status"] == "source_rule_complete":
            ready["execution_assumption_status"] = "execution_contract_complete"
            ready["research_contract_status"] = "execution_contract_complete"
            ready["readiness_decision"] = "eligible_for_pre_backtest_gates_only"
            ready["promotion_allowed"] = False
        else:
            ready["execution_assumption_status"] = "not_evaluated"
            ready["research_contract_status"] = "historical_filter_rejected" if source_record["re_evaluation_status"] == "filter_rejected_primary" else "needs_review"
            ready["readiness_decision"] = "blocked_by_frozen_primary_signal_filter" if source_record["re_evaluation_status"] == "filter_rejected_primary" else "blocked_by_source_rule_review"
            ready["promotion_allowed"] = False
        records.append(ready)
    output = {
        "readiness_version": "freqtrade_batch_001_execution_contract_readiness_v1_2",
        "source_reassessment": str(reassessment_path),
        "source_reassessment_sha256": sha256(reassessment_path),
        "manifest_path": str(manifest_path),
        "manifest_id": manifest["manifest_id"],
        "manifest_sha256": manifest["manifest_sha256"],
        "manifest_status": manifest["status"],
        "candidate_count": len(records),
        "research_contract_status_counts": {"execution_contract_complete": sum(r["research_contract_status"] == "execution_contract_complete" for r in records), "needs_review": sum(r["research_contract_status"] == "needs_review" for r in records), "historical_filter_rejected": sum(r["research_contract_status"] == "historical_filter_rejected" for r in records)},
        "analysis_only": True,
        "backtest_authorized": False,
        "backtest_run": False,
        "market_data_downloaded": False,
        "trial_created": False,
        "promotion_allowed": False,
        "trial_ledger_n": 893,
        "records": records,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(records), "research_contract_status_counts": output["research_contract_status_counts"], "manifest_sha256": manifest["manifest_sha256"], "backtest_authorized": False, "trial_ledger_n": 893}, sort_keys=True))


if __name__ == "__main__":
    main()
