from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


EXPECTED_COLUMNS = [
    "campaign_name",
    "adset_name",
    "date",
    "spend",
    "impressions",
    "clicks",
    "ctr",
    "purchases",
    "revenue",
    "roas",
    "creative_type",
    "creative_message",
    "audience_type",
    "platform",
    "country",
]


@dataclass
class LoadResult:
    df: pd.DataFrame
    source_path: str
    notes: list[str]


def _coerce_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _normalize_campaign_name(name: str) -> str:
    if not isinstance(name, str):
        return name
    collapsed = " ".join(name.replace("_", " ").split())
    return collapsed.strip().title()


def load_csv(csv_path: Optional[str]) -> LoadResult:
    notes: list[str] = []

    if csv_path is None or not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)

    # Basic schema validation
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Parse and coerce types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    numeric_cols = ["spend", "impressions", "clicks", "ctr", "purchases", "revenue", "roas"]
    for col in numeric_cols:
        df[col] = _coerce_numeric(df[col])

    # Replace NaN with 0 for numeric columns (user requested)
    df[numeric_cols] = df[numeric_cols].fillna(0.0)

    # Normalizations
    df["campaign_name"] = df["campaign_name"].map(_normalize_campaign_name)

    # Derived metrics (use 0 instead of NaN when denominator is 0)
    # CPC: spend / clicks  (0 when clicks == 0)
    df["cpc"] = np.where(df["clicks"] > 0, df["spend"] / df["clicks"], 0.0)

    # CPM: (spend / impressions) * 1000  (0 when impressions == 0)
    df["cpm"] = np.where(df["impressions"] > 0, df["spend"] / df["impressions"] * 1000.0, 0.0)

    # CVR: purchases / clicks  (0 when clicks == 0)
    df["cvr"] = np.where(df["clicks"] > 0, df["purchases"] / df["clicks"], 0.0)

    # Recompute ROAS where spend > 0; otherwise 0
    recomputed_roas = np.where(df["spend"] > 0, df["revenue"] / df["spend"], 0.0)

    # Use existing roas if it is non-zero, otherwise use recomputed_roas.
    # This updates the single 'roas' column in-place (no new columns added).
    df["roas"] = np.where(df["roas"] != 0.0, df["roas"], recomputed_roas)

    # Data quality notes (after NaN->0 conversion)
    zero_spend_count = int((df["spend"] == 0).sum())
    if zero_spend_count > 0:
        notes.append(f"{zero_spend_count} rows have spend == 0; these were set to 0 after cleaning.")
    if df["date"].isna().any():
        notes.append("Some rows have invalid dates and were set to NaT.")

    # Decide which rows to drop:
    # Current rule: drop rows that are *completely empty* in all main numeric fields:
    main_numeric = ["spend", "impressions", "clicks", "purchases", "revenue", "roas"]
    all_zero_mask = (df[main_numeric] == 0.0).all(axis=1)

    # campaign_name missing check: treat empty string or whitespace as missing
    camp_missing_mask = df["campaign_name"].isna() | (df["campaign_name"].astype(str).str.strip() == "")

    date_missing_mask = df["date"].isna()

    conservative_drop_mask = all_zero_mask & (date_missing_mask | camp_missing_mask)
    dropped_count = int(conservative_drop_mask.sum())

    if dropped_count > 0:
        notes.append(
            f"Dropped {dropped_count} rows by conservative rule: all main numerics == 0 and (date missing OR campaign_name missing)."
        )
        # optionally: save dropped rows somewhere or keep a copy for audit
        # dropped_rows = df.loc[conservative_drop_mask].copy()
        df = df.loc[~conservative_drop_mask].reset_index(drop=True)

    # 7) Data quality notes (post-processing)
    if (df["spend"] == 0).any():
        notes.append("Some rows have spend == 0 after cleaning (these remain in dataset unless they met conservative drop criteria).")
    if df["date"].isna().any():
        notes.append("Some rows have invalid dates and were set to NaT (not dropped).") 

    return LoadResult(df=df, source_path=csv_path, notes=notes)



def resolve_data_path(use_sample: bool, sample_path: str, env_var: str) -> Optional[str]:
    if use_sample:
        return sample_path if os.path.exists(sample_path) else None
    return os.getenv(env_var)


