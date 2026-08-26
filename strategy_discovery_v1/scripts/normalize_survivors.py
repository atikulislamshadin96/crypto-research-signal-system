#!/usr/bin/env python3
"""Conservatively normalize filtered discovery records.

The collection batches contain source metadata and abstracts. Unless a source
record has an independently verified deterministic rule disclosure locator and
structured rule payload, this stage rejects it as incomplete_disclosure. It
never invents entry, exit, SL/TP, sizing, timing, or cost rules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    inputs = sorted(input_dir.glob("filtered_candidates_batch_*.json"))
    if not inputs:
        raise SystemExit("no filtered candidate batches found")
    rejected: list[dict[str, object]] = []
    normalized: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    raw_count = 0
    for path in inputs:
        payload = json.loads(path.read_text())
        for source_record in payload["candidates"]:
            raw_count += 1
            # This first implementation intentionally requires structured rule
            # material, not merely a paper URL or abstract keyword.
            if source_record.get("rule_disclosure_status") != "verified_deterministic_rule" or not source_record.get("deterministic_rule_payload"):
                counts["incomplete_disclosure"] += 1
                rejected.append({
                    "document_id": source_record.get("document_id"),
                    "document_title": source_record.get("document_title"),
                    "source_class": source_record.get("source_class"),
                    "source_refs": [source_record.get("canonical_url")],
                    "rule_disclosure_locator": source_record.get("rule_disclosure_locator"),
                    "rejection_category": "incomplete_disclosure",
                    "reason": "No verified deterministic entry/exit/SL/TP/position-sizing payload was available at normalization time; abstract metadata was not interpreted as rules.",
                })
                continue
            rule_payload = source_record["deterministic_rule_payload"]
            normalized.append({
                "strategy_id": "sdv1-" + str(source_record["document_id"]).replace("/", "-").replace(".", "-"),
                "source_record": source_record,
                "rule_payload": rule_payload,
                "canonical_rule_hash": canonical_hash(rule_payload),
            })
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "normalization_version": "normalized_strategy_v1",
        "source_filter_version": "strategy_discovery_rejection_filter_v1",
        "input_batches": [str(path) for path in inputs],
        "filtered_candidate_count": raw_count,
        "normalized_candidate_count": len(normalized),
        "rejection_counts": dict(sorted(counts.items())),
        "normalized_candidates": normalized,
        "rejected_candidates": rejected,
        "rejection_reporting": "summary_counts_only_for_final_reports; detailed_records_retained_for_audit",
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"filtered": raw_count, "normalized": len(normalized), "rejection_counts": dict(sorted(counts.items())), "output": str(output)}, sort_keys=True))


if __name__ == "__main__":
    main()
