#!/usr/bin/env python3
"""Non-measured Freqtrade re-evaluation under flexible completeness v2.

This script consumes only the existing structured batch and its short evidence
snippets. It never fetches code, runs a backtest, edits the historical filter,
or creates a trial. Partial/opaque entry snippets are sent to review.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

EXECUTION_FIELDS = (
    "instrument_universe", "venue", "quote_currency", "position_sizing",
    "risk_budget", "notional_cap", "leverage_cap", "commission", "slippage",
    "spread", "fill_rule", "latency", "funding_or_borrow", "external_config",
    "missing_data_behavior", "invalid_bar_behavior",
)
BANNED_INDICATOR_PARTS = ("rsi", "ema", "sma", "macd", "bollinger", "stochastic")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def snippet_text(record: dict, key: str) -> str:
    snippet = record.get("evidence_bundle", {}).get("snippets", {}).get(key, {})
    return str(snippet.get("verbatim", ""))


def parse_snippet(record: dict, key: str) -> tuple[ast.AST | None, str | None]:
    raw = snippet_text(record, key)
    if not raw.strip():
        return None, f"{key}_evidence_missing"
    try:
        return ast.parse(textwrap.dedent(raw)), None
    except SyntaxError as exc:
        return None, f"{key}_snippet_not_parseable:{exc.msg}"


def has_entry_write(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    return any(
        isinstance(child, ast.Constant) and child.value in {"enter_long", "enter_short"}
        for target in node.targets
        for child in ast.walk(target)
    )


def has_exit_write(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    return any(
        isinstance(child, ast.Constant) and child.value in {"exit_long", "exit_short"}
        for target in node.targets
        for child in ast.walk(target)
    )


def indicator_names(tree: ast.AST) -> list[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            token = node.id.lower()
            if any(part in token for part in BANNED_INDICATOR_PARTS):
                names.add(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            token = node.value.lower()
            if any(part in token for part in BANNED_INDICATOR_PARTS):
                names.add(node.value)
    return sorted(names)


def entry_condition_expressions(node: ast.AST) -> list[ast.AST]:
    expressions: list[ast.AST] = []
    if not isinstance(node, ast.Assign):
        return expressions
    for target in node.targets:
        if isinstance(target, ast.Subscript):
            sliced = target.slice
            if isinstance(sliced, ast.Tuple) and sliced.elts:
                expressions.append(sliced.elts[0])
            elif not isinstance(sliced, ast.Constant):
                expressions.append(sliced)
    return expressions


def primary_signal_filter(record: dict) -> dict:
    """Use only direct entry-test AST, not whole-file indicator tokens."""
    raw = snippet_text(record, "entry")
    tree, parse_error = parse_snippet(record, "entry")
    if parse_error:
        return {"decision": "review", "category": "primary_signal_unresolved", "reason": parse_error, "evidence": {"snippet": raw[:1600]}}
    assert tree is not None
    writes = [node for node in ast.walk(tree) if has_entry_write(node)]
    if not writes:
        return {"decision": "review", "category": "primary_signal_unresolved", "reason": "no_explicit_entry_field_write_in_snippet", "evidence": {"snippet": raw[:1600]}}
    direct_tests: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and any(has_entry_write(child) for child in ast.walk(node)):
            direct_tests.append(node.test)
    for write in writes:
        direct_tests.extend(entry_condition_expressions(write))
    direct_tree = ast.Module(body=direct_tests, type_ignores=[])
    banned = indicator_names(direct_tree)
    if banned:
        return {"decision": "reject", "category": "lagging_indicator_primary", "evidence": {"entry_tokens": banned, "snippet": raw[:1600]}}
    opaque_names = {"conditions", "condition", "entry_condition", "entry_conditions"}
    if any(isinstance(node, ast.Name) and node.id in opaque_names for node in ast.walk(direct_tree)):
        return {"decision": "review", "category": "primary_signal_unresolved", "reason": "entry_condition_delegated_to_opaque_variable", "evidence": {"snippet": raw[:1600]}}
    return {"decision": "pass", "category": None, "evidence": {"entry_tokens": [], "snippet": raw[:1600]}}


def explicit_source_fields(record: dict) -> tuple[dict[str, bool], list[str]]:
    entry_tree, entry_error = parse_snippet(record, "entry")
    exit_tree, exit_error = parse_snippet(record, "exit")
    snippets = record.get("evidence_bundle", {}).get("snippets", {})
    fields = {
        "timeframe": "timeframe" in snippets,
        "entry_logic": bool(entry_tree and any(has_entry_write(node) for node in ast.walk(entry_tree))),
        "exit_logic": bool(exit_tree and any(has_exit_write(node) for node in ast.walk(exit_tree))),
        "stop_or_target": any(key in snippets for key in ("stoploss", "minimal_roi", "trailing_stop")),
    }
    missing = [name for name, present in fields.items() if not present]
    if entry_error and "entry_logic" not in missing:
        missing.append(entry_error)
    if exit_error and "exit_logic" not in missing:
        missing.append(exit_error)
    return fields, missing


def evaluate(record: dict) -> dict:
    fields, missing = explicit_source_fields(record)
    primary = primary_signal_filter(record)
    if primary["decision"] == "reject":
        source_status, decision, status = "rejected_incomplete", "rejected_incomplete", "filter_rejected_primary"
        reasons = ["primary_signal_matches_frozen_lagging_indicator_category"]
    elif primary["decision"] == "review":
        source_status, decision, status = "needs_review", "needs_review", "needs_review"
        reasons = [primary["reason"]]
    elif missing:
        source_status, decision, status = "needs_review", "needs_review", "needs_review"
        reasons = [f"missing_explicit_source_rule_field:{name}" for name in missing]
    else:
        source_status, decision, status = "source_rule_complete", "execution_assumption_required", "execution_assumption_required"
        reasons = ["source_rule_complete_but_execution_assumption_manifest_not_frozen"]
    return {
        "document_id": record["document_id"],
        "source_path": record["source_path"],
        "source_repo": record["source_repo"],
        "source_commit": record["source_commit"],
        "license": record["license"],
        "source_snapshot_sha256": record["source_snapshot_sha256"],
        "adapter_id": "freqtrade_strategy_v1",
        "source_rule_fields": fields,
        "source_rule_status": source_status,
        "re_evaluation_status": status,
        "execution_assumption_status": "execution_assumption_required" if source_status == "source_rule_complete" else "not_evaluated",
        "execution_assumption_fields": list(EXECUTION_FIELDS) if source_status == "source_rule_complete" else [],
        "execution_assumption_manifest": {"status": "not_present", "manifest_id": "execution_assumption_manifest_v1", "manifest_sha256": None},
        "primary_signal_filter": primary,
        "promotion_decision": decision,
        "review_reasons": reasons,
        "reconstruction_performed": False,
        "analysis_only": True,
        "backtest_run": False,
        "market_data_downloaded": False,
        "trial_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    input_path = Path(args.input)
    source = load(input_path)
    if source.get("batch_id") != "freqtrade-strategies-001":
        raise SystemExit("input is not the immutable Freqtrade batch 001")
    evaluations = [evaluate(record) for record in source["candidates"]]
    status_counts = Counter(item["re_evaluation_status"] for item in evaluations)
    source_counts = Counter(item["source_rule_status"] for item in evaluations)
    output = {
        "re_evaluation_version": "freqtrade_strategy_v2_flexible_completeness",
        "input_batch_id": source["batch_id"],
        "input_source_commit": source["source_commit"],
        "input_sha256": sha256(input_path.read_bytes()),
        "adapter_id": "freqtrade_strategy_v1",
        "source_rule_contract": "explicit_code_evidence_for_timeframe_entry_exit_and_stop_or_target",
        "execution_assumption_contract": "single_batch_manifest_required_for_missing_execution_fields",
        "candidate_count": len(evaluations),
        "source_rule_status_counts": dict(sorted(source_counts.items())),
        "re_evaluation_status_counts": dict(sorted(status_counts.items())),
        "analysis_only": True,
        "backtest_run": False,
        "market_data_downloaded": False,
        "trial_created": False,
        "trial_ledger_n": 893,
        "evaluated_at": now(),
        "evaluations": evaluations,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"candidate_count": len(evaluations), "source_rule_status_counts": dict(sorted(source_counts.items())), "re_evaluation_status_counts": dict(sorted(status_counts.items())), "trial_ledger_n": 893}, sort_keys=True))


if __name__ == "__main__":
    main()
