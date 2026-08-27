#!/usr/bin/env python3
"""Select a fixed 40-lead sample from the immutable original 893 records."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_filtered(data_dir: Path) -> list[dict]:
    records: list[dict] = []
    for path in sorted(data_dir.glob("filtered_candidates_batch_*.json")):
        records.extend(json.loads(path.read_text(encoding="utf-8"))["candidates"])
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-size", type=int, default=40)
    args = parser.parse_args()
    records = load_filtered(Path(args.input_dir))
    assert len(records) == 893, len(records)
    source_classes = Counter(str(r.get("source_class")) for r in records)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        cats = sorted(str(x) for x in r.get("categories", []))
        qfin = [c for c in cats if c.startswith("q-fin.")]
        # The original source_class is homogeneous academic_preprint. Use the
        # relevant q-fin category as the internal diversity dimension, while
        # preserving every original category in each selected record.
        grouped[(qfin[0] if qfin else "non_qfin")].append(r)
    category_order = sorted(k for k in grouped if k.startswith("q-fin."))
    if not category_order:
        raise SystemExit("original population has no q-fin category records")
    quota_base = args.sample_size // len(category_order)
    remainder = args.sample_size % len(category_order)
    selected: list[dict] = []
    allocation: dict[str, int] = {}
    for index, category in enumerate(category_order):
        target = quota_base + (1 if index < remainder else 0)
        pool = sorted(grouped[category], key=lambda r: str(r.get("document_id")))
        if target > len(pool):
            target = len(pool)
        if target:
            step = max(len(pool) / target, 1)
            positions = [min(int(i * step), len(pool) - 1) for i in range(target)]
            chosen = [pool[pos] for pos in positions]
            selected.extend(chosen)
            allocation[category] = len(chosen)
    selected = sorted(selected, key=lambda r: str(r.get("document_id")))[: args.sample_size]
    # If category caps or duplicate multi-category assignments leave a shortfall,
    # deterministically fill from the remaining records.
    selected_ids = {str(r.get("document_id")) for r in selected}
    if len(selected) < args.sample_size:
        for r in sorted(records, key=lambda x: str(x.get("document_id"))):
            if str(r.get("document_id")) not in selected_ids:
                selected.append(r)
                selected_ids.add(str(r.get("document_id")))
                if len(selected) == args.sample_size:
                    break
    assert len(selected) == args.sample_size
    payload = {
        "sample_version": "original_893_stratified_sample_v1",
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
        "trial_ledger_n": 0,
        "source_dataset": "immutable_original_893_filtered_candidates",
        "population_count": len(records),
        "sample_count": len(selected),
        "stratification_dimension": "q_fin_arxiv_category_because_source_class_is_homogeneous",
        "source_class_counts": dict(sorted(source_classes.items())),
        "category_allocation": dict(sorted(allocation.items())),
        "selected_category_counts": dict(sorted(Counter(next((str(c) for c in sorted(r.get("categories", [])) if str(c).startswith("q-fin.")), "non_qfin") for r in selected).items())),
        "candidates": selected,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"population": len(records), "sample": len(selected), "source_class_counts": dict(sorted(source_classes.items())), "category_allocation": dict(sorted(allocation.items()))}, sort_keys=True))


if __name__ == "__main__":
    main()
