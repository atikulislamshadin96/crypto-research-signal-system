#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE = "a3665dccaf8cada2352a182594d5fdc206a6d235"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    sample = load(ROOT / "data" / "original_893_stratified_sample.json")
    result = load(ROOT / "data" / "original_893_extraction_poc_results.json")
    assert sample["population_count"] == 893
    assert sample["sample_count"] == 40
    assert sample["source_class_counts"] == {"academic_preprint": 893}
    assert len(sample["candidates"]) == 40
    assert set(sample["selected_category_counts"]) == {"q-fin.CP", "q-fin.GN", "q-fin.MF", "q-fin.PM", "q-fin.PR", "q-fin.RM", "q-fin.ST", "q-fin.TR"}
    assert result["sample_processed"] == 40
    counts = {k: result[k] for k in ("candidate_complete_count", "needs_review_count", "rejected_incomplete_count")}
    assert sum(counts.values()) == 40
    assert counts["candidate_complete_count"] == 0
    assert counts["needs_review_count"] == 40
    assert counts["rejected_incomplete_count"] == 0
    assert result["trial_ledger_n"] == 0
    assert result["reconstruction_performed"] is False
    assert result["market_data_downloaded"] is False
    assert result["backtest_run"] is False
    bundles = result["bundles"]
    assert len(bundles) == 40
    assert all(b["promotion_decision"] == "needs_review" for b in bundles)
    assert all(b["reconstruction_performed"] is False for b in bundles)
    for bundle in bundles:
        snap = bundle["snapshot"]
        assert snap["byte_size"] > 0
        path = ROOT / "original_893_poc_snapshots" / (snap["content_sha256"] + ".source")
        assert path.exists()
        raw = path.read_bytes()
        assert len(raw) == snap["byte_size"]
        assert hashlib.sha256(raw).hexdigest() == snap["content_sha256"]
        evidence = [e for claim in bundle["field_claims"] for e in claim["evidence"]]
        assert evidence
        assert all(e["snapshot_sha256"] == snap["content_sha256"] for e in evidence)
    ledger = load(REPO / "strategy_discovery_v1" / "data" / "global_trial_ledger.json")
    assert ledger["n_trials"] == 0 and ledger["last_sequence"] == 0
    tracked_changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], cwd=REPO, text=True).splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=REPO, text=True).splitlines()
    changed = sorted(set(tracked_changed + untracked))
    assert changed and all(p.startswith("strategy_discovery_v1/second_collection_v1/") for p in changed), changed
    for rel in [
        "strategy_discovery_v1/data/normalization_review.json",
        "strategy_discovery_v1/data/global_trial_ledger.json",
        "strategy_discovery_v1/schemas/normalized_strategy.schema.json",
        "strategy_discovery_v1/protocols/dsr_pbo_cpcv_v1.json",
    ]:
        old = subprocess.check_output(["git", "show", f"{BASE}:{rel}"], cwd=REPO)
        assert hashlib.sha256(old).hexdigest() == hashlib.sha256((REPO / rel).read_bytes()).hexdigest(), rel
    print(json.dumps({"validation": "PASS", "population": sample["population_count"], "sample": sample["sample_count"], "sample_category_counts": sample["selected_category_counts"], "outcomes": counts, "ledger_n": ledger["n_trials"], "scoped_changed_files": len(changed)}, sort_keys=True))


if __name__ == "__main__":
    main()
