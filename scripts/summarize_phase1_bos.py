from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("artifacts/bos-4h-daily/phase1_bos_extension")


def summary(report: dict) -> dict:
    final = report["final_oos"]
    final_summary = final.get("summary", final)
    costs = {}
    for key, item in report["cost_stress"].items():
        s = item.get("summary", item)
        costs[key] = {
            "trades": item.get("trade_count", s.get("trades")),
            "expectancy_r": s.get("expectancy_r"),
            "win_rate": s.get("win_rate"),
            "profit_factor": s.get("profit_factor"),
            "max_dd_pct": s.get("maximum_drawdown_percent"),
            "prop_return_pct": item.get("prop_firm", {}).get("return_percent"),
            "prop_breach": item.get("prop_firm", {}).get("breach"),
        }
    perturb = report.get("parameter_perturbation", {})
    variants = perturb.get("variants", perturb.get("results", [])) if isinstance(perturb, dict) else []
    return {
        "period_start": report.get("period_start"),
        "period_end": report.get("period_end"),
        "observations": report.get("observations"),
        "rejected": report.get("rejected"),
        "reasons": report.get("rejection_reasons"),
        "flow_filter_status": report.get("flow_filter_status"),
        "final_oos": {
            "trades": final.get("trade_count", final_summary.get("trades")),
            "expectancy_r": final_summary.get("expectancy_r"),
            "win_rate": final_summary.get("win_rate"),
            "profit_factor": final_summary.get("profit_factor"),
            "max_dd_pct": final_summary.get("maximum_drawdown_percent"),
            "uncertainty": final.get("uncertainty"),
            "prop_firm": final.get("prop_firm"),
        },
        "cost_stress": costs,
        "walk_forward": {
            "windows": len(report.get("walk_forward", [])),
            "negative_windows": report.get("walk_forward_negative_windows"),
            "terminal_oos": report.get("terminal_walk_forward_oos"),
        },
        "purged_cpcv": report.get("purged_cpcv"),
        "parameter_perturbation": {
            "keys": list(perturb.keys()) if isinstance(perturb, dict) else [],
            "variant_count": len(variants) if isinstance(variants, list) else None,
            "raw": perturb,
        },
    }


def main() -> None:
    out = {}
    for path in sorted(ROOT.glob("*-phase1-validation.json")):
        out[path.stem.split("-")[0]] = summary(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
