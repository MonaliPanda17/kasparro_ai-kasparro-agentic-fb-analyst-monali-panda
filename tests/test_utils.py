"""Unit tests for utils module."""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from src.utils import load_csv, generate_data_summary


def test_load_csv_valid_file():
    """Test loading a valid CSV file."""
    # Create a minimal test CSV
    test_data = {
        "date": [datetime.now().date()] * 5,
        "campaign_name": ["Test Campaign"] * 5,
        "adset_name": ["Test Adset"] * 5,
        "spend": [100.0, 200.0, 300.0, 400.0, 500.0],
        "impressions": [1000, 2000, 3000, 4000, 5000],
        "clicks": [50, 100, 150, 200, 250],
        "purchases": [5, 10, 15, 20, 25],
        "revenue": [250.0, 500.0, 750.0, 1000.0, 1250.0],
        "roas": [2.5, 2.5, 2.5, 2.5, 2.5],
        "creative_type": ["Image"] * 5,
        "platform": ["Facebook"] * 5,
        "country": ["US"] * 5,
        "audience_type": ["Broad"] * 5,
    }
    
    df = pd.DataFrame(test_data)
    # Convert date to string for CSV
    df["date"] = df["date"].astype(str)
    
    # Write temporary CSV
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        result = load_csv(temp_path)
        assert result.df is not None
        assert len(result.df) == 5
        assert "spend" in result.df.columns
    finally:
        os.unlink(temp_path)


def test_generate_data_summary():
    """Test data summary generation."""
    test_data = {
        "date": pd.to_datetime([datetime.now() - timedelta(days=i) for i in range(10)]),
        "campaign_name": ["Campaign A"] * 5 + ["Campaign B"] * 5,
        "spend": [100.0] * 10,
        "impressions": [1000.0] * 10,
        "clicks": [50.0] * 10,
        "purchases": [5.0] * 10,
        "revenue": [250.0] * 10,
        "roas": [2.5] * 10,
        "creative_type": ["Image"] * 10,
        "platform": ["Facebook"] * 10,
        "country": ["US"] * 10,
        "audience_type": ["Broad"] * 10,
    }
    
    df = pd.DataFrame(test_data)
    summary = generate_data_summary(df, top_n=3)
    
    assert "date_range" in summary
    assert "overall_metrics" in summary
    assert "top_segments" in summary
    assert "data_quality" in summary
    
    # Check date range
    assert "min" in summary["date_range"]
    assert "max" in summary["date_range"]
    
    # Check overall metrics
    assert "spend" in summary["overall_metrics"]
    assert "revenue" in summary["overall_metrics"]
    assert "aggregate_roas" in summary["overall_metrics"]
    
    # Check top segments
    assert "campaign_name" in summary["top_segments"]


def test_generate_data_summary_empty():
    """Test summary generation with empty DataFrame."""
    df = pd.DataFrame()
    summary = generate_data_summary(df)
    
    assert isinstance(summary, dict)
    assert "date_range" in summary
    assert "overall_metrics" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
