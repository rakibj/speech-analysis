"""
Enumerations for standardized verdict and readiness values.

Provides type-safe constants for analysis verdicts and readiness assessments.
"""

from enum import Enum


class Readiness(str, Enum):
    """IELTS readiness assessment verdicts."""
    
    # Passing bands
    READY = "ready"                      # 6.5+: Ready for target use
    READY_WITH_CAUTION = "ready_with_caution"  # 6.0-6.5: Somewhat ready
    
    # Non-passing bands
    NOT_READY = "not_ready"              # 5.0-6.0: Needs improvement
    NOT_READY_SIGNIFICANT_GAPS = "not_ready_significant_gaps"  # <5.0: Major gaps
    
    # Analysis errors
    INSUFFICIENT_DURATION = "insufficient_audio_duration"
    NO_SPEECH_DETECTED = "no_speech_detected"
    ANALYSIS_FAILED = "analysis_failed"
    
    def __str__(self) -> str:
        """Return human-readable name."""
        return self.value
    
    @classmethod
    def from_score(cls, score: float) -> "Readiness":
        """
        Determine readiness from fluency score.
        
        Args:
            score: Fluency score (0-100)
            
        Returns:
            Readiness enum value
        """
        if score is None:
            return cls.ANALYSIS_FAILED
        elif score >= 65:
            return cls.READY
        elif score >= 60:
            return cls.READY_WITH_CAUTION
        elif score >= 50:
            return cls.NOT_READY
        else:
            return cls.NOT_READY_SIGNIFICANT_GAPS


class IELTSBand(float, Enum):
    """IELTS band scale (0.0 to 9.0)."""
    
    BAND_9_0 = 9.0
    BAND_8_5 = 8.5
    BAND_8_0 = 8.0
    BAND_7_5 = 7.5
    BAND_7_0 = 7.0
    BAND_6_5 = 6.5
    BAND_6_0 = 6.0
    BAND_5_5 = 5.5
    BAND_5_0 = 5.0
    BAND_4_5 = 4.5
    BAND_4_0 = 4.0
    
    def __str__(self) -> str:
        """Return band as string."""
        return f"{self.value}"
    
    def readiness(self) -> Readiness:
        """Get readiness assessment for this band."""
        return Readiness.from_score(self.value * 10)


class SpeechContext(str, Enum):
    """Valid speech analysis contexts."""
    
    CONVERSATIONAL = "conversational"  # Casual speaking
    NARRATIVE = "narrative"             # Storytelling
    PRESENTATION = "presentation"       # Formal presentation
    INTERVIEW = "interview"             # Interview setting
    
    def __str__(self) -> str:
        """Return context value."""
        return self.value


class ListenerEffort(str, Enum):
    """Listener effort level (from LLM evaluation)."""
    
    LOW = "low"          # Effortless to follow
    MEDIUM = "medium"    # Occasional effort required
    HIGH = "high"        # Frequent effort/reprocessing needed
    
    def __str__(self) -> str:
        return self.value


class FlowControl(str, Enum):
    """Speech flow control stability (from LLM evaluation)."""
    
    STABLE = "stable"         # Consistent pacing
    MIXED = "mixed"           # Uneven but manageable
    UNSTABLE = "unstable"     # Erratic/broken rhythm
    
    def __str__(self) -> str:
        return self.value


class ClarityScore(int, Enum):
    """Overall clarity score scale (1-5)."""
    
    EXTREMELY_CLEAR = 5      # Effortless to understand
    FAIRLY_CLEAR = 4         # Generally clear, minimal strain
    MODERATELY_CLEAR = 3     # Generally clear, some strain
    SOMEWHAT_UNCLEAR = 2     # Effort required to understand
    VERY_UNCLEAR = 1         # Hard to follow
    
    def __str__(self) -> str:
        return str(self.value)
