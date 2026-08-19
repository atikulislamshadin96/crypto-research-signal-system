from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("data/focused_ohlcv_phase1/4h")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


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
            matches = 0
            existing = 0
            rows_ok = 0
            for entry in manifest["files"]:
                path = Path(entry["path"])
                exists = path.exists()
                existing += int(exists)
                if not exists:
                    continue
                matches += int(sha256(path) == entry["sha256"] and path.stat().st_size == entry["bytes"])
                with path.open(encoding="utf-8") as handle:
                    row_count = sum(1 for _ in handle) - 1
                rows_ok += int(row_count == entry["rows"] and row_count > 0)
            results.append({
                "symbol": symbol,
                "manifest": str(manifest_path),
                "entries": len(manifest["files"]),
                "existing": existing,
                "checksum_matches": matches,
                "row_counts_match": rows_ok,
                "checksum_scope": manifest.get("checksum_scope"),
                "first_key": manifest["files"][0]["month" if "month" in manifest["files"][0] else "day"],
                "last_key": manifest["files"][-1]["month" if "month" in manifest["files"][-1] else "day"],
            })
    print(json.dumps(results, indent=2))
    if any(item["entries"] != item["existing"] or item["entries"] != item["checksum_matches"] or item["entries"] != item["row_counts_match"] for item in results):
        raise SystemExit("Phase 1 manifest verification failed")


if __name__ == "__main__":
    main()
