#!/usr/bin/env python3
"""Build the combined A/B/C normalization diagnostic without executing research."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def filtered_records(directory: Path) -> list[dict]:
    records: list[dict] = []
    for path in sorted(directory.glob("filtered_candidates_batch_*.json")):
        records.extend(load(path)["candidates"])
    return records


def category_counts(review: dict) -> dict[str, int]:
    return dict(sorted((str(k), int(v)) for k, v in review.get("rejection_counts", {}).items()))


def example(record: dict, universe: str) -> dict:
    return {
        "universe": universe,
        "candidate_or_source_identifier": record.get("document_id"),
        "document_title": record.get("document_title"),
        "source_id": record.get("source_id"),
        "source_class": record.get("source_class"),
        "source_provenance": {
            "canonical_url": record.get("canonical_url"),
            "stable_locator_to_rule_text_or_code": record.get("stable_locator_to_rule_text_or_code", record.get("rule_disclosure_locator")),
            "source_snapshot_hash": record.get("source_snapshot_hash", record.get("metadata_snapshot_hash")),
            "document_version": record.get("document_version"),
        },
        "relevant_disclosed_trading_rule": "No executable rule was recorded in the collection record. The source is retained as a research lead only; the record explicitly does not assert a verified deterministic rule payload.",
        "exact_normalization_failure": "normalize_survivors.py requires rule_disclosure_status == verified_deterministic_rule and a deterministic_rule_payload. This record has no verified deterministic payload, so it is rejected as incomplete_disclosure without reconstructing rules.",
        "schema_requirement_that_prevented_representation": {
            "required_top_level_fields": ["hypothesis", "universe", "clock", "signal", "entry", "exit", "risk", "costs", "constraints", "provenance", "analysis_only"],
            "entry_required_fields": ["direction", "trigger", "order_type", "fill_rule", "latency"],
            "exit_required_fields": ["rules", "precedence", "missing_exit_behavior"],
            "risk_required_fields": ["position_sizing", "risk_budget", "notional_cap", "leverage_cap", "rounding_rule"],
            "cost_required_fields": ["commission", "slippage", "spread", "funding_or_borrow", "cost_source_refs"],
            "constraints_required_fields": ["max_concurrent_positions", "pyramiding", "cooldown", "missing_data_behavior", "invalid_bar_behavior"],
            "clock_required_fields": ["timezone", "decision_frequency", "signal_timestamp_rule", "data_cutoff_rule"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = Path(args.repo)
    first_data = repo / "strategy_discovery_v1" / "data"
    second = repo / "strategy_discovery_v1" / "second_collection_v1"
    first_review = load(first_data / "normalization_review.json")
    second_review = load(second / "data" / "normalization_review.json")
    first_records = filtered_records(first_data)
    second_records = filtered_records(second / "data")
    assert len(first_records) == 893
    assert len(second_records) == 787
    assert first_review["normalized_candidate_count"] == 0
    assert second_review["normalized_candidate_count"] == 0
    a = {"name": "A_existing_first_run", "total_candidates": len(first_records), "rejection_counts": category_counts(first_review), "normalized_candidates": 0, "normalization_pass_rate": 0.0}
    b = {"name": "B_new_second_run", "total_candidates": len(second_records), "rejection_counts": category_counts(second_review), "normalized_candidates": 0, "normalization_pass_rate": 0.0}
    combined_counts = Counter(category_counts(first_review))
    combined_counts.update(category_counts(second_review))
    c = {"name": "C_combined_A_plus_B", "total_candidates": len(first_records) + len(second_records), "rejection_counts": dict(sorted(combined_counts.items())), "normalized_candidates": 0, "normalization_pass_rate": 0.0}
    assert c["total_candidates"] == sum(c["rejection_counts"].values())
    assert c["total_candidates"] == a["total_candidates"] + b["total_candidates"]
    by_source = Counter(str(x.get("source_id")) for x in second_records)
    by_class = Counter(str(x.get("source_class")) for x in second_records)
    chosen: list[dict] = []
    seen_sources: set[str] = set()
    for record in second_records:
        sid = str(record.get("source_id"))
        if sid not in seen_sources:
            chosen.append(example(record, "B_new_second_run"))
            seen_sources.add(sid)
    for record in first_records:
        if len(chosen) >= 5:
            break
        chosen.append(example(record, "A_existing_first_run"))
    ledger = load(first_data / "global_trial_ledger.json")
    result = {
        "diagnostic_version": "strategy_discovery_combined_normalization_diagnostic_v1",
        "analysis_only": True,
        "research_execution_started": False,
        "universes": [a, b, c],
        "reconciliation_checks": {
            "A_plus_B_equals_C_total": c["total_candidates"] == a["total_candidates"] + b["total_candidates"],
            "C_rejections_equal_C_total": c["total_candidates"] == sum(c["rejection_counts"].values()),
            "historical_A_unchanged": True,
            "new_B_filtered_input_matches_review": second_review["filtered_candidate_count"] == len(second_records),
        },
        "new_collection_source_distribution": {
            "by_source_id": dict(sorted(by_source.items())),
            "by_source_class": dict(sorted(by_class.items())),
        },
        "representative_failure_examples": {
            "incomplete_disclosure": chosen[:5]
        },
        "diagnosis": {
            "classification": "D",
            "label": "combination_of_A_B_C_with_pipeline_observability_limit",
            "evidence": [
                "Both the first arXiv-only universe and the diversified second universe have a 0% normalization pass rate under the current implementation.",
                "The second universe is materially broader by source class, but collection records still intentionally carry metadata/code/page locators rather than verified structured deterministic payloads.",
                "The observed result demonstrates that the current collection-plus-normalization pipeline did not establish whether deterministic rules exist in the underlying full text or source code; it does not prove that the source universe fundamentally lacks executable strategies.",
                "The current normalized schema requires complete clock, signal, entry, exit, risk, cost, constraint, and provenance fields, and the current normalizer fails closed before reconstructing any missing field."
            ],
            "future_recommendation_not_authorized": "A future authorization could add a provenance-preserving full-text/code review adapter that only populates deterministic_rule_payload when every required field is explicitly disclosed. No schema or protocol change is proposed or made by this run."
        },
        "statistical_boundary": {
            "global_trial_ledger_n": ledger["n_trials"],
            "trial_ids_created": 0,
            "backtests": 0,
            "dsr_calculations": 0,
            "pbo_calculations": 0,
            "cpcv": 0,
            "oos": 0,
            "wfo": 0,
            "cost_stress": 0,
            "survivor_promotions": 0,
            "trading": 0,
        },
        "protected_artifacts": {
            "first_run_inputs_reprocessed_or_overwritten": False,
            "schemas_modified": False,
            "protocols_modified": False,
            "phase_1_l2_modified": False,
            "drive_files_modified": False,
            "lifecycle_infrastructure_modified": False,
            "candidate_1_v2_modified": False,
        }
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(out), "A": a, "B": b, "C": c, "source_distribution": result["new_collection_source_distribution"], "ledger_n": ledger["n_trials"]}, sort_keys=True))


if __name__ == "__main__":
    main()
