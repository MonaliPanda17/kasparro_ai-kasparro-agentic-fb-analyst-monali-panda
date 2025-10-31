from __future__ import annotations

from typing import Dict, Any, List, Optional


def _find_low_ctr_campaigns(
    segments: Dict[str, Any], overview: Optional[Dict[str, Any]] = None, min_spend: float = 1000.0
) -> List[Dict[str, Any]]:
    """Identify low-CTR campaigns/adsets that need creative refresh."""
    low_ctr_targets = []
    
    # Calculate median CTR from overview or segments
    all_ctrs = []
    for dim in ["campaign_name", "adset_name"]:
        if dim in segments:
            dim_data = segments[dim]
            for row in dim_data.get("top_gainers", []) + dim_data.get("top_losers", []):
                ctr_cur = row.get("ctr_cur")
                if isinstance(ctr_cur, (int, float)) and ctr_cur > 0:
                    all_ctrs.append(ctr_cur)
    
    median_ctr = sorted(all_ctrs)[len(all_ctrs) // 2] if all_ctrs else 0.015
    ctr_threshold = median_ctr * 0.8  # Below 80% of median
    
    # Find campaigns/adsets with low CTR and sufficient spend
    for dim in ["campaign_name", "adset_name"]:
        if dim in segments:
            dim_data = segments[dim]
            for row in dim_data.get("top_losers", []) + dim_data.get("top_gainers", []):
                ctr_cur = row.get("ctr_cur", 0)
                spend_cur = row.get("spend_cur", 0)
                roas_cur = row.get("roas_cur", 0)
                
                if (ctr_cur < ctr_threshold or ctr_cur < 0.015) and spend_cur >= min_spend:
                    low_ctr_targets.append({
                        "segment_type": dim,
                        "segment_name": row.get("segment"),
                        "ctr": ctr_cur,
                        "roas": roas_cur,
                        "spend": spend_cur,
                        "platform": segments.get("platform", {}).get("top_by_spend", [{}])[0].get("name") if "platform" in segments else None,
                        "country": segments.get("country", {}).get("top_by_spend", [{}])[0].get("name") if "country" in segments else None,
                    })
                    if len(low_ctr_targets) >= 5:
                        break
            if len(low_ctr_targets) >= 5:
                break
    
    return sorted(low_ctr_targets, key=lambda x: x["spend"], reverse=True)


def _find_winning_patterns(segments: Dict[str, Any]) -> Dict[str, Any]:
    """Extract winning creative patterns from high-performing segments."""
    patterns = {
        "creative_types": [],
        "messages": [],
        "platforms": [],
        "countries": [],
    }
    
    # Find top creative types by ROAS
    if "creative_type" in segments:
        creative_data = segments["creative_type"]
        top_creatives = sorted(
            creative_data.get("top_gainers", []),
            key=lambda x: float(x.get("roas_cur", 0)),
            reverse=True,
        )[:3]
        patterns["creative_types"] = [r.get("segment") for r in top_creatives if r.get("segment")]
    
    # Top platforms
    if "platform" in segments:
        platform_data = segments["platform"]
        top_platforms = sorted(
            platform_data.get("top_gainers", []),
            key=lambda x: float(x.get("roas_cur", 0)),
            reverse=True,
        )[:2]
        patterns["platforms"] = [r.get("segment") for r in top_platforms if r.get("segment")]
    
    # Top countries
    if "country" in segments:
        country_data = segments["country"]
        top_countries = sorted(
            country_data.get("top_gainers", []),
            key=lambda x: float(x.get("roas_cur", 0)),
            reverse=True,
        )[:3]
        patterns["countries"] = [r.get("segment") for r in top_countries if r.get("segment")]
    
    return patterns


def generate_creatives(
    segments: Dict[str, Any],
    overview: Optional[Dict[str, Any]] = None,
    validated_insights: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Generate creative recommendations for low-CTR campaigns.
    
    Args:
        segments: Segment comparison data
        overview: Optional overview metrics
        validated_insights: Optional validated insights to inform creative strategy
    """
    creatives = []
    
    # Find low-CTR targets
    low_ctr_targets = _find_low_ctr_campaigns(segments, overview, min_spend=1000.0)
    
    # Find winning patterns to adapt
    winning_patterns = _find_winning_patterns(segments)
    
    # Creative templates with reasoning
    templates = [
        {
            "hook": "90% of customers switch after trying these — here's why",
            "body": "Seamless comfort that moves with you. No ride-up, no bunching, all-day freedom. Made with breathable organic cotton.",
            "cta": "Shop the 3-pack deal",
            "strategy": "social_proof",
        },
        {
            "hook": "Stop the ride-up. Stop the bunching. Start the comfort.",
            "body": "Show the comfort in motion. Spotlight sweat-wicking fabric in a real-life demo.",
            "cta": "Shop now",
            "strategy": "problem_solve",
        },
        {
            "hook": "No Ride-Up Guarantee — try risk-free",
            "body": "Call out the guarantee and pair with a 10s UGC testimonial clip.",
            "cta": "Try risk-free",
            "strategy": "guarantee",
        },
        {
            "hook": "Seamless Under Everything",
            "body": "Contrast before/after silhouettes. Emphasize invisible seams and breathable cotton.",
            "cta": "See the fit",
            "strategy": "visual_benefit",
        },
    ]
    
    # Generate creatives for each low-CTR target
    for target in low_ctr_targets[:5]:  # Top 5 low-CTR campaigns
        # Use winning platform/country if available, otherwise use target's
        platform = target.get("platform") or (winning_patterns["platforms"][0] if winning_patterns["platforms"] else "Facebook")
        country = target.get("country") or (winning_patterns["countries"][0] if winning_patterns["countries"] else "US")
        creative_type = winning_patterns["creative_types"][0] if winning_patterns["creative_types"] else "Image"
        
        # Select template based on target's current performance
        if target["roas"] < 2.0:
            # Very low ROAS - use social proof
            template = templates[0]
        elif target["ctr"] < 0.01:
            # Very low CTR - use problem-solve
            template = templates[1]
        else:
            # Moderate - use guarantee or visual
            template = templates[2] if target["roas"] < 3.0 else templates[3]
        
        # Calculate expected improvement
        current_ctr = target["ctr"]
        # Aim for 30-50% CTR improvement based on winning patterns
        target_ctr = current_ctr * 1.4
        
        creatives.append({
            "target_campaign": target["segment_name"],
            "target_segment": {
                "platform": platform,
                "country": country,
                "audience_type": "Broad",  # Default, could be extracted
            },
            "current_performance": {
                "ctr": current_ctr,
                "roas": target["roas"],
                "spend": target["spend"],
            },
            "creative": {
                "hook": template["hook"],
                "body": template["body"],
                "cta": template["cta"],
            },
            "rationale": f"Campaign '{target['segment_name']}' has CTR {current_ctr:.4f} (below threshold) with ${target['spend']:,.0f} spend. Adapting '{template['strategy']}' strategy from top-performing creatives. Expected to improve CTR through {template['strategy']} messaging.",
            "expected_improvement": {
                "ctr_target": target_ctr,
                "confidence": 0.7 if current_ctr < 0.012 else 0.6,
            },
        })
    
    # If no low-CTR targets found, generate general recommendations
    if not creatives and winning_patterns["platforms"]:
        platform = winning_patterns["platforms"][0]
        country = winning_patterns["countries"][0] if winning_patterns["countries"] else "US"
        creative_type = winning_patterns["creative_types"][0] if winning_patterns["creative_types"] else "Image"
        
        for template in templates[:3]:
            creatives.append({
                "target_campaign": "General recommendation",
                "target_segment": {
                    "platform": platform,
                    "country": country,
                    "audience_type": "Broad",
                },
                "current_performance": {
                    "ctr": 0.015,
                    "roas": 3.0,
                    "spend": 0,
                },
                "creative": {
                    "hook": template["hook"],
                    "body": template["body"],
                    "cta": template["cta"],
                },
                "rationale": f"Based on top-performing patterns: {platform} + {country} + {creative_type}. Use this template for new campaigns.",
                "expected_improvement": {
                    "ctr_target": 0.018,
                    "confidence": 0.65,
                },
            })
    
    return creatives[:6]


