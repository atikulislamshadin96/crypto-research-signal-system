#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def main() -> None:
    output = Path('strategy_discovery_v1/data/global_trial_ledger.json')
    payload = {
        'ledger_id': 'strategy_discovery_global_trial_ledger_v1',
        'protocol_id': 'dsr_pbo_cpcv_v1',
        'version': '1.0.0',
        'status': 'initialized_empty_no_measured_trials',
        'created_at': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'n_trials': 0,
        'last_sequence': 0,
        'prior_global_ledger_hash': None,
        'trials': [],
        'analysis_only': True,
        'trading': False,
        'paper_trading': False,
        'deployment': False,
    }
    # The hash covers the complete canonical ledger payload, including the
    # creation timestamp fixed at artifact-generation time.
    payload['global_ledger_hash'] = hashlib.sha256(canonical(payload)).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'n_trials': payload['n_trials'], 'global_ledger_hash': payload['global_ledger_hash']}, sort_keys=True))


if __name__ == '__main__':
    main()
