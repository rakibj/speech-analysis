"""Test LLM processing with error handling."""
import pytest
import os
from unittest.mock import patch, MagicMock
from src.utils.llm_processing import aggregate_llm_metrics, LLMSpeechAnnotations, Span
from src.utils.exceptions import (
    ConfigurationError,
    LLMValidationError,
    LLMAPIError,
)


def test_aggregate_llm_metrics():
    """Test LLM metrics aggregation."""
    llm = LLMSpeechAnnotations(
        topic_relevance=True,
        listener_effort_level="low",
        flow_control_level="stable",
        overall_clarity_score=5,
        cascading_grammar_failure=False,
        coherence_breaks=[],
        clause_completion_issues=[],
        word_choice_errors=[],
        advanced_vocabulary=[Span(text="sophisticated", label="advanced_vocabulary")],
        idiomatic_or_collocational_use=[],
        grammar_errors=[],
        meaning_blocking_grammar_errors=[],
        complex_structures_attempted=[],
        complex_structures_accurate=[],
        successful_paraphrase=[],
        failed_paraphrase=[],
        register_mismatch=[],
    )
    
    metrics = aggregate_llm_metrics(llm)
    
    assert metrics["topic_relevance"] is True
    assert metrics["listener_effort_high"] is False
    assert metrics["flow_instability_present"] is False
    assert metrics["overall_clarity_score"] == 5
    assert metrics["advanced_vocabulary_count"] == 1
    assert metrics["grammar_error_count"] == 0


def test_extract_llm_annotations_missing_api_key(monkeypatch):
    """Test extract_llm_annotations raises error without API key."""
    from src.utils.llm_processing import extract_llm_annotations
    
    # Ensure API key is not set
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    with pytest.raises(ConfigurationError, match="OpenAI API key"):
        extract_llm_annotations("test transcript")


def test_extract_llm_annotations_empty_transcript(monkeypatch):
    """Test extract_llm_annotations raises error for empty transcript."""
    from src.utils.llm_processing import extract_llm_annotations
    
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    with pytest.raises(LLMValidationError, match="Empty transcript"):
        extract_llm_annotations("")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
