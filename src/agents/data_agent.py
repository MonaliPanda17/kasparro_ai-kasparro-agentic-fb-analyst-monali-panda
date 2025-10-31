from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd


@dataclass
class Period:
    start: pd.Timestamp
    end: pd.Timestamp


def _select_periods(df: pd.DataFrame, window_days: int) -> Tuple[Period, Period]:
    if df["date"].isna().all():
        raise ValueError("All dates are NaT; cannot select periods")
    max_date: pd.Timestamp = df["date"].max()
    cur_end = max_date.normalize()
    cur_start = cur_end - timedelta(days=window_days - 1)
    base_end = cur_start - timedelta(days=1)
    base_start = base_end - timedelta(days=window_days - 1)
    return Period(cur_start, cur_end), Period(base_start, base_end)


def _mask_range(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df["date"] >= start) & (df["date"] <= end)]


def _aggregate_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    spend = float(np.nansum(df["spend"]))
    impressions = float(np.nansum(df["impressions"]))
    clicks = float(np.nansum(df["clicks"]))
    purchases = float(np.nansum(df["purchases"]))
    revenue = float(np.nansum(df["revenue"]))

    ctr = clicks / impressions if impressions > 0 else np.nan
    cpc = spend / clicks if clicks > 0 else np.nan
    cpm = spend / impressions * 1000.0 if impressions > 0 else np.nan
    cvr = purchases / clicks if clicks > 0 else np.nan
    roas = revenue / spend if spend > 0 else np.nan
    aov = revenue / purchases if purchases > 0 else np.nan
    cpa = spend / purchases if purchases > 0 else np.nan

    return {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "purchases": purchases,
        "revenue": revenue,
        "ctr": ctr,
        "cpc": cpc,
        "cpm": cpm,
        "cvr": cvr,
        "roas": roas,
        "aov": aov,
        "cpa": cpa,
    }


def compare_overview(df: pd.DataFrame, window_days: int) -> Dict[str, Any]:
    current, baseline = _select_periods(df, window_days)
    cur_df = _mask_range(df, current.start, current.end)
    base_df = _mask_range(df, baseline.start, baseline.end)

    cur = _aggregate_metrics(cur_df)
    base = _aggregate_metrics(base_df)

    def delta(a: float, b: float) -> float:
        if np.isnan(a) or np.isnan(b):
            return np.nan
        return a - b

    def pct_change(a: float, b: float) -> float:
        if np.isnan(a) or np.isnan(b) or b == 0:
            return np.nan
        return (a - b) / b

    metrics = list(cur.keys())
    deltas = {m: delta(cur[m], base[m]) for m in metrics}
    pct = {m: pct_change(cur[m], base[m]) for m in metrics}

    return {
        "window_days": window_days,
        "current_period": {"start": str(current.start.date()), "end": str(current.end.date())},
        "baseline_period": {"start": str(baseline.start.date()), "end": str(baseline.end.date())},
        "current": cur,
        "baseline": base,
        "delta": deltas,
        "pct_change": pct,
    }


def _group_aggregate(df: pd.DataFrame, by: str) -> pd.DataFrame:
    agg = df.groupby(by, dropna=False).agg(
        spend=("spend", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        purchases=("purchases", "sum"),
        revenue=("revenue", "sum"),
    )
    agg = agg.reset_index().rename(columns={by: "segment"})
    # Rates
    agg["ctr"] = np.where(agg["impressions"] > 0, agg["clicks"] / agg["impressions"], np.nan)
    agg["cvr"] = np.where(agg["clicks"] > 0, agg["purchases"] / agg["clicks"], np.nan)
    agg["roas"] = np.where(agg["spend"] > 0, agg["revenue"] / agg["spend"], np.nan)
    agg["cpa"] = np.where(agg["purchases"] > 0, agg["spend"] / agg["purchases"], np.nan)
    return agg


def segment_compare(df: pd.DataFrame, window_days: int, dim: str, top_n: int = 15) -> Dict[str, Any]:
    current, baseline = _select_periods(df, window_days)
    cur_df = _mask_range(df, current.start, current.end)
    base_df = _mask_range(df, baseline.start, baseline.end)

    cur_g = _group_aggregate(cur_df, dim)
    base_g = _group_aggregate(base_df, dim)

    merged = cur_g.merge(base_g, on="segment", how="outer", suffixes=("_cur", "_base")).fillna(0.0)

    def d(col: str):
        return merged[f"{col}_cur"] - merged[f"{col}_base"]

    out = merged.copy()
    for metric in ["spend", "impressions", "clicks", "purchases", "revenue", "ctr", "cvr", "roas", "cpa"]:
        out[f"{metric}_delta"] = out.get(f"{metric}_cur", np.nan) - out.get(f"{metric}_base", np.nan)
        base_vals = out.get(f"{metric}_base", np.nan)
        cur_vals = out.get(f"{metric}_cur", np.nan)
        with np.errstate(divide='ignore', invalid='ignore'):
            out[f"{metric}_pct_change"] = np.where(base_vals != 0, (cur_vals - base_vals) / base_vals, np.nan)

    total_rev_delta = float(np.nansum(out["revenue_delta"]))
    total_rev_cur = float(np.nansum(out["revenue_cur"]))
    total_rev_base = float(np.nansum(out["revenue_base"]))
    # Contribution shares
    out["share_of_revenue_cur"] = np.where(total_rev_cur > 0, out["revenue_cur"] / total_rev_cur, np.nan)
    out["share_of_revenue_base"] = np.where(total_rev_base > 0, out["revenue_base"] / total_rev_base, np.nan)
    out["share_of_revenue_change"] = np.where(total_rev_delta != 0, out["revenue_delta"] / total_rev_delta, np.nan)

    # Top movers by revenue_delta magnitude
    out_sorted = out.sort_values(by="revenue_delta", ascending=False)
    top_gainers = out_sorted.head(top_n)
    top_losers = out.sort_values(by="revenue_delta", ascending=True).head(top_n)

    cols_to_keep = [
        "segment",
        "revenue_cur", "revenue_base", "revenue_delta", "revenue_pct_change",
        "spend_cur", "spend_base", "spend_delta", "spend_pct_change",
        "roas_cur", "roas_base", "roas_delta", "roas_pct_change",
        "ctr_cur", "ctr_base", "ctr_delta", "ctr_pct_change",
        "cvr_cur", "cvr_base", "cvr_delta", "cvr_pct_change",
        "cpa_cur", "cpa_base", "cpa_delta", "cpa_pct_change",
        "share_of_revenue_cur", "share_of_revenue_base", "share_of_revenue_change",
    ]
    safe_cols = [c for c in cols_to_keep if c in out.columns]

    return {
        "dimension": dim,
        "current_period": {"start": str(current.start.date()), "end": str(current.end.date())},
        "baseline_period": {"start": str(baseline.start.date()), "end": str(baseline.end.date())},
        "top_gainers": top_gainers[safe_cols].to_dict(orient="records"),
        "top_losers": top_losers[safe_cols].to_dict(orient="records"),
    }


def multi_segment_compare(df: pd.DataFrame, window_days: int, dims: List[str], top_n: int = 15) -> Dict[str, Any]:
    results = {}
    for dim in dims:
        try:
            results[dim] = segment_compare(df, window_days, dim, top_n)
        except Exception as e:
            results[dim] = {"error": str(e)}
    return results


