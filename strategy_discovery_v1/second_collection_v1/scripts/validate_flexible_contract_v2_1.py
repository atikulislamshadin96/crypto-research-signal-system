#!/usr/bin/env python3
"""Validate the v2.1 flexible-completeness field contract.

This validator is read-only. It checks that the schema, manifest template, and
Freqtrade reassessment script expose the same required harness fields.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "extraction_evidence_bundle_v2_1.schema.json"
TEMPLATE = ROOT / "execution_assumption_manifest_v1_1.template.json"
SCRIPT = ROOT / "scripts" / "re_evaluate_freqtrade_v2_1.py"


def canonical_hash(fields: list[str]) -> str:
    payload = json.dumps(fields, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def script_fields() -> list[str]:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "EXECUTION_FIELDS" for target in node.targets)
    )
    return [element.value for element in assignment.value.elts]


def main() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    schema_fields = schema["properties"]["execution_assumption_fields"]["items"]["enum"]
    template_fields = template["required_fields"]
    reassessment_fields = script_fields()
    sets = {"schema": set(schema_fields), "template": set(template_fields), "script": set(reassessment_fields)}
    if len({frozenset(value) for value in sets.values()}) != 1:
        raise SystemExit(json.dumps({"error": "field_set_mismatch", "fields": {key: sorted(value) for key, value in sets.items()}}, sort_keys=True))
    if schema.get("$id", "").endswith("extraction_evidence_bundle_v2.schema.json"):
        raise SystemExit("schema id still points to v2")
    if schema["properties"]["extraction_version"]["const"] != "deterministic_rule_extraction_v2_1":
        raise SystemExit("schema extraction version is not v2.1")
    if template["manifest_version"] != "execution_assumption_manifest_v1_1" or template["status"] != "template_not_frozen":
        raise SystemExit("template version/status is invalid")
    if template["field_value_contract"]["origin"] != "external_assumption":
        raise SystemExit("template does not require external_assumption origin")
    result = {
        "status": "ok",
        "field_count": len(schema_fields),
        "fields": schema_fields,
        "field_contract_sha256": canonical_hash(schema_fields),
        "schema_version": schema["properties"]["extraction_version"]["const"],
        "manifest_template_version": template["manifest_version"],
        "analysis_only": True,
        "backtest_authorized": False,
        "trial_creation": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
