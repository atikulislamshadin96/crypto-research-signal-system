#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
MEASURED=ROOT/'strategy_discovery_v1/second_collection_v1/data/freqtrade_batch_001_measured_backtest_v1.json'
LEDGER=ROOT/'strategy_discovery_v1/data/global_trial_ledger.json'
PROTOCOL=ROOT/'strategy_discovery_v1/protocols/dsr_pbo_cpcv_v1.json'
OUT=ROOT/'strategy_discovery_v1/second_collection_v1/data/freqtrade_batch_001_statistical_manifest_v1.json'

def file_hash(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def h(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

m=json.loads(MEASURED.read_text()); ledger=json.loads(LEDGER.read_text())
if ledger['n_trials']!=898 or ledger['last_sequence']!=898: raise SystemExit('ledger must be N=898 before statistics')
if m['measured_count']!=5: raise SystemExit('expected five measured trials')
obj={
 'statistical_manifest_version':'freqtrade_batch_001_statistical_manifest_v1',
 'status':'frozen_pre_statistics',
 'created_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),
 'batch_id':m['batch_id'],
 'measured_artifact_sha256':file_hash(MEASURED),
 'trial_ledger_n_at_selection':ledger['n_trials'],
 'trial_ledger_hash_at_selection':ledger['global_ledger_hash'],
 'protocol_id':m['protocol_id'],
 'protocol_hash':file_hash(PROTOCOL),
 'return_series':{'input_frequency':'source_timeframe_bar','comparison_frequency':'daily_utc_end_of_day','aggregation':'compound_bar_returns_within_utc_day','missing_data':'fail_closed_no_forward_fill_across_missing_day'},
 'dsr':{'sr_benchmark':0.0,'sr_std_null':1.0,'minimum_observations':3,'annualization':'daily_returns_sqrt_365','selection_scope':'all five measured trials plus prior ledger N'},
 'cpcv':{'n_groups':6,'test_groups_per_split':2,'split_count':15,'path_count':5,'group_assignment':'six contiguous chronological daily blocks','purge_days':30,'embargo_days':30,'selection_objective':'maximum_annualized_sharpe_on_training_returns','tie_break':'lexicographically smallest trial_id after equal metric','fit_isolation':'no_fitted_transform_or_parameter_selection_outside_source_declared_fixed_parameters'},
 'pbo':{'test_metric':'annualized_sharpe_on_pooled_daily_test_returns','path_selected_candidate':'most_frequent_per_split_training_winner; ties resolved by highest mean training Sharpe then lexicographically smallest trial_id','omega_ties':'midrank','lambda':'log(omega/(1-omega))','gate_maximum':0.10},
 'paths':[
  {'path_id':0,'test_pairs':[[0,1],[2,3],[4,5]]},
  {'path_id':1,'test_pairs':[[0,2],[1,4],[3,5]]},
  {'path_id':2,'test_pairs':[[0,3],[1,5],[2,4]]},
  {'path_id':3,'test_pairs':[[0,4],[1,3],[2,5]]},
  {'path_id':4,'test_pairs':[[0,5],[1,2],[3,4]]},
 ],
 'authorization':{'backtest_run_authorized':True,'statistics_run_authorized':True,'promotion_authorized':False,'live_or_paper_trading_authorized':False}
}
obj['statistical_manifest_sha256']=h(obj)
OUT.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print(json.dumps({'statistical_manifest_sha256':obj['statistical_manifest_sha256'],'ledger_n':ledger['n_trials'],'measured_count':m['measured_count']},sort_keys=True))
