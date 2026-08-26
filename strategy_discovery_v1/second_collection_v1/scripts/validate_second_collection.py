#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

BASE = "b703ef1bf3d1a4f7a4a5012763430110cce77c35"
ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    data = ROOT / "data"
    first_data = REPO / "strategy_discovery_v1" / "data"
    raw = sorted(data.glob("raw_candidates_batch_*.json"))
    filt = sorted(data.glob("filtered_candidates_batch_*.json"))
    assert len(raw) == len(filt) == 8
    raw_total = sum(load(p)["raw_candidate_count"] for p in raw)
    filtered_total = sum(load(p)["filtered_candidate_count"] for p in filt)
    assert raw_total == 1000
    assert filtered_total == 787
    diagnostic = load(data / "combined_normalization_diagnostic.json")
    A, B, C = diagnostic["universes"]
    assert (A["total_candidates"], B["total_candidates"], C["total_candidates"]) == (893, 787, 1680)
    assert A["normalized_candidates"] == B["normalized_candidates"] == C["normalized_candidates"] == 0
    assert C["rejection_counts"] == {"incomplete_disclosure": 1680}
    assert diagnostic["reconciliation_checks"] == {
        "A_plus_B_equals_C_total": True,
        "C_rejections_equal_C_total": True,
        "historical_A_unchanged": True,
        "new_B_filtered_input_matches_review": True,
    }
    assert diagnostic["statistical_boundary"]["global_trial_ledger_n"] == 0
    assert diagnostic["statistical_boundary"]["trial_ids_created"] == 0
    assert len(diagnostic["representative_failure_examples"]["incomplete_disclosure"]) == 5
    source_counts = diagnostic["new_collection_source_distribution"]["by_source_id"]
    assert sum(source_counts.values()) == 787
    assert source_counts == {
        "academic_systematic_research": 276,
        "aqr_public_research": 75,
        "man_institute_research": 75,
        "microstructure_research": 292,
        "quantconnect_research": 69,
    }
    ledger = load(first_data / "global_trial_ledger.json")
    assert ledger["n_trials"] == 0 and ledger["last_sequence"] == 0
    changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], cwd=REPO, text=True).splitlines()
    assert changed and all(p.startswith("strategy_discovery_v1/second_collection_v1/") for p in changed), changed
    for rel in [
        "strategy_discovery_v1/data/normalization_review.json",
        "strategy_discovery_v1/data/global_trial_ledger.json",
        "strategy_discovery_v1/reports/collection_normalization_report.md",
    ]:
        old = subprocess.check_output(["git", "show", f"{BASE}:{rel}"], cwd=REPO)
        new = (REPO / rel).read_bytes()
        assert hashlib.sha256(old).hexdigest() == hashlib.sha256(new).hexdigest(), rel
    report = (ROOT / "reports" / "combined_normalization_diagnostic_report.md").read_text(encoding="utf-8")
    for heading in ["## A. New collection", "## B. Existing first run", "## C. Combined universe", "## D. Representative failure analysis", "## E. Diagnosis", "## F. Integrity and statistical boundary", "## G. References"]:
        assert heading in report, heading
    assert "No schema, protocol, reconstruction experiment, backtest" in report
    print(json.dumps({
        "validation": "PASS",
        "raw_total": raw_total,
        "filtered_total": filtered_total,
        "combined_total": C["total_candidates"],
        "representative_examples": len(diagnostic["representative_failure_examples"]["incomplete_disclosure"]),
        "ledger_n": ledger["n_trials"],
        "scoped_changed_files": len(changed),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
