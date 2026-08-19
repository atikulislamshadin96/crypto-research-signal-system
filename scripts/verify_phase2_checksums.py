from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("data/focused_ohlcv_phase2/4h")
SYMBOLS = ("BNBUSDT", "XRPUSDT", "ADAUSDT")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    results = []
    for symbol in SYMBOLS:
        directory = ROOT / symbol
        for manifest_name in ("manifest-4h.json", "manifest-4h-daily.json"):
            manifest_path = directory / manifest_name
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            existing = checksum_matches = row_matches = 0
            for entry in manifest["files"]:
                path = Path(entry["path"])
                if not path.exists():
                    continue
                existing += 1
                checksum_matches += int(sha256(path) == entry["sha256"] and path.stat().st_size == entry["bytes"])
                with path.open(encoding="utf-8") as handle:
                    row_count = sum(1 for _ in handle) - 1
                row_matches += int(row_count == entry["rows"] and row_count > 0)
            results.append({
                "symbol": symbol,
                "manifest": str(manifest_path),
                "entries": len(manifest["files"]),
                "existing": existing,
                "checksum_matches": checksum_matches,
                "row_counts_match": row_matches,
                "checksum_scope": manifest.get("checksum_scope"),
            })
    print(json.dumps(results, indent=2))
    if any(item["entries"] != item["existing"] or item["entries"] != item["checksum_matches"] or item["entries"] != item["row_counts_match"] for item in results):
        raise SystemExit("Phase 2 manifest verification failed")


if __name__ == "__main__":
    main()
