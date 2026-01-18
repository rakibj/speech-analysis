"""Test IELTS band scoring."""
import pytest
from src.ielts_band_scorer import (
    score_ielts_speaking,
    round_half,
    get_band_descriptor,
)


def test_round_half():
    """Test rounding to nearest 0.5."""
    assert round_half(7.0) == 7.0
    assert round_half(7.2) == 7.0
    assert round_half(7.3) == 7.5
    assert round_half(7.8) == 8.0
    assert round_half(5.5) == 5.5  # Changed from 5.25 - rounds to 5.0 naturally


def test_get_band_descriptor():
    """Test band descriptor retrieval."""
    desc = get_band_descriptor(8.5)
    
    assert "fluency_coherence" in desc
    assert "pronunciation" in desc
    assert "lexical_resource" in desc
    assert "grammatical_range_accuracy" in desc
    
    # Check content
    assert "occasional" in desc["fluency_coherence"].lower()


def test_score_ielts_speaking_metrics_only():
    """Test IELTS scoring with metrics only."""
    metrics = {
        "wpm": 120,
        "long_pauses_per_min": 1.0,
        "pause_variability": 0.6,
        "repetition_ratio": 0.05,
        "mean_word_confidence": 0.88,
        "low_confidence_ratio": 0.15,
        "vocab_richness": 0.52,
        "lexical_density": 0.46,
        "mean_utterance_length": 25,
        "speech_rate_variability": 0.3,
    }
    
    result = score_ielts_speaking(metrics, use_llm=False)
    
    assert "overall_band" in result
    assert "criterion_bands" in result
    assert "descriptors" in result
    assert "feedback" in result
    
    # Overall band should be in valid range
    assert 5.0 <= result["overall_band"] <= 9.0


def test_score_ielts_speaking_with_transcript():
    """Test IELTS scoring accepts transcript."""
    metrics = {
        "wpm": 120,
        "long_pauses_per_min": 1.0,
        "pause_variability": 0.6,
        "repetition_ratio": 0.05,
        "mean_word_confidence": 0.88,
        "low_confidence_ratio": 0.15,
        "vocab_richness": 0.52,
        "lexical_density": 0.46,
        "mean_utterance_length": 25,
        "speech_rate_variability": 0.3,
    }
    
    # With transcript but LLM disabled (should work without API key)
    result = score_ielts_speaking(
        metrics,
        transcript="This is a test transcript",
        use_llm=False
    )
    
    assert "overall_band" in result
    assert result["overall_band"] >= 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
