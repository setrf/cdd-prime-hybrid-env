#!/usr/bin/env python3
"""Enrich raw deal rows with market-based outcome labels.

Label rule (default):
- terminated deal => outcome_label = 0
- completed deal => outcome_label = 1 if 730d abnormal return >= 0 else 0
"""

from __future__ import annotations

import argparse
import csv
import io
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen


@dataclass
class PricePoint:
    dt: date
    close: float


class PriceStore:
    def __init__(self) -> None:
        self._cache: Dict[str, List[PricePoint]] = {}

    def _download(self, ticker: str) -> List[PricePoint]:
        t = ticker.lower().strip()
        if "." not in t:
            t = f"{t}.us"
        url = f"https://stooq.com/q/d/l/?s={t}&i=d"
        raw = urlopen(url, timeout=30).read().decode("utf-8", errors="ignore")
        if not raw.strip() or raw.startswith("No data"):
            return []
        reader = csv.DictReader(io.StringIO(raw))
        out: List[PricePoint] = []
        for row in reader:
            d = row.get("Date", "").strip()
            c = row.get("Close", "").strip()
            if not d or not c:
                continue
            try:
                out.append(PricePoint(dt=date.fromisoformat(d), close=float(c)))
            except ValueError:
                continue
        out.sort(key=lambda x: x.dt)
        return out

    def get(self, ticker: str) -> List[PricePoint]:
        key = ticker.upper().strip()
        if key not in self._cache:
            self._cache[key] = self._download(key)
        return self._cache[key]

    @staticmethod
    def _find_on_or_after(points: List[PricePoint], target: date, max_slip_days: int = 10) -> Optional[PricePoint]:
        for p in points:
            if p.dt >= target and (p.dt - target).days <= max_slip_days:
                return p
        return None

    @staticmethod
    def _find_on_or_before(points: List[PricePoint], target: date, max_slip_days: int = 10) -> Optional[PricePoint]:
        for p in reversed(points):
            if p.dt <= target and (target - p.dt).days <= max_slip_days:
                return p
        return None

    def get_pair(self, ticker: str, start: date, end: date) -> tuple[Optional[PricePoint], Optional[PricePoint], str]:
        points = self.get(ticker)
        if not points:
            return None, None, "no_price_series"

        start_pp = self._find_on_or_after(points, start)
        if start_pp is None:
            return None, None, "missing_start_price"

        end_pp = self._find_on_or_after(points, end)
        mode = "on_or_after"
        if end_pp is None:
            end_pp = self._find_on_or_before(points, end)
            mode = "on_or_before"
        if end_pp is None:
            return start_pp, None, "missing_end_price"

        return start_pp, end_pp, mode


def pct_return(start_price: float, end_price: float) -> float:
    if start_price <= 0:
        raise ValueError("start_price must be positive")
    return (end_price / start_price) - 1.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build outcome-enriched deal dataset")
    parser.add_argument("--input", default="data/raw/deals_seed.csv")
    parser.add_argument("--output", default="data/interim/deals_enriched.csv")
    parser.add_argument("--benchmark-ticker", default="SPY")
    parser.add_argument("--horizon-days", type=int, default=730)
    parser.add_argument("--threshold", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(input_path.open()))
    if not rows:
        raise RuntimeError("input file has no rows")

    prices = PriceStore()

    enriched: List[dict[str, str]] = []
    completed = terminated = labeled = 0

    for row in rows:
        status = row["status"].strip().lower()
        decision_date = date.fromisoformat(row["decision_date"])
        horizon_date = decision_date + timedelta(days=args.horizon_days)

        row_out = dict(row)
        row_out["horizon_date"] = horizon_date.isoformat()
        row_out["benchmark_ticker"] = args.benchmark_ticker.upper()

        if status == "terminated":
            terminated += 1
            row_out["entry_price"] = ""
            row_out["horizon_price"] = ""
            row_out["benchmark_entry"] = ""
            row_out["benchmark_horizon"] = ""
            row_out["acquirer_return_730d"] = ""
            row_out["benchmark_return_730d"] = ""
            row_out["abnormal_return_730d"] = ""
            row_out["price_mode"] = "terminated"
            row_out["outcome_label"] = "0"
            row_out["outcome_rule"] = "terminated_deal"
            row_out["data_quality_flag"] = "ok"
            labeled += 1
            enriched.append(row_out)
            continue

        completed += 1
        ticker = row["acquirer_ticker"].strip().upper()
        start_pp, end_pp, mode = prices.get_pair(ticker, decision_date, horizon_date)
        b_start_pp, b_end_pp, b_mode = prices.get_pair(args.benchmark_ticker, decision_date, horizon_date)

        if start_pp and end_pp and b_start_pp and b_end_pp:
            acq_ret = pct_return(start_pp.close, end_pp.close)
            bmk_ret = pct_return(b_start_pp.close, b_end_pp.close)
            abn = acq_ret - bmk_ret
            label = 1 if abn >= args.threshold else 0

            row_out["entry_price"] = f"{start_pp.close:.6f}"
            row_out["horizon_price"] = f"{end_pp.close:.6f}"
            row_out["benchmark_entry"] = f"{b_start_pp.close:.6f}"
            row_out["benchmark_horizon"] = f"{b_end_pp.close:.6f}"
            row_out["acquirer_return_730d"] = f"{acq_ret:.8f}"
            row_out["benchmark_return_730d"] = f"{bmk_ret:.8f}"
            row_out["abnormal_return_730d"] = f"{abn:.8f}"
            row_out["price_mode"] = f"acq:{mode};bmk:{b_mode}"
            row_out["outcome_label"] = str(label)
            row_out["outcome_rule"] = f"completed_abnormal_return_{'>=' if label == 1 else '<'}_{args.threshold}"
            row_out["data_quality_flag"] = "ok"
            labeled += 1
        else:
            row_out["entry_price"] = ""
            row_out["horizon_price"] = ""
            row_out["benchmark_entry"] = ""
            row_out["benchmark_horizon"] = ""
            row_out["acquirer_return_730d"] = ""
            row_out["benchmark_return_730d"] = ""
            row_out["abnormal_return_730d"] = ""
            row_out["price_mode"] = f"acq:{mode};bmk:{b_mode}"
            row_out["outcome_label"] = ""
            row_out["outcome_rule"] = "missing_price_data"
            row_out["data_quality_flag"] = "review"

        enriched.append(row_out)

    fieldnames = list(enriched[0].keys())
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)

    print(f"wrote {output_path}")
    print(f"rows={len(enriched)} completed={completed} terminated={terminated} labeled={labeled}")


if __name__ == "__main__":
    main()
