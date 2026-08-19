from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("artifacts/bos-4h-daily/advanced_bos_extension")
for path in sorted(ROOT.glob("*-advanced-validation.json")):
    report = json.loads(path.read_text(encoding="utf-8"))
    oos = report["final_oos"]
    s = oos["summary"]
    stress = {k: v["summary"]["expectancy_r"] for k, v in report["cost_stress"].items()}
    cpcv = report["purged_cpcv"]
    perturb = report["parameter_perturbation"]
    positive_perturb = sum(1 for item in perturb if item.get("rejected") is False)
    print(json.dumps({
        "asset": path.name.split("-")[0],
        "observations": report["observations"],
        "period_start": report["period_start"],
        "period_end": report["period_end"],
        "oos_trades": oos["trade_count"],
        "oos_expectancy_r": s["expectancy_r"],
        "oos_win_rate": s["win_rate"],
        "oos_profit_factor": s["profit_factor"],
        "oos_bootstrap_p05": oos["uncertainty"]["p05_r"],
        "cost_stress_expectancy_r": stress,
        "negative_wf_windows": report["walk_forward_negative_windows"],
        "cpcv_p50": cpcv["expectancy_r_quantiles"]["p50"],
        "cpcv_positive_path_fraction": cpcv["positive_path_fraction"],
        "perturbation_count": len(perturb),
        "perturbation_positive_variants": positive_perturb,
        "prop_firm_return_percent": oos["prop_firm"]["return_percent"],
        "prop_firm_breach": oos["prop_firm"]["breach"],
        "rejected": report["rejected"],
        "reasons": report["rejection_reasons"],
    }, sort_keys=True))
