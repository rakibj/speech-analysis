"""Test custom exception classes."""
import pytest
from src.exceptions import (
    SpeechAnalysisError,
    AudioProcessingError,
    AudioNotFoundError,
    TranscriptionError,
    ValidationError,
    InvalidContextError,
)


def test_base_exception():
    """Test base exception creation."""
    exc = SpeechAnalysisError("Test error")
    assert "Test error" in str(exc)


def test_exception_with_details():
    """Test exception with details dictionary."""
    exc = AudioNotFoundError(
        "File not found",
        {"file_path": "/test/path"}
    )
    assert "File not found" in str(exc)
    assert "file_path=/test/path" in str(exc)


def test_audio_not_found_error():
    """Test AudioNotFoundError is subclass of AudioProcessingError."""
    exc = AudioNotFoundError("Not found")
    assert isinstance(exc, AudioProcessingError)
    assert isinstance(exc, SpeechAnalysisError)


def test_validation_error():
    """Test ValidationError creation."""
    exc = InvalidContextError(
        "Invalid context",
        {"context": "invalid_value"}
    )
    assert isinstance(exc, ValidationError)
    assert isinstance(exc, SpeechAnalysisError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
