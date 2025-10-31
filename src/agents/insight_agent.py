from __future__ import annotations

from typing import Dict, Any, List, Optional

from src.schema_validator import validate_insights


def _format_delta(v: float) -> str:
    try:
        return f"{v:,.2f}"
    except Exception:
        return "nan"


def _pick_top(entries: List[dict], key: str, n: int, reverse: bool = True) -> List[dict]:
    entries = [e for e in entries if isinstance(e.get(key), (int, float))]
    entries.sort(key=lambda x: x.get(key, 0.0), reverse=reverse)
    return entries[:n]


def _generate_reasoning(
    row: Dict[str, Any], dim: str, overview: Dict[str, Any], is_winner: bool
) -> Dict[str, str]:
    """Generate Think → Analyze → Conclude reasoning structure."""
    segment_name = row.get("segment", "Unknown")
    roas_cur = row.get("roas_cur")
    roas_base = row.get("roas_base")
    revenue_delta = row.get("revenue_delta", 0)
    spend_share = row.get("share_of_revenue_cur", 0) or row.get("share_of_spend_cur", 0)
    
    agg_roas = overview.get("current", {}).get("roas", 0)
    
    if is_winner:
        think = f"Data shows {dim} '{segment_name}' gained ${abs(revenue_delta):,.0f} in revenue with ROAS of {roas_cur:.2f}."
        analyze = f"This segment outperforms aggregate ROAS ({agg_roas:.2f}) by {((roas_cur/agg_roas - 1)*100):.1f}%. Possible factors: effective targeting, strong creative, optimal platform mix, or favorable audience."
        conclude = f"Scale budget allocation to this segment. Evidence: ROAS advantage combined with positive revenue delta. Recommended action: Increase spend by 20-30% to capitalize on performance."
    else:
        think = f"Data shows {dim} '{segment_name}' lost ${abs(revenue_delta):,.0f} with ROAS of {roas_cur:.2f} vs baseline {roas_base:.2f}."
        analyze = f"ROAS declined by {((roas_cur/roas_base - 1)*100):.1f}% while holding {spend_share:.1f}% of spend. Possible causes: creative fatigue, audience dilution, competitive pressure, or platform algorithm changes."
        conclude = f"Reallocate 50-70% of budget from this underperforming segment to winners. Evidence: ROAS gap and negative revenue impact justify reallocation. Immediate action: Pause or reduce spend to test if performance recovers."
    
    return {"think": think, "analyze": analyze, "conclude": conclude}


def _calculate_impact(revenue_delta: float, roas_delta: float, spend_share: float) -> str:
    """Calculate impact level based on metrics."""
    abs_rev_delta = abs(revenue_delta)
    abs_roas_delta = abs(roas_delta)
    
    if (abs_rev_delta > 10000 and spend_share > 0.1) or abs_roas_delta > 2.0:
        return "high"
    elif (abs_rev_delta > 5000 and spend_share > 0.05) or abs_roas_delta > 1.0:
        return "medium"
    else:
        return "low"


