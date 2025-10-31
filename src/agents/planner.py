from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

PRIMARY_KPIS = ["roas", "revenue", "cpa", "ctr"]
# Default problem types (can be overridden via config)
DEFAULT_PROBLEM_TYPES = ["roas_drop", "revenue_decline", "cpa_spike", "ctr_decline", "performance_issue"]


def _classify_problem(task: str) -> Tuple[str, List[str]]:
    """Classify the problem type and return relevant hypotheses."""
    task_l = task.lower()
    
    # Problem types
    if any(k in task_l for k in ["roas", "return on ad spend", "return on spend"]):
        problem_type = "roas_drop"
        hypotheses = [
            "Budget shifted to lower-ROAS segments (campaigns/adsets/countries)",
            "Creative fatigue: older creatives losing effectiveness",
            "Audience dilution: targeting broadened, quality declined",
            "Platform mix changed: budget moved to lower-ROAS platforms",
            "Spend efficiency: CVR or AOV declined while spend increased"
        ]
        return problem_type, hypotheses
    
    if any(k in task_l for k in ["revenue", "sales", "income"]):
        problem_type = "revenue_decline"
        hypotheses = [
            "Total spend decreased",
            "ROAS declined across segments",
            "High-revenue segments underperforming",
            "Volume drop: fewer purchases despite similar spend"
        ]
        return problem_type, hypotheses
    
    if any(k in task_l for k in ["cpa", "cost per acquisition", "cost per purchase", "acquisition cost"]):
        problem_type = "cpa_spike"
        hypotheses = [
            "Conversion funnel: CTR or CVR declined",
            "Audience quality: targeting less qualified users",
            "Creative relevance: messages not resonating",
            "Platform mix: shifted to higher-CPA channels"
        ]
        return problem_type, hypotheses
    
    if any(k in task_l for k in ["ctr", "click-through", "click rate", "engagement"]):
        problem_type = "ctr_decline"
        hypotheses = [
            "Creative fatigue: messages no longer compelling",
            "Audience mismatch: wrong targeting",
            "Competitive landscape: more competition for attention",
            "Platform algorithm: lower organic reach"
        ]
        return problem_type, hypotheses
    
    # Additional problem types
    if any(k in task_l for k in ["budget", "spend allocation", "spend distribution", "budget optimization"]):
        problem_type = "budget_allocation"
        hypotheses = [
            "Budget concentrated in low-ROAS segments",
            "High-performing segments underfunded",
            "Platform budget mix suboptimal",
            "Campaign-level spend inefficiency"
        ]
        return problem_type, hypotheses
    
    if any(k in task_l for k in ["creative", "ad creative", "creative test", "creative performance"]):
        problem_type = "creative_performance"
        hypotheses = [
            "Creative fatigue: older creatives declining",
            "Creative type mix suboptimal",
            "Message relevance declining",
            "New creative opportunities identified"
        ]
        return problem_type, hypotheses
    
    if any(k in task_l for k in ["audience", "targeting", "audience quality", "audience performance"]):
        problem_type = "audience_quality"
        hypotheses = [
            "Audience dilution: targeting too broad",
            "Lookalike audiences underperforming",
            "Retargeting effectiveness declining",
            "New audience segments to test"
        ]
        return problem_type, hypotheses
    
    if any(k in task_l for k in ["seasonal", "season", "time period", "month over month", "yoy"]):
        problem_type = "seasonal_analysis"
        hypotheses = [
            "Seasonal patterns affecting performance",
            "Period-over-period comparison needed",
            "Cyclical trends in metrics",
            "Timing-based optimization opportunities"
        ]
        return problem_type, hypotheses
    
    # Default: general performance issue
    problem_type = "performance_issue"
    hypotheses = [
        "Multi-dimensional: check ROAS, revenue, CPA, CTR holistically",
        "Budget allocation: spend mix shifted",
        "Segment-specific: certain campaigns/adsets/platforms underperforming"
    ]
    return problem_type, hypotheses


def _extract_window_days(task: str, allowed: List[int]) -> int:
    task_l = task.lower()
    # Look for explicit numbers like "last 7 days", "past 14d"
    m = re.search(r"(last|past)\s*(\d{1,3})\s*(days|day|d)", task_l)
    if m:
        value = int(m.group(2))
        # Choose closest allowed window
        return min(allowed, key=lambda x: abs(x - value))
    # Heuristic by keywords
    if any(k in task_l for k in ["week", "7d", "7 days", "last week"]):
        return 7 if 7 in allowed else allowed[0]
    if any(k in task_l for k in ["fortnight", "14d", "2 weeks"]):
        return 14 if 14 in allowed else allowed[0]
    if any(k in task_l for k in ["month", "28d", "30d"]):
        # prefer 28 if present
        if 28 in allowed:
            return 28
        return min(allowed, key=lambda x: abs(x - 30))
    # Default to smallest window for responsiveness
    return min(allowed)


