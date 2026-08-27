#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
MEASURED=ROOT/'strategy_discovery_v1/second_collection_v1/data/freqtrade_batch_001_measured_backtest_v1.json'
STATS=ROOT/'strategy_discovery_v1/second_collection_v1/data/freqtrade_batch_001_statistics_v1.json'
SM=ROOT/'strategy_discovery_v1/second_collection_v1/data/freqtrade_batch_001_statistical_manifest_v1.json'
LEDGER=ROOT/'strategy_discovery_v1/data/global_trial_ledger.json'
MANIFEST=ROOT/'strategy_discovery_v1/second_collection_v1/data/execution_assumption_manifest_v1_2_frozen.json'
PROFILE=ROOT/'strategy_discovery_v1/second_collection_v1/data/freqtrade_batch_001_research_harness_v1.json'

def fh(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ch(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

m=json.loads(MEASURED.read_text()); s=json.loads(STATS.read_text()); sm=json.loads(SM.read_text()); l=json.loads(LEDGER.read_text()); man=json.loads(MANIFEST.read_text()); profile=json.loads(PROFILE.read_text())
assert m['measured_count']==5 and m['exclusion_count']==6 and m['candidate_universe_authorized']==11
assert m['manifest_sha256']==man['manifest_sha256'] and m['harness_profile_sha256']==profile['harness_profile_sha256']
assert all(r['measured'] and r['trial_created'] and r['analysis_only'] is False for r in m['results'])
assert all(e['trial_created'] is False for e in m['exclusions'])
assert len({r['trial_id'] for r in m['results']})==5
assert s['measured_artifact_sha256']==fh(MEASURED) and s['statistical_manifest_sha256']==sm['statistical_manifest_sha256']
assert s['trial_ledger_n_at_selection']==898 and len(s['cpcv']['split_results'])==15 and s['cpcv']['path_count']==5
assert s['dsr']['gate'] is False and s['pbo']['gate'] is True and s['promotion_allowed'] is False
assert l['n_trials']==898 and l['last_sequence']==898 and l['global_ledger_hash']=='2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e'
assert l['latest_statistics']['statistics_artifact_sha256']==fh(STATS)
assert l['latest_statistics']['dsr']==s['dsr'] and l['latest_statistics']['pbo']==s['pbo']
assert l['deployment'] is False and l['paper_trading'] is False and l['trading'] is False
print(json.dumps({'status':'ok','measured_count':m['measured_count'],'exclusion_count':m['exclusion_count'],'ledger_n':l['n_trials'],'ledger_hash':l['global_ledger_hash'],'dsr':s['dsr'],'pbo':s['pbo'],'promotion_allowed':s['promotion_allowed']},sort_keys=True))
