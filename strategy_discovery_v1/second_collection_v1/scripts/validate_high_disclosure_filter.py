#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import random
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE = "41d54ff49e734549b6f781b209546cb1e7d88b28"
PATTERNS = {
    "numbered_algorithm_or_pseudocode_block": re.compile(r"^\s*(?:Algorithm|Pseudocode)\s+(?:No\.?\s*)?\d+(?:\s*[:.-].*)?$", re.I),
    "explicit_implementation_section": re.compile(r"^\s*(?:\d+(?:\.\d+)*\s+)?Implementation(?:\s+Details)?\s*[:.]?\s*$", re.I),
    "appendix_trading_rules_section": re.compile(r"^\s*Appendix(?:\s+[A-Z])?\s*[:.-]\s*Trading\s+Rules\s*[:.]?\s*$", re.I),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    criteria = load(ROOT / "high_disclosure_criteria_v1.json")
    result = load(ROOT / "data" / "high_disclosure_filter_results.json")
    sample = load(ROOT / "data" / "high_disclosure_random_sample.json")
    assert criteria["criteria_version"] == "high_disclosure_paper_selection_v1"
    assert criteria["frozen_before_application"] is True
    assert result["criteria_version"] == criteria["criteria_version"]
    assert result["criteria_sha256"] == hashlib.sha256((ROOT / "high_disclosure_criteria_v1.json").read_bytes()).hexdigest()
    assert result["population_count"] == 893
    assert result["pass_count"] == 62
    assert result["fail_count"] == 831
    assert result["pass_count"] + result["fail_count"] == result["population_count"]
    assert result["matched_pattern_counts"] == {"explicit_implementation_section": 18, "numbered_algorithm_or_pseudocode_block": 45}
    assert result["failure_reason_counts"] == {"RuntimeError:acquisition_failed:HTTPError": 3, "no_frozen_high_disclosure_pattern_with_three_nonempty_lookahead_lines": 828}
    assert result["analysis_only"] is True and result["market_data_downloaded"] is False and result["backtest_run"] is False and result["trial_ledger_n"] == 0
    records = result["records"]
    assert len(records) == 893
    for record in records:
        if record["decision"] == "pass":
            assert record["acquisition_status"] == "success"
            assert record["text_extraction_status"] == "success"
            assert record["matched_pattern_families"]
            for m in record["matched_headings"]:
                assert m["lookahead_nonempty_line_count"] >= 3
                assert any(PATTERNS[m["pattern_family"]].fullmatch(m["heading"]) for _ in [0])
            snap = ROOT / "high_disclosure_snapshots" / (record["content_sha256"] + ".pdf")
            assert snap.exists()
            assert snap.stat().st_size == record["content_bytes"]
            assert hashlib.sha256(snap.read_bytes()).hexdigest() == record["content_sha256"]
        else:
            assert record["decision"] == "fail"
            assert record["failure_reason"]
            if record["acquisition_status"] == "success":
                assert record["text_extraction_status"] == "success"
                assert not record["matched_pattern_families"]
    pass_ids = [r["document_id"] for r in records if r["decision"] == "pass"]
    rng = random.Random(criteria["sampling"]["seed"])
    expected = rng.sample(pass_ids, min(criteria["sampling"]["target_sample_size"], len(pass_ids)))
    assert sample["sample_count"] == 30
    assert sample["sample_seed"] == 20260827
    assert sample["sample_document_ids"] == expected
    assert sample["analysis_only"] is True and sample["trial_ledger_n"] == 0
    ledger = load(REPO / "strategy_discovery_v1" / "data" / "global_trial_ledger.json")
    assert ledger["n_trials"] == 0 and ledger["last_sequence"] == 0
    changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], cwd=REPO, text=True).splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=REPO, text=True).splitlines()
    status = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).splitlines()
    modified = [line[3:] for line in status if line.startswith(" M ")]
    all_changed = sorted(set(changed + untracked + modified))
    assert all_changed and all(p.startswith("strategy_discovery_v1/second_collection_v1/") for p in all_changed), all_changed
    print(json.dumps({"validation": "PASS", "population": 893, "pass": result["pass_count"], "fail": result["fail_count"], "sample": sample["sample_count"], "sample_seed": sample["sample_seed"], "ledger_n": ledger["n_trials"], "scoped_working_tree_files": len(all_changed)}, sort_keys=True))


if __name__ == "__main__":
    main()
