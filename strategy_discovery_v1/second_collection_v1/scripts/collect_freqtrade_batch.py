#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_URL = "https://github.com/freqtrade/freqtrade-strategies"
LICENSE = "GPL-3.0"
BATCH_ID = "freqtrade-strategies-001"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def literal(node: ast.AST | None):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def source_lines(source: str, start: int, end: int) -> list[str]:
    lines = source.splitlines()
    return lines[max(0, start - 1) : min(len(lines), end)]


def short_method_snippet(source: str, node: ast.FunctionDef, tokens: tuple[str, ...]) -> dict:
    lines = source.splitlines()
    lo = node.lineno - 1
    hi = min(len(lines), getattr(node, "end_lineno", node.lineno))
    hits = [i for i in range(lo, hi) if any(token.lower() in lines[i].lower() for token in tokens)]
    if hits:
        start = max(lo, hits[0] - 1)
        end = min(hi, start + 8)
        if hits[-1] >= end:
            start = max(lo, hits[-1] - 4)
            end = min(hi, start + 8)
    else:
        start, end = lo, min(hi, lo + 5)
    excerpt = "\n".join(lines[start:end]).strip()
    return {"locator": f"lines={start + 1}-{end}", "verbatim": excerpt[:1600], "line_count": len(excerpt.splitlines())}


def find_strategy_class(tree: ast.Module) -> ast.ClassDef | None:
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    for cls in classes:
        bases = [ast.unparse(base) for base in cls.bases]
        if any("IStrategy" in base or "Strategy" in base for base in bases):
            return cls
    return classes[0] if classes else None


def parse_file(path: Path, source_commit: str) -> dict:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    tree = ast.parse(text, filename=str(path))
    cls = find_strategy_class(tree)
    if cls is None:
        raise ValueError("no_strategy_class")
    assignments: dict[str, ast.AST] = {}
    methods: dict[str, ast.FunctionDef] = {}
    for node in cls.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = node.value
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[node.name] = node
    method_names = sorted(methods)
    indicators = []
    lower = text.lower()
    for token in ("rsi", "ema", "sma", "macd", "bollinger", "stochastic", "atr", "adx", "cci", "mfi", "obv", "sar"):
        if token in lower:
            indicators.append(token)
    timeframe = literal(assignments.get("timeframe"))
    minimal_roi = literal(assignments.get("minimal_roi"))
    stoploss = literal(assignments.get("stoploss"))
    trailing_stop = literal(assignments.get("trailing_stop"))
    entry = methods.get("populate_entry_trend") or methods.get("populate_buy_trend")
    exit_ = methods.get("populate_exit_trend") or methods.get("populate_sell_trend")
    custom_stake = methods.get("custom_stake_amount")
    snippets = {}
    if entry:
        snippets["entry"] = short_method_snippet(text, entry, ("enter_long", "buy", "dataframe[", "cross"))
    if exit_:
        snippets["exit"] = short_method_snippet(text, exit_, ("exit_long", "sell", "dataframe[", "cross"))
    for field, token in (("minimal_roi", "minimal_roi"), ("stoploss", "stoploss"), ("trailing_stop", "trailing_stop"), ("timeframe", "timeframe")):
        for i, line in enumerate(text.splitlines(), 1):
            if token in line.lower() and "=" in line:
                snippets[field] = {"locator": f"line={i}", "verbatim": line.strip()[:800], "line_count": 1}
                break
    if custom_stake:
        snippets["sizing"] = short_method_snippet(text, custom_stake, ("return", "stake", "amount"))
    github_url = f"{REPO_URL}/blob/{source_commit}/user_data/strategies/{path.name}"
    summary = (
        f"Freqtrade IStrategy source file; class={cls.name}; timeframe={timeframe!r}; "
        f"minimal_roi_explicit={minimal_roi is not None}; stoploss_explicit={stoploss is not None}; "
        f"trailing_stop_explicit={trailing_stop is not None}; entry_method={entry.name if entry else None}; "
        f"exit_method={exit_.name if exit_ else None}; custom_stake_method={custom_stake is not None}; "
        f"indicator_tokens={','.join(indicators) if indicators else 'none'}"
    )
    return {
        "document_id": f"{source_commit}:user_data/strategies/{path.name}",
        "document_title": f"Freqtrade strategy: {path.name}",
        "abstract": summary,
        "authors": [],
        "categories": ["open_quant_code", "freqtrade"],
        "canonical_url": github_url,
        "document_version": source_commit,
        "published_at": None,
        "retrieved_at": now(),
        "rule_disclosure_locator": github_url,
        "rule_disclosure_status": "pending_adapter_review",
        "source_class": "open_quant_archive",
        "source_id": "freqtrade_strategies",
        "source_repo": REPO_URL,
        "source_path": f"user_data/strategies/{path.name}",
        "source_commit": source_commit,
        "license": LICENSE,
        "source_snapshot_sha256": sha256_bytes(raw),
        "source_snapshot_bytes": len(raw),
        "evidence_bundle": {
            "adapter_id": "freqtrade_strategy_v1",
            "source_snapshot_sha256": sha256_bytes(raw),
            "source_repo": REPO_URL,
            "source_commit": source_commit,
            "source_path": f"user_data/strategies/{path.name}",
            "license": LICENSE,
            "snippets": snippets,
            "snippet_policy": "short_field_supporting_excerpts_only_never_full_file",
        },
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--evidence-output", required=True)
    parser.add_argument("--max-candidates", type=int, default=25)
    args = parser.parse_args()
    source_dir = Path(args.source_dir)
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_dir, text=True).strip()
    files = sorted((source_dir / "user_data/strategies").glob("*.py"), key=lambda p: p.name)[: args.max_candidates]
    assert 20 <= len(files) <= 25, len(files)
    records = [parse_file(path, source_commit) for path in files]
    payload = {
        "batch_id": BATCH_ID,
        "source_repo": REPO_URL,
        "source_commit": source_commit,
        "license": LICENSE,
        "adapter_id": "freqtrade_strategy_v1",
        "raw_candidate_count": len(records),
        "candidates": records,
        "evidence_policy": "short_field_supporting_excerpts_only_never_full_file",
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
    }
    evidence = {
        "batch_id": BATCH_ID,
        "adapter_id": "freqtrade_strategy_v1",
        "source_repo": REPO_URL,
        "source_commit": source_commit,
        "license": LICENSE,
        "bundle_count": len(records),
        "bundles": [
            {
                "document_id": r["document_id"],
                "source_path": r["source_path"],
                "source_snapshot_sha256": r["source_snapshot_sha256"],
                "license": LICENSE,
                "snippets": r["evidence_bundle"]["snippets"],
            }
            for r in records
        ],
        "snippet_policy": "short_field_supporting_excerpts_only_never_full_file",
        "analysis_only": True,
    }
    for target, data in ((Path(args.output), payload), (Path(args.evidence_output), evidence)):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"batch_id": BATCH_ID, "raw": len(records), "source_commit": source_commit, "license": LICENSE, "paths": [p.name for p in files]}, sort_keys=True))


if __name__ == "__main__":
    main()
