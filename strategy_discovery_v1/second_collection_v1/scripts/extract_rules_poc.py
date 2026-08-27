#!/usr/bin/env python3
"""Fail-closed deterministic-rule extraction proof of concept.

This POC extracts only evidence snippets from a small real sample of collected
leads. It does not infer expressions, build normalized strategies, download
market data, or create trials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_PATHS = [
    "hypothesis", "universe.instruments", "universe.venues", "clock.timezone",
    "clock.decision_frequency", "clock.signal_timestamp_rule", "clock.data_cutoff_rule",
    "signal", "entry.direction", "entry.trigger", "entry.order_type", "entry.fill_rule",
    "entry.latency", "exit.rules", "exit.precedence", "exit.missing_exit_behavior",
    "risk.position_sizing", "risk.risk_budget", "risk.notional_cap", "risk.leverage_cap",
    "risk.rounding_rule", "costs.commission", "costs.slippage", "costs.spread",
    "costs.funding_or_borrow", "costs.cost_source_refs", "constraints.max_concurrent_positions",
    "constraints.pyramiding", "constraints.cooldown", "constraints.missing_data_behavior",
    "constraints.invalid_bar_behavior", "provenance.source_refs", "provenance.source_snapshot",
    "provenance.normalization_version", "provenance.canonical_rule_hash", "analysis_only",
]

PATTERNS = {
    "hypothesis": re.compile(r"\b(hypothes(?:is|e)|we find|we show|strategy aims|objective)\b", re.I),
    "clock": re.compile(r"\b(15-minute|30-minute|hourly|daily|weekly|monthly|each bar|rebalance|timestamp|timezone|cut[- ]off|cutoff)\b", re.I),
    "signal": re.compile(r"\b(if|when|condition|signal|z[- ]?score|momentum|mean reversion|order flow|volatility)\b", re.I),
    "entry": re.compile(r"\b(buy|sell short|enter|entry|go long|go short|market order|limit order|stop order|submitorder|marketorder|limitorder)\b", re.I),
    "exit": re.compile(r"\b(exit|close|sell|cover|stop[- ]loss|take[- ]profit|profit target|holding period|liquidat)\b", re.I),
    "risk": re.compile(r"\b(position siz|risk per trade|risk budget|leverage|notional|allocation|capital|margin|weight)\b", re.I),
    "costs": re.compile(r"\b(commission|fee|slippage|spread|funding|borrow|transaction cost)\b", re.I),
    "constraints": re.compile(r"\b(max(?:imum)? positions?|pyramiding|cooldown|missing data|invalid bar|concurrent)\b", re.I),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "strategy-discovery-v1-rule-extraction-poc/1.0", "Accept": "text/html,application/pdf,text/plain,*/*"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), response.headers.get("Content-Type", "")


def adapter_for(record: dict) -> str:
    cls = str(record.get("source_class", ""))
    url = str(record.get("rule_disclosure_locator") or record.get("stable_locator_to_rule_text_or_code") or record.get("canonical_url"))
    if cls == "open_quant_archive" or url.endswith((".cs", ".py", ".ipynb")):
        return "quantconnect_code_v1" if not url.endswith(".ipynb") else "notebook_v1"
    if cls == "published_quant_research":
        return "published_html_v1"
    if url.lower().endswith(".pdf") or cls in {"academic_preprint", "order_flow_microstructure"}:
        return "arxiv_pdf_v1"
    return "published_html_v1"


def content_to_lines(data: bytes, content_type: str, adapter: str) -> list[tuple[str, str]]:
    if adapter == "arxiv_pdf_v1" or "pdf" in content_type.lower():
        proc = subprocess.run(["pdftotext", "-layout", "-", "-"], input=data, capture_output=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError("pdftotext_failed")
        text = proc.stdout.decode("utf-8", errors="replace")
        pages = text.split("\f")
        return [(f"page={page_no}; line={line_no}", line.strip()) for page_no, page in enumerate(pages, 1) for line_no, line in enumerate(page.splitlines(), 1) if line.strip()]
    text = data.decode("utf-8", errors="replace")
    if adapter == "published_html_v1":
        try:
            from bs4 import BeautifulSoup
            text = BeautifulSoup(text, "html.parser").get_text("\n", strip=True)
        except Exception:
            pass
    return [(f"line={line_no}", line.strip()) for line_no, line in enumerate(text.splitlines(), 1) if line.strip()]


def source_url(record: dict) -> str:
    return str(record.get("rule_disclosure_locator") or record.get("stable_locator_to_rule_text_or_code") or record.get("canonical_url"))


def choose_sample(records: list[dict], limit: int) -> list[dict]:
    if limit >= len(records):
        return list(records)
    grouped: dict[str, list[dict]] = {}
    for record in records:
        grouped.setdefault(str(record.get("source_id")), []).append(record)
    selected: list[dict] = []
    for sid in sorted(grouped):
        pool = grouped[sid]
        if sid == "quantconnect_research":
            pool = sorted(pool, key=lambda r: ("/Alphas/" not in str(r.get("source_path", "")), str(r.get("source_path", ""))))
        selected.append(pool[0])
        if len(selected) >= limit:
            break
    return selected


def claim(field_path: str, status: str, evidence: list[dict], method: str, flags: list[str], value: object = None) -> dict:
    item = {"field_path": field_path, "status": status, "evidence": evidence, "extraction_method": method, "ambiguity_flags": flags}
    if value is not None:
        item["value"] = value
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--sample-size", type=int, default=5)
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    output = Path(args.output)
    snapshot_dir = Path(args.snapshot_dir)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for path in sorted(input_dir.glob("filtered_candidates_batch_*.json")):
        records.extend(json.loads(path.read_text(encoding="utf-8"))["candidates"])
    selected = choose_sample(records, args.sample_size)
    bundles: list[dict] = []
    for record in selected:
        url = source_url(record)
        adapter = adapter_for(record)
        bundle_base = {
            "extraction_version": "deterministic_rule_extraction_v1_poc",
            "analysis_only": True,
            "source_identity": {
                "document_id": str(record.get("document_id")),
                "source_id": str(record.get("source_id")),
                "source_class": str(record.get("source_class")),
                "canonical_url": str(record.get("canonical_url")),
                "document_version": str(record.get("document_version", "")),
            },
            "reconstruction_performed": False,
            "review_reasons": [],
        }
        try:
            data, content_type = fetch(url)
            content_hash = sha256(data)
            snapshot_path = snapshot_dir / (content_hash + ".source")
            snapshot_path.write_bytes(data)
            lines = content_to_lines(data, content_type, adapter)
            content_type_enum = "application/pdf" if (adapter == "arxiv_pdf_v1" or "pdf" in content_type.lower()) else ("text/html" if adapter == "published_html_v1" else "text/plain")
            bundle_base["snapshot"] = {
                "content_type": content_type_enum,
                "content_sha256": content_hash,
                "byte_size": len(data),
                "retrieved_at": now(),
                "adapter_id": adapter,
                "source_snapshot_hash": str(record.get("source_snapshot_hash", "")),
            }
            evidence_by_field: dict[str, list[dict]] = {k: [] for k in PATTERNS}
            for locator, text in lines:
                for field, pattern in PATTERNS.items():
                    if pattern.search(text):
                        evidence_by_field[field].append({
                            "source_url": url,
                            "snapshot_sha256": content_hash,
                            "locator_type": "pdf_page_chars" if adapter == "arxiv_pdf_v1" else ("html_dom_chars" if adapter == "published_html_v1" else "code_lines"),
                            "locator": locator,
                            "verbatim": text[:2000],
                        })
            claims: list[dict] = []
            for field, evidence in evidence_by_field.items():
                if evidence:
                    # A pattern hit is evidence for human review, not a parsed schema value.
                    claims.append(claim(field, "explicit_but_ambiguous", evidence[:3], "deterministic_pattern", ["pattern_hit_not_semantic_parse", "value_not_mapped_to_normalized_schema"]))
                else:
                    claims.append(claim(field, "not_found", [], "manual_review_required", ["no_matching_explicit_text_or_code_fragment"]))
            for path in REQUIRED_PATHS:
                if path.split(".", 1)[0] not in PATTERNS:
                    claims.append(claim(path, "not_found", [], "manual_review_required", ["nested_field_requires_explicit_structured_mapping"]))
            bundle_base["field_claims"] = claims
            found = sum(1 for c in claims if c["status"] in {"explicit", "explicit_but_ambiguous"} and c["evidence"])
            bundle_base["promotion_decision"] = "needs_review" if found else "rejected_incomplete"
            bundle_base["review_reasons"] = ["pattern evidence exists but no safe semantic/schema mapping was attempted", "all normalized nested fields require explicit values and evidence", "no candidate promotion is allowed by this POC"]
            bundles.append(bundle_base)
        except Exception as exc:
            bundle_base["snapshot"] = {
                "content_type": "unknown",
                "content_sha256": "0" * 64,
                "byte_size": 0,
                "retrieved_at": now(),
                "adapter_id": adapter,
                "source_snapshot_hash": str(record.get("source_snapshot_hash", "")),
            }
            bundle_base["field_claims"] = [claim(path, "not_found", [], "manual_review_required", ["source_acquisition_failed", type(exc).__name__]) for path in REQUIRED_PATHS]
            bundle_base["promotion_decision"] = "needs_review"
            bundle_base["review_reasons"] = ["source acquisition or parsing failed", "do not infer rules from metadata"]
            bundle_base["acquisition_error"] = type(exc).__name__
            bundles.append(bundle_base)
    result = {
        "poc_version": "deterministic_rule_extraction_v1_poc",
        "analysis_only": True,
        "reconstruction_performed": False,
        "market_data_downloaded": False,
        "backtest_run": False,
        "trial_ledger_n": 0,
        "sample_requested": args.sample_size,
        "sample_processed": len(bundles),
        "candidate_complete_count": sum(1 for x in bundles if x["promotion_decision"] == "candidate_complete"),
        "needs_review_count": sum(1 for x in bundles if x["promotion_decision"] == "needs_review"),
        "rejected_incomplete_count": sum(1 for x in bundles if x["promotion_decision"] == "rejected_incomplete"),
        "bundles": bundles,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("sample_processed", "candidate_complete_count", "needs_review_count", "rejected_incomplete_count", "trial_ledger_n")}, sort_keys=True))


if __name__ == "__main__":
    main()
