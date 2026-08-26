#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE = "b703ef1bf3d1a4f7a4a5012763430110cce77c35"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    result = load(ROOT / "data" / "extraction_poc_results.json")
    schema = load(ROOT / "schemas" / "extraction_evidence_bundle.schema.json")
    assert schema["properties"]["analysis_only"]["const"] is True
    assert schema["properties"]["reconstruction_performed"]["const"] is False
    assert result["sample_requested"] == 5
    assert result["sample_processed"] == 5
    assert result["candidate_complete_count"] == 0
    assert result["needs_review_count"] == 5
    assert result["rejected_incomplete_count"] == 0
    assert result["analysis_only"] is True
    assert result["reconstruction_performed"] is False
    assert result["market_data_downloaded"] is False
    assert result["backtest_run"] is False
    assert result["trial_ledger_n"] == 0
    bundles = result["bundles"]
    assert {b["source_identity"]["source_id"] for b in bundles} == {
        "academic_systematic_research", "aqr_public_research", "man_institute_research", "microstructure_research", "quantconnect_research"
    }
    for bundle in bundles:
        snap = bundle["snapshot"]
        assert bundle["analysis_only"] is True
        assert bundle["reconstruction_performed"] is False
        assert bundle["promotion_decision"] == "needs_review"
        assert snap["byte_size"] > 0
        snapshot_path = ROOT / "poc_snapshots" / (snap["content_sha256"] + ".source")
        assert snapshot_path.exists()
        raw = snapshot_path.read_bytes()
        assert len(raw) == snap["byte_size"]
        assert hashlib.sha256(raw).hexdigest() == snap["content_sha256"]
        evidence = [e for claim in bundle["field_claims"] for e in claim["evidence"]]
        assert evidence
        assert all(e["snapshot_sha256"] == snap["content_sha256"] for e in evidence)
        assert all(e["verbatim"] for e in evidence)
        assert all(claim["status"] in {"explicit_but_ambiguous", "not_found"} for claim in bundle["field_claims"])
    ledger = load(REPO / "strategy_discovery_v1" / "data" / "global_trial_ledger.json")
    assert ledger["n_trials"] == 0
    assert ledger["last_sequence"] == 0
    changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], cwd=REPO, text=True).splitlines()
    assert changed and all(p.startswith("strategy_discovery_v1/second_collection_v1/") for p in changed), changed
    for rel in [
        "strategy_discovery_v1/data/normalization_review.json",
        "strategy_discovery_v1/data/global_trial_ledger.json",
        "strategy_discovery_v1/schemas/normalized_strategy.schema.json",
        "strategy_discovery_v1/protocols/dsr_pbo_cpcv_v1.json",
    ]:
        old = subprocess.check_output(["git", "show", f"{BASE}:{rel}"], cwd=REPO)
        assert hashlib.sha256(old).hexdigest() == hashlib.sha256((REPO / rel).read_bytes()).hexdigest(), rel
    print(json.dumps({"validation": "PASS", "sample": len(bundles), "candidate_complete": result["candidate_complete_count"], "needs_review": result["needs_review_count"], "ledger_n": ledger["n_trials"], "scoped_changed_files": len(changed)}, sort_keys=True))


if __name__ == "__main__":
    main()
