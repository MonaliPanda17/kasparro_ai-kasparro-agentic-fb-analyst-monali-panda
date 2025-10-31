"""Unit tests for schema validation."""

import pytest
from src.schema_validator import validate_insight, validate_insights, validate_creative, validate_creatives
from src.io_schemas import Insight, CreativeIdea


def test_validate_insight_valid():
    """Test validating a valid insight."""
    insight_dict = {
        "title": "Campaign X has high ROAS",
        "metric_delta": {"roas_cur": 5.5, "roas_base": 4.0},
        "segment_filters": {"campaign_name": "Campaign X"},
        "evidence_refs": ["segments:campaign_name"],
        "confidence": 0.8,
        "reasoning": {"think": "...", "analyze": "...", "conclude": "..."},  # Extra field allowed
    }
    
    validated = validate_insight(insight_dict, strict=False)
    assert isinstance(validated, Insight)
    assert validated.title == "Campaign X has high ROAS"
    assert validated.confidence == 0.8
    assert validated.evidence_refs == ["segments:campaign_name"]


def test_validate_insights_list():
    """Test validating a list of insights."""
    insights = [
        {
            "title": "Insight 1",
            "metric_delta": {"roas_cur": 5.0},
            "segment_filters": {},
            "evidence_refs": ["overview"],
            "confidence": 0.7,
        },
        {
            "title": "Insight 2",
            "metric_delta": {"revenue_delta": 1000},
            "segment_filters": {"country": "US"},
            "evidence_refs": ["segments:country"],
            "confidence": 0.75,
        },
    ]
    
    validated = validate_insights(insights, strict=False)
    assert len(validated) == 2
    assert all(isinstance(ins, Insight) for ins in validated)
    assert validated[0].title == "Insight 1"
    assert validated[1].title == "Insight 2"


def test_validate_creative_valid():
    """Test validating a valid creative."""
    creative_dict = {
        "hook": "Test hook",
        "body": "Test body",
        "cta": "Shop now",
    }
    
    validated = validate_creative(creative_dict, strict=False)
    assert isinstance(validated, CreativeIdea)
    assert validated.hook == "Test hook"
    assert validated.body == "Test body"
    assert validated.cta == "Shop now"


def test_validate_creatives_list():
    """Test validating a list of creatives."""
    creatives = [
        {"hook": "Hook 1", "body": "Body 1", "cta": "CTA 1"},
        {"hook": "Hook 2", "body": "Body 2", "cta": "CTA 2"},
    ]
    
    validated = validate_creatives(creatives, strict=False)
    assert len(validated) == 2
    assert all(isinstance(cr, CreativeIdea) for cr in validated)
    assert validated[0].hook == "Hook 1"
    assert validated[1].hook == "Hook 2"


def test_validate_insight_missing_fields():
    """Test that missing fields use defaults in non-strict mode."""
    incomplete_insight = {
        "title": "Test",
        # Missing other fields
    }
    
    validated = validate_insight(incomplete_insight, strict=False)
    assert isinstance(validated, Insight)
    assert validated.title == "Test"
    assert validated.confidence == 0.0  # Default
    assert validated.evidence_refs == []  # Default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

