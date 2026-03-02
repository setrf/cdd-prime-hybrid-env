#!/usr/bin/env python3
"""Enrich raw deal rows with market-based outcomes and multi-target labels.

Primary labels:
- close_label: 1 if completed else 0
- outcome_label: 1 if (completed and abnormal_return_730d >= threshold) else 0
- thesis_hit_label: 1 if outcome_label=1 and max_drawdown_365d > drawdown_cutoff
"""

from __future__ import annotations

import argparse
import csv
import io
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional
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
        raw = urlopen(f"https://stooq.com/q/d/l/?s={t}&i=d", timeout=30).read().decode("utf-8", errors="ignore")
        if not raw.strip() or raw.startswith("No data"):
            return []
        reader = csv.DictReader(io.StringIO(raw))
        out: List[PricePoint] = []
        for row in reader:
            d, c = row.get("Date", "").strip(), row.get("Close", "").strip()
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

    def window(self, ticker: str, start: date, end: date) -> list[PricePoint]:
        points = self.get(ticker)
        return [p for p in points if start <= p.dt <= end]


def pct_return(start_price: float, end_price: float) -> float:
    if start_price <= 0:
        raise ValueError("start_price must be positive")
    return (end_price / start_price) - 1.0


def max_drawdown(points: list[PricePoint], start_price: float) -> float:
    if start_price <= 0:
        return 0.0
    peak = start_price
    worst = 0.0
    for p in points:
        if p.close > peak:
            peak = p.close
        dd = (p.close / peak) - 1.0
        if dd < worst:
            worst = dd
    return worst


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build outcome-enriched deal dataset")
    p.add_argument("--input", default="data/raw/deals_seed.csv")
    p.add_argument("--output", default="data/interim/deals_enriched.csv")
    p.add_argument("--benchmark-ticker", default="SPY")
    p.add_argument("--threshold", type=float, default=0.0, help="abnormal 730d threshold for outcome_label")
    p.add_argument(
        "--drawdown-cutoff",
        type=float,
        default=-0.25,
        help="max_drawdown_365d cutoff for thesis_hit_label (must be > cutoff)",
    )
    return p.parse_args()


