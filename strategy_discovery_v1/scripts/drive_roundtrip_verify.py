#!/usr/bin/env python3
"""Upload OHLCV files to Google Drive and verify byte-for-byte round trips."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_gws(args: list[str]) -> object:
    result = subprocess.run(["gws", *args], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def find_existing(name: str) -> str | None:
    query = f"name = '{name}' and trashed = false"
    listing = run_gws([
        "drive", "files", "list",
        "--params", json.dumps({"q": query, "pageSize": 10, "fields": "files(id,name,createdTime)"}),
        "--format", "json",
    ])
    matches = listing.get("files", [])
    return str(matches[0]["id"]) if matches else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    files = sorted(data_dir.glob("*.csv"))
    if len(files) != 10:
        raise SystemExit(f"expected 10 OHLCV CSV files, found {len(files)}")
    records: list[dict[str, object]] = []
    for path in files:
        local_hash = sha256(path)
        file_id = find_existing(path.name)
        reused_drive_file = file_id is not None
        if file_id is None:
            upload = run_gws([
                "drive", "files", "create",
                "--upload", str(path),
                "--upload-content-type", "text/csv",
                "--json", json.dumps({"name": path.name, "mimeType": "text/csv"}),
                "--format", "json",
            ])
            file_id = str(upload["id"])
        metadata = run_gws([
            "drive", "files", "get",
            "--params", json.dumps({"fileId": file_id, "fields": "id,name,size,md5Checksum,mimeType"}),
            "--format", "json",
        ])
        with tempfile.TemporaryDirectory(prefix="drive_roundtrip_", dir=str(data_dir)) as roundtrip_dir:
            returned_path = Path(roundtrip_dir) / path.name
            subprocess.run([
                "gws", "drive", "files", "get",
                "--params", json.dumps({"fileId": file_id, "alt": "media"}),
                "--output", str(returned_path),
            ], check=True, capture_output=True, text=True)
            returned_hash = sha256(returned_path)
            returned_size = returned_path.stat().st_size
        records.append({
            "local_path": str(path),
            "file_name": path.name,
            "drive_file_id": file_id,
            "reused_existing_drive_file": reused_drive_file,
            "local_size": path.stat().st_size,
            "remote_metadata": metadata,
            "local_sha256": local_hash,
            "roundtrip_sha256": returned_hash,
            "roundtrip_size": returned_size,
            "byte_for_byte_equal": local_hash == returned_hash and path.stat().st_size == returned_size,
        })
        print(json.dumps({"file": path.name, "drive_file_id": file_id, "byte_for_byte_equal": records[-1]["byte_for_byte_equal"]}, sort_keys=True))
    result = {
        "verification_id": "bybit_linear_ohlcv_drive_roundtrip_v1",
        "verified_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "data_dir": str(data_dir),
        "file_count": len(records),
        "all_byte_for_byte_equal": all(bool(item["byte_for_byte_equal"]) for item in records),
        "files": records,
        "analysis_only": True,
        "trading": False,
        "paper_trading": False,
        "deployment": False,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(output), "file_count": len(records), "all_byte_for_byte_equal": result["all_byte_for_byte_equal"]}, sort_keys=True))


if __name__ == "__main__":
    main()
