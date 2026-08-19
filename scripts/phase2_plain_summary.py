from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("artifacts/bos-phase2-4h")


def get_summary(item: dict) -> dict:
    return item.get("summary", item)


def main() -> None:
    for path in sorted(ROOT.glob("*-phase2-validation.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        final = report["final_oos"]
        fs = get_summary(final)
        print(path.name)
        print(f" period={report['period_start']}..{report['period_end']} observations={report['observations']} rejected={report['rejected']}")
        print(f" final trades={final.get('trade_count', fs.get('trades'))} expR={fs.get('expectancy_r')} win={fs.get('win_rate')} PF={fs.get('profit_factor')} DD={fs.get('maximum_drawdown_percent')} prop_return={final.get('prop_firm',{}).get('return_percent')} p05={final.get('uncertainty',{}).get('p05_r')} p50={final.get('uncertainty',{}).get('p50_r')} p95={final.get('uncertainty',{}).get('p95_r')}")
        for key in ("5bps", "10bps", "15bps"):
            item = report["cost_stress"][key]
            cs = get_summary(item)
            print(f" {key} trades={item.get('trade_count',cs.get('trades'))} expR={cs.get('expectancy_r')} win={cs.get('win_rate')} PF={cs.get('profit_factor')} DD={cs.get('maximum_drawdown_percent')}")
        print(f" walk_forward windows={len(report.get('walk_forward', []))} negative={report.get('walk_forward_negative_windows')}")
        cpcv = report.get("purged_cpcv", {})
        q = cpcv.get("expectancy_r_quantiles", {}) if isinstance(cpcv, dict) else {}
        print(f" cpcv paths={cpcv.get('path_count')} paths_with_trades={cpcv.get('paths_with_trades')} p05={q.get('p05')} p50={q.get('p50')} p95={q.get('p95')} positive_fraction={cpcv.get('positive_path_fraction')}")
        print(f" perturbation_variants={len(report.get('parameter_perturbation', [])) if isinstance(report.get('parameter_perturbation'), list) else 'dict'}")
        print(f" reasons={report.get('rejection_reasons')}")


if __name__ == "__main__":
    main()
