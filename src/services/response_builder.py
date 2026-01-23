"""Response filtering and data transformation for tiered API responses."""
from typing import Optional, Dict, Any, Literal
import math
from src.models import AudioAnalysisResponseDefault, AudioAnalysisResponseFeedback, AudioAnalysisResponseFull


def sanitize_value(value: Any) -> Any:
    """
    Sanitize a value to ensure it's JSON-compliant.
    Converts NaN and infinity to null or 0.
    
    Args:
        value: Any value that might contain non-JSON-compliant floats
        
    Returns:
        Sanitized value safe for JSON serialization
    """
    if value is None:
        return None
    
    if isinstance(value, float):
        # Handle NaN and infinity
        if math.isnan(value) or math.isinf(value):
            return None  # or return 0.0 if you prefer
        return value
    
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    
    return value


def transform_engine_output(raw_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform engine_runner output to match API response schema.
    
    Maps engine output fields to API response fields:
    - Engine returns: timestamped_words, timestamped_fillers, metrics_for_scoring, etc.
    - API expects: word_timestamps, filler_events, normalized_metrics, etc.
    
    Args:
        raw_analysis: Raw output from engine_runner
        
    Returns:
        Transformed analysis with all expected fields
    """
    if not raw_analysis:
        return raw_analysis
    
    transformed = dict(raw_analysis)  # Copy to avoid mutation
    
    # Map engine output fields to API expected fields
    # ================================================
    
    # Map timestamped_words -> word_timestamps
    if "word_timestamps" not in transformed or transformed["word_timestamps"] is None:
        if "timestamped_words" in transformed and transformed["timestamped_words"]:
            transformed["word_timestamps"] = transformed["timestamped_words"]
        else:
            transformed["word_timestamps"] = None
    
    # Map timestamped_fillers -> filler_events
    if "filler_events" not in transformed or transformed["filler_events"] is None:
        if "timestamped_fillers" in transformed and transformed["timestamped_fillers"]:
            transformed["filler_events"] = transformed["timestamped_fillers"]
        else:
            transformed["filler_events"] = None
    
    # Extract content_words from statistics
    if "content_words" not in transformed or transformed["content_words"] is None:
        statistics = transformed.get("statistics", {})
        transformed["content_words"] = statistics.get("content_words")
    
    # Map band_scores to expected fields
    band_scores = transformed.get("band_scores", {})
    if band_scores:
        # Flatten band_scores structure
        transformed["overall_band"] = band_scores.get("overall_band")
        transformed["criterion_bands"] = band_scores.get("criterion_bands")
        transformed["confidence"] = band_scores.get("confidence")
        transformed["scoring_config"] = {}  # Placeholder config
    
    # Extract llm_analysis if not at top level
    if "llm_analysis" not in transformed:
        # Check if it's nested in band_scores or elsewhere
        if "band_scores" in transformed and "llm_analysis" in transformed["band_scores"]:
            transformed["llm_analysis"] = transformed["band_scores"]["llm_analysis"]
        else:
            transformed["llm_analysis"] = {}
    
    # Generate normalized_metrics from speech_quality and statistics
    if "normalized_metrics" not in transformed or transformed["normalized_metrics"] is None:
        speech_quality = transformed.get("speech_quality", {})
        statistics = transformed.get("statistics", {})
        
        # Calculate metrics from available data
        transformed["normalized_metrics"] = {
            "speech_rate_wpm": statistics.get("speech_rate", 0),
            "articulation_rate_wpm": statistics.get("articulation_rate", 0),
            "filler_frequency": statistics.get("filler_percentage", 0),
            "pause_frequency": statistics.get("pause_frequency", 0),
            "mean_word_confidence": speech_quality.get("mean_word_confidence", 0),
        }
    
    # Generate missing feedback-tier fields
    llm_analysis = transformed.get("llm_analysis", {})
    
    if not transformed.get("grammar_errors"):
        grammar_error_count = llm_analysis.get("grammar_error_count", 0)
        if grammar_error_count > 0:
            transformed["grammar_errors"] = {
                "count": grammar_error_count,
                "severity": "high" if grammar_error_count > 3 else "low",
                "note": f"Found {grammar_error_count} grammar error(s)"
            }
        else:
            transformed["grammar_errors"] = {
                "count": 0,
                "severity": "none",
                "note": "No grammar errors detected"
            }
    
    if not transformed.get("word_choice_errors"):
        word_choice_count = llm_analysis.get("word_choice_error_count", 0)
        transformed["word_choice_errors"] = {
            "count": word_choice_count,
            "advanced_vocab_used": llm_analysis.get("advanced_vocabulary_count", 0),
            "note": f"Found {word_choice_count} word choice issue(s)" if word_choice_count > 0 else "Word choice is appropriate"
        }
    
    if not transformed.get("examiner_descriptors"):
        # Generate descriptors from llm_analysis flags
        descriptors = []
        if not llm_analysis.get("listener_effort_high"):
            descriptors.append("easy_to_follow")
        if not llm_analysis.get("flow_instability_present"):
            descriptors.append("smooth_flow")
        if llm_analysis.get("topic_relevance"):
            descriptors.append("topic_relevant")
        if llm_analysis.get("overall_clarity_score", 0) >= 3:
            descriptors.append("clear")
        
        transformed["examiner_descriptors"] = descriptors
    
    if not transformed.get("fluency_notes"):
        # Generate notes from llm_analysis
        notes = []
        if llm_analysis.get("flow_instability_present"):
            notes.append("Speech flow is unstable")
        if llm_analysis.get("listener_effort_high"):
            notes.append("High listener effort required")
        if llm_analysis.get("coherence_break_count", 0) > 0:
            notes.append(f"Coherence breaks: {llm_analysis.get('coherence_break_count')}")
        
        transformed["fluency_notes"] = " | ".join(notes) if notes else "Fluency adequate"
    
    return transformed


def build_response(
    job_id: str,
    status: str,
    raw_analysis: Optional[Dict[str, Any]],
    detail: Optional[Literal["feedback", "full"]] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build a tiered response based on detail parameter.
    
    Args:
        job_id: Job identifier
        status: Job status (processing, completed, error)
        raw_analysis: Raw analysis output from engine_runner (full data)
        detail: Response tier ("feedback" or "full", default is minimal)
        error: Error message if status is "error"
        
    Returns:
        Dictionary with appropriate fields based on detail level
    """
    
    # If error, return error response
    if status == "error":
        return {
            "job_id": job_id,
            "status": status,
            "error": error
        }
    
    # If still processing
    if status == "processing":
        return {
            "job_id": job_id,
            "status": status,
            "message": "Analysis in progress..."
        }
    
    if not raw_analysis:
        return {
            "job_id": job_id,
            "status": status,
            "error": "No analysis data available"
        }
    
    # Transform engine output to fill missing fields
    raw_analysis = transform_engine_output(raw_analysis)
    
    # Sanitize all values to ensure JSON compliance
    raw_analysis = sanitize_value(raw_analysis)
    
    # Extract common fields (always included)
    base_response = {
        "job_id": job_id,
        "status": status,
        "engine_version": raw_analysis.get("engine_version", "0.1.0"),
        "scoring_config": raw_analysis.get("scoring_config", {}),
        "overall_band": raw_analysis.get("overall_band"),
        "criterion_bands": raw_analysis.get("criterion_bands"),
        "confidence": raw_analysis.get("confidence"),
    }
    
    # Add feedback tier fields if requested
    if detail == "feedback" or detail == "full":
        base_response.update({
            "transcript": raw_analysis.get("transcript"),
            "grammar_errors": raw_analysis.get("grammar_errors"),
            "word_choice_errors": raw_analysis.get("word_choice_errors"),
            "examiner_descriptors": raw_analysis.get("examiner_descriptors"),
            "fluency_notes": raw_analysis.get("fluency_notes"),
        })
    
    # Add full tier fields if requested
    if detail == "full":
        base_response.update({
            "word_timestamps": raw_analysis.get("word_timestamps"),
            "content_words": raw_analysis.get("content_words"),
            "segment_timestamps": raw_analysis.get("segment_timestamps"),
            "filler_events": raw_analysis.get("filler_events"),
            "statistics": raw_analysis.get("statistics"),
            "normalized_metrics": raw_analysis.get("normalized_metrics"),
            "opinions": raw_analysis.get("opinions"),
            "benchmarking": raw_analysis.get("benchmarking"),
            "llm_analysis": raw_analysis.get("llm_analysis"),
            "confidence_multipliers": raw_analysis.get("confidence_multipliers"),
            "timestamped_feedback": raw_analysis.get("timestamped_feedback"),
            "speech_quality": raw_analysis.get("speech_quality"),
        })
    
    # Final sanitization to ensure all values are JSON-compliant
    base_response = sanitize_value(base_response)
    
    return base_response
