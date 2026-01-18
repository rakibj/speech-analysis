"""
Custom exception classes for speech analysis system.

Provides structured error handling with specific exception types
for different failure modes in audio processing, transcription, and analysis.
"""


class SpeechAnalysisError(Exception):
    """Base exception for all speech analysis errors."""
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize exception with message and optional details.
        
        Args:
            message: Human-readable error message
            details: Optional dict with additional context (file path, model name, etc)
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details and isinstance(self.details, dict):
            details_str = " | " + " | ".join(
                f"{k}={v}" for k, v in self.details.items()
            )
            return f"{self.message}{details_str}"
        return self.message


class AudioProcessingError(SpeechAnalysisError):
    """Raised when audio loading or preprocessing fails."""
    pass


class AudioNotFoundError(AudioProcessingError):
    """Raised when audio file does not exist."""
    pass


class AudioFormatError(AudioProcessingError):
    """Raised when audio file format is unsupported or corrupted."""
    pass


class AudioDurationError(AudioProcessingError):
    """Raised when audio duration is insufficient for analysis."""
    pass


class TranscriptionError(SpeechAnalysisError):
    """Raised when transcription (Whisper/WhisperX) fails."""
    pass


class ModelLoadError(SpeechAnalysisError):
    """Raised when AI model (Whisper, Wav2Vec2, etc) fails to load."""
    pass


class NoSpeechDetectedError(SpeechAnalysisError):
    """Raised when no speech is detected in audio."""
    pass


class LLMProcessingError(SpeechAnalysisError):
    """Raised when LLM annotation extraction fails."""
    pass


class LLMAPIError(LLMProcessingError):
    """Raised when OpenAI API call fails."""
    pass


class LLMValidationError(LLMProcessingError):
    """Raised when LLM output doesn't match expected schema."""
    pass


class ConfigurationError(SpeechAnalysisError):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(SpeechAnalysisError):
    """Raised when input validation fails."""
    pass


class InvalidContextError(ValidationError):
    """Raised when speech context is not in valid set."""
    pass


class DeviceError(SpeechAnalysisError):
    """Raised when requested compute device is unavailable."""
    pass
