#!/usr/bin/env python3
"""Expand historical deal universe from Wikipedia acquisition list pages.

This script intentionally filters to rows with:
- parseable acquisition date
- citation-backed source URL (when available)
- date >= source-specific min_date_for_prices
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from dateutil import parser as dtparser


USER_AGENT = "Mozilla/5.0 (compatible; cdd-prime-ingest/1.0)"


@dataclass(frozen=True)
class SourceConfig:
    page: str
    acquirer: str
    ticker: str
    sector: str
    min_date_for_prices: str


SOURCES: list[SourceConfig] = [
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_Alphabet",
        acquirer="Alphabet",
        ticker="GOOG",
        sector="Software",
        min_date_for_prices="2004-08-19",
    ),
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_Apple",
        acquirer="Apple",
        ticker="AAPL",
        sector="Technology",
        min_date_for_prices="1980-12-12",
    ),
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_Microsoft",
        acquirer="Microsoft",
        ticker="MSFT",
        sector="Software",
        min_date_for_prices="1986-03-13",
    ),
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_Meta_Platforms",
        acquirer="Meta Platforms",
        ticker="META",
        sector="Technology",
        min_date_for_prices="2012-05-18",
    ),
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_Amazon",
        acquirer="Amazon",
        ticker="AMZN",
        sector="E-commerce & Cloud",
        min_date_for_prices="1997-05-15",
    ),
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_IBM",
        acquirer="IBM",
        ticker="IBM",
        sector="Technology",
        min_date_for_prices="1970-01-01",
    ),
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_Intel",
        acquirer="Intel",
        ticker="INTC",
        sector="Semiconductors",
        min_date_for_prices="1980-01-01",
    ),
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_SAP",
        acquirer="SAP",
        ticker="SAP",
        sector="Software",
        min_date_for_prices="1998-01-01",
    ),
    SourceConfig(
        page="https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_Dell",
        acquirer="Dell",
        ticker="DELL",
        sector="Technology Hardware",
        min_date_for_prices="2018-12-28",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expand deal universe from Wikipedia source pages")
    parser.add_argument("--output", default="data/raw/deals_expanded.csv")
    parser.add_argument("--min-citation-links", type=int, default=0)
    return parser.parse_args()


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="ignore")


def _norm_header(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _pick_column(headers: list[str], candidates: list[str]) -> int | None:
    normalized = [_norm_header(h) for h in headers]
    for i, h in enumerate(normalized):
        for c in candidates:
            if c in h:
                return i
    return None


def _parse_date(text: str) -> date | None:
    t = re.sub(r"\[[^\]]*\]", "", text or "").strip()
    if not t:
        return None
    try:
        return dtparser.parse(t, fuzzy=True, default=dtparser.parse("2000-01-01")).date()
    except Exception:
        return None


def _slug(x: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", x.lower()).strip("_")
    return s[:80] if len(s) > 80 else s


def _parse_billions(price_text: str) -> str:
    t = (price_text or "").lower().replace(",", "")
    if not t or "undisclosed" in t or t in {"na", "n/a", "-"}:
        return ""

    m = re.search(r"(\d+(?:\.\d+)?)", t)
    if not m:
        return ""

    value = float(m.group(1))
    if any(u in t for u in ["billion", " bn", " b ", "usd b", "$b", "us$b"]):
        return f"{value:.3f}"
    if any(u in t for u in ["million", " mn", " m ", "usd m", "$m", "us$m"]):
        return f"{value / 1000.0:.3f}"

    # If unit unknown and value is large, assume millions to avoid absurd B values.
    if value > 1000:
        return f"{value / 1000.0:.3f}"
    return ""


def _is_cross_border(country_text: str) -> str:
    t = (country_text or "").strip().lower()
    if not t:
        return "no"
    us_tokens = {"us", "u.s.", "united states", "usa", "u.s.a."}
    return "no" if t in us_tokens else "yes"


def _risk_from_size_and_border(deal_value_b: str, cross_border: str) -> str:
    try:
        v = float(deal_value_b)
    except Exception:
        v = 0.0

    if v >= 20 or (cross_border == "yes" and v >= 5):
        return "high"
    if v >= 5 or cross_border == "yes":
        return "medium"
    return "low"


def _source_quality(url: str) -> str:
    if not url:
        return "0.45"
    host = (urlparse(url).netloc or "").lower()
    if any(x in host for x in ["sec.gov", "investor", "ir.", "newsroom", "press"]):
        return "0.95"
    if any(x in host for x in ["reuters", "wsj", "ft.com", "bloomberg", "cnbc"]):
        return "0.85"
    if "web.archive.org" in host:
        return "0.70"
    if "wikipedia.org" in host:
        return "0.50"
    return "0.65"


def _citation_urls_for_row(soup: BeautifulSoup, tr) -> list[str]:
    cite_ids: list[str] = []
    for a in tr.select("sup.reference a"):
        href = a.get("href", "")
        if href.startswith("#cite_note-"):
            cid = href.lstrip("#")
            cite_ids.append(cid)

    urls: list[str] = []
    for cid in cite_ids:
        li = soup.find(id=cid)
        if not li:
            continue
        for link in li.select("a.external.text"):
            href = link.get("href")
            if href:
                urls.append(href)

    # de-dup preserve order
    dedup: list[str] = []
    seen: set[str] = set()
    for u in urls:
        if u not in seen:
            seen.add(u)
            dedup.append(u)
    return dedup


def _extract_rows(source: SourceConfig) -> list[dict[str, str]]:
    html = fetch_html(source.page)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="wikitable")
    if table is None:
        return []

    rows = table.find_all("tr")
    if not rows:
        return []

    headers = [th.get_text(" ", strip=True) for th in rows[0].find_all(["th", "td"])]

    date_i = _pick_column(headers, ["acquisition date", "date acquired", "date"])
    company_i = _pick_column(headers, ["company", "acquired", "target"])
    business_i = _pick_column(headers, ["business", "description", "notes"])
    country_i = _pick_column(headers, ["country"])
    price_i = _pick_column(headers, ["price"])

    if date_i is None or company_i is None:
        return []

    min_date = date.fromisoformat(source.min_date_for_prices)
    output: list[dict[str, str]] = []

    for tr in rows[1:]:
        cells = tr.find_all("td")
        if not cells:
            continue

        values = [td.get_text(" ", strip=True) for td in cells]
        max_idx = max([x for x in [date_i, company_i, business_i, country_i, price_i] if x is not None], default=0)
        if len(values) <= max_idx:
            continue

        decision = _parse_date(values[date_i])
        if decision is None or decision < min_date:
            continue

        target = values[company_i].strip()
        if not target or target.lower() in {"nan", "none"}:
            continue

        business = values[business_i].strip() if business_i is not None and business_i < len(values) else ""
        country = values[country_i].strip() if country_i is not None and country_i < len(values) else ""
        price_text = values[price_i].strip() if price_i is not None and price_i < len(values) else ""

        citation_urls = _citation_urls_for_row(soup, tr)
        primary_source = citation_urls[0] if citation_urls else source.page

        cross_border = _is_cross_border(country)
        deal_value_b = _parse_billions(price_text)
        regulatory_risk = _risk_from_size_and_border(deal_value_b, cross_border)

        base = f"{source.ticker}|{target}|{decision.isoformat()}"
        digest = hashlib.md5(base.encode("utf-8")).hexdigest()[:8]
        deal_id = f"{_slug(source.ticker)}_{_slug(target)}_{decision.year}_{digest}"

        output.append(
            {
                "deal_id": deal_id,
                "acquirer": source.acquirer,
                "target": target,
                "acquirer_ticker": source.ticker,
                "announce_date": decision.isoformat(),
                "decision_date": decision.isoformat(),
                "close_or_termination_date": decision.isoformat(),
                "status": "completed",
                "deal_value_usd_b": deal_value_b,
                "sector": source.sector,
                "deal_type": "horizontal",
                "payment_type": "unknown",
                "cross_border": cross_border,
                "premium_pct": "25",
                "regulatory_risk": regulatory_risk,
                "notes": business[:280],
                "primary_source": primary_source,
                "source_page": source.page,
                "citation_count": str(len(citation_urls)),
                "source_quality_score": _source_quality(primary_source),
            }
        )

    return output


def _dedupe(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    by_key: dict[str, dict[str, str]] = {}
    for row in rows:
        key = "|".join(
            [
                row.get("acquirer_ticker", "").upper(),
                row.get("target", "").strip().lower(),
                row.get("decision_date", ""),
            ]
        )
        prev = by_key.get(key)
        if prev is None:
            by_key[key] = row
            continue
        # Prefer row with higher citation count and non-wikipedia source.
        prev_c = int(prev.get("citation_count", "0") or "0")
        cur_c = int(row.get("citation_count", "0") or "0")
        prev_is_wiki = "wikipedia.org" in prev.get("primary_source", "")
        cur_is_wiki = "wikipedia.org" in row.get("primary_source", "")
        if (cur_c > prev_c) or (prev_is_wiki and not cur_is_wiki):
            by_key[key] = row
    return list(by_key.values())


def main() -> None:
    args = parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, str]] = []
    for src in SOURCES:
        rows = _extract_rows(src)
        if args.min_citation_links > 0:
            rows = [r for r in rows if int(r.get("citation_count", "0") or "0") >= args.min_citation_links]
        print(f"source={src.acquirer:<14} rows={len(rows)} page={src.page}")
        all_rows.extend(rows)

    deduped = _dedupe(all_rows)
    deduped.sort(key=lambda r: (r["decision_date"], r["acquirer_ticker"], r["target"].lower()))

    if not deduped:
        raise RuntimeError("no rows extracted")

    fieldnames = list(deduped[0].keys())
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(deduped)

    print(f"wrote {out_path}")
    print(f"rows_total={len(all_rows)} rows_deduped={len(deduped)}")


if __name__ == "__main__":
    main()
