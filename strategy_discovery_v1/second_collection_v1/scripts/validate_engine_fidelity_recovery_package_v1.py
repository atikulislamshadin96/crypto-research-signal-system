#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, itertools, subprocess
from collections import Counter
from pathlib import Path
import jsonschema

REPO=Path(__file__).resolve().parents[3]
PACKAGE=REPO/'strategy_discovery_v1/second_collection_v1/data/engine_fidelity_recovery_package_v1.json'
SCHEMA=REPO/'strategy_discovery_v1/second_collection_v1/schemas/engine_fidelity_recovery_package_v1.schema.json'

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(d:dict)->str: return hashlib.sha256(json.dumps({k:v for k,v in d.items() if k!='package_canonical_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def main():
    schema=json.loads(SCHEMA.read_text(encoding='utf-8')); package=json.loads(PACKAGE.read_text(encoding='utf-8'))
    jsonschema.Draft7Validator(schema).validate(package)
    assert package['package_canonical_sha256']==canonical(package)
    assert package['integrity_references']['schema_sha256']==sha(SCHEMA)
    assert package['status']=='frozen_pre_measurement'
    assert all(v is False for v in package['authorization_boundary'].values())
    assert all(v is False for v in package['current_state'].values())
    budget=package['candidate_budget']; assert budget['additional_valid_candidate_families_max']==18 and budget['round_count']==3 and budget['candidates_per_round_max']==6 and budget['hard_cancel_if_additional_valid_failures']==18 and budget['attempted_leads_max']==30 and budget['cancel_if_valid_measurable_candidates_below']==18
    assert budget['total_measured_family_budget']==budget['existing_v2_4_failed_candidate_families']+budget['additional_valid_candidate_families_max']==24
    rounds=package['rounds']; assert [r['round_id'] for r in rounds]==['recovery_A','recovery_B','recovery_C'] and all(r['max_new_candidate_families']==6 for r in rounds)
    c=package['cpcv']; paths=c['path_pairings']; assert c['n_groups']==12 and c['test_groups_per_split']==2 and c['split_count']==66 and c['path_count']==11 and c['minimum_training_observations']==60 and len(paths)==11
    allpairs=[]
    for p in paths:
        pairs=[tuple(sorted(x)) for x in p['test_pairs']]
        assert len(pairs)==6 and len(set(pairs))==6
        flat=[g for pair in pairs for g in pair]; assert len(flat)==12 and len(set(flat))==12 and set(flat)==set(range(12))
        allpairs.extend(pairs)
    assert len(allpairs)==66 and len(set(allpairs))==66 and set(allpairs)=={(i,j) for i in range(12) for j in range(i+1,12)}
    cost=package['execution_cost_gate']; assert cost['native_fee_control']=='--fee' and cost['base_fee_per_side']==0.00055 and cost['fee_sensitivity_ladder_per_side']==[0.00055,0.00075,0.001] and cost['slippage_value']==0.0 and cost['global_adverse_slippage_control_available'] is False and not cost['price_modification_allowed'] and not cost['return_postprocessing_allowed'] and not cost['engine_patch_allowed']
    hold=package['holdout']; assert not hold['selection_uses_holdout'] and not hold['tuning_uses_holdout'] and hold['positive_after_cost_required'] is True and hold['minimum_observations']==60
    gates=package['survivor_gates']; assert len(gates)==8 and [g['gate_id'] for g in gates]==['executability','after_cost_economics','both_pair_result','activity_floor','dsr','cpcv_pbo','untouched_holdout','concentration'] and all(g['failure_action']=='candidate_family_fails; no post-result relaxation' for g in gates)
    protected=package['integrity_references']['protected_files']
    assert len(protected)==8 and all(len(x['sha256'])==64 for x in protected)
    for x in protected: assert sha(REPO/x['path'])==x['sha256'], x['path']
    assert not package['current_state']['measurement_ready'] and not package['current_state']['trial_ids_created'] and not package['current_state']['ledger_changed']
    print(json.dumps({'status':'ok','package_canonical_sha256':package['package_canonical_sha256'],'package_file_sha256':sha(PACKAGE),'schema_sha256':sha(SCHEMA),'cpcv_path_count':len(paths),'cpcv_split_count':c['split_count'],'cpcv_pair_count':len(allpairs),'additional_candidate_budget':budget['additional_valid_candidate_families_max'],'hard_cancel_failures':budget['hard_cancel_if_additional_valid_failures'],'attempted_leads_max':budget['attempted_leads_max'],'measurement_authorized':False,'trial_ids_created':False,'ledger_changed':False,'statistics_run':False,'promotion_allowed':False},indent=2))
if __name__=='__main__': main()