def _choose_kpis(task: str, problem_type: str) -> List[str]:
    """Choose KPIs based on problem type and task keywords."""
    task_l = task.lower()
    kpis: List[str] = []
    
    # Problem-specific KPI selection
    if problem_type == "roas_drop":
        kpis.append("roas")  # Primary
        kpis.append("revenue")  # To see if it's revenue or spend issue
        kpis.append("cpa")  # Inverse of ROAS, helps diagnose
        if "spend" in task_l or "budget" in task_l:
            # Add spend efficiency metrics
            pass  # Already have ROAS/CPA
    
    elif problem_type == "revenue_decline":
        kpis.append("revenue")  # Primary
        kpis.append("roas")  # Efficiency driver
        kpis.append("cpa")  # Cost side
    
    elif problem_type == "cpa_spike":
        kpis.append("cpa")  # Primary
        kpis.append("ctr")  # Funnel metric
        kpis.append("cvr")  # Conversion side
        kpis.append("roas")  # Overall efficiency
    
    elif problem_type == "ctr_decline":
        kpis.append("ctr")  # Primary
        kpis.append("cvr")  # Funnel completeness
        kpis.append("cpa")  # Impact on cost
    
    else:
        # General: look at everything
        kpis.append("roas")
        kpis.append("revenue")
    
    # Override with explicit mentions
    explicit_kpis = []
    if "roas" in task_l:
        explicit_kpis.append("roas")
    if any(x in task_l for x in ["revenue", "sales"]):
        explicit_kpis.append("revenue")
    if any(x in task_l for x in ["cpa", "cost per acquisition", "cost/purchase"]):
        explicit_kpis.append("cpa")
    if any(x in task_l for x in ["ctr", "click-through", "click through"]):
        explicit_kpis.append("ctr")
    
    # Prefer explicit, but merge intelligently
    if explicit_kpis:
        # Add explicit first, then problem-specific if not already there
        result = explicit_kpis.copy()
        for kpi in kpis:
            if kpi not in result:
                result.append(kpi)
        kpis = result
    
    # Remove duplicates while preserving order
    seen = set()
    ordered = []
    for k in kpis:
        if k not in seen:
            ordered.append(k)
            seen.add(k)
    
    # Fallback if empty
    if not ordered:
        ordered = ["roas", "revenue"]
    
    return ordered


def _choose_segments(available: List[str], problem_type: str) -> List[str]:
    """Prioritize segments based on problem type and analyst logic."""
    
    # Analyst thinking: Order by actionability and signal strength
    # Most actionable: campaign > adset > creative_type > audience_type > platform > country
    
    base_priority = [
        "campaign_name",      # Can pause/scale campaigns
        "adset_name",          # Can adjust adset budgets/targeting
        "creative_type",        # Can refresh creatives
        "audience_type",       # Can refine targeting
        "platform",            # Can reallocate budget
        "country",             # Can geo-pause (less common)
    ]
    
    # Problem-specific adjustments
    if problem_type == "roas_drop":
        # ROAS issues: prioritize where budget is (campaign/adset) and creative quality
        priority = ["campaign_name", "adset_name", "creative_type", "platform", "audience_type", "country"]
    elif problem_type == "revenue_decline":
        # Revenue: focus on spend allocation and volume drivers
        priority = ["campaign_name", "adset_name", "platform", "country", "creative_type", "audience_type"]
    elif problem_type == "cpa_spike":
        # CPA: focus on audience and creative quality
        priority = ["audience_type", "creative_type", "campaign_name", "adset_name", "platform", "country"]
    elif problem_type == "ctr_decline":
        # CTR: creative and audience are key
        priority = ["creative_type", "audience_type", "campaign_name", "platform", "adset_name", "country"]
    else:
        priority = base_priority
    
    # Return segments in priority order that exist in available
    result = [d for d in priority if d in available]
    # Add any remaining available segments not in priority
    for d in available:
        if d not in result:
            result.append(d)
    
    return result


