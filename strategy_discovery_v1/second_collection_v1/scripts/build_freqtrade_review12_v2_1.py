#!/usr/bin/env python3
"""Build the immutable review queue for the 12 non-rejected Freqtrade records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

INPUT = Path(__file__).resolve().parents[1] / "data" / "freqtrade_batch_001_pinned_source_evidence_v2_1.json"
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "freqtrade_batch_001_review12_v2_1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    records = [record for record in payload["records"] if record["re_evaluation_status"] == "needs_review"]
    if len(records) != 12:
        raise SystemExit(f"expected 12 needs_review records, found {len(records)}")
    queue = []
    for record in records:
        queue.append({
            "document_id": record["document_id"],
            "source_path": record["source_path"],
            "source_repo": record["source_repo"],
            "source_commit": record["source_commit"],
            "license": record["license"],
            "source_snapshot_sha256": record["source_snapshot_sha256"],
            "source_rule_fields": record["source_rule_fields"],
            "source_rule_status": record["source_rule_status"],
            "primary_signal_filter": record["primary_signal_filter"],
            "field_claims": record["field_claims"],
            "review_reasons": record["review_reasons"],
            "execution_assumption_status": record["execution_assumption_status"],
            "promotion_decision": record["promotion_decision"],
            "analysis_only": True,
            "backtest_run": False,
            "market_data_downloaded": False,
            "trial_created": False,
        })
    output = {
        "review_queue_version": "freqtrade_batch_001_review12_v2_1",
        "source_evidence_artifact": str(INPUT),
        "source_evidence_artifact_sha256": sha256(INPUT),
        "source_commit": payload["input_source_commit"],
        "source_repo": payload["source_repo"],
        "license": payload["license"],
        "review_count": len(queue),
        "review_scope": "instrument_applicability_timeframe_exit_semantics_and_unresolved_control_flow",
        "analysis_only": True,
        "backtest_run": False,
        "market_data_downloaded": False,
        "trial_created": False,
        "trial_ledger_n": 893,
        "records": queue,
    }
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"review_count": len(queue), "trial_ledger_n": 893, "output": str(OUTPUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
