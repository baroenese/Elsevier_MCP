"""Tests for prompt templates in elsevier_mcp.prompts."""

import pytest

from elsevier_mcp.prompts import get_prompt


def test_paper_deep_dive_prompt() -> None:
    """paper_deep_dive includes the target paper and analysis depth."""
    res = get_prompt("paper_deep_dive", {"paper_title_or_eid": "2-s2.0-123", "analysis_depth": "methodology_breakdown"})
    text = res["messages"][0]["content"]["text"]
    assert "2-s2.0-123" in text
    assert "methodology_breakdown" in text
    assert res["description"] == "Deep Dive Analysis for 2-s2.0-123"


def test_paper_deep_dive_defaults() -> None:
    """Omitted arguments fall back to readable defaults."""
    res = get_prompt("paper_deep_dive", {})
    text = res["messages"][0]["content"]["text"]
    assert "the target paper" in text
    assert "critical_appraisal" in text


def test_research_trend_analysis_prompt() -> None:
    """research_trend_analysis includes the field and timeframe."""
    res = get_prompt("research_trend_analysis", {"field": "Federated Learning", "timeframe": "2021-2025"})
    text = res["messages"][0]["content"]["text"]
    assert "Federated Learning" in text
    assert "2021-2025" in text
    assert res["description"] == "Research Trend Analysis for Federated Learning"


def test_unknown_prompt_raises_value_error() -> None:
    """Unknown prompt names raise ValueError."""
    with pytest.raises(ValueError, match="Prompt not found"):
        get_prompt("nonexistent_prompt", {})
