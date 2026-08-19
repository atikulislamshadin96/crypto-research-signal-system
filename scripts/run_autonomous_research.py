#!/usr/bin/env python3
"""Run one bounded autonomous research cycle; never submits orders."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow direct execution from a clean GitHub Actions checkout.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_signal_system.research_engine import (  # noqa: E402
    HypothesisRegistry,
    dataset_manifest_hash,
    frozen_candidate_grid,
    make_fingerprint,
)
from crypto_signal_system.research_evaluation import ResearchEvaluator  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded analysis-only autonomous research")
    parser.add_argument("--registry", default="artifacts/research_engine/registry.sqlite3")
    parser.add_argument("--output-dir", default="artifacts/research_engine/cycles")
    parser.add_argument("--queue", default="config/research_queue.json")
    parser.add_argument("--data-path", action="append", dest="data_paths", default=[], help="Required data file; repeat for multiple files")
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--stale-after-hours", type=float, default=36.0)
    return parser.parse_args()


def load_priority_candidates(queue_path: str | Path) -> tuple[list[object], str | None]:
    """Load only immutable queue entries; fall back to the full frozen grid if absent."""
    path = Path(queue_path)
    if not path.is_absolute():
        path = ROOT / path
    all_candidates = frozen_candidate_grid()
    if not path.exists():
        return all_candidates, None
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_id = {candidate.hypothesis_id: candidate for candidate in all_candidates}
    ordered: list[object] = []
    for row in sorted(payload.get("candidates", []), key=lambda item: int(item.get("priority", 9999))):
        hypothesis_id = row.get("hypothesis_id")
        candidate = by_id.get(hypothesis_id)
        if candidate is not None:
            ordered.append(candidate)
    if not ordered:
        return all_candidates, str(path)
    return ordered, str(path)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cycle_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = output_dir / f"{cycle_id}.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.FileHandler(log_path), logging.StreamHandler()])
    logger = logging.getLogger("autonomous-research")

    data_paths = [Path(item) for item in args.data_paths]
    data_hash = dataset_manifest_hash(data_paths or [output_dir / "<required-data-not-supplied>"])
    dataset_available = bool(data_paths) and all(path.exists() and path.is_file() for path in data_paths)
    if dataset_available:
        newest_mtime = max(path.stat().st_mtime for path in data_paths)
        age_hours = (datetime.now(timezone.utc).timestamp() - newest_mtime) / 3600.0
        dataset_fresh = age_hours <= args.stale_after_hours
    else:
        age_hours = None
        dataset_fresh = False

    registry = HypothesisRegistry(args.registry)
    evaluator = ResearchEvaluator(registry)
    candidates, queue_path = load_priority_candidates(args.queue)
    candidates = candidates[: max(0, args.max_candidates)]
    cycle_rows: list[dict[str, object]] = []
    registered = 0
    skipped = 0
    try:
        for spec in candidates:
            identity = make_fingerprint(spec, data_hash)
            if not registry.register(spec, identity):
                skipped += 1
                cycle_rows.append({"hypothesis_id": spec.hypothesis_id, "fingerprint": identity.fingerprint, "status": "duplicate_skipped"})
                continue
            registered += 1
            result = evaluator.evaluate(spec, identity, dataset_available=dataset_available, dataset_fresh=dataset_fresh)
            row = result.to_dict()
            row["title"] = spec.title
            row["family"] = spec.family
            cycle_rows.append(row)
            logger.info("%s -> %s", spec.hypothesis_id, result.status)

        summary = {
            "cycle_id": cycle_id,
            "engine_version": "0.1.0",
            "protocol_version": "research-ladder-v1",
            "queue_path": queue_path,
            "queue_priority_order": [spec.hypothesis_id for spec in candidates],
            "analysis_only": True,
            "live_execution_enabled": False,
            "dataset_hash": data_hash,
            "dataset_paths": [str(path) for path in data_paths],
            "dataset_available": dataset_available,
            "dataset_age_hours": age_hours,
            "registered": registered,
            "duplicate_skipped": skipped,
            "results": cycle_rows,
        }
        json_path = output_dir / f"{cycle_id}.json"
        json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        md_path = output_dir / f"{cycle_id}.md"
        lines = [
            f"# Autonomous Research Cycle {cycle_id}",
            "",
            "> Analysis-only. Live order execution is permanently disabled by design.",
            "",
            f"Dataset available: **{dataset_available}**; fresh: **{dataset_fresh}**; registered: **{registered}**; duplicate skipped: **{skipped}**.",
            "",
            "| Hypothesis | Family | Status | Blocked stage | Reason |",
            "|---|---|---|---|---|",
        ]
        for row in cycle_rows:
            lines.append(f"| {row.get('hypothesis_id','')} | {row.get('family','')} | {row.get('status','')} | {row.get('blocked_stage','')} | {row.get('rejection_reason','')} |")
        lines.extend(["", "No result in this artifact authorizes paper trading or live execution.", ""])
        md_path.write_text("\n".join(lines), encoding="utf-8")
        registry.export_json(output_dir / "registry.json")
        print(json.dumps({"cycle_id": cycle_id, "json": str(json_path), "markdown": str(md_path), "log": str(log_path), "registered": registered, "duplicate_skipped": skipped, "analysis_only": True, "live_execution_enabled": False}, indent=2))
        return 0
    finally:
        registry.close()


if __name__ == "__main__":
    raise SystemExit(main())
