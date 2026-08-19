from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("artifacts/bos-4h-daily/phase1_bos_extension")


def s(item: dict) -> dict:
    return item.get("summary", item)


def main() -> None:
    for path in sorted(ROOT.glob("*-phase1-validation.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        final = report["final_oos"]
        fs = s(final)
        print(f"{path.name}")
        print(f" period={report['period_start']}..{report['period_end']} observations={report['observations']} rejected={report['rejected']}")
        print(f" final trades={final.get('trade_count', fs.get('trades'))} expR={fs.get('expectancy_r')} win={fs.get('win_rate')} PF={fs.get('profit_factor')} DD={fs.get('maximum_drawdown_percent')} prop_return={final.get('prop_firm',{}).get('return_percent')} p05={final.get('uncertainty',{}).get('p05_r')} p50={final.get('uncertainty',{}).get('p50_r')} p95={final.get('uncertainty',{}).get('p95_r')}")
        print(f" costs:")
        for key in ("5bps", "10bps", "15bps"):
            item = report["cost_stress"][key]
            cs = s(item)
            print(f"  {key} trades={item.get('trade_count',cs.get('trades'))} expR={cs.get('expectancy_r')} win={cs.get('win_rate')} PF={cs.get('profit_factor')} DD={cs.get('maximum_drawdown_percent')}")
        wf = report.get("walk_forward", [])
        terminal = report.get("terminal_walk_forward_oos")
        print(f" walk_forward windows={len(wf)} negative={report.get('walk_forward_negative_windows')} terminal={terminal}")
        cpcv = report.get("purged_cpcv", {})
        if isinstance(cpcv, dict):
            quantiles = cpcv.get("expectancy_r_quantiles", {})
            print(f" cpcv paths={cpcv.get('path_count')} paths_with_trades={cpcv.get('paths_with_trades')} p05={quantiles.get('p05')} p50={quantiles.get('p50')} p95={quantiles.get('p95')} positive_fraction={cpcv.get('positive_path_fraction')}")
        else:
            print(f" cpcv={type(cpcv).__name__}")
        print(f" perturbation_variants={len(report.get('parameter_perturbation', [])) if isinstance(report.get('parameter_perturbation'), list) else 'dict'}")
        print(f" reasons={report.get('rejection_reasons')}")


if __name__ == "__main__":
    main()
