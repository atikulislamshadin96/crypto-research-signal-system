from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def oos(payload: dict) -> dict:
    for split in payload["splits"]:
        if split["name"] == "untouched_out_of_sample_test":
            return split["summary"]
    raise KeyError("untouched_out_of_sample_test")

for path in sys.argv[1:]:
    data = load(path)
    print(Path(path).name)
    for symbol, payload in data["symbols"].items():
        full = payload["full_year"]
        test = oos(payload)
        print(json.dumps({
            "symbol": symbol,
            "full_year": {k: full.get(k) for k in ("trades", "wins", "win_rate", "expectancy_r", "profit_factor", "maximum_drawdown_percent")},
            "oos": {k: test.get(k) for k in ("trades", "wins", "win_rate", "expectancy_r", "profit_factor", "maximum_drawdown_percent")},
        }, sort_keys=True))
