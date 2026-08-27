#!/usr/bin/env python3
"""Validate the v2.2 external-applicability policy reassessment."""
from __future__ import annotations

import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "extraction_evidence_bundle_v2_2.schema.json"
TEMPLATE = ROOT / "execution_assumption_manifest_v1_2.template.json"
REASSESSMENT = ROOT / "data" / "freqtrade_batch_001_reassessment_v2_2.json"


def main() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    reassessment = json.loads(REASSESSMENT.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    fields = schema["properties"]["execution_assumption_fields"]["items"]["enum"]
    assert template["manifest_version"] == "execution_assumption_manifest_v1_2"
    assert template["status"] == "template_not_frozen"
    assert template["applicability_policy"] == "uniform_external_research_scope_permitted_v2_2"
    assert set(fields) == set(template["required_fields"])
    assert template["applicability_field_contract"]["origin"] == "external_assumption"
    assert reassessment["re_evaluation_status_counts"] == {"execution_assumption_required": 11, "filter_rejected_primary": 13, "needs_review": 1}
    assert reassessment["source_rule_status_counts"] == {"needs_review": 1, "rejected_incomplete": 13, "source_rule_complete": 11}
    assert reassessment["policy_decision"] == "accept_uniform_external_research_scope"
    assert reassessment["execution_assumption_manifest"]["status"] == "not_present"
    assert reassessment["trial_ledger_n"] == 893
    assert reassessment["analysis_only"] and not reassessment["backtest_run"] and not reassessment["market_data_downloaded"] and not reassessment["trial_created"]
    complete = [r for r in reassessment["records"] if r["source_rule_status"] == "source_rule_complete"]
    assert len(complete) == 11
    assert all(r["source_applicability_resolution"] == "uniform_external_research_scope" for r in complete)
    assert all(set(r["execution_assumption_fields"]) == set(fields) for r in complete)
    review = [r for r in reassessment["records"] if r["re_evaluation_status"] == "needs_review"]
    assert [r["source_path"] for r in review] == ["user_data/strategies/FixedRiskRewardLoss.py"]
    print(json.dumps({"status": "ok", "field_count": len(fields), "reassessment": reassessment["re_evaluation_status_counts"], "complete_source_rules": len(complete), "review": len(review), "trial_ledger_n": 893}, sort_keys=True))


if __name__ == "__main__":
    main()
