from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/historical-backtest-2025-15m-validated.json")
data = json.loads(path.read_text())
for symbol, payload in data.get("symbols", {}).items():
    groups = defaultdict(lambda: {"trades": 0, "wins": 0, "r": 0.0, "fees": 0.0, "funding": 0.0, "slippage": 0.0})
    for trade in payload.get("trades", []):
        key = trade.get("strategy", "unknown")
        g = groups[key]
        g["trades"] += 1
        r_multiple = float(trade.get("r_multiple", 0.0))
        if r_multiple > 0:
            g["wins"] += 1
        g["r"] += r_multiple
        g["fees"] += float(trade.get("fees", 0.0) or 0.0)
        g["funding"] += float(trade.get("funding", 0.0) or 0.0)
        g["slippage"] += float(trade.get("slippage", 0.0) or 0.0)
    print(symbol)
    for strategy, g in sorted(groups.items()):
        avg = g["r"] / g["trades"] if g["trades"] else 0.0
        win = g["wins"] / g["trades"] if g["trades"] else 0.0
        print(json.dumps({"strategy": strategy, **g, "win_rate": win, "average_r": avg}, sort_keys=True))
    print("rejections", json.dumps(payload.get("rejection_reasons", []), sort_keys=True))
    print()
