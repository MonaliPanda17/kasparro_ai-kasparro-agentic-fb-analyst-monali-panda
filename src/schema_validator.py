"""Schema validation utilities for agent I/O."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import ValidationError

from src.io_schemas import Insight, CreativeIdea, Evaluation


def validate_insight(insight_dict: Dict[str, Any], strict: bool = False) -> Insight:
    """Validate and convert insight dict to Insight schema.
    
    Args:
        insight_dict: Dictionary containing insight data
        strict: If True, raises ValidationError on mismatch. If False, converts compatible dicts.
    
    Returns:
        Validated Insight instance
    
    Raises:
        ValidationError: If validation fails and strict=True
    """
    # Insight schema requires: title, metric_delta, segment_filters, evidence_refs, confidence
    # Additional fields like 'reasoning' and 'impact' are allowed but not in base schema
    required_fields = {
        "title": insight_dict.get("title", ""),
        "metric_delta": insight_dict.get("metric_delta", {}),
        "segment_filters": insight_dict.get("segment_filters", {}),
        "evidence_refs": insight_dict.get("evidence_refs", []),
        "confidence": insight_dict.get("confidence", 0.0),
    }
    
    try:
        return Insight(**required_fields)
    except ValidationError as e:
        if strict:
            raise
        # For non-strict mode, try to construct with defaults
        defaults = {
            "title": "",
            "metric_delta": {},
            "segment_filters": {},
            "evidence_refs": [],
            "confidence": 0.0,
        }
        defaults.update(required_fields)
        return Insight(**defaults)


def validate_insights(insights: List[Dict[str, Any]], strict: bool = False) -> List[Insight]:
    """Validate a list of insight dicts.
    
    Args:
        insights: List of insight dictionaries
        strict: If True, raises ValidationError on any failure
    
    Returns:
        List of validated Insight instances
    """
    validated = []
    for ins in insights:
        try:
            validated.append(validate_insight(ins, strict=strict))
        except ValidationError as e:
            if strict:
                raise
            # Skip invalid insights in non-strict mode
            continue
    return validated


def validate_creative(creative_dict: Dict[str, Any], strict: bool = False) -> CreativeIdea:
    """Validate and convert creative dict to CreativeIdea schema.
    
    Args:
        creative_dict: Dictionary containing creative data
        strict: If True, raises ValidationError on mismatch
    
    Returns:
        Validated CreativeIdea instance
    """
    required_fields = {
        "hook": creative_dict.get("hook", ""),
        "body": creative_dict.get("body", ""),
        "cta": creative_dict.get("cta", ""),
    }
    
    try:
        return CreativeIdea(**required_fields)
    except ValidationError as e:
        if strict:
            raise
        return CreativeIdea(hook="", body="", cta="")


def validate_creatives(creatives: List[Dict[str, Any]], strict: bool = False) -> List[CreativeIdea]:
    """Validate a list of creative dicts.
    
    Args:
        creatives: List of creative dictionaries
        strict: If True, raises ValidationError on any failure
    
    Returns:
        List of validated CreativeIdea instances
    """
    validated = []
    for cr in creatives:
        try:
            validated.append(validate_creative(cr, strict=strict))
        except ValidationError as e:
            if strict:
                raise
            continue
    return validated


def validate_evaluation(eval_dict: Dict[str, Any], strict: bool = False) -> Evaluation:
    """Validate and convert evaluation dict to Evaluation schema.
    
    Args:
        eval_dict: Dictionary containing evaluation data
        strict: If True, raises ValidationError on mismatch
    
    Returns:
        Validated Evaluation instance
    """
    required_fields = {
        "correctness": eval_dict.get("correctness", 0.0),
        "specificity": eval_dict.get("specificity", 0.0),
        "actionability": eval_dict.get("actionability", 0.0),
        "alignment": eval_dict.get("alignment", 0.0),
        "comments": eval_dict.get("comments", ""),
    }
    
    try:
        return Evaluation(**required_fields)
    except ValidationError as e:
        if strict:
            raise
        return Evaluation(
            correctness=0.0,
            specificity=0.0,
            actionability=0.0,
            alignment=0.0,
            comments="",
        )

