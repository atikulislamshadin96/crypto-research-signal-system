#!/usr/bin/env python3
"""Compute DSR, CPCV, and PBO for the authorized measured batch."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr, ndtri

GAMMA = 0.5772156649015329


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def sharpe(series: pd.Series) -> float:
    if len(series) < 2:
        return 0.0
    std = float(series.std(ddof=1))
    return float(series.mean() / std * math.sqrt(365.0)) if std > 0 else 0.0


def daily_returns(records: list[dict]) -> pd.Series:
    frame = pd.DataFrame(records)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["date"] = frame["timestamp"].dt.floor("D")
    return frame.groupby("date")["return"].apply(lambda x: float(np.prod(1.0 + x.to_numpy())) - 1.0).sort_index()


def dsr_value(sr: float, n: int, t: int, skew: float, kurtosis: float, sr_benchmark: float, sr_std_null: float) -> float:
    if t < 3 or not all(math.isfinite(x) for x in (sr, skew, kurtosis, sr_benchmark, sr_std_null)) or sr_std_null < 0:
        raise ValueError("invalid DSR input")
    if n > 1:
        c_n = (1.0 - GAMMA) * ndtri(1.0 - 1.0 / n) + GAMMA * ndtri(1.0 - 1.0 / (n * math.e))
    else:
        c_n = 0.0
    selection_benchmark = sr_benchmark + sr_std_null * c_n
    denom_sq = 1.0 - skew * sr + ((kurtosis - 1.0) / 4.0) * sr * sr
    if denom_sq <= 0 or not math.isfinite(denom_sq):
        raise ValueError("invalid DSR denominator")
    z = (sr - selection_benchmark) * math.sqrt(t - 1.0) / math.sqrt(denom_sq)
    return float(ndtr(z))


def midrank_percentile(values: list[float], value: float) -> float:
    n = len(values)
    less = sum(v < value for v in values)
    equal = sum(v == value for v in values)
    return (less + 0.5 * equal) / n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--measured", required=True)
    parser.add_argument("--stats-manifest", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    measured_path = Path(args.measured)
    stats_path = Path(args.stats_manifest)
    ledger_path = Path(args.ledger)
    measured = json.loads(measured_path.read_text(encoding="utf-8"))
    stats_manifest = json.loads(stats_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if stats_manifest["status"] != "frozen_pre_statistics" or ledger["n_trials"] != 898:
        raise SystemExit("statistics preconditions are not satisfied")
    if measured["measured_count"] != 5:
        raise SystemExit("expected five measured candidates")
    series = {r["trial_id"]: daily_returns(r["return_series"]) for r in measured["results"]}
    common_index = sorted(set.intersection(*(set(s.index) for s in series.values())))
    if len(common_index) < 365:
        raise SystemExit(f"common daily return index too short: {len(common_index)}")
    index = pd.DatetimeIndex(common_index)
    series = {k: v.reindex(index).fillna(0.0) for k, v in series.items()}
    candidate_ids = sorted(series)
    daily_metrics = {}
    for trial_id in candidate_ids:
        s = series[trial_id]
        sr = sharpe(s)
        daily_metrics[trial_id] = {"observations": len(s), "annualized_sharpe": sr, "sample_skewness": float(s.skew()), "sample_pearson_kurtosis": float(s.kurtosis() + 3.0), "total_return": float((1.0 + s).prod() - 1.0), "dsr": dsr_value(sr, ledger["n_trials"], len(s), float(s.skew()), float(s.kurtosis() + 3.0), stats_manifest["dsr"]["sr_benchmark"], stats_manifest["dsr"]["sr_std_null"])}
    selected_trial_id = max(candidate_ids, key=lambda x: (daily_metrics[x]["annualized_sharpe"], x))
    groups = [list(x) for x in np.array_split(index, stats_manifest["cpcv"]["n_groups"])]
    group_id = {d: i for i, group in enumerate(groups) for d in group}
    pair_to_path = {tuple(sorted(pair)): p["path_id"] for p in stats_manifest["paths"] for pair in p["test_pairs"]}
    split_results = []
    for test_groups in itertools.combinations(range(6), 2):
        test_groups = tuple(test_groups)
        test_dates = index[[group_id[d] in test_groups for d in index]]
        test_start, test_end = min(test_dates), max(test_dates)
        purge = pd.Timedelta(days=stats_manifest["cpcv"]["purge_days"])
        embargo = pd.Timedelta(days=stats_manifest["cpcv"]["embargo_days"])
        boundary = max(purge, embargo)
        train_dates = index[[d not in set(test_dates) and not (test_start - boundary <= d <= test_end + boundary) for d in index]]
        train_scores = {tid: sharpe(series[tid].reindex(train_dates).fillna(0.0)) for tid in candidate_ids}
        winner = max(candidate_ids, key=lambda x: (train_scores[x], x))
        test_scores = {tid: sharpe(series[tid].reindex(test_dates).fillna(0.0)) for tid in candidate_ids}
        omega = midrank_percentile(list(test_scores.values()), test_scores[winner])
        if not 0.0 < omega < 1.0:
            raise SystemExit("PBO omega is not strictly between zero and one")
        split_results.append({"test_groups": list(test_groups), "path_id": pair_to_path[test_groups], "train_observations": len(train_dates), "test_observations": len(test_dates), "purge_embargo_days": int(boundary.days), "training_scores": train_scores, "selected_trial_id": winner, "test_scores": test_scores, "omega_midrank": omega, "lambda": math.log(omega / (1.0 - omega))})
    path_results = []
    for path_id in range(5):
        splits = [s for s in split_results if s["path_id"] == path_id]
        counts = {tid: sum(s["selected_trial_id"] == tid for s in splits) for tid in candidate_ids}
        path_winner = max(candidate_ids, key=lambda x: (counts[x], np.mean([s["training_scores"][x] for s in splits]), x))
        pooled_test_dates = pd.DatetimeIndex(sorted(set().union(*(set(pd.to_datetime(index[[group_id[d] in tuple(s["test_groups"]) for d in index]], utc=True)) for s in splits))))
        pooled_test_scores = {tid: sharpe(series[tid].reindex(pooled_test_dates).fillna(0.0)) for tid in candidate_ids}
        pooled_omega = midrank_percentile(list(pooled_test_scores.values()), pooled_test_scores[path_winner])
        if not 0.0 < pooled_omega < 1.0:
            raise SystemExit("pooled PBO omega is not strictly between zero and one")
        pooled_lambda = math.log(pooled_omega / (1.0 - pooled_omega))
        path_results.append({"path_id": path_id, "split_count": len(splits), "selected_trial_id": path_winner, "selection_frequency": counts[path_winner], "split_omegas": [s["omega_midrank"] for s in splits], "split_lambdas": [s["lambda"] for s in splits], "pooled_test_observations": len(pooled_test_dates), "pooled_test_scores": pooled_test_scores, "pooled_omega_midrank": pooled_omega, "pooled_lambda": pooled_lambda, "path_below_median": bool(pooled_lambda < 0.0)})
    pbo = sum(p["path_below_median"] for p in path_results) / len(path_results)
    out = {"statistics_version": "freqtrade_batch_001_statistics_v1", "status": "computed_research_only", "measured_artifact_sha256": hashlib.sha256(measured_path.read_bytes()).hexdigest(), "statistical_manifest_sha256": stats_manifest["statistical_manifest_sha256"], "trial_ledger_n_at_selection": ledger["n_trials"], "trial_ledger_hash_at_selection": ledger["global_ledger_hash"], "candidate_count_measured": len(candidate_ids), "common_daily_observations": len(index), "selected_trial_id": selected_trial_id, "candidate_daily_metrics": daily_metrics, "cpcv": {"split_results": split_results, "path_results": path_results, "path_count": len(path_results)}, "pbo": {"value": pbo, "gate": pbo <= stats_manifest["pbo"]["gate_maximum"], "maximum": stats_manifest["pbo"]["gate_maximum"]}, "dsr": {"selected_trial_id": selected_trial_id, "value": daily_metrics[selected_trial_id]["dsr"], "gate": daily_metrics[selected_trial_id]["dsr"] >= 0.95, "minimum": 0.95}, "promotion_allowed": False, "live_or_paper_trading_allowed": False, "research_only": True}
    Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"selected_trial_id": selected_trial_id, "dsr": out["dsr"], "pbo": out["pbo"], "path_count": len(path_results), "ledger_n": ledger["n_trials"]}, sort_keys=True))


if __name__ == "__main__":
    main()
