"""Test audio processing module with error handling."""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from src.audio_processing import (
    is_filler_word,
    normalize_word,
    mark_filler_words,
    get_content_words,
    MIN_AUDIO_DURATION_SEC,
)
from src.exceptions import AudioNotFoundError, AudioDurationError


def test_normalize_word():
    """Test word normalization."""
    assert normalize_word("um") == "um"
    assert normalize_word("UM") == "um"
    assert normalize_word("um...") == "um"
    assert normalize_word("...um...") == "um"
    assert normalize_word("") == ""


def test_is_filler_word():
    """Test filler word detection."""
    # Known fillers
    assert is_filler_word("um") is True
    assert is_filler_word("uh") is True
    assert is_filler_word("er") is True
    assert is_filler_word("erm") is True
    
    # Elongated fillers
    assert is_filler_word("uhhhhh") is True
    assert is_filler_word("ummmm") is True
    assert is_filler_word("errrr") is True
    
    # Non-fillers
    assert is_filler_word("the") is False
    assert is_filler_word("hello") is False
    assert is_filler_word("world") is False


def test_mark_filler_words():
    """Test filler word marking."""
    df = pd.DataFrame({
        "word": ["hello", "um", "world", "uh", "today"],
        "start": [0.0, 1.0, 2.0, 3.0, 4.0],
        "end": [1.0, 1.5, 2.5, 3.5, 5.0],
    })
    
    result = mark_filler_words(df)
    
    assert "is_filler" in result.columns
    assert result["is_filler"].tolist() == [False, True, False, True, False]


def test_get_content_words():
    """Test content word extraction."""
    df = pd.DataFrame({
        "word": ["hello", "um", "world"],
        "is_filler": [False, True, False],
    })
    
    content = get_content_words(df)
    
    assert len(content) == 2
    assert content["word"].tolist() == ["hello", "world"]


def test_get_content_words_missing_column():
    """Test get_content_words raises error for missing column."""
    df = pd.DataFrame({"word": ["hello", "um"]})
    
    with pytest.raises(ValueError, match="is_filler"):
        get_content_words(df)


def test_load_audio_missing_file():
    """Test load_audio raises error for missing file."""
    from src.audio_processing import load_audio
    
    with pytest.raises(AudioNotFoundError):
        load_audio("/nonexistent/file.wav")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
