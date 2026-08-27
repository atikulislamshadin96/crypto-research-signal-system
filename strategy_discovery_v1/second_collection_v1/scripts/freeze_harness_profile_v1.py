#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1] / 'data' / 'freqtrade_batch_001_research_harness_v1.json'

def h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()

obj=json.loads(PROFILE.read_text(encoding='utf-8'))
obj.pop('harness_profile_sha256', None)
obj['harness_profile_sha256']=h(obj)
PROFILE.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n', encoding='utf-8')
print(obj['harness_profile_sha256'])
