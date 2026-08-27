from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

EXPECTED_ENGINE = 'eb1a668ceb0f29b7d578156bfc24c45278c0c0f8'
EXPECTED_TECHNICAL = '720ff67483e346271165d49cf37265f78739c74c'
EXPECTED_SOURCE = 'eff78d3ce3456b52c68a4e9a33cc055a56b801ff'
EXPECTED_SUPERTREND = '8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838'
EXPECTED_V1_2_MANIFEST = '7820c7c832c1a0a4eabf0fc02a4d38b48699f851feadfbfd57a477ac7691f51e'
EXPECTED_V2 = '2206c0ff15dda0483496305eba0814df7975aeabd23dedcb4ac8a58af81a5757'
EXPECTED_V2_1 = 'd2b8d10439c17ddd98c5c6b877ae5b6a85be0b4a1de24f6840803e86d8255216'
EXPECTED_V2_2 = '93939f072200a20bc26a3f431a4f388e221c83d54f2356ce67f80a7b11d60b7b'
EXPECTED_V2_3 = '5983aef407027a4cfe61de38a1dc3c890c94bd05e63a2f407d8d5b93c275a9f0'
EXPECTED_LEDGER = '9642d0daa824d2ab49d7f4018d72f9b5e2e29cdea13bdcb73cd8af69653722eb'
EXPECTED_LEDGER_CANONICAL = '2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e'
EXPECTED_ACQ_CANONICAL = '81893e47e4426cb1be27685dd4bdd8d5f4825eaaa490e5c69fc4e1ffffbe695f'
EXPECTED_FUNDING_MANIFEST_CANONICAL = 'cd4679e1e8278e224add40836f0a25e4d9f6599c6a6360580b3306b23aba6898'
EXPECTED_NATIVE_EXECUTION_MANIFEST_CANONICAL = '1972e26f85feefe152abdef4b8b2812db9b12c4732d4f7366855b700f8a81d42'
EXPECTED_RUNTIME_LOCK = '7d3e20fadf1dcffd00dc5396a1b1dca8ea426abe28f1e5c1649dbaa80b46b15d'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_hash(data: dict, *excluded: str) -> str:
    copy = dict(data)
    for field in excluded:
        copy.pop(field, None)
    return hashlib.sha256((json.dumps(copy, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()


def package_filesystem_hash(package: dict) -> str:
    copy = dict(package)
    copy.pop('package_filesystem_sha256', None)
    return hashlib.sha256((json.dumps(copy, indent=2) + '\n').encode()).hexdigest()


def manifest_canonical_hash(manifest: dict) -> str:
    return canonical_json_hash(manifest, 'manifest_sha256')


def assert_file(repo: Path, rel: str, expected: str) -> None:
    actual = sha256(repo / rel)
    assert actual == expected, f'{rel}: {actual} != {expected}'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--package', required=True)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--engine-root', type=Path, required=True)
    parser.add_argument('--technical-root', type=Path, required=True)
    parser.add_argument('--strategies-root', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    package_path = repo / args.package
    package = json.loads(package_path.read_text(encoding='utf-8'))
    assert package['package_id'] == 'freqtrade_batch_001_engine_fidelity_measurement_freeze_v2_4'
    assert package['version'] == '2.4.0'
    assert package['status'] == 'validated_request_measurement_approval'
    assert package['authorization'] == {'measurement_authorized': False, 'trial_creation_authorized': False, 'backtest_authorized': False, 'ledger_update_authorized': False, 'new_market_data_authorized': False, 'promotion_allowed': False, 'trading_allowed': False}
    assert package['measurement_boundary']['measurement_requires_separate_authorization'] is True
    assert package['measurement_boundary']['next_status_if_validated'] == 'V2_4_VALIDATED_REQUEST_MEASUREMENT_APPROVAL'
    assert package['package_canonical_sha256'] == canonical_json_hash(package, 'package_canonical_sha256', 'package_filesystem_sha256')
    assert package['package_filesystem_sha256'] == package_filesystem_hash(package)

    state = package['immutable_starting_state']
    assert state == {'ledger_n': 898, 'last_sequence': 898, 'ledger_canonical_sha256': EXPECTED_LEDGER_CANONICAL, 'v2_package_sha256': EXPECTED_V2, 'v2_1_package_sha256': EXPECTED_V2_1, 'v2_2_package_sha256': EXPECTED_V2_2, 'v2_3_package_sha256': EXPECTED_V2_3, 'acquisition_manifest_canonical_sha256': EXPECTED_ACQ_CANONICAL, 'starting_commit': 'afa73f470b3945d018d7fa147fef610636c6827d'}
    assert package['execution_policy'] == {'id': 'native_fee_only_v1', 'commission_model': 'VIP0_taker_base_rate_proxy', 'commission_rate_per_side': 0.00055, 'slippage_model': 'native_engine_no_global_adverse_slippage', 'slippage_value': 0.0, 'native_fee_control': 'freqtrade_cli_fee_override_only', 'global_adverse_slippage_control_available': False, 'price_postprocessing_allowed': False, 'return_postprocessing_allowed': False, 'engine_patch_allowed': False}
    assert package['pinned_inputs']['runtime_lock_sha256'] == EXPECTED_RUNTIME_LOCK
    runtime_lock_path = repo / package['integrity_references']['runtime_lock_path']
    assert sha256(runtime_lock_path) == EXPECTED_RUNTIME_LOCK
    assert package['integrity_references']['runtime_lock_sha256'] == EXPECTED_RUNTIME_LOCK
    assert package['funding_policy']['id'] == 'actual_historical_bybit_funding_rate_v1'
    assert package['funding_policy']['model'] == 'actual_historical_bybit_funding_rate'
    assert package['funding_policy']['zero_funding_proxy_allowed'] is False
    assert package['funding_policy']['actual_rate_used'] is True
    assert package['funding_policy']['source_manifest_canonical_sha256'] == EXPECTED_FUNDING_MANIFEST_CANONICAL

    ledger = json.loads((repo / 'strategy_discovery_v1/data/global_trial_ledger.json').read_text(encoding='utf-8'))
    assert ledger['last_sequence'] == 898
    assert_file(repo, 'strategy_discovery_v1/data/global_trial_ledger.json', EXPECTED_LEDGER)
    assert_file(repo, 'strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2.json', EXPECTED_V2)
    assert_file(repo, 'strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2_1.json', EXPECTED_V2_1)
    assert_file(repo, 'strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2_2.json', EXPECTED_V2_2)
    assert_file(repo, 'strategy_discovery_v1/second_collection_v1/data/engine_fidelity_measurement_freeze_package_v2_3.json', EXPECTED_V2_3)
    assert_file(repo, 'strategy_discovery_v1/second_collection_v1/data/execution_assumption_manifest_v1_2_frozen.json', EXPECTED_V1_2_MANIFEST)

    acq_path = repo / package['funding_policy']['source_manifest_path'].replace('execution_assumption_manifest_v1_3_actual_funding_frozen.json', 'bybit_linear_derivatives_history_v2/acquisition_manifest.json')
    acq = json.loads(acq_path.read_text(encoding='utf-8'))
    assert acq['canonical_sha256'] == EXPECTED_ACQ_CANONICAL
    assert package['data_scope']['acquisition_manifest_canonical_sha256'] == EXPECTED_ACQ_CANONICAL
    assert_file(repo, package['integrity_references']['acquisition_manifest_path'], package['integrity_references']['acquisition_manifest_filesystem_sha256'])

    native_execution_manifest_path = repo / package['integrity_references']['native_execution_manifest_path']
    native_execution_manifest = json.loads(native_execution_manifest_path.read_text(encoding='utf-8'))
    assert native_execution_manifest['manifest_sha256'] == EXPECTED_NATIVE_EXECUTION_MANIFEST_CANONICAL
    assert manifest_canonical_hash(native_execution_manifest) == EXPECTED_NATIVE_EXECUTION_MANIFEST_CANONICAL
    assert native_execution_manifest['field_values']['slippage']['value'] == 0.0
    assert native_execution_manifest['field_values']['slippage']['global_adverse_slippage_control_available_in_pinned_engine'] is False
    assert native_execution_manifest['field_values']['slippage']['price_postprocessing_allowed'] is False
    assert native_execution_manifest['field_values']['slippage']['return_postprocessing_allowed'] is False
    assert native_execution_manifest['field_values']['slippage']['engine_patch_allowed'] is False
    assert native_execution_manifest['field_values']['native_fee_policy']['commission_control'] == 'pinned_freqtrade_native_fee_override'
    assert_file(repo, package['integrity_references']['native_execution_manifest_path'], package['integrity_references']['native_execution_manifest_filesystem_sha256'])

    funding_manifest_path = repo / package['funding_policy']['source_manifest_path']
    funding_manifest = json.loads(funding_manifest_path.read_text(encoding='utf-8'))
    assert funding_manifest['manifest_sha256'] == EXPECTED_FUNDING_MANIFEST_CANONICAL
    assert manifest_canonical_hash(funding_manifest) == EXPECTED_FUNDING_MANIFEST_CANONICAL
    assert funding_manifest['field_values']['funding_or_borrow']['model'] == 'actual_historical_bybit_funding_rate'
    assert funding_manifest['field_values']['funding_or_borrow']['zero_funding_proxy_allowed'] is False
    assert_file(repo, package['integrity_references']['funding_execution_manifest_path'], package['integrity_references']['funding_execution_manifest_filesystem_sha256'])

    for rel, expected in package['integrity_references']['repository_files'].items():
        assert_file(repo, rel, expected)

    layout_path = repo / package['native_layout']['manifest_path']
    layout = json.loads(layout_path.read_text(encoding='utf-8'))
    assert package['integrity_references']['native_layout_manifest_sha256'] == sha256(layout_path)
    assert package['integrity_references']['native_files'] == {item['path']: item['sha256'] for item in layout['files']}
    for rel, expected in package['integrity_references']['native_files'].items():
        assert_file(repo, rel, expected)
    assert sha256(layout_path) == package['native_layout']['manifest_sha256']
    assert layout['exchange_options'] == {'mark_ohlcv_price': 'mark', 'mark_ohlcv_timeframe': '15m', 'funding_fee_timeframe': '8h'}
    assert layout['ft_has_params_override'] == {'mark_ohlcv_timeframe': '15m', 'funding_fee_timeframe': '8h'}
    assert layout['placeholder_policy']['mark_price_volume_value'] == 0
    assert layout['placeholder_policy']['observed_market_volume'] is False
    assert layout['source_policy'] == {'no_resampling': True, 'no_forward_fill': True, 'mark_ohlc_exact_source_copy': True, 'funding_native_timestamps': True}

    sys.path.insert(0, str(args.engine_root))
    from freqtrade.data.history.history_utils import load_pair_history
    from freqtrade.enums import CandleType
    checked = []
    for item in layout['files']:
        path = repo / item['path']
        assert sha256(path) == item['sha256']
        rows = json.loads(path.read_text(encoding='utf-8'))
        assert len(rows) == item['row_count']
        if item['kind'] == 'mark_price':
            assert all(row[5] == 0 for row in rows)
            loaded = load_pair_history(item['pair'], item['timeframe'], layout_path.parent, fill_up_missing=False, drop_incomplete=False, data_format='json', candle_type=CandleType.MARK)
            assert len(loaded) == item['row_count']
            assert list(loaded.columns) == ['date', 'open', 'high', 'low', 'close', 'volume']
            assert loaded['volume'].eq(0).all()
        else:
            assert all(len(row) == 2 for row in rows)
            assert any(row[1] != 0 for row in rows)
            loaded = load_pair_history(item['pair'], item['timeframe'], layout_path.parent, fill_up_missing=False, drop_incomplete=False, data_format='json', candle_type=CandleType.FUNDING_RATE)
            assert len(loaded) == item['row_count']
            assert list(loaded.columns) == ['date', 'funding_rate', 'open']
            assert loaded['open'].equals(loaded['funding_rate'])
        checked.append({'kind': item['kind'], 'symbol': item['symbol'], 'rows': len(rows), 'sha256': item['sha256']})

    exchange_source = (args.engine_root / 'freqtrade/exchange/exchange.py').read_text(encoding='utf-8')
    assert 'if exchange_conf.get("_ft_has_params")' in exchange_source
    assert 'self._ft_has = deep_merge_dicts(exchange_conf.get("_ft_has_params"), self._ft_has)' in exchange_source
    assert 'relevant_cols = ["date", "open_mark", "open_fund"]' in exchange_source
    assert '"volume"' not in exchange_source[exchange_source.index('def combine_funding_and_mark'):exchange_source.index('def calculate_funding_fees')]
    technical_source = args.technical_root / 'technical/indicators/supertrend.py'
    assert sha256(technical_source) == EXPECTED_SUPERTREND
    expected_candidates = {'CustomStoplossWithPSAR.py': '1h', 'Heracles.py': '4h', 'HourBasedStrategy.py': '1h', 'MultiMa.py': '4h', 'PatternRecognition.py': '1d', 'Supertrend.py': '1h'}
    assert {Path(item['path']).name: item['main_timeframe'] for item in package['candidate_eligibility']['candidates']} == expected_candidates
    source_evidence = package['source_evidence']
    assert source_evidence['source_commit'] == EXPECTED_SOURCE
    evidence_path = repo / source_evidence['path']
    assert sha256(evidence_path) == source_evidence['filesystem_sha256']
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    assert evidence['input_source_commit'] == EXPECTED_SOURCE
    for rel, expected_snapshot in source_evidence['snapshot_sha256'].items():
        record = next(r for r in evidence['records'] if r['document_id'] == f'{EXPECTED_SOURCE}:{rel}')
        observed = {e['snapshot_sha256'] for claim in record.get('field_claims', []) for e in claim.get('evidence', [])}
        assert observed == {expected_snapshot}, f'{rel}: source snapshot evidence mismatch'
        assert sha256(args.strategies_root / rel) == expected_snapshot, f'{rel}: pinned source file mismatch'
    assert all(item['status'] == 'eligible_after_v2_4_validation' for item in package['candidate_eligibility']['candidates'])
    for rel in package['authorized_strategy_paths']:
        assert (args.strategies_root / rel).is_file()
    print(json.dumps({'status': 'ok', 'package': package['package_id'], 'actual_funding_policy': True, 'zero_funding_proxy_allowed': False, 'native_loader_smoke': 'pass', 'files_checked': checked, 'candidate_count': 6, 'ledger_n': 898, 'trial_ids_created': 0, 'backtest_run': False}, indent=2))


if __name__ == '__main__':
    main()
