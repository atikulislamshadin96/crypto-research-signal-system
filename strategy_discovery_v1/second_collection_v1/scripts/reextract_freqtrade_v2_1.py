#!/usr/bin/env python3
"""Extract bounded evidence from the authorized pinned Freqtrade source.

The source checkout is temporary input. This script commits only structured
fields, hashes, locators, and <=8-line fact-supporting snippets. It never runs
Freqtrade, downloads market data, backtests, or creates trials.
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

REPO_URL = "https://github.com/freqtrade/freqtrade-strategies"
COMMIT = "eff78d3ce3456b52c68a4e9a33cc055a56b801ff"
LICENSE = "GPL-3.0"
ADAPTER_ID = "freqtrade_strategy_v1"
EXECUTION_FIELDS = (
    "instrument_universe", "venue", "quote_currency", "applicable_asset_timeframe_constraints",
    "position_sizing", "risk_budget", "notional_cap", "leverage_cap", "commission", "slippage",
    "spread", "fill_rule", "latency", "funding_or_borrow", "rounding_rule",
    "insufficient_margin_behavior", "external_config", "missing_data_behavior",
    "invalid_bar_behavior", "ohlcv_manifest_refs",
)
BANNED_INDICATOR_PARTS = ("rsi", "ema", "sma", "macd", "bollinger", "stochastic")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_hash(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def literal(node: ast.AST | None):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def class_assignments(cls: ast.ClassDef) -> dict[str, ast.AST]:
    assignments: dict[str, ast.AST] = {}
    for node in cls.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assignments[node.target.id] = node.value
    return assignments


def find_strategy_class(tree: ast.Module) -> ast.ClassDef | None:
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    for cls in classes:
        bases = [ast.unparse(base) for base in cls.bases]
        if any("IStrategy" in base or "Strategy" in base for base in bases):
            return cls
    return classes[0] if classes else None


def methods_in(cls: ast.ClassDef) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {node.name: node for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def lines_for(source: str, start: int, end: int, max_lines: int = 8) -> str:
    lines = source.splitlines()
    start = max(1, start)
    end = min(len(lines), end)
    selected = lines[start - 1:end]
    if len(selected) > max_lines:
        selected = selected[:max_lines]
    return "\n".join(selected).strip()[:2000]


def locator(start: int, end: int) -> str:
    return f"lines={start}-{end}"


def evidence(source_url: str, source_hash: str, start: int, end: int, text: str) -> list[dict]:
    return [{"source_url": source_url, "snapshot_sha256": source_hash, "locator_type": "code_lines", "locator": locator(start, end), "verbatim": text}]


def claim(field_path: str, status: str, origin: str, source_url: str, source_hash: str, start: int | None, end: int | None, verbatim: str | None, value=None, method="ast_control_flow", flags=None) -> dict:
    item = {"field_path": field_path, "status": status, "claim_origin": origin, "evidence": [], "extraction_method": method, "ambiguity_flags": flags or []}
    if value is not None:
        item["value"] = value
    if start is not None and end is not None and verbatim:
        item["evidence"] = evidence(source_url, source_hash, start, end, verbatim)
    return item


def is_target_field(node: ast.AST, names: set[str]) -> bool:
    return any(isinstance(child, ast.Constant) and child.value in names for child in ast.walk(node))


def assignment_writes(node: ast.AST, names: set[str]) -> bool:
    return isinstance(node, ast.Assign) and any(is_target_field(target, names) for target in node.targets)


def written_fields(node: ast.AST) -> list[str]:
    if not isinstance(node, ast.Assign):
        return []
    return sorted({child.value for target in node.targets for child in ast.walk(target) if isinstance(child, ast.Constant) and child.value in {"enter_long", "enter_short", "exit_long", "exit_short"}})


def target_condition(node: ast.Assign) -> ast.AST | None:
    for target in node.targets:
        if not isinstance(target, ast.Subscript):
            continue
        sliced = target.slice
        if isinstance(sliced, ast.Tuple) and sliced.elts:
            first = sliced.elts[0]
            if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                return first
    return None


def names_with_indicator(tree: ast.AST) -> list[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        token = None
        if isinstance(node, ast.Name):
            token = node.id
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            token = node.value
        if token and any(part in token.lower() for part in BANNED_INDICATOR_PARTS):
            found.add(token)
    return sorted(found)


def resolve_condition(method: ast.FunctionDef | ast.AsyncFunctionDef, expr: ast.AST) -> tuple[ast.AST | None, list[str], str | None]:
    """Resolve simple local condition variables; fail closed for opaque helpers."""
    if isinstance(expr, ast.Name):
        matches: list[ast.AST] = []
        for node in ast.walk(method):
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == expr.id for target in node.targets):
                matches.append(node.value)
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == expr.id and node.value:
                matches.append(node.value)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"append", "extend"} and isinstance(node.func.value, ast.Name) and node.func.value.id == expr.id:
                matches.extend(node.args)
        if not matches:
            return None, [], f"opaque_condition_variable:{expr.id}"
        combined = ast.Module(body=matches, type_ignores=[])
        return combined, names_with_indicator(combined), None
    return expr, names_with_indicator(expr), None


def node_spans(nodes: list[ast.AST]) -> list[tuple[int, int]]:
    spans: set[tuple[int, int]] = set()
    for node in nodes:
        line_numbers = [getattr(child, "lineno", None) for child in ast.walk(node) if getattr(child, "lineno", None) is not None]
        if line_numbers:
            spans.add((min(line_numbers), max(getattr(child, "end_lineno", getattr(child, "lineno")) for child in ast.walk(node) if getattr(child, "lineno", None) is not None)))
    return sorted(spans)


def method_entry_evidence(source: str, source_hash: str, source_url: str, method: ast.FunctionDef | ast.AsyncFunctionDef, entry: bool) -> tuple[dict, dict]:
    target_names = {"enter_long", "enter_short"} if entry else {"exit_long", "exit_short"}
    writes = [node for node in ast.walk(method) if assignment_writes(node, target_names)]
    label = "entry" if entry else "exit"
    if not writes:
        return {"status": "not_found", "node": None, "condition": None, "indicators": [], "reason": f"no_{label}_field_write"}, claim(f"{label}.trigger", "not_found", "source", source_url, source_hash, method.lineno, getattr(method, "end_lineno", method.lineno), lines_for(source, method.lineno, min(getattr(method, "end_lineno", method.lineno), method.lineno + 7)), method="ast_control_flow", flags=[f"no_{label}_field_write"])
    condition_nodes: list[ast.AST] = []
    unresolved: list[str] = []
    indicators: set[str] = set()
    for write in writes:
        direct = target_condition(write)
        if direct is not None:
            resolved, found, error = resolve_condition(method, direct)
            if resolved is not None:
                condition_nodes.append(resolved)
            indicators.update(found)
            if error:
                unresolved.append(error)
        for parent in ast.walk(method):
            if isinstance(parent, ast.If) and any(child is write for child in ast.walk(parent)):
                resolved, found, error = resolve_condition(method, parent.test)
                if resolved is not None:
                    condition_nodes.append(resolved)
                indicators.update(found)
                if error:
                    unresolved.append(error)
    first = writes[0]
    start = max(method.lineno, min(node.lineno for node in writes) - 2)
    end = min(getattr(method, "end_lineno", first.lineno), start + 7)
    fragment = lines_for(source, start, end)
    spans = node_spans(condition_nodes)
    result = {"status": "explicit" if not unresolved else "explicit_but_ambiguous", "node": first, "condition": condition_nodes, "condition_spans": spans, "indicators": sorted(indicators), "reason": unresolved}
    status = result["status"]
    flags = unresolved
    return result, claim(f"{label}.trigger", status, "source", source_url, source_hash, start, end, fragment, value={"assignment_count": len(writes), "direction_fields": sorted({field for write in writes for field in written_fields(write)}), "condition_spans": [locator(s, e) for s, e in spans]}, flags=flags)


def parameter_claims(source: str, source_hash: str, source_url: str, assignments: dict[str, ast.AST]) -> tuple[list[dict], dict[str, object]]:
    claims: list[dict] = []
    values: dict[str, object] = {}
    for field in ("timeframe", "minimal_roi", "stoploss", "trailing_stop"):
        node = assignments.get(field)
        value = literal(node)
        if node is None or value is None:
            claims.append(claim(f"source.{field}", "not_found", "source", source_url, source_hash, None, None, None, flags=["no_literal_class_assignment"]))
            continue
        values[field] = value
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", start)
        claims.append(claim(f"source.{field}", "explicit", "source", source_url, source_hash, start, min(end, start + 7), lines_for(source, start, min(end, start + 7)), value=value, method="deterministic_pattern"))
    return claims, values


def custom_exit_claim(source: str, source_hash: str, source_url: str, method: ast.FunctionDef | ast.AsyncFunctionDef | None) -> dict:
    if method is None:
        return claim("exit.custom_exit", "not_found", "source", source_url, source_hash, None, None, None, flags=["custom_exit_method_absent"])
    returns = [node for node in ast.walk(method) if isinstance(node, ast.Return) and node.value is not None]
    string_returns = [literal(node.value) for node in returns if isinstance(literal(node.value), str)]
    start = method.lineno
    end = min(getattr(method, "end_lineno", start), start + 7)
    if not string_returns:
        return claim("exit.custom_exit", "explicit_but_ambiguous", "source", source_url, source_hash, start, end, lines_for(source, start, end), flags=["custom_exit_has_no_literal_exit_tag"])
    return claim("exit.custom_exit", "explicit", "source", source_url, source_hash, start, end, lines_for(source, start, end), value={"return_tags": sorted(set(string_returns))})


def parse_record(record: dict, source_dir: Path) -> dict:
    rel = Path(record["source_path"])
    path = source_dir / rel
    raw = path.read_bytes()
    source_hash = sha256_bytes(raw)
    if source_hash != record["source_snapshot_sha256"]:
        raise SystemExit(f"source hash mismatch for {rel}: {source_hash} != {record['source_snapshot_sha256']}")
    text = raw.decode("utf-8")
    tree = ast.parse(text, filename=str(path))
    cls = find_strategy_class(tree)
    if cls is None:
        raise SystemExit(f"no strategy class: {rel}")
    methods = methods_in(cls)
    assignments = class_assignments(cls)
    source_url = f"{REPO_URL}/blob/{COMMIT}/{record['source_path']}"
    claims, values = parameter_claims(text, source_hash, source_url, assignments)
    entry = methods.get("populate_entry_trend") or methods.get("populate_buy_trend")
    exit_ = methods.get("populate_exit_trend") or methods.get("populate_sell_trend")
    entry_result, entry_claim = method_entry_evidence(text, source_hash, source_url, entry, True) if entry else ({"status": "not_found", "node": None, "condition": None, "indicators": [], "reason": ["entry_method_absent"]}, claim("entry.trigger", "not_found", "source", source_url, source_hash, None, None, None, flags=["entry_method_absent"]))
    exit_result, exit_claim = method_entry_evidence(text, source_hash, source_url, exit_, False) if exit_ else ({"status": "not_found", "node": None, "condition": None, "indicators": [], "reason": ["exit_method_absent"]}, claim("exit.trigger", "not_found", "source", source_url, source_hash, None, None, None, flags=["exit_method_absent"]))
    custom_exit = methods.get("custom_exit")
    claims.extend([entry_claim, exit_claim, custom_exit_claim(text, source_hash, source_url, custom_exit)])
    # Instrument applicability is source-complete only when a pair/universe rule
    # is explicitly present in the strategy class. Framework-wide applicability
    # is not silently inferred.
    pair_names = {"pair_whitelist", "pairlist", "pairs", "informative_pairs"}
    pair_nodes = [node for node in ast.walk(cls) if isinstance(node, (ast.Assign, ast.AnnAssign)) and is_target_field(node, pair_names)]
    if pair_nodes:
        node = pair_nodes[0]
        start = getattr(node, "lineno", cls.lineno); end = min(getattr(node, "end_lineno", start), start + 7)
        claims.append(claim("universe.instrument_applicability", "explicit", "source", source_url, source_hash, start, end, lines_for(text, start, end), value=ast.unparse(node)[:600], method="ast_control_flow"))
        applicability_explicit = True
    else:
        claims.append(claim("universe.instrument_applicability", "not_found", "source", source_url, source_hash, None, None, None, flags=["no_source_pair_or_universe_rule"]))
        applicability_explicit = False
    # Entry/exit indicators are primary only when they occur in resolved direct
    # entry condition AST. Indicators elsewhere remain secondary/unclassified.
    primary_indicators = entry_result["indicators"]
    if primary_indicators:
        primary_evidence = [{"source_url": source_url, "snapshot_sha256": source_hash, "locator_type": "code_lines", "locator": locator(s, e), "verbatim": lines_for(text, s, min(e, s + 7))} for s, e in entry_result.get("condition_spans", [])]
        primary = {"decision": "reject", "category": "lagging_indicator_primary", "evidence": {"entry_indicator_tokens": primary_indicators, "entry_method": entry.name if entry else None, "direct_condition_spans": primary_evidence}}
    elif entry_result["status"] != "explicit":
        primary = {"decision": "review", "category": "primary_signal_unresolved", "evidence": {"entry_method": entry.name if entry else None, "reason": entry_result["reason"]}}
    else:
        primary = {"decision": "pass", "category": None, "evidence": {"entry_method": entry.name if entry else None, "entry_indicator_tokens": []}}
    source_fields = {
        "instrument_applicability": applicability_explicit,
        "timeframe": "timeframe" in values,
        "entry_logic": entry_result["status"] == "explicit",
        "exit_logic": exit_result["status"] == "explicit" or custom_exit is not None,
        "stop_or_target_or_time_exit": any(field in values for field in ("stoploss", "minimal_roi", "trailing_stop")) or custom_exit is not None,
    }
    missing = [key for key, present in source_fields.items() if not present]
    if primary["decision"] == "reject":
        source_status, decision, status = "rejected_incomplete", "rejected_incomplete", "filter_rejected_primary"
        reasons = ["primary_signal_matches_frozen_lagging_indicator_category"]
    elif primary["decision"] == "review":
        source_status, decision, status = "needs_review", "needs_review", "needs_review"
        reasons = ["primary_signal_unresolved"] + list(entry_result["reason"])
    elif missing:
        source_status, decision, status = "needs_review", "needs_review", "needs_review"
        reasons = [f"missing_explicit_source_rule_field:{name}" for name in missing]
    else:
        source_status, decision, status = "source_rule_complete", "execution_assumption_required", "execution_assumption_required"
        reasons = ["source_rule_complete_but_execution_assumption_manifest_not_frozen"]
    return {
        "document_id": record["document_id"], "source_path": record["source_path"], "canonical_url": source_url,
        "source_repo": REPO_URL, "source_commit": COMMIT, "license": LICENSE, "source_snapshot_sha256": source_hash,
        "source_snapshot_bytes": len(raw), "adapter_id": ADAPTER_ID, "source_rule_fields": source_fields,
        "source_rule_status": source_status, "re_evaluation_status": status,
        "execution_assumption_status": "execution_assumption_required" if source_status == "source_rule_complete" else "not_evaluated",
        "execution_assumption_fields": list(EXECUTION_FIELDS) if source_status == "source_rule_complete" else [],
        "execution_assumption_field_contract_sha256": canonical_hash(list(EXECUTION_FIELDS)),
        "primary_signal_filter": primary, "promotion_decision": decision, "review_reasons": reasons,
        "field_claims": claims, "reconstruction_performed": False, "analysis_only": True,
        "backtest_run": False, "market_data_downloaded": False, "trial_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--input-batch", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = json.loads(Path(args.input_batch).read_text(encoding="utf-8"))
    if source.get("batch_id") != "freqtrade-strategies-001" or source.get("source_commit") != COMMIT:
        raise SystemExit("input batch is not the authorized immutable Freqtrade batch 001")
    records = [parse_record(record, Path(args.source_dir)) for record in source["candidates"]]
    counts = Counter(record["re_evaluation_status"] for record in records)
    source_counts = Counter(record["source_rule_status"] for record in records)
    output = {
        "extraction_version": "deterministic_rule_extraction_v2_1",
        "re_evaluation_version": "freqtrade_strategy_v2_1_pinned_source_evidence",
        "input_batch_id": source["batch_id"], "input_source_commit": COMMIT,
        "source_repo": REPO_URL, "license": LICENSE, "adapter_id": ADAPTER_ID,
        "candidate_count": len(records), "source_rule_status_counts": dict(sorted(source_counts.items())),
        "re_evaluation_status_counts": dict(sorted(counts.items())),
        "analysis_only": True, "backtest_run": False, "market_data_downloaded": False,
        "trial_created": False, "trial_ledger_n": 893, "reconstruction_performed": False,
        "evidence_retention": "structured_fields_and_short_snippets_only_no_full_source",
        "evaluated_at": now(), "records": records,
    }
    output_path = Path(args.output); output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"candidate_count": len(records), "re_evaluation_status_counts": dict(sorted(counts.items())), "source_rule_status_counts": dict(sorted(source_counts.items())), "trial_ledger_n": 893}, sort_keys=True))


if __name__ == "__main__":
    main()
