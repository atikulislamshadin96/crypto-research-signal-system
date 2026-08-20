from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "v1"
EXPECTED_PHASE4_FLOW_FINGERPRINT = "86a8608328a77a9d60cfc95570ac05cf178207995f9243906f7c081d38f47cfd"
DEFAULT_PROTOCOL_PATH = Path("protocols/phase4_flow_construction_v1.json")


def canonical_protocol_bytes(protocol: dict[str, Any]) -> bytes:
    payload = dict(protocol)
    payload.pop("protocol_fingerprint_sha256", None)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def compute_protocol_fingerprint(protocol: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_protocol_bytes(protocol)).hexdigest()


def load_verified_phase4_protocol(
    path: str | Path = DEFAULT_PROTOCOL_PATH,
    *,
    expected_version: str = PROTOCOL_VERSION,
    expected_fingerprint: str | None = None,
) -> dict[str, Any]:
    protocol_path = Path(path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    actual_version = protocol.get("protocol_version")
    if actual_version != expected_version:
        raise RuntimeError(f"Phase 4 protocol version mismatch: expected {expected_version}, got {actual_version}")
    recorded = protocol.get("protocol_fingerprint_sha256")
    computed = compute_protocol_fingerprint(protocol)
    if not recorded or recorded != computed:
        raise RuntimeError(f"Phase 4 protocol fingerprint mismatch: recorded {recorded}, computed {computed}")
    if expected_fingerprint is not None and computed != expected_fingerprint:
        raise RuntimeError(f"Phase 4 protocol fingerprint mismatch: expected {expected_fingerprint}, got {computed}")
    return protocol
