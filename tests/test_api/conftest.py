"""Test configuration and fixtures."""
import pytest
from pathlib import Path


@pytest.fixture
def sample_audio_path():
    """Path to a sample audio file for testing."""
    return Path("samples/sample.wav")


@pytest.fixture
def test_audio_short():
    """Path to a short audio file."""
    return Path("samples/short_audio.wav")


@pytest.fixture
def test_contexts():
    """Valid speech contexts for testing."""
    return ["conversational", "narrative", "presentation", "interview"]