def generate_insights(
    overview: Dict[str, Any], segments: Dict[str, Any], plan: Dict[str, Any], top_n: int = 5
) -> List[Dict[str, Any]]:
    insights: List[Dict[str, Any]] = []

    # Overall ROAS/revenue insight with reasoning
    cur = overview.get("current", {})
    base = overview.get("baseline", {})
    delta = overview.get("delta", {})
    pct = overview.get("pct_change", {})

    roas_cur = cur.get("roas")
    roas_base = base.get("roas")
    roas_pct = pct.get("roas")
    revenue_delta = delta.get("revenue")

    roas_change = ((roas_cur - roas_base) / roas_base * 100) if roas_base and roas_base > 0 else 0
    
    title = f"Overall ROAS {'declined' if roas_pct < 0 else 'improved'} by {abs(roas_pct or 0):.1f}% ({roas_cur:.2f} vs {roas_base:.2f})"
    
    reasoning = {
        "think": f"Overall ROAS changed from {roas_base:.2f} to {roas_cur:.2f}, a {abs(roas_pct or 0):.1f}% {'decline' if roas_pct < 0 else 'improvement'}. Revenue {'lost' if revenue_delta < 0 else 'gained'} ${abs(revenue_delta or 0):,.0f}.",
        "analyze": f"This {'performance decline' if roas_pct < 0 else 'improvement'} suggests {'budget misallocation' if roas_pct < 0 else 'effective optimization'}. Multiple factors could contribute: spend shifts, creative changes, audience adjustments, or external market conditions.",
        "conclude": f"{'Investigate root causes' if roas_pct < 0 else 'Maintain winning strategies'} through segment-level analysis. {'Reallocate budget' if roas_pct < 0 else 'Scale successful segments'} based on contribution analysis.",
    }
    
    insights.append({
        "title": title,
        "reasoning": reasoning,
        "metric_delta": {
            "roas_cur": roas_cur,
            "roas_base": roas_base,
            "roas_pct_change": roas_pct,
            "revenue_delta": revenue_delta,
        },
        "segment_filters": {},
        "evidence_refs": ["overview"],
        "confidence": 0.85,
        "impact": _calculate_impact(revenue_delta or 0, roas_change, 1.0),
    })

    # Segment-level insights per dimension: top gainers/losers by revenue_delta
    dims: List[str] = plan.get("segment_dims", [])
    for dim in dims:
        res = segments.get(dim, {})
        top_gainers = res.get("top_gainers", [])
        top_losers = res.get("top_losers", [])

        for row in _pick_top(top_gainers, "revenue_delta", top_n, reverse=True):
            revenue_delta_val = row.get("revenue_delta", 0)
            roas_cur_val = row.get("roas_cur", 0)
            spend_share = row.get("share_of_revenue_cur", 0) or row.get("share_of_spend_cur", 0)
            
            reasoning = _generate_reasoning(row, dim, overview, is_winner=True)
            title = f"{dim}: '{row.get('segment')}' gained ${revenue_delta_val:,.0f} revenue (ROAS {roas_cur_val:.2f})"
            
            insights.append({
                "title": title,
                "reasoning": reasoning,
                "metric_delta": {
                    "revenue_delta": revenue_delta_val,
                    "roas_delta": row.get("roas_delta"),
                    "roas_cur": roas_cur_val,
                    "spend_delta": row.get("spend_delta"),
                    "spend_share": spend_share,
                },
                "segment_filters": {dim: row.get("segment")},
                "evidence_refs": [f"segments:{dim}:top_gainers"],
                "confidence": 0.75 if revenue_delta_val > 5000 else 0.65,
                "impact": _calculate_impact(revenue_delta_val, row.get("roas_delta", 0), spend_share),
            })

        for row in _pick_top(top_losers, "revenue_delta", top_n, reverse=False):
            revenue_delta_val = row.get("revenue_delta", 0)
            roas_cur_val = row.get("roas_cur", 0)
            roas_base_val = row.get("roas_base", 0)
            spend_share = row.get("share_of_revenue_cur", 0) or row.get("share_of_spend_cur", 0)
            
            reasoning = _generate_reasoning(row, dim, overview, is_winner=False)
            title = f"{dim}: '{row.get('segment')}' lost ${abs(revenue_delta_val):,.0f} revenue (ROAS {roas_cur_val:.2f} vs {roas_base_val:.2f})"
            
            insights.append({
                "title": title,
                "reasoning": reasoning,
                "metric_delta": {
                    "revenue_delta": revenue_delta_val,
                    "roas_delta": row.get("roas_delta"),
                    "roas_cur": roas_cur_val,
                    "roas_base": roas_base_val,
                    "spend_delta": row.get("spend_delta"),
                    "spend_share": spend_share,
                },
                "segment_filters": {dim: row.get("segment")},
                "evidence_refs": [f"segments:{dim}:top_losers"],
                "confidence": 0.75 if abs(revenue_delta_val) > 5000 else 0.65,
                "impact": _calculate_impact(revenue_delta_val, row.get("roas_delta", 0), spend_share),
            })

    # Validate insights against schema (non-strict: allows extra fields)
    try:
        validated = validate_insights(insights, strict=False)
        # Convert back to dicts for backward compatibility, but structure is validated
        return [ins.model_dump() for ins in validated]
    except Exception:
        # If validation fails, return original (shouldn't happen in non-strict mode)
        return insights


