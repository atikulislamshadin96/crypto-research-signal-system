#!/usr/bin/env python3
"""Collect a bounded batch of academic candidate leads from arXiv q-fin.

This script collects source records only. It does not download market data, run a
backtest, or infer a deterministic strategy from an abstract. Full-text review
and normalization are separate stages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean(text: str | None) -> str:
    return " ".join((text or "").split())


def sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def query_arxiv(query: str, start: int, max_results: int) -> tuple[int, list[dict[str, object]]]:
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = "https://export.arxiv.org/api/query?" + params
    request = urllib.request.Request(url, headers={"User-Agent": "strategy-discovery-v1/1.0 research metadata collector"})
    with urllib.request.urlopen(request, timeout=60) as response:
        root = ET.fromstring(response.read())
    total = int(root.findtext(OPENSEARCH + "totalResults", "0"))
    records: list[dict[str, object]] = []
    for entry in root.findall(ATOM + "entry"):
        raw_id = clean(entry.findtext(ATOM + "id"))
        arxiv_id = raw_id.rsplit("/", 1)[-1]
        title = clean(entry.findtext(ATOM + "title"))
        abstract = clean(entry.findtext(ATOM + "summary"))
        updated = clean(entry.findtext(ATOM + "updated"))
        published = clean(entry.findtext(ATOM + "published"))
        categories = [node.attrib.get("term", "") for node in entry.findall(ATOM + "category")]
        authors = [clean(node.findtext(ATOM + "name")) for node in entry.findall(ATOM + "author")]
        links = {node.attrib.get("title", node.attrib.get("rel", "")): node.attrib.get("href", "") for node in entry.findall(ATOM + "link")}
        versioned_abs = links.get("alternate", f"https://arxiv.org/abs/{arxiv_id}")
        pdf = links.get("pdf", f"https://arxiv.org/pdf/{arxiv_id}")
        records.append({
            "source_class": "academic_preprint",
            "source_id": "arxiv_qfin",
            "document_id": arxiv_id,
            "document_version": arxiv_id.rsplit("v", 1)[-1] if "v" in arxiv_id else "unknown",
            "document_title": title,
            "authors": authors,
            "abstract": abstract,
            "categories": categories,
            "published_at": published,
            "updated_at": updated,
            "canonical_url": versioned_abs,
            "rule_disclosure_locator": pdf,
            "rule_disclosure_status": "pending_full_text_review",
            "retrieved_at": utc_now(),
            "metadata_snapshot_hash": sha256_json({"id": arxiv_id, "title": title, "abstract": abstract, "updated": updated, "categories": categories}),
            "primary_source_policy": "allowed_academic_preprint_pending_deterministic_rule_review",
        })
    return total, records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not 1 <= args.limit <= 200:
        raise SystemExit("limit must be between 1 and 200")

    # Query categories allowed by the frozen source policy. A broad query is
    # used for a source batch; exact source class remains academic_preprint.
    query = "cat:q-fin.TR OR cat:q-fin.PM OR cat:q-fin.ST OR cat:q-fin.RM"
    total, records = query_arxiv(query, args.start, args.limit)
    # arXiv can expose cross-listed duplicates; retain one record per versioned id.
    deduped = {str(item["document_id"]): item for item in records}
    records = list(deduped.values())
    payload = {
        "batch_id": args.batch_id,
        "collection_version": "strategy_discovery_collection_v1",
        "source_registry_version": "strategy_discovery_source_registry_v1",
        "retrieved_at": utc_now(),
        "query": query,
        "api_total_results": total,
        "requested_limit": args.limit,
        "raw_candidate_count": len(records),
        "candidates": records,
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"batch_id": args.batch_id, "raw_candidate_count": len(records), "output": str(output), "api_total_results": total}, sort_keys=True))


if __name__ == "__main__":
    main()
