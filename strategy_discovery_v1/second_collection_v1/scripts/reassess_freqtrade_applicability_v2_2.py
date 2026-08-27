#!/usr/bin/env python3
"""Apply the v2.2 Freqtrade applicability policy without measuring.

The policy permits a single batch-level research pairlist/venue scope to satisfy
applicability when the strategy source has no conflicting pair restriction. The
scope remains an external assumption and is not frozen or assigned values here.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_URL = "https://github.com/freqtrade/freqtrade-strategies"
COMMIT = "eff78d3ce3456b52c68a4e9a33cc055a56b801ff"
LICENSE = "GPL-3.0"
ADAPTER_ID = "freqtrade_strategy_v1"
MANIFEST_ID = "execution_assumption_manifest_v1_2"
EXECUTION_FIELDS = (
    "instrument_universe", "venue", "quote_currency", "applicable_asset_timeframe_constraints",
    "position_sizing", "risk_budget", "notional_cap", "leverage_cap", "commission", "slippage",
    "spread", "fill_rule", "latency", "funding_or_borrow", "rounding_rule",
    "insufficient_margin_behavior", "external_config", "missing_data_behavior",
    "invalid_bar_behavior", "ohlcv_manifest_refs",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_hash(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def short_lines(source: str, start: int, end: int) -> str:
    lines = source.splitlines()
    selected = lines[max(0, start - 1): min(len(lines), end)]
    return "\n".join(selected[:8]).strip()[:2000]


def locator(start: int, end: int) -> str:
    return f"lines={start}-{end}"


def find_class(tree: ast.Module) -> ast.ClassDef | None:
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    for cls in classes:
        if any("Strategy" in ast.unparse(base) for base in cls.bases):
            return cls
    return classes[0] if classes else None


def field_claim(field_path: str, status: str, origin: str, source_url: str, source_hash: str, start: int | None, end: int | None, snippet: str | None, value=None, flags=None) -> dict:
    item = {"field_path": field_path, "status": status, "claim_origin": origin, "evidence": [], "extraction_method": "ast_control_flow", "ambiguity_flags": flags or []}
    if value is not None:
        item["value"] = value
    if start is not None and end is not None and snippet:
        item["evidence"] = [{"source_url": source_url, "snapshot_sha256": source_hash, "locator_type": "code_lines", "locator": locator(start, end), "verbatim": snippet}]
    return item


def pair_applicability(tree: ast.Module, cls: ast.ClassDef, source: str, source_url: str, source_hash: str) -> tuple[str, dict, dict]:
    restrictions = []
    metadata_refs = []
    informative = []
    for node in ast.walk(cls):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.lower() in {"pair_whitelist", "pairlist", "pairs"}:
                    restrictions.append(node)
        if isinstance(node, ast.FunctionDef) and node.name == "informative_pairs":
            informative.append(node)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == "pair":
            metadata_refs.append(node)
    if restrictions:
        node = restrictions[0]
        start = node.lineno; end = min(getattr(node, "end_lineno", start), start + 7)
        return "source_explicit", {"mode": "source_explicit", "reason": "class_pair_or_universe_assignment", "evidence": locator(start, end)}, field_claim("universe.instrument_applicability", "explicit", "source", source_url, source_hash, start, end, short_lines(source, start, end), value=ast.unparse(node)[:800])
    for method in informative:
        returns = [node for node in ast.walk(method) if isinstance(node, ast.Return) and node.value is not None]
        if returns:
            value = None
            try:
                value = ast.literal_eval(returns[-1].value)
            except Exception:
                value = None
            start = returns[-1].lineno; end = min(getattr(returns[-1], "end_lineno", start), start + 7)
            if value == []:
                return "uniform_external_research_scope", {"mode": "uniform_external_research_scope", "reason": "informative_pairs_explicitly_empty", "evidence": locator(start, end)}, field_claim("universe.instrument_applicability", "explicit_but_ambiguous", "source", source_url, source_hash, start, end, short_lines(source, start, end), value="informative_pairs=[]", flags=["empty_informative_pairs_does_not_declare_trade_universe"])
            return "conflict_review", {"mode": "conflict_review", "reason": "nonempty_or_nonliteral_informative_pairs", "evidence": locator(start, end)}, field_claim("universe.instrument_applicability", "explicit_but_ambiguous", "source", source_url, source_hash, start, end, short_lines(source, start, end), flags=["source_declares_informative_pair_scope"])
    # metadata['pair'] used only as runtime context is not a pairlist restriction.
    if metadata_refs:
        node = metadata_refs[0]
        start = node.lineno; end = min(getattr(node, "end_lineno", start), start + 7)
        return "uniform_external_research_scope", {"mode": "uniform_external_research_scope", "reason": "runtime_pair_metadata_reference_without_universe_restriction", "evidence": locator(start, end)}, field_claim("universe.instrument_applicability", "explicit_but_ambiguous", "source", source_url, source_hash, start, end, short_lines(source, start, end), flags=["metadata_pair_context_is_not_pairlist"])
    return "uniform_external_research_scope", {"mode": "uniform_external_research_scope", "reason": "no_source_pair_or_universe_restriction", "evidence": None}, field_claim("universe.instrument_applicability", "not_found", "source", source_url, source_hash, None, None, None, flags=["no_source_pair_or_universe_rule_external_scope_required"])


def effective_record(record: dict, source_dir: Path, policy_manifest: dict) -> dict:
    path = source_dir / record["source_path"]
    raw = path.read_bytes()
    source_hash = sha256_bytes(raw)
    if source_hash != record["source_snapshot_sha256"]:
        raise SystemExit(f"source hash mismatch: {record['source_path']}")
    source = raw.decode("utf-8")
    tree = ast.parse(source, filename=str(path))
    cls = find_class(tree)
    if cls is None:
        raise SystemExit(f"strategy class missing: {record['source_path']}")
    source_url = f"{REPO_URL}/blob/{COMMIT}/{record['source_path']}"
    resolution, applicability_meta, applicability_claim = pair_applicability(tree, cls, source, source_url, source_hash)
    fields = dict(record["source_rule_fields"])
    original_instrument = fields.get("instrument_applicability", False)
    fields["instrument_applicability"] = original_instrument or resolution in {"source_explicit", "uniform_external_research_scope"}
    claims = [claim for claim in record["field_claims"] if claim["field_path"] != "universe.instrument_applicability"]
    claims.append(applicability_claim)
    primary = record["primary_signal_filter"]
    source_complete = resolution in {"source_explicit", "uniform_external_research_scope"} and all(fields.values()) and primary["decision"] == "pass"
    if primary["decision"] == "reject":
        source_status = "rejected_incomplete"
        reassessment_status = "filter_rejected_primary"
        execution_status = "not_evaluated"
        decision = "rejected_incomplete"
        reasons = ["primary_signal_matches_frozen_lagging_indicator_category"]
    elif resolution == "conflict_review":
        source_status = "needs_review"
        reassessment_status = "needs_review"
        execution_status = "not_evaluated"
        decision = "needs_review"
        reasons = list(record["review_reasons"]) + ["source_pair_scope_requires_review"]
    elif source_complete:
        source_status = "source_rule_complete"
        reassessment_status = "execution_assumption_required"
        execution_status = "execution_assumption_required"
        decision = "execution_assumption_required"
        reasons = ["uniform_external_research_scope_accepted_as_external_assumption", "execution_assumption_manifest_not_frozen"]
    else:
        source_status = "needs_review"
        reassessment_status = "needs_review"
        execution_status = "not_evaluated"
        decision = "needs_review"
        reasons = list(record["review_reasons"])
        if not fields.get("timeframe", False):
            reasons.append("missing_explicit_source_rule_field:timeframe")
    return {
        "document_id": record["document_id"], "source_path": record["source_path"], "canonical_url": source_url,
        "source_repo": REPO_URL, "source_commit": COMMIT, "license": LICENSE, "source_snapshot_sha256": source_hash,
        "source_snapshot_bytes": len(raw), "adapter_id": ADAPTER_ID,
        "source_rule_fields": dict(record["source_rule_fields"]), "effective_source_rule_fields": fields,
        "source_rule_status": source_status, "source_rule_completion_basis": "source_logic_plus_uniform_external_research_scope_policy_v2_2" if source_complete else "incomplete_or_conflicted_source_logic",
        "source_applicability_resolution": resolution, "source_applicability_evidence": applicability_meta,
        "primary_signal_filter": primary, "field_claims": claims,
        "execution_assumption_status": execution_status,
        "execution_assumption_fields": list(EXECUTION_FIELDS) if source_complete else [],
        "execution_assumption_field_contract_sha256": canonical_hash(list(EXECUTION_FIELDS)),
        "execution_assumption_manifest": policy_manifest,
        "re_evaluation_status": reassessment_status, "promotion_decision": decision, "review_reasons": reasons,
        "reconstruction_performed": False, "analysis_only": True, "backtest_run": False,
        "market_data_downloaded": False, "trial_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if source_payload.get("input_source_commit") != COMMIT:
        raise SystemExit("input source commit is not the authorized pinned commit")
    policy_manifest = {"status": "not_present", "manifest_id": MANIFEST_ID}
    records = [effective_record(record, Path(args.source_dir), policy_manifest) for record in source_payload["records"]]
    counts = Counter(record["re_evaluation_status"] for record in records)
    source_counts = Counter(record["source_rule_status"] for record in records)
    output = {
        "extraction_version": "deterministic_rule_extraction_v2_2",
        "re_evaluation_version": "freqtrade_strategy_v2_2_uniform_external_applicability",
        "policy_decision": "accept_uniform_external_research_scope",
        "policy_condition": "Configured pairlist, venue, quote currency, and research timeframe are external assumptions; same values apply uniformly to the batch and must be frozen before measurement.",
        "input_artifact": str(Path(args.input)), "input_sha256": sha256_bytes(Path(args.input).read_bytes()),
        "input_source_commit": COMMIT, "source_repo": REPO_URL, "license": LICENSE, "adapter_id": ADAPTER_ID,
        "candidate_count": len(records), "source_rule_status_counts": dict(sorted(source_counts.items())),
        "re_evaluation_status_counts": dict(sorted(counts.items())),
        "execution_assumption_manifest": policy_manifest, "execution_assumption_field_contract_sha256": canonical_hash(list(EXECUTION_FIELDS)),
        "analysis_only": True, "backtest_run": False, "market_data_downloaded": False,
        "trial_created": False, "trial_ledger_n": 893, "reconstruction_performed": False,
        "evidence_retention": "structured_fields_and_short_snippets_only_no_full_source",
        "evaluated_at": now(), "records": records,
    }
    output_path = Path(args.output); output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"candidate_count": len(records), "source_rule_status_counts": dict(sorted(source_counts.items())), "re_evaluation_status_counts": dict(sorted(counts.items())), "trial_ledger_n": 893}, sort_keys=True))


if __name__ == "__main__":
    main()
