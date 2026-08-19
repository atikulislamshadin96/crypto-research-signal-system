from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("artifacts/bos-4h-daily/phase1_bos_extension")


def get_summary(item: dict) -> dict:
    return item.get("summary", item)


def main() -> None:
    rows = []
    for path in sorted(ROOT.glob("*-phase1-validation.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        asset = path.name.split("-")[0]
        final = report["final_oos"]
        final_s = get_summary(final)
        costs = {}
        for key in ("5bps", "10bps", "15bps"):
            item = report["cost_stress"][key]
            s = get_summary(item)
            costs[key] = {
                "trades": item.get("trade_count", s.get("trades")),
                "exp_r": round(s.get("expectancy_r", 0), 6),
                "wr": round(s.get("win_rate", 0), 4),
                "pf": round(s.get("profit_factor", 0), 4),
                "dd_pct": round(s.get("maximum_drawdown_percent", 0), 4),
            }
        wf = report.get("walk_forward", [])
        perturbation = report.get("parameter_perturbation", [])
        perturbation_count = len(perturbation) if isinstance(perturbation, list) else len(perturbation.get("variants", []))
        rows.append({
            "asset": asset,
            "period": [report.get("period_start"), report.get("period_end")],
            "observations": report.get("observations"),
            "final_oos": {
                "trades": final.get("trade_count", final_s.get("trades")),
                "exp_r": round(final_s.get("expectancy_r", 0), 6),
                "wr": round(final_s.get("win_rate", 0), 4),
                "pf": round(final_s.get("profit_factor", 0), 4),
                "dd_pct": round(final_s.get("maximum_drawdown_percent", 0), 4),
                "prop_return_pct": round(final.get("prop_firm", {}).get("return_percent", 0), 4),
                "prop_breach": final.get("prop_firm", {}).get("breach"),
                "bootstrap_p05": round(final.get("uncertainty", {}).get("p05_r", 0), 6),
                "bootstrap_p50": round(final.get("uncertainty", {}).get("p50_r", 0), 6),
                "bootstrap_p95": round(final.get("uncertainty", {}).get("p95_r", 0), 6),
            },
            "costs": costs,
            "wf_windows": len(wf),
            "wf_negative": report.get("walk_forward_negative_windows"),
            "terminal_wf": report.get("terminal_walk_forward_oos"),
            "cpcv": report.get("purged_cpcv"),
            "perturbation_variant_count": perturbation_count,
            "rejected": report.get("rejected"),
            "reasons": report.get("rejection_reasons"),
        })
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
