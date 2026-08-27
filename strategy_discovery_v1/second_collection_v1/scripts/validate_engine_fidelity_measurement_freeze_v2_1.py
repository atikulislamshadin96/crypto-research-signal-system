#!/usr/bin/env python3
"""Read-only validator for the v2.1 measurement-freeze package.

No OHLCV is read, no strategy indicators are run, no backtest/trial/return
artifact is created, and the ledger is never modified.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
EXPECTED_LEDGER_FILE_SHA = '9642d0daa824d2ab49d7f4018d72f9b5e2e29cdea13bdcb73cd8af69653722eb'
EXPECTED_LEDGER_CANONICAL = '2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e'
EXPECTED_CANDIDATES = {
    'user_data/strategies/CustomStoplossWithPSAR.py': '1h',
    'user_data/strategies/Heracles.py': '4h',
    'user_data/strategies/HourBasedStrategy.py': '1h',
    'user_data/strategies/MultiMa.py': '4h',
    'user_data/strategies/PatternRecognition.py': '1d',
    'user_data/strategies/Supertrend.py': '1h',
}

def load(rel): return json.loads((ROOT / rel).read_text())
def sha(rel): return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
def check(actual, expected, label):
    if actual != expected: raise AssertionError(f'{label}: expected {expected!r}, got {actual!r}')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--engine-root', type=Path, required=True)
    ap.add_argument('--technical-root', type=Path, required=True)
    ap.add_argument('--package', type=Path, required=True)
    ap.add_argument('--schema', type=Path, required=True)
    args=ap.parse_args()
    p=json.loads(args.package.read_text())
    s=json.loads(args.schema.read_text())
    errors=sorted(Draft202012Validator(s).iter_errors(p), key=lambda e:list(e.path))
    if errors: raise AssertionError('schema errors: ' + '; '.join(f'{list(e.path)} {e.message}' for e in errors))
    check(p['status'], 'measurement_ready', 'package status')
    check(p['measurement_authorized'], False, 'measurement authorization')
    check(p['new_trial_ids_authorized'], False, 'trial authorization')
    if any(p['authorization'].values()): raise AssertionError('package has an unexpected true authorization flag')
    check(p['runtime']['python'], '3.12.3', 'runtime Python')
    check(sha(p['runtime']['lock_path']), p['runtime']['lock_sha256'], 'hash-locked runtime')
    lock=(ROOT/p['runtime']['lock_path']).read_text()
    for text in ('--hash=sha256:', 'freqtrade @ git+https://github.com/freqtrade/freqtrade.git@eb1a668ceb0f29b7d578156bfc24c45278c0c0f8', 'technical @ git+https://github.com/freqtrade/technical.git@720ff67483e346271165d49cf37265f78739c74c'):
        if text not in lock: raise AssertionError(f'runtime lock missing {text}')
    em=p['execution_manifest']
    check(sha(em['path']), em['file_sha256'], 'execution manifest file')
    check(load(em['path'])['manifest_sha256'], em['canonical_sha256'], 'execution manifest canonical hash')
    refs=p['integrity_references']
    for path_key, hash_key in [('protocol_path','protocol_sha256'),('dependency_pin_manifest_path','dependency_pin_manifest_sha256'),('source_evidence_path','source_evidence_sha256'),('reassessment_path','reassessment_sha256'),('exclusion_resolution_path','exclusion_resolution_sha256'),('instrument_metadata_path','instrument_metadata_sha256'),('engine_native_smoke_path','engine_native_smoke_sha256'),('freeze_validator_path','freeze_validator_sha256')]:
        check(sha(refs[path_key]), refs[hash_key], f'integrity {path_key}')
    check(sha(p['data']['main_manifest_path']), p['data']['main_manifest_sha256'], 'main manifest')
    check(sha(p['data']['detail_manifest_path']), p['data']['detail_manifest_sha256'], 'detail manifest')
    manifest=load(p['data']['main_manifest_path'])
    declared={x['local_path']:x for x in p['data']['exact_csv_files']}
    for path, item in declared.items():
        f=ROOT/path
        if not f.is_file(): raise AssertionError(f'missing CSV {path}')
        check(f.stat().st_size, item['byte_size'], f'CSV size {path}')
        check(sha(path), item['sha256'], f'CSV hash {path}')
    check(set(declared), {x['local_path'] for x in manifest['files']}, 'CSV manifest path set')
    meta=load(refs['instrument_metadata_path'])
    check(meta['fail_closed'], False, 'Bybit metadata fail-closed flag')
    required={'price_tick_size','quantity_step','minimum_order_qty','minimum_notional'}
    for row in meta['records']:
        if row['missing_required_fields'] or set(row['required_fields']) != required: raise AssertionError(f'incomplete Bybit metadata {row["symbol"]}')
        if not row['response_sha256']: raise AssertionError(f'missing response hash {row["symbol"]}')
    limits=p['execution_policy']['precision_limits_policy']
    check(limits['status'], 'frozen_external_metadata', 'precision metadata status')
    check(limits['required_before_measurement'], True, 'precision gate')
    check(limits['missing_metadata_action'], 'fail_closed', 'missing precision behavior')
    check(p['pairlist_venue']['dynamic_pairlist_allowed'], False, 'dynamic pairlist')
    check(p['data']['detail_scope']['no_resampling'], True, 'resampling policy')
    candidates={x['source_path']:x['timeframe'] for x in p['candidate_eligibility']['eligible']}
    check(candidates, EXPECTED_CANDIDATES, 'eligible candidate set')
    check(p['candidate_eligibility']['measurement_eligible_count'], 6, 'eligible count')
    check(p['candidate_eligibility']['conditional_count'], 0, 'conditional count')
    excluded={x['source_path'] for x in p['candidate_eligibility']['remain_excluded']}
    check(excluded, {'user_data/strategies/BreakEven.py','user_data/strategies/Diamond.py','user_data/strategies/PowerTower.py','user_data/strategies/Strategy004.py','user_data/strategies/GodStra.py'}, 'excluded set')
    ledger=load('strategy_discovery_v1/data/global_trial_ledger.json')
    check(len(ledger['trials']), 898, 'ledger N')
    check(ledger['last_sequence'], 898, 'ledger sequence')
    check(sha('strategy_discovery_v1/data/global_trial_ledger.json'), EXPECTED_LEDGER_FILE_SHA, 'ledger filesystem hash')
    check(p['ledger']['global_ledger_hash'], EXPECTED_LEDGER_CANONICAL, 'ledger canonical hash')
    print(json.dumps({'status':'ok','schema':'pass','hashes':'pass','runtime_lock':'hashlocked','engine_native_environment':'pip_check_passed_and_smoke_passed','bybit_metadata':'complete','measurement':'not_run','trial_ids_created':0,'ledger_n':898}, sort_keys=True))

if __name__=='__main__': main()