def _call_llm_planner(
    task: str, data_summary: Optional[Dict[str, Any]], config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Call LLM to generate plan with structured output validation."""
    llm_cfg = config.get("llm", {})
    provider = llm_cfg.get("provider", "").lower()
    model = llm_cfg.get("model", "gpt-4o-mini")
    temperature = float(llm_cfg.get("temperature", 0.2))
    max_retries = int(llm_cfg.get("max_retries", 2))
    timeout = int(llm_cfg.get("timeout_seconds", 10))

    if provider != "openai":
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=timeout)

        # Load prompt template
        prompt_path = Path("prompts/planner.md")
        if not prompt_path.exists():
            return None

        prompt_template = prompt_path.read_text(encoding="utf-8")

        # Build prompt
        data_summary_str = json.dumps(data_summary, indent=2) if data_summary else "No data summary available"
        allowed_windows = config.get("time_windows", [7, 14, 28])
        available_segments = config.get("segment_dims", [])

        full_prompt = f"""{prompt_template}

## Current Input
**Task**: {task}
**Allowed Windows**: {allowed_windows}
**Available Segments**: {available_segments}
**Data Summary**: {data_summary_str}

**IMPORTANT**: Include "subtasks" array in your response. Each subtask should specify:
- task_id: unique identifier
- agent: which agent executes (data_agent, insight_agent, evaluator_agent, creative_generator)
- action: what action to perform
- description: what it does
- inputs: list of required inputs
- outputs: list of outputs it produces

Return ONLY valid JSON matching the output format above. Do not include markdown code blocks.
"""

        # Retry logic with exponential backoff
        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert Facebook Ads Performance Analyst. Always return valid JSON."},
                        {"role": "user", "content": full_prompt},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )

                result_text = response.choices[0].message.content
                plan_json = json.loads(result_text)

                # Validate output
                if _validate_llm_plan(plan_json, config):
                    plan_json["plan_source"] = "llm"
                    return plan_json

            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                # Last attempt failed
                break

    except Exception:
        pass

    return None


def _decompose_into_subtasks(problem_type: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate subtask decomposition for the problem type."""
    base_subtasks = [
        {
            "task_id": "data_load",
            "agent": "data_agent",
            "action": "load_and_summarize",
            "description": "Load dataset and generate overview metrics",
            "inputs": ["csv_path"],
            "outputs": ["overview_metrics"],
        },
        {
            "task_id": "data_segment",
            "agent": "data_agent",
            "action": "segment_compare",
            "description": "Compare segments across dimensions",
            "inputs": ["overview_metrics", "segment_dims"],
            "outputs": ["segment_tables"],
        },
        {
            "task_id": "insight_gen",
            "agent": "insight_agent",
            "action": "generate_hypotheses",
            "description": "Generate insights from segment data",
            "inputs": ["segment_tables", "plan"],
            "outputs": ["insights"],
        },
        {
            "task_id": "eval_validate",
            "agent": "evaluator_agent",
            "action": "validate_insights",
            "description": "Quantitatively validate insights",
            "inputs": ["insights", "segment_tables"],
            "outputs": ["validated_insights"],
        },
        {
            "task_id": "creative_gen",
            "agent": "creative_generator",
            "action": "generate_for_low_ctr",
            "description": "Generate creatives for low-CTR campaigns",
            "inputs": ["validated_insights", "segment_tables"],
            "outputs": ["creative_recommendations"],
        },
    ]
    
    # Add problem-specific subtasks
    if problem_type == "ctr_decline":
        base_subtasks.insert(-1, {
            "task_id": "creative_analysis",
            "agent": "data_agent",
            "action": "analyze_creative_performance",
            "description": "Deep dive into creative type performance",
            "inputs": ["segment_tables"],
            "outputs": ["creative_analysis"],
        })
    
    return base_subtasks


def _validate_llm_plan(plan: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Validate LLM-generated plan against requirements."""
    # Required fields
    required = ["problem_type", "hypotheses", "time_window_days", "primary_kpis", "segment_dims"]
    if not all(field in plan for field in required):
        return False

    # Problem type validation (flexible: configurable list + optional custom types)
    planner_cfg = config.get("planner", {})
    allowed_types = planner_cfg.get("problem_types", DEFAULT_PROBLEM_TYPES)
    allow_custom = bool(planner_cfg.get("allow_custom_problem_types", True))
    
    problem_type = plan["problem_type"]
    
    # Must be a string
    if not isinstance(problem_type, str) or len(problem_type) < 3:
        return False
    
    # Check if it's in allowed list OR custom types are allowed
    if problem_type not in allowed_types:
        if not allow_custom:
            return False
        # Custom type allowed - validate it's reasonable (alphanumeric + underscore, not too long)
        if not re.match(r"^[a-z][a-z0-9_]{1,30}$", problem_type):
            return False

    # Hypotheses validation
    if not isinstance(plan["hypotheses"], list) or len(plan["hypotheses"]) == 0:
        return False
    if not all(isinstance(h, str) and len(h) > 10 for h in plan["hypotheses"]):
        return False

    # Time window validation
    allowed_windows = config.get("time_windows", [7, 14, 28])
    if plan["time_window_days"] not in allowed_windows:
        return False

    # KPIs validation
    if not isinstance(plan["primary_kpis"], list) or len(plan["primary_kpis"]) == 0:
        return False
    if not all(kpi in PRIMARY_KPIS for kpi in plan["primary_kpis"]):
        return False

    # Segments validation
    available_segments = config.get("segment_dims", [])
    if not isinstance(plan["segment_dims"], list) or len(plan["segment_dims"]) == 0:
        return False
    if not all(seg in available_segments for seg in plan["segment_dims"]):
        return False

    # Subtasks validation (optional but recommended)
    if "subtasks" in plan:
        if not isinstance(plan["subtasks"], list):
            return False
        # Validate subtask structure if present
        for subtask in plan["subtasks"]:
            if not isinstance(subtask, dict):
                return False
            required_fields = ["task_id", "agent", "action", "description"]
            if not all(field in subtask for field in required_fields):
                return False

    return True


def _plan_rule_based(task: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback rule-based planner (original logic)."""
    allowed_windows: List[int] = list(config.get("time_windows", [7, 14, 28]))
    segments_available: List[str] = list(config.get("segment_dims", []))

    problem_type, hypotheses = _classify_problem(task)
    window_days = _extract_window_days(task, allowed_windows)
    kpis = _choose_kpis(task, problem_type)
    segments = _choose_segments(segments_available, problem_type)
    subtasks = _decompose_into_subtasks(problem_type, config)

    return {
        "task": task,
        "problem_type": problem_type,
        "reasoning": {
            "think": f"User query: {task}. Problem classified as {problem_type}.",
            "analyze": f"Focus on {', '.join(kpis)} metrics across {', '.join(segments[:3])} dimensions.",
            "conclude": f"Execute {len(subtasks)} subtasks to generate insights and recommendations.",
        },
        "subtasks": subtasks,
        "hypotheses": hypotheses,
        "time_window_days": window_days,
        "primary_kpis": kpis,
        "segment_dims": segments,
        "analysis_strategy": _get_analysis_strategy(problem_type),
        "plan_source": "rule_based",
    }


def plan(
    task: str, config: Dict[str, Any], data_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Hybrid planner: try LLM first, fallback to rule-based.
    
    Args:
        task: User query/question
        config: Configuration dict
        data_summary: Optional data summary JSON (recommended for LLM planner)
    
    Returns:
        Analysis plan dict with 'plan_source' field indicating 'llm' or 'rule_based'
    """
    llm_cfg = config.get("llm", {})
    use_llm = bool(llm_cfg.get("use_llm_planner", False))

    # Try LLM planner if enabled
    if use_llm and data_summary:
        llm_plan = _call_llm_planner(task, data_summary, config)
        if llm_plan:
            return llm_plan

    # Fallback to rule-based
    return _plan_rule_based(task, config)


def _get_analysis_strategy(problem_type: str) -> str:
    """Return analysis strategy description for the problem type."""
    strategies = {
        "roas_drop": "Focus on contribution analysis: which segments drove ROAS decline? Check spend shifts, creative performance, and platform mix.",
        "revenue_decline": "Analyze revenue drivers: total spend changes, ROAS efficiency, and volume (purchases) per segment.",
        "cpa_spike": "Funnel analysis: diagnose CTR and CVR changes. Check audience quality and creative relevance.",
        "ctr_decline": "Creative and audience focus: identify fatigued creatives and audience mismatches.",
        "performance_issue": "Holistic review: examine ROAS, revenue, CPA, and CTR across all segments to identify root cause.",
        "budget_allocation": "Analyze spend distribution across campaigns/adsets/platforms. Identify optimization opportunities for budget reallocation.",
        "creative_performance": "Compare creative types and messages. Identify top performers and refresh underperforming creatives.",
        "audience_quality": "Evaluate audience segments by conversion rates and cost efficiency. Refine targeting strategies.",
        "seasonal_analysis": "Compare performance across time periods. Identify seasonal patterns and adjust strategy accordingly.",
    }
    # Default strategy for unknown types
    default = "Holistic review: examine key metrics across all segments to identify root cause and optimization opportunities."
    return strategies.get(problem_type, default)


