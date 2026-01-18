"""Tests for AnalysisService."""
import pytest
import asyncio
from pathlib import Path

from src.services import AnalysisService


@pytest.mark.asyncio
async def test_analysis_service_with_invalid_file():
    """Test service with non-existent audio file."""
    with pytest.raises(FileNotFoundError):
        await AnalysisService.analyze_speech(
            audio_path="/invalid/path/audio.wav",
            speech_context="conversational"
        )


@pytest.mark.asyncio
async def test_analysis_service_response_structure():
    """Test that service returns correct response structure."""
    # When file doesn't exist, we expect FileNotFoundError
    # When file exists but is too short, we expect AudioDurationError
    # When file is valid, we get the full response
    
    # This test documents the expected structure
    expected_keys = {
        "verdict",
        "benchmarking",
        "normalized_metrics",
        "opinions",
        "word_timestamps",
        "content_words",
        "segment_timestamps",
        "filler_events",
        "statistics"
    }
    
    # When no speech is detected
    empty_response = AnalysisService._empty_response()
    assert all(key in empty_response for key in expected_keys)
    assert empty_response["verdict"]["readiness"] == "no_speech_detected"
    assert empty_response["statistics"]["total_words_transcribed"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
