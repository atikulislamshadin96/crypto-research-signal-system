#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
LEDGER=ROOT/'strategy_discovery_v1/data/global_trial_ledger.json'
STATS=ROOT/'strategy_discovery_v1/second_collection_v1/data/freqtrade_batch_001_statistics_v1.json'

def h(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def fh(p): return hashlib.sha256(p.read_bytes()).hexdigest()

ledger=json.loads(LEDGER.read_text()); stats=json.loads(STATS.read_text())
if ledger['n_trials']!=898 or ledger['last_sequence']!=898: raise SystemExit('ledger must be at N=898')
if stats['trial_ledger_n_at_selection']!=898: raise SystemExit('statistics selection N mismatch')
if ledger.get('latest_statistics',{}): raise SystemExit('statistics already recorded')
ledger['latest_statistics']={
 'batch_id':'freqtrade-strategies-001-measured-v1',
 'statistics_artifact_sha256':fh(STATS),
 'statistical_manifest_sha256':stats['statistical_manifest_sha256'],
 'trial_ledger_n_at_selection':stats['trial_ledger_n_at_selection'],
 'trial_ledger_hash_at_selection':stats['trial_ledger_hash_at_selection'],
 'candidate_count_measured':stats['candidate_count_measured'],
 'cpcv_split_count':len(stats['cpcv']['split_results']),
 'cpcv_path_count':stats['cpcv']['path_count'],
 'dsr':stats['dsr'],
 'pbo':stats['pbo'],
 'selected_trial_id':stats['selected_trial_id'],
 'selection_status':'research_gates_evaluated_no_promotion',
 'promotion_allowed':False,
 'live_or_paper_trading_allowed':False,
}
ledger['status']='statistical_gates_evaluated_no_promotion'
ledger['global_ledger_hash']=h({k:v for k,v in ledger.items() if k!='global_ledger_hash'})
LEDGER.write_text(json.dumps(ledger,indent=2,sort_keys=True)+'\n')
print(json.dumps({'n_trials':ledger['n_trials'],'global_ledger_hash':ledger['global_ledger_hash'],'dsr':stats['dsr'],'pbo':stats['pbo'],'selected_trial_id':stats['selected_trial_id'],'promotion_allowed':False},sort_keys=True))
