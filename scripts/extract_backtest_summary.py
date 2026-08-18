from __future__ import annotations

import json
from pathlib import Path

source = Path("artifacts/historical-backtest-2025-15m-validated.json")
target = Path("artifacts/historical-backtest-2025-15m-summary.json")
data = json.loads(source.read_text(encoding="utf-8"))
summary = {"year": data["year"], "timeframe": data["timeframe"], "source": data["source"], "symbols": {}}
for symbol, payload in data["symbols"].items():
    validation = payload["validation"]
    summary["symbols"][symbol] = {
        "archive_files": len(payload["manifest"]["files"]),
        "archive_rows": sum(item["rows"] for item in payload["manifest"]["files"]),
        "full_year": payload["summary"],
        "splits": [
            {
                "name": window["name"],
                "start": window["start"],
                "end": window["end"],
                "summary": window["summary"],
                "warnings": window["warnings"],
            }
            for window in validation["splits"]
        ],
        "walk_forward": [
            {"name": window["name"], "summary": window["summary"], "warnings": window["warnings"]}
            for window in validation["walk_forward"]
        ],
        "sensitivity": validation["sensitivity"],
        "rejected": validation["rejected"],
        "rejection_reasons": validation["rejection_reasons"],
    }
target.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(target)