def generate_data_summary(df: pd.DataFrame, top_n: int = 5) -> dict:
    """Generate a comprehensive summary JSON from the DataFrame for planner agent.
    
    Returns a structured summary with:
    - Date range and coverage
    - Overall metrics
    - Top segments by dimension
    - Key patterns
    """
    summary: dict = {
        "date_range": {},
        "overall_metrics": {},
        "top_segments": {},
        "data_quality": {},
    }
    
    if df.empty:
        return summary
    
    # Date range
    if "date" in df.columns and not df["date"].isna().all():
        valid_dates = df[df["date"].notna()]["date"]
        if not valid_dates.empty:
            summary["date_range"] = {
                "min": str(valid_dates.min().date()),
                "max": str(valid_dates.max().date()),
                "days_covered": int((valid_dates.max() - valid_dates.min()).days + 1),
                "total_rows": len(df),
            }
    
    # Overall metrics
    numeric_cols = ["spend", "impressions", "clicks", "purchases", "revenue", "roas"]
    for col in numeric_cols:
        if col in df.columns:
            col_data = df[col].replace([np.inf, -np.inf], np.nan)
            summary["overall_metrics"][col] = {
                "total": float(col_data.sum()),
                "mean": float(col_data.mean()) if not col_data.isna().all() else None,
                "median": float(col_data.median()) if not col_data.isna().all() else None,
                "min": float(col_data.min()) if not col_data.isna().all() else None,
                "max": float(col_data.max()) if not col_data.isna().all() else None,
            }
    
    # Derived overall metrics
    total_spend = summary["overall_metrics"].get("spend", {}).get("total", 0)
    total_revenue = summary["overall_metrics"].get("revenue", {}).get("total", 0)
    total_clicks = summary["overall_metrics"].get("clicks", {}).get("total", 0)
    total_impressions = summary["overall_metrics"].get("impressions", {}).get("total", 0)
    total_purchases = summary["overall_metrics"].get("purchases", {}).get("total", 0)
    
    summary["overall_metrics"]["aggregate_roas"] = (
        total_revenue / total_spend if total_spend > 0 else None
    )
    summary["overall_metrics"]["aggregate_ctr"] = (
        total_clicks / total_impressions if total_impressions > 0 else None
    )
    summary["overall_metrics"]["aggregate_cvr"] = (
        total_purchases / total_clicks if total_clicks > 0 else None
    )
    summary["overall_metrics"]["aggregate_cpa"] = (
        total_spend / total_purchases if total_purchases > 0 else None
    )
    
    # Top segments by dimension
    segment_dims = ["campaign_name", "adset_name", "platform", "country", "creative_type", "audience_type"]
    
    for dim in segment_dims:
        if dim not in df.columns:
            continue
        
        # Top by spend
        spend_top = df.groupby(dim)["spend"].sum().sort_values(ascending=False).head(top_n)
        revenue_top = df.groupby(dim)["revenue"].sum().sort_values(ascending=False).head(top_n)
        
        # Calculate ROAS for top spenders
        spend_segments = []
        for seg_name in spend_top.index:
            seg_df = df[df[dim] == seg_name]
            seg_spend = seg_df["spend"].sum()
            seg_revenue = seg_df["revenue"].sum()
            seg_roas = seg_revenue / seg_spend if seg_spend > 0 else 0
            spend_segments.append({
                "name": str(seg_name),
                "spend": float(seg_spend),
                "revenue": float(seg_revenue),
                "roas": float(seg_roas),
                "share_of_spend": float(seg_spend / total_spend * 100) if total_spend > 0 else 0,
            })
        
        revenue_segments = []
        for seg_name in revenue_top.index:
            seg_df = df[df[dim] == seg_name]
            seg_revenue = seg_df["revenue"].sum()
            seg_spend = seg_df["spend"].sum()
            seg_roas = seg_revenue / seg_spend if seg_spend > 0 else 0
            revenue_segments.append({
                "name": str(seg_name),
                "spend": float(seg_spend),
                "revenue": float(seg_revenue),
                "roas": float(seg_roas),
                "share_of_revenue": float(seg_revenue / total_revenue * 100) if total_revenue > 0 else 0,
            })
        
        summary["top_segments"][dim] = {
            "top_by_spend": spend_segments,
            "top_by_revenue": revenue_segments,
        }
    
    # Data quality metrics
    summary["data_quality"] = {
        "rows_with_zero_spend": int((df["spend"] == 0).sum()),
        "rows_with_missing_date": int(df["date"].isna().sum()),
        "unique_campaigns": int(df["campaign_name"].nunique()) if "campaign_name" in df.columns else 0,
        "unique_platforms": int(df["platform"].nunique()) if "platform" in df.columns else 0,
        "unique_countries": int(df["country"].nunique()) if "country" in df.columns else 0,
    }
    
    return summary

