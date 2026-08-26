#!/usr/bin/env python3
"""Collect bounded second-run source leads from verified allowed source families."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
OPEN = "{http://a9.com/-/spec/opensearch/1.1/}"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean(text: str | None) -> str:
    return " ".join((text or "").split())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


def fetch_text(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "strategy-discovery-v1-second-collection/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def collect_arxiv(limit: int, start: int, systematic: bool = False) -> tuple[list[dict[str, object]], dict[str, object]]:
    query = ('(cat:q-fin.ST OR cat:q-fin.TR OR cat:q-fin.RM) AND '
             '(all:"statistical arbitrage" OR all:"pairs trading" OR all:cointegration OR all:momentum OR all:"trend following" OR all:volatility OR all:carry)') if systematic else 'cat:q-fin.MF AND (all:"market microstructure" OR all:"order flow" OR all:"limit order book" OR all:"price discovery" OR all:"liquidity")'
    params = urllib.parse.urlencode({"search_query": query, "start": start, "max_results": limit, "sortBy": "submittedDate", "sortOrder": "descending"})
    url = "https://export.arxiv.org/api/query?" + params
    raw = fetch_text(url)
    root = ET.fromstring(raw)
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
        canonical = links.get("alternate", f"https://arxiv.org/abs/{arxiv_id}")
        pdf = links.get("pdf", f"https://arxiv.org/pdf/{arxiv_id}")
        records.append({
            "source_class": "order_flow_microstructure",
            "source_id": "microstructure_research",
            "document_id": arxiv_id,
            "document_version": arxiv_id.rsplit("v", 1)[-1] if "v" in arxiv_id else "unknown",
            "document_title": title,
            "authors": authors,
            "abstract": abstract,
            "recorded_rule_description": "Metadata lead only; full deterministic rule disclosure is not asserted at collection time.",
            "categories": categories,
            "published_at": published,
            "updated_at": updated,
            "canonical_url": canonical,
            "stable_locator_to_rule_text_or_code": pdf,
            "rule_disclosure_locator": pdf,
            "rule_disclosure_status": "pending_full_text_review",
            "retrieved_at": now(),
            "source_snapshot_hash": sha256_bytes(raw),
            "metadata_snapshot_hash": sha256_json({"id": arxiv_id, "title": title, "abstract": abstract, "updated": updated, "categories": categories}),
            "admissibility_decision": "pending_normalization_review",
            "admissibility_reason": "Allowed q-fin.MF microstructure source lead; deterministic rule disclosure remains a separate gate.",
            "rejection_category_if_rejected": None,
            "primary_source_policy": "allowed_academic_preprint_pending_deterministic_rule_review",
        })
    total = int(root.findtext(OPEN + "totalResults", "0"))
    return records, {"endpoint": url, "api_total_results": total, "retrieval_snapshot_hash": sha256_bytes(raw)}


def gh_api(path: str) -> object:
    result = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True, env={**__import__("os").environ, "NO_COLOR": "1", "GH_FORCE_TTY": "0"})
    return json.loads(result.stdout)


def collect_quantconnect(limit: int, start: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    sources = [("QuantConnect/Research", "master"), ("QuantConnect/Lean", "master")]
    all_items: list[dict[str, object]] = []
    for repo, ref in sources:
        tree = gh_api(f"repos/{repo}/git/trees/{ref}?recursive=1")
        tree_sha = str(tree.get("sha", ""))
        for item in tree.get("tree", []):
            path = str(item.get("path", ""))
            if item.get("type") != "blob" or not path.lower().endswith((".ipynb", ".py", ".cs")):
                continue
            low = path.lower()
            if repo == "QuantConnect/Research":
                if not path.lower().endswith(".ipynb") or path.startswith(("Documentation/", "Scratch ")):
                    continue
            else:
                if not path.startswith(("Algorithm.CSharp/", "Algorithm.Python/")):
                    continue
                if any(term in low for term in ("regression", "benchmark", "basict​​emplate", "basictemplate", "test", "integration", "brokerage", "order", "customdata", "consolidator", "universe", "history", "security", "model", "margin", "currency", "settlement", "delisting", "fill", "fee", "account", "indicator")):
                    continue
            if not any(term in low for term in ("alpha", "strategy", "meanreversion", "mean_reversion", "pairs", "cointegration", "momentum", "trend", "volatility", "arbitrage", "carry", "rotation", "dual", "gap", "kalman", "zscore", "stationary", "vix", "value", "factor", "reversion", "risk")) and repo == "QuantConnect/Lean":
                continue
            all_items.append({"repo": repo, "ref": ref, "tree_sha": tree_sha, "path": path, "blob_sha": item.get("sha"), "size": item.get("size")})
    all_items.sort(key=lambda x: (str(x["repo"]), str(x["path"])))
    selected = all_items[start:start + limit]
    records: list[dict[str, object]] = []
    for item in selected:
        repo = str(item["repo"]); ref = str(item["ref"]); path = str(item["path"])
        url = f"https://github.com/{repo}/blob/{ref}/{urllib.parse.quote(path)}"
        raw_url = f"https://raw.githubusercontent.com/{repo}/{ref}/{urllib.parse.quote(path)}"
        snapshot = {"repo": repo, "ref": ref, "tree_sha": item["tree_sha"], "path": path, "blob_sha": item["blob_sha"]}
        title = Path(path).stem.replace("_", " ").replace("-", " ")
        records.append({
            "source_class": "open_quant_archive",
            "source_id": "quantconnect_research",
            "document_id": f"{repo}@{item['blob_sha']}:{path}",
            "document_version": str(item["blob_sha"]),
            "document_title": title,
            "authors": ["QuantConnect"],
            "abstract": f"Stable open QuantConnect LEAN source file at {repo} path {path}; source code is the recorded rule locator.",
            "recorded_rule_description": "Source-code lead only; deterministic extraction is deferred to the frozen normalization gate.",
            "canonical_url": url,
            "stable_locator_to_rule_text_or_code": raw_url,
            "rule_disclosure_locator": raw_url,
            "rule_disclosure_status": "pending_full_text_review",
            "retrieved_at": now(),
            "source_snapshot_hash": sha256_json(snapshot),
            "metadata_snapshot_hash": sha256_json({"title": title, **snapshot}),
            "admissibility_decision": "pending_normalization_review",
            "admissibility_reason": "Stable open-quant repository revision/path; source code is retained as the rule locator.",
            "rejection_category_if_rejected": None,
            "repository": repo,
            "repository_ref": ref,
            "repository_tree_sha": item["tree_sha"],
            "repository_blob_sha": item["blob_sha"],
            "source_path": path,
        })
    return records, {"repositories": [repo for repo, _ in sources], "candidate_pool_before_slice": len(all_items), "slice_start": start}


def collect_web_index(source_id: str, base_url: str, limit: int, start: int, match_pattern: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    from bs4 import BeautifulSoup
    records_by_url: dict[str, dict[str, object]] = {}
    for page in range(0, 80):
        url = base_url if page == 0 else base_url + ("&" if "?" in base_url else "?") + f"page={page}"
        try:
            raw = fetch_text(url)
        except Exception:
            continue
        soup = BeautifulSoup(raw, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urllib.parse.urljoin(base_url, a.get("href"))
            if not re.search(match_pattern, href, flags=re.I):
                continue
            if href.rstrip("/") in {base_url.rstrip("/"), "https://www.man.com/insights"}:
                continue
            title = clean(a.get_text(" ", strip=True))
            if len(title) < 8:
                continue
            records_by_url.setdefault(href, {"url": href, "title": title, "index_url": url, "index_snapshot_hash": sha256_bytes(raw)})
        if len(records_by_url) >= start + limit:
            break
    values = sorted(records_by_url.values(), key=lambda x: x["url"])[start:start + limit]
    records: list[dict[str, object]] = []
    for item in values:
        title = str(item["title"])
        records.append({
            "source_class": "published_quant_research",
            "source_id": source_id,
            "document_id": item["url"],
            "document_version": "retrieved_page",
            "document_title": title,
            "authors": [],
            "abstract": f"Official published quantitative research page lead: {title}.",
            "recorded_rule_description": "Published research lead only; exact executable rules are not asserted at collection time.",
            "canonical_url": item["url"],
            "stable_locator_to_rule_text_or_code": item["url"],
            "rule_disclosure_locator": item["url"],
            "rule_disclosure_status": "pending_full_text_review",
            "retrieved_at": now(),
            "source_snapshot_hash": item["index_snapshot_hash"],
            "metadata_snapshot_hash": sha256_json(item),
            "admissibility_decision": "pending_normalization_review",
            "admissibility_reason": "Allowed published-quant-research source lead; full deterministic disclosure remains a separate gate.",
            "rejection_category_if_rejected": None,
        })
    return records, {"index": base_url, "candidate_pool_before_slice": len(records_by_url), "slice_start": start}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("arxiv_microstructure", "academic_systematic", "quantconnect", "published_quant", "aqr", "man"), required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not 1 <= args.limit <= 200:
        raise SystemExit("limit must be between 1 and 200")
    if args.kind == "arxiv_microstructure":
        records, details = collect_arxiv(args.limit, args.start, systematic=False)
    elif args.kind == "academic_systematic":
        records, details = collect_arxiv(args.limit, args.start, systematic=True)
        for record in records:
            record["source_id"] = "academic_systematic_research"
            record["source_class"] = "academic_preprint"
            record["admissibility_reason"] = "Allowed q-fin systematic-trading source lead; deterministic rule disclosure remains a separate gate."
    elif args.kind == "quantconnect":
        records, details = collect_quantconnect(args.limit, args.start)
    elif args.kind == "published_quant":
        aqr, aqr_details = collect_web_index("aqr_public_research", "https://www.aqr.com/Insights/Research", args.limit // 2, args.start, r"/Insights/Research/")
        man, man_details = collect_web_index("man_institute_research", "https://www.man.com/insights", args.limit - args.limit // 2, args.start, r"https://www\.man\.com/insights/[^?#]+$")
        records, details = aqr + man, {"aqr": aqr_details, "man": man_details}
    elif args.kind == "aqr":
        records, details = collect_web_index("aqr_public_research", "https://www.aqr.com/Insights/Research", args.limit, args.start, r"/Insights/Research/")
    else:
        records, details = collect_web_index("man_institute_research", "https://www.man.com/insights", args.limit, args.start, r"https://www\.man\.com/insights/[^?#]+$")
    if len(records) < args.limit:
        raise SystemExit(f"source kind {args.kind} yielded {len(records)} records, below requested {args.limit}")
    payload = {
        "batch_id": args.batch_id,
        "collection_version": "strategy_discovery_second_collection_v1",
        "source_registry_version": "strategy_discovery_source_registry_v1",
        "source_kind": args.kind,
        "retrieved_at": now(),
        "requested_limit": args.limit,
        "slice_start": args.start,
        "raw_candidate_count": len(records),
        "source_details": details,
        "candidates": records,
        "analysis_only": True,
        "market_data_downloaded": False,
        "backtest_run": False,
        "trial_ledger_n": 0,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"batch_id": args.batch_id, "kind": args.kind, "raw_candidate_count": len(records), "output": str(output), "source_details": details}, sort_keys=True))


if __name__ == "__main__":
    main()