def _blank_metrics(row_out: dict[str, str]) -> None:
    for k in [
        "entry_price",
        "horizon365_price",
        "horizon730_price",
        "benchmark_entry",
        "benchmark_horizon365",
        "benchmark_horizon730",
        "acquirer_return_365d",
        "acquirer_return_730d",
        "benchmark_return_365d",
        "benchmark_return_730d",
        "abnormal_return_365d",
        "abnormal_return_730d",
        "max_drawdown_365d",
        "max_drawdown_730d",
    ]:
        row_out[k] = ""


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(in_path.open()))
    if not rows:
        raise RuntimeError("input file has no rows")

    prices = PriceStore()
    enriched: List[dict[str, str]] = []

    completed = terminated = labeled = review = 0

    for row in rows:
        status = row.get("status", "").strip().lower()
        decision = date.fromisoformat(row["decision_date"])
        h365 = decision + timedelta(days=365)
        h730 = decision + timedelta(days=730)

        row_out = dict(row)
        row_out["horizon365_date"] = h365.isoformat()
        row_out["horizon730_date"] = h730.isoformat()
        row_out["benchmark_ticker"] = args.benchmark_ticker.upper()
        row_out["close_label"] = "1" if status == "completed" else "0"

        if status == "terminated":
            terminated += 1
            _blank_metrics(row_out)
            row_out["price_mode"] = "terminated"
            row_out["outcome_label"] = "0"
            row_out["thesis_hit_label"] = "0"
            row_out["outcome_rule"] = "terminated_deal"
            row_out["data_quality_flag"] = "ok"
            labeled += 1
            enriched.append(row_out)
            continue

        completed += 1
        ticker = row["acquirer_ticker"].strip().upper()

        s_pp, e365_pp, mode365 = prices.get_pair(ticker, decision, h365)
        _, e730_pp, mode730 = prices.get_pair(ticker, decision, h730)
        b_s_pp, b_e365_pp, b_mode365 = prices.get_pair(args.benchmark_ticker, decision, h365)
        _, b_e730_pp, b_mode730 = prices.get_pair(args.benchmark_ticker, decision, h730)

        if s_pp and e365_pp and e730_pp and b_s_pp and b_e365_pp and b_e730_pp:
            acq_ret365 = pct_return(s_pp.close, e365_pp.close)
            acq_ret730 = pct_return(s_pp.close, e730_pp.close)
            bmk_ret365 = pct_return(b_s_pp.close, b_e365_pp.close)
            bmk_ret730 = pct_return(b_s_pp.close, b_e730_pp.close)
            abn365 = acq_ret365 - bmk_ret365
            abn730 = acq_ret730 - bmk_ret730

            win365 = prices.window(ticker, s_pp.dt, e365_pp.dt)
            win730 = prices.window(ticker, s_pp.dt, e730_pp.dt)
            dd365 = max_drawdown(win365, s_pp.close)
            dd730 = max_drawdown(win730, s_pp.close)

            outcome = 1 if abn730 >= args.threshold else 0
            thesis_hit = 1 if (outcome == 1 and dd365 > args.drawdown_cutoff) else 0

            row_out["entry_price"] = f"{s_pp.close:.6f}"
            row_out["horizon365_price"] = f"{e365_pp.close:.6f}"
            row_out["horizon730_price"] = f"{e730_pp.close:.6f}"
            row_out["benchmark_entry"] = f"{b_s_pp.close:.6f}"
            row_out["benchmark_horizon365"] = f"{b_e365_pp.close:.6f}"
            row_out["benchmark_horizon730"] = f"{b_e730_pp.close:.6f}"
            row_out["acquirer_return_365d"] = f"{acq_ret365:.8f}"
            row_out["acquirer_return_730d"] = f"{acq_ret730:.8f}"
            row_out["benchmark_return_365d"] = f"{bmk_ret365:.8f}"
            row_out["benchmark_return_730d"] = f"{bmk_ret730:.8f}"
            row_out["abnormal_return_365d"] = f"{abn365:.8f}"
            row_out["abnormal_return_730d"] = f"{abn730:.8f}"
            row_out["max_drawdown_365d"] = f"{dd365:.8f}"
            row_out["max_drawdown_730d"] = f"{dd730:.8f}"
            row_out["price_mode"] = f"acq365:{mode365};acq730:{mode730};bmk365:{b_mode365};bmk730:{b_mode730}"
            row_out["outcome_label"] = str(outcome)
            row_out["thesis_hit_label"] = str(thesis_hit)
            row_out["outcome_rule"] = (
                f"completed_abn730_{'>=' if outcome == 1 else '<'}_{args.threshold};"
                f"thesis_hit_if_dd365>{args.drawdown_cutoff}"
            )
            row_out["data_quality_flag"] = "ok"
            labeled += 1
        else:
            _blank_metrics(row_out)
            row_out["price_mode"] = f"acq365:{mode365};acq730:{mode730};bmk365:{b_mode365};bmk730:{b_mode730}"
            row_out["outcome_label"] = ""
            row_out["thesis_hit_label"] = ""
            row_out["outcome_rule"] = "missing_price_data"
            row_out["data_quality_flag"] = "review"
            review += 1

        enriched.append(row_out)

    fieldnames: list[str] = []
    seen: set[str] = set()
    for r in enriched:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in enriched:
            w.writerow(r)

    print(f"wrote {out_path}")
    print(
        " ".join(
            [
                f"rows={len(enriched)}",
                f"completed={completed}",
                f"terminated={terminated}",
                f"labeled={labeled}",
                f"review={review}",
            ]
        )
    )


if __name__ == "__main__":
    main()
