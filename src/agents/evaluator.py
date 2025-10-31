from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple


def _validate_quantitative(insight: Dict[str, Any], segments: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """Quantitatively validate insight numbers against evidence data."""
    validation_notes = []
    all_valid = True
    
    metric_delta = insight.get("metric_delta", {})
    evidence_refs = insight.get("evidence_refs", [])
    segment_filters = insight.get("segment_filters", {})
    
    # Check 1: Numeric values are present
    if not metric_delta:
        validation_notes.append("Missing metric_delta - no quantitative data")
        all_valid = False
        return all_valid, validation_notes
    
    # Check 2: Evidence references exist
    if not evidence_refs:
        validation_notes.append("Missing evidence_refs - cannot verify source")
        all_valid = False
    
    # Check 3: Cross-validate percentages (if present)
    if "roas_pct_change" in metric_delta and "roas_cur" in metric_delta and "roas_base" in metric_delta:
        roas_cur = metric_delta.get("roas_cur")
        roas_base = metric_delta.get("roas_base")
        pct_claimed = metric_delta.get("roas_pct_change")
        
        if all(isinstance(x, (int, float)) for x in [roas_cur, roas_base, pct_claimed]):
            if roas_base != 0:
                pct_calculated = ((roas_cur - roas_base) / roas_base) * 100
                pct_diff = abs(pct_calculated - pct_claimed)
                if pct_diff > 1.0:  # Allow 1% tolerance for rounding
                    validation_notes.append(f"ROAS pct_change mismatch: claimed {pct_claimed:.2f}%, calculated {pct_calculated:.2f}%")
                    all_valid = False
                else:
                    validation_notes.append(f"ROAS pct_change validated: {pct_calculated:.2f}%")
    
    # Check 4: Cross-validate with segments data if available
    if segments and segment_filters:
        for dim, seg_value in segment_filters.items():
            if dim in segments:
                dim_data = segments[dim]
                # Try to find matching segment in gainers/losers
                found = False
                for source in ["top_gainers", "top_losers"]:
                    for row in dim_data.get(source, []):
                        if str(row.get("segment")) == str(seg_value):
                            found = True
                            # Validate ROAS if present
                            if "roas_cur" in metric_delta and "roas_cur" in row:
                                if abs(metric_delta["roas_cur"] - row["roas_cur"]) > 0.01:
                                    validation_notes.append(f"ROAS mismatch: insight claims {metric_delta['roas_cur']:.2f}, data shows {row['roas_cur']:.2f}")
                                    all_valid = False
                                else:
                                    validation_notes.append(f"ROAS validated: {row['roas_cur']:.2f}")
                            break
                    if found:
                        break
                if not found:
                    validation_notes.append(f"Segment '{seg_value}' not found in {dim} data")
    
    if not validation_notes:
        validation_notes.append("All quantitative checks passed")
    
    return all_valid, validation_notes


def _score_single(
    insight: Dict[str, Any], segments: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Score insight with quantitative validation."""
    score = {
        "correctness": 0.0,
        "specificity": 0.0,
        "actionability": 0.0,
        "alignment": 0.0,
    }
    
    # Quantitative validation
    quant_valid, validation_notes = _validate_quantitative(insight, segments)
    
    # Correctness: quantitative validation + evidence refs + reasoning
    metric_delta = insight.get("metric_delta", {})
    has_number = any(isinstance(v, (int, float)) for v in metric_delta.values())
    has_refs = bool(insight.get("evidence_refs"))
    has_reasoning = bool(insight.get("reasoning"))
    
    if quant_valid and has_number and has_refs:
        score["correctness"] = 1.0
    elif has_number and has_refs:
        score["correctness"] = 0.7  # Numbers present but not fully validated
    elif has_number or has_refs:
        score["correctness"] = 0.4
    else:
        score["correctness"] = 0.0
    
    # Bonus for reasoning structure
    if has_reasoning:
        reasoning = insight.get("reasoning", {})
        if all(k in reasoning for k in ["think", "analyze", "conclude"]):
            score["correctness"] = min(1.0, score["correctness"] + 0.1)

    # Specificity: concrete details, segment filters, precise numbers
    seg = insight.get("segment_filters", {})
    title = (insight.get("title") or "").lower()
    mentions_metric = any(k in title for k in ["roas", "revenue", "cpa", "ctr"]) or bool(metric_delta)
    
    # Check for specific numbers in title
    has_numbers_in_title = any(c.isdigit() for c in title)
    has_segment_name = any(len(v) > 2 for v in seg.values()) if seg else False
    
    if has_segment_name and has_numbers_in_title:
        score["specificity"] = 1.0
    elif has_segment_name or mentions_metric:
        score["specificity"] = 0.7
    elif mentions_metric:
        score["specificity"] = 0.4
    else:
        score["specificity"] = 0.2

    # Actionability: clear action in reasoning.conclude or title
    is_change = any(k in title for k in ["gained", "lost", "drop", "rise", "decline", "improve", "reallocate", "scale", "pause"])
    
    reasoning = insight.get("reasoning", {})
    conclude = (reasoning.get("conclude", "") or "").lower()
    has_action = any(k in conclude for k in ["reallocate", "increase", "decrease", "pause", "scale", "refresh", "adjust"]) if conclude else False
    
    if has_action or is_change:
        score["actionability"] = 0.9
    elif mentions_metric:
        score["actionability"] = 0.5
    else:
        score["actionability"] = 0.2

    # Alignment: matches problem focus (ROAS, revenue, etc.)
    aligned = ("roas" in title) or ("revenue" in title) or ("cpa" in title) or ("ctr" in title)
    score["alignment"] = 1.0 if aligned else 0.6 if mentions_metric else 0.3

    # Calculate final score
    final = sum(score.values()) / 4.0
    
    # Generate feedback
    strengths = []
    improvements = []
    
    if score["correctness"] >= 0.8:
        strengths.append("Numbers validated and evidence cited")
    else:
        improvements.append("Add quantitative validation or evidence references")
    
    if score["specificity"] >= 0.8:
        strengths.append("Specific segment names and metrics included")
    else:
        improvements.append("Include concrete segment names and numeric values")
    
    if score["actionability"] >= 0.8:
        strengths.append("Clear actionable recommendation")
    else:
        improvements.append("Add specific action (e.g., 'reallocate 50% budget')")
    
    if not strengths:
        strengths.append("Insight structure is present")
    
    return {
        "scores": score,
        "final": final,
        "confidence": final,  # Use final score as confidence
        "feedback": {
            "strengths": strengths,
            "improvements": improvements,
            "validation_notes": validation_notes,
        },
    }


def evaluate_insights(
    insights: List[Dict[str, Any]],
    confidence_min: float = 0.6,
    segments: Optional[Dict[str, Any]] = None,
    enable_reflection: bool = True,
) -> List[Dict[str, Any]]:
    """Evaluate insights with quantitative validation and reflection logic.
    
    Args:
        insights: List of insights to evaluate
        confidence_min: Minimum confidence threshold
        segments: Optional segment data for cross-validation
        enable_reflection: If True, flag low-confidence insights for retry
    """
    evaluated = []
    needs_retry = []
    
    for ins in insights:
        s = _score_single(ins, segments)
        
        # Merge evaluation into insight
        out = {
            **ins,
            "evaluation": s,
            "confidence": max(ins.get("confidence", 0.0), s["confidence"]),
        }
        
        # Reflection logic: flag for retry if confidence too low
        if enable_reflection and out["confidence"] < confidence_min:
            out["needs_retry"] = True
            out["retry_reason"] = f"Confidence {out['confidence']:.2f} below threshold {confidence_min:.2f}"
            needs_retry.append(out)
        else:
            out["needs_retry"] = False
        
        evaluated.append(out)
    
    # Sort by final score descending
    evaluated.sort(key=lambda x: x["evaluation"]["final"], reverse=True)
    
    # Filter out low-confidence insights (but keep them for reporting)
    validated = [e for e in evaluated if e["confidence"] >= confidence_min]
    
    return {
        "validated": validated,
        "all_insights": evaluated,
        "needs_retry": needs_retry,
        "summary": {
            "total": len(insights),
            "validated": len(validated),
            "low_confidence": len(needs_retry),
            "avg_confidence": sum(e["confidence"] for e in evaluated) / len(evaluated) if evaluated else 0.0,
        },
    }


