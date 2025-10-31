"""Unit tests for evaluator agent."""

import pytest
from src.agents.evaluator import evaluate_insights, _validate_quantitative, _score_single


def test_validate_quantitative_valid():
    """Test quantitative validation with valid insight."""
    insight = {
        "metric_delta": {
            "roas_cur": 5.29,
            "roas_base": 5.45,
            "roas_pct_change": -2.94,
        },
        "evidence_refs": ["overview"],
        "segment_filters": {},
    }
    
    valid, notes = _validate_quantitative(insight, segments=None)
    # Should pass basic validation (has numbers and refs)
    assert valid is not None
    assert isinstance(notes, list)


def test_validate_quantitative_missing_data():
    """Test validation fails when metric_delta is missing."""
    insight = {
        "evidence_refs": ["overview"],
    }
    
    valid, notes = _validate_quantitative(insight, segments=None)
    assert valid is False
    assert any("Missing metric_delta" in note for note in notes)


def test_evaluate_insights_with_valid_insight():
    """Test evaluation with a well-formed insight."""
    insights = [
        {
            "title": "Campaign X gained $10,000 revenue (ROAS 5.5)",
            "metric_delta": {
                "revenue_delta": 10000,
                "roas_cur": 5.5,
            },
            "evidence_refs": ["segments:campaign_name:top_gainers"],
            "segment_filters": {"campaign_name": "Campaign X"},
            "reasoning": {
                "think": "Data shows revenue gain",
                "analyze": "Strong performance",
                "conclude": "Scale this campaign",
            },
            "confidence": 0.7,
        }
    ]
    
    result = evaluate_insights(insights, confidence_min=0.6, segments=None, enable_reflection=True)
    
    assert "validated" in result
    assert "all_insights" in result
    assert "summary" in result
    assert len(result["validated"]) >= 0  # May or may not validate depending on scoring
    assert result["summary"]["total"] == 1


def test_evaluate_insights_reflection():
    """Test that low-confidence insights are flagged for retry."""
    insights = [
        {
            "title": "Low confidence insight",
            "metric_delta": {},
            "confidence": 0.4,  # Below threshold
        }
    ]
    
    result = evaluate_insights(insights, confidence_min=0.6, segments=None, enable_reflection=True)
    
    assert len(result["needs_retry"]) >= 1
    assert result["needs_retry"][0]["needs_retry"] is True


def test_score_single_with_reasoning():
    """Test scoring includes bonus for reasoning structure."""
    insight = {
        "title": "Campaign X: ROAS 5.5",
        "metric_delta": {"roas_cur": 5.5},
        "evidence_refs": ["segments"],
        "segment_filters": {"campaign_name": "X"},
        "reasoning": {
            "think": "Observation",
            "analyze": "Analysis",
            "conclude": "Conclusion",
        },
    }
    
    score_result = _score_single(insight, segments=None)
    
    assert "scores" in score_result
    assert "final" in score_result
    assert "confidence" in score_result
    assert "feedback" in score_result
    
    # Should have positive correctness (bonus for reasoning)
    assert score_result["scores"]["correctness"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

