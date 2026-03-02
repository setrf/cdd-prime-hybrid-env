#!/usr/bin/env python3
"""Ingest richer textual evidence snippets (filings, calls, decks, press pages)."""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0 (compatible; cdd-prime-text-evidence/1.0)"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build text-evidence snippets per deal")
    p.add_argument("--input", default="data/interim/deals_enriched.csv")
    p.add_argument("--output", default="data/interim/text_evidence.jsonl")
    p.add_argument("--max-deals", type=int, default=300)
    p.add_argument("--max-unique-urls", type=int, default=250)
    p.add_argument("--timeout", type=int, default=12)
    p.add_argument("--max-chars", type=int, default=500)
    return p.parse_args()


def _domain(url: str) -> str:
    return (urlparse(url).netloc or "").lower()


def _source_type(url: str) -> str:
    u = url.lower()
    host = _domain(url)
    if "sec.gov" in host:
        return "sec_filing_excerpt"
    if ".pdf" in u or "deck" in u or "presentation" in u:
        return "investor_deck_excerpt"
    if "transcript" in u or "earnings" in u or "conference" in u:
        return "call_transcript_excerpt"
    if "investor" in host or "ir." in host:
        return "investor_relations_excerpt"
    return "press_or_news_excerpt"


def _clean_text(x: str) -> str:
    x = re.sub(r"\s+", " ", x).strip()
    return x


def _fetch_html(url: str, timeout: int) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _extract_snippet(html: str, max_chars: int) -> str:
    soup = BeautifulSoup(html, "html.parser")
    parts: list[str] = []

    for meta in soup.select("meta[name='description'], meta[property='og:description']"):
        content = _clean_text(meta.get("content", ""))
        if content and len(content) >= 40:
            parts.append(content)

    for p in soup.find_all("p"):
        txt = _clean_text(p.get_text(" ", strip=True))
        if len(txt) >= 60:
            parts.append(txt)
        if len(parts) >= 3:
            break

    if not parts:
        body = _clean_text(soup.get_text(" ", strip=True))
        if body:
            parts.append(body[: max_chars * 2])

    snippet = " ".join(parts)
    return snippet[:max_chars]


def _row_date(row: dict[str, str]) -> str:
    announce = row.get("announce_date", "").strip()
    decision = row.get("decision_date", "").strip()
    if announce and decision:
        return announce if announce <= decision else decision
    return decision or announce or "2000-01-01"


def _quality(row: dict[str, str]) -> float:
    try:
        return float(row.get("source_quality_score", "0.65") or "0.65")
    except Exception:
        return 0.65


def main() -> None:
    args = parse_args()
    rows = list(csv.DictReader(Path(args.input).open()))
    if not rows:
        raise RuntimeError("input has no rows")

    if args.max_deals > 0:
        rows = rows[: args.max_deals]

    url_cache: dict[str, str] = {}
    errors = 0
    url_fetches = 0
    outputs: list[dict[str, Any]] = []

    for row in rows:
        deal_id = row["deal_id"]
        urls = []
        for k in ("primary_source", "source_page"):
            u = str(row.get(k, "")).strip()
            if u and u not in urls:
                urls.append(u)

        chosen_url = urls[0] if urls else ""
        snippet = ""
        for u in urls:
            if u not in url_cache and len(url_cache) < args.max_unique_urls:
                try:
                    html = _fetch_html(u, timeout=args.timeout)
                    url_cache[u] = _extract_snippet(html, max_chars=args.max_chars)
                    url_fetches += 1
                except Exception:
                    url_cache[u] = ""
                    errors += 1
            cached = url_cache.get(u, "")
            if cached:
                chosen_url = u
                snippet = cached
                break

        if not snippet:
            snippet = _clean_text(row.get("notes", ""))[: args.max_chars]
        if not snippet:
            snippet = f"{row.get('acquirer', '')} acquiring {row.get('target', '')} in {row.get('sector', '')}."

        evidence = {
            "evidence_id": f"EVTXT_{deal_id}",
            "source_type": _source_type(chosen_url),
            "source_url": chosen_url,
            "source_date": _row_date(row),
            "source_quality_score": _quality(row),
            "summary": snippet[:240],
            "text_excerpt": snippet,
        }
        outputs.append({"deal_id": deal_id, "text_evidence": [evidence]})

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for row in outputs:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    print(f"wrote {out_path}")
    print(
        " ".join(
            [
                f"deals={len(outputs)}",
                f"unique_urls_cached={len(url_cache)}",
                f"url_fetches={url_fetches}",
                f"fetch_errors={errors}",
            ]
        )
    )


if __name__ == "__main__":
    main()
