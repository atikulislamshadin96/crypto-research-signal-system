#!/usr/bin/env python3
"""Apply frozen high-disclosure paper criteria to all original 893 records."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

LOOKAHEAD_NONEMPTY = 3
LOOKAHEAD_MAX = 25
PATTERNS = {
    "numbered_algorithm_or_pseudocode_block": re.compile(r"^\s*(?:Algorithm|Pseudocode)\s+(?:No\.?\s*)?\d+(?:\s*[:.-].*)?$", re.I),
    "explicit_implementation_section": re.compile(r"^\s*(?:\d+(?:\.\d+)*\s+)?Implementation(?:\s+Details)?\s*[:.]?\s*$", re.I),
    "appendix_trading_rules_section": re.compile(r"^\s*Appendix(?:\s+[A-Z])?\s*[:.-]\s*Trading\s+Rules\s*[:.]?\s*$", re.I),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_pdf(url: str, attempts: int = 3) -> tuple[bytes, str]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            req = Request(url, headers={"User-Agent": "strategy-discovery-v1-high-disclosure-filter/1.0", "Accept": "application/pdf,*/*"})
            with urlopen(req, timeout=60) as resp:
                data = resp.read()
                if not data:
                    raise RuntimeError("empty_response")
                return data, resp.headers.get("Content-Type", "")
        except Exception as exc:
            last = exc
    raise RuntimeError(f"acquisition_failed:{type(last).__name__}")


def pdf_lines(data: bytes) -> list[str]:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as source:
        source.write(data)
        source.flush()
        proc = subprocess.run(["pdftotext", "-layout", source.name, "-"], capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError("pdftotext_failed")
    return proc.stdout.decode("utf-8", errors="replace").splitlines()


def classify(record: dict, snapshot_dir: Path) -> dict:
    url = str(record.get("rule_disclosure_locator") or "")
    base = {
        "document_id": str(record.get("document_id")),
        "document_title": str(record.get("document_title")),
        "source_class": str(record.get("source_class")),
        "source_id": str(record.get("source_id")),
        "canonical_url": str(record.get("canonical_url")),
        "rule_disclosure_locator": url,
        "document_version": str(record.get("document_version", "")),
        "retrieved_at": now(),
        "decision": "fail",
        "matched_pattern_families": [],
        "matched_headings": [],
        "acquisition_status": "failed",
        "text_extraction_status": "not_attempted",
        "content_sha256": None,
        "content_bytes": 0,
        "failure_reason": None,
    }
    try:
        data, content_type = fetch_pdf(url)
        digest = sha256(data)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        (snapshot_dir / f"{digest}.pdf").write_bytes(data)
        base["content_sha256"] = digest
        base["content_bytes"] = len(data)
        base["acquisition_status"] = "success"
        lines = pdf_lines(data)
        base["text_extraction_status"] = "success"
        for i, line in enumerate(lines):
            for name, pattern in PATTERNS.items():
                if pattern.fullmatch(line):
                    following = [x.strip() for x in lines[i + 1 : i + 1 + LOOKAHEAD_MAX] if x.strip()]
                    if len(following) >= LOOKAHEAD_NONEMPTY:
                        base["matched_pattern_families"].append(name)
                        base["matched_headings"].append({"pattern_family": name, "line_number": i + 1, "heading": line.strip(), "lookahead_nonempty_line_count": len(following[:LOOKAHEAD_MAX]), "lookahead_excerpt": following[:5]})
        base["matched_pattern_families"] = sorted(set(base["matched_pattern_families"]))
        base["decision"] = "pass" if base["matched_pattern_families"] else "fail"
        if base["decision"] == "fail":
            base["failure_reason"] = "no_frozen_high_disclosure_pattern_with_three_nonempty_lookahead_lines"
    except Exception as exc:
        base["failure_reason"] = type(exc).__name__ + (":" + str(exc) if str(exc) else "")
    return base


def load_records(input_dir: Path) -> list[dict]:
    records: list[dict] = []
    for path in sorted(input_dir.glob("filtered_candidates_batch_*.json")):
        records.extend(json.loads(path.read_text(encoding="utf-8"))["candidates"])
    assert len(records) == 893, len(records)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--criteria", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-output", required=True)
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    criteria_path = Path(args.criteria)
    criteria = json.loads(criteria_path.read_text(encoding="utf-8"))
    assert criteria["criteria_version"] == "high_disclosure_paper_selection_v1"
    assert criteria["frozen_before_application"] is True
    assert criteria["normalization"]["lookahead_nonempty_lines"] == LOOKAHEAD_NONEMPTY
    assert criteria["normalization"]["lookahead_max_lines"] == LOOKAHEAD_MAX
    records = load_records(Path(args.input_dir))
    snapshot_dir = Path(args.snapshot_dir)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_map = {pool.submit(classify, record, snapshot_dir): record for record in records}
        for future in as_completed(future_map):
            results.append(future.result())
    results.sort(key=lambda x: x["document_id"])
    passers = [x for x in results if x["decision"] == "pass"]
    failures = [x for x in results if x["decision"] == "fail"]
    rng = random.Random(criteria["sampling"]["seed"])
    ordered_ids = [x["document_id"] for x in passers]
    sample_ids = rng.sample(ordered_ids, min(criteria["sampling"]["target_sample_size"], len(ordered_ids)))
    sample_set = set(sample_ids)
    sample = [x for x in passers if x["document_id"] in sample_set]
    sample.sort(key=lambda x: sample_ids.index(x["document_id"]))
    output = {
        "criteria_version": criteria["criteria_version"],
        "criteria_sha256": sha256(criteria_path.read_bytes()),
        "population_count": len(records),
        "pass_count": len(passers),
        "fail_count": len(failures),
        "failure_reason_counts": dict(sorted(Counter(str(x["failure_reason"]) for x in failures).items())),
        "matched_pattern_counts": dict(sorted(Counter(name for x in passers for name in x["matched_pattern_families"]).items())),
        "source_class_counts": dict(sorted(Counter(str(x["source_class"]) for x in records).items())),
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
        "trial_ledger_n": 0,
        "records": results,
    }
    sample_output = {
        "criteria_version": criteria["criteria_version"],
        "criteria_sha256": output["criteria_sha256"],
        "population_count": len(records),
        "pass_count": len(passers),
        "sample_seed": criteria["sampling"]["seed"],
        "sample_method": criteria["sampling"]["method"],
        "sample_count": len(sample),
        "sample_document_ids": sample_ids,
        "sample_records": sample,
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
        "trial_ledger_n": 0,
    }
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    sout = Path(args.sample_output); sout.parent.mkdir(parents=True, exist_ok=True); sout.write_text(json.dumps(sample_output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"population": len(records), "pass": len(passers), "fail": len(failures), "sample": len(sample), "failure_reason_counts": output["failure_reason_counts"], "matched_pattern_counts": output["matched_pattern_counts"], "seed": criteria["sampling"]["seed"]}, sort_keys=True))


if __name__ == "__main__":
    main()
