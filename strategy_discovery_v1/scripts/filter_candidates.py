#!/usr/bin/env python3
"""Apply the frozen pre-normalization rejection taxonomy to raw source records."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

PATTERNS = {
    "lagging_indicator_primary": [
        r"\brsi\b", r"\bema\b", r"\bsma\b", r"moving average", r"\bmacd\b", r"stochastic", r"bollinger",
    ],
    "generic_price_pattern_primary": [
        r"support and resistance", r"support/resistance", r"generic breakout", r"breakout strategy", r"breakout trading",
    ],
    "standalone_smc_ict_primary": [
        r"\bfvg\b", r"fair value gap", r"order block", r"\bbos\b", r"\bchoch\b", r"change of character",
    ],
    "retail_marketing_source": [r"win rate", r"signal seller", r"guaranteed returns", r"90%"],
}


def classify(record: dict[str, object]) -> str | None:
    haystack = f"{record.get('document_title', '')} {record.get('abstract', '')}".lower()
    for category, patterns in PATTERNS.items():
        if any(re.search(pattern, haystack) for pattern in patterns):
            return category
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = json.loads(Path(args.input).read_text())
    survivors: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    for record in source["candidates"]:
        category = classify(record)
        if category:
            counts[category] += 1
        else:
            survivors.append(record)
    payload = {
        "batch_id": source["batch_id"],
        "filter_version": "strategy_discovery_rejection_filter_v1",
        "source_file": args.input,
        "raw_candidate_count": len(source["candidates"]),
        "filtered_candidate_count": len(survivors),
        "rejection_counts": dict(sorted(counts.items())),
        "candidates": survivors,
        "rejection_reporting": "summary_counts_only",
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"batch_id": source["batch_id"], "raw": len(source["candidates"]), "survivors": len(survivors), "rejection_counts": dict(sorted(counts.items()))}, sort_keys=True))


if __name__ == "__main__":
    main()
