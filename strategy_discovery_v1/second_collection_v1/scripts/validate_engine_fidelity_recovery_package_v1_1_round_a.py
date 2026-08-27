#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, subprocess
from pathlib import Path
import jsonschema
REPO=Path(__file__).resolve().parents[3]
PACKAGE=REPO/'strategy_discovery_v1/second_collection_v1/data/engine_fidelity_recovery_package_v1_1_round_a.json'
REG=REPO/'strategy_discovery_v1/second_collection_v1/data/quantconnect_lean_round_a_candidate_registry_v1.json'
SCHEMA=REPO/'strategy_discovery_v1/second_collection_v1/schemas/engine_fidelity_recovery_package_v1_1_round_a.schema.json'
PARENT=REPO/'strategy_discovery_v1/second_collection_v1/data/engine_fidelity_recovery_package_v1.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(d): return hashlib.sha256(json.dumps({k:v for k,v in d.items() if k!='package_canonical_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-root',required=True); args=ap.parse_args(); src=Path(args.source_root).resolve()
    schema=json.loads(SCHEMA.read_text()); package=json.loads(PACKAGE.read_text()); reg=json.loads(REG.read_text()); parent=json.loads(PARENT.read_text())
    jsonschema.Draft7Validator(schema).validate(package)
    assert package['package_canonical_sha256']==canonical(package)
    assert package['candidate_registry']['file_sha256']==sha(REG)
    assert package['candidate_registry']['source_commit']=='07fb0182bfe229edd9445cf675ac6509d0069539'
    assert subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()==package['candidate_registry']['source_commit']
    remote=subprocess.check_output(['git','-C',str(src),'remote','get-url','origin'],text=True).strip().lower(); assert 'quantconnect/lean' in remote
    assert package['parent_package']['canonical_sha256']==parent['package_canonical_sha256'] and package['parent_package']['file_sha256']==sha(PARENT)
    assert package['inherited_policy']['candidate_budget']==parent['candidate_budget']
    for key in ('holdout','execution_cost_gate','survivor_gates','trial_accounting'):
        assert package['inherited_policy'][key]==parent[key], key
    parent_cpcv={k:parent['cpcv'][k] for k in ['protocol_id','n_groups','test_groups_per_split','split_count','path_count','group_assignment','purge_days','embargo_days','minimum_training_observations','zero_training_split_policy','fit_isolation']}
    assert package['inherited_policy']['cpcv']==parent_cpcv
    candidate_paths=[x['repository_path'] for x in package['round_a_candidates']]
    assert [x['rank'] for x in package['round_a_candidates']]==list(range(1,7))
    expected=['Algorithm.Framework/Alphas/BasePairsTradingAlphaModel.py','Algorithm.Framework/Alphas/ConstantAlphaModel.py','Algorithm.Framework/Alphas/EmaCrossAlphaModel.py','Algorithm.Framework/Alphas/HistoricalReturnsAlphaModel.py','Algorithm.Framework/Alphas/MacdAlphaModel.py','Algorithm.Framework/Alphas/RsiAlphaModel.py']
    assert candidate_paths==expected
    all_py=sorted([p.relative_to(src).as_posix() for p in (src/'Algorithm.Framework/Alphas').glob('*.py')],key=lambda x:x.encode())
    assert all_py==['Algorithm.Framework/Alphas/BasePairsTradingAlphaModel.py','Algorithm.Framework/Alphas/ConstantAlphaModel.py','Algorithm.Framework/Alphas/EmaCrossAlphaModel.py','Algorithm.Framework/Alphas/HistoricalReturnsAlphaModel.py','Algorithm.Framework/Alphas/MacdAlphaModel.py','Algorithm.Framework/Alphas/PearsonCorrelationPairsTradingAlphaModel.py','Algorithm.Framework/Alphas/RsiAlphaModel.py']
    excluded=package['excluded_candidates'][0]; assert excluded['repository_path']==all_py[5]
    for row in package['round_a_candidates']+[excluded]:
        fp=src/row['repository_path']; assert fp.is_file() and sha(fp)==row['file_sha256'],row['repository_path']
        tree=ast.parse(fp.read_text()); classes=[x.name for x in tree.body if isinstance(x,ast.ClassDef)]; assert row['class_name'] in classes,row['repository_path']
    assert package['candidate_registry']['eligible_count']==6 and package['candidate_registry']['excluded_count']==1
    assert package['authorization_boundary']['candidate_registry_creation_authorized'] is True
    assert all(not package['authorization_boundary'][k] for k in package['authorization_boundary'] if k!='candidate_registry_creation_authorized')
    assert all(v is False for v in package['current_state'].values())
    print(json.dumps({'status':'ok','package_canonical_sha256':package['package_canonical_sha256'],'package_file_sha256':sha(PACKAGE),'schema_sha256':sha(SCHEMA),'registry_sha256':sha(REG),'source_commit':package['candidate_registry']['source_commit'],'candidate_count':len(package['round_a_candidates']),'candidate_paths':candidate_paths,'excluded_path':excluded['repository_path'],'measurement_authorized':False,'trial_ids_created':False,'ledger_changed':False,'statistics_run':False,'promotion_allowed':False},indent=2))
if __name__=='__main__': main()
