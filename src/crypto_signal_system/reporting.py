from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crypto_signal_system.models import RunResult, Signal


def _fmt(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def render_signal(signal: Signal) -> str:
    sources = ", ".join(f"{item.get('source')} @ {item.get('observed_at')}" for item in signal.sources) or "none"
    failures = "; ".join(signal.failure_reasons) or "none"
    why_fail = "; ".join(signal.why_may_fail) or "not recorded"
    return "\n".join([
        f"### {signal.symbol} — {signal.status}",
        f"- Direction: {_fmt(signal.direction)}",
        f"- Strategy: {_fmt(signal.strategy)}",
        f"- Entry zone: {_fmt(signal.entry_zone)}",
        f"- Stop Loss: {_fmt(signal.stop_loss)}",
        f"- Take Profit: {_fmt(signal.take_profit)}",
        f"- Expected reward-to-risk: {_fmt(signal.rr)}",
        f"- Evidence score: {_fmt(signal.evidence_score)}",
        f"- Calibration status: {signal.calibration_status}",
        f"- Confidence label: {_fmt(signal.confidence_label)}",
        f"- Invalidation: {_fmt(signal.invalidation)}",
        f"- Expiry: {_fmt(signal.expiry)}",
        f"- Risk controls: {_fmt(signal.risk_controls)}",
        f"- Cost estimate: {_fmt(signal.cost_estimate)}",
        f"- Position sizing: {_fmt(signal.position_size)}",
        f"- Sources and timestamps: {sources}",
        f"- Failure reasons: {failures}",
        f"- Why this may fail: {why_fail}",
    ])


def render_markdown(result: RunResult) -> str:
    confirmed = sum(1 for s in result.signals if s.status == "CONFIRMED")
    rejected = len(result.rejected_candidates)
    lines = [
        f"# Crypto Signal Analysis Run `{result.run_id}`",
        "",
        "> **Analysis-only output.** This report is not a trade instruction, does not contain a calibrated probability of profit, and cannot guarantee performance or prop-firm outcomes. Live order execution is disabled.",
        "",
        f"- Generated at: {result.generated_at.isoformat()}",
        f"- Data as of: {_fmt(result.data_as_of.isoformat() if result.data_as_of else None)}",
        f"- System version: {result.system_version}",
        f"- Market regime: {result.market_regime}",
        f"- Signals evaluated: {len(result.signals)}; confirmed: {confirmed}; rejected candidates: {rejected}",
        "",
        "## Risk state",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    for key, value in result.risk_state.to_dict().items():
        lines.append(f"| {key} | {_fmt(value)} |")
    lines.extend(["", "## Signals", ""])
    if result.signals:
        lines.extend(render_signal(signal) for signal in result.signals)
    else:
        lines.append("NO TRADE — no candidate passed the configured evidence, data-quality, cost, reward-to-risk, and risk guardrails.")
    lines.extend(["", "## Rejected candidates", ""])
    if result.rejected_candidates:
        lines.append("| Symbol | Strategy | Direction | Score | Reasons |")
        lines.append("|---|---|---|---:|---|")
        for item in result.rejected_candidates:
            lines.append(f"| {item.get('symbol')} | {item.get('strategy')} | {item.get('direction')} | {_fmt(item.get('evidence_score'))} | {item.get('reasons')} |")
    else:
        lines.append("None.")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in result.warnings) or lines.append("None.")
    lines.extend(["", "## Audit notes", "", "Every numerical value in this report is either sourced from the provider metadata recorded in the run or derived by versioned deterministic code. Missing values remain `null`; they are never silently replaced with zero."])
    return "\n".join(lines) + "\n"


def write_artifacts(result: RunResult, output_dir: str | Path) -> tuple[Path, Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stem = result.run_id
    markdown_path = directory / f"{stem}.md"
    json_path = directory / f"{stem}.json"
    log_path = directory / f"{stem}.log"
    markdown_path.write_text(render_markdown(result), encoding="utf-8")
    json_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    log_lines = [
        f"run_id={result.run_id}",
        f"generated_at={result.generated_at.isoformat()}",
        f"data_as_of={result.data_as_of.isoformat() if result.data_as_of else 'null'}",
        f"signals={len(result.signals)}",
        f"rejected_candidates={len(result.rejected_candidates)}",
    ]
    log_lines.extend(f"warning={warning}" for warning in result.warnings)
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return markdown_path, json_path, log_path
