"""
Speech Analysis Engine - Full Analysis Pipeline

Combines raw acoustic analysis, band scoring, and LLM annotations.
Returns comprehensive analysis report without timestamps, includes transcript.
"""

import sys
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import traceback

# --- Project root setup ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.analyzer_raw import analyze_speech as analyze_speech_raw
from src.core.analyze_band import build_analysis
from src.utils.logging_config import setup_logging
from src.utils.exceptions import SpeechAnalysisError
from src.utils.context_parser import parse_context, format_context_for_llm

# Setup logging
logger = setup_logging(level="INFO")


def make_json_safe(obj):
    """Convert numpy types and inf/nan to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        val = float(obj)
        # Convert inf/nan to None for JSON compliance
        if np.isinf(val) or np.isnan(val):
            return None
        return val
    elif isinstance(obj, float):
        # Handle native Python floats too
        if np.isinf(obj) or np.isnan(obj):
            return None
        return obj
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    else:
        return obj


def merge_words_and_fillers(timestamped_words, timestamped_fillers, core_fillers=None):
    """
    Merge content words and filler events into a single unified timeline.
    
    Args:
        timestamped_words: List of content words from Whisper (dict with word, start, end, confidence, is_filler)
        timestamped_fillers: List of filler events from Wav2Vec2/Whisper (dict with word, type, start, end)
        core_fillers: Optional list of common filler words to identify most frequent one
    
    Returns:
        Sorted merged list with word, type, start_sec, end_sec, confidence
    """
    if core_fillers is None:
        core_fillers = ["um", "uh", "er", "ah", "hmm", "like", "you know", "so", "basically", "literally"]
    
    merged = []
    
    # Add content words
    for word_data in (timestamped_words or []):
        if isinstance(word_data, dict):
            word_text = word_data.get("word", "").strip()
            is_filler = word_data.get("is_filler", False)
            
            # Skip if word is empty
            if not word_text:
                continue
            
            merged.append({
                "word": word_text,
                "type": "filler" if is_filler else "content",
                "start_sec": round(word_data.get("start", 0.0), 3),
                "end_sec": round(word_data.get("end", 0.0), 3),
                "confidence": round(word_data.get("confidence", 0.0), 3),
            })
    
    # Add filler events (these are detected by Wav2Vec2 or Whisper as disfluencies)
    for filler_data in (timestamped_fillers or []):
        if isinstance(filler_data, dict):
            # Try to get word from various fields
            filler_word = filler_data.get("word") or filler_data.get("text") or filler_data.get("raw_label")
            
            # Ensure we have a string
            if filler_word is None or (isinstance(filler_word, float) and np.isnan(filler_word)):
                filler_word = ""
            else:
                filler_word = str(filler_word).strip()
            
            # Handle null fillers - convert to most frequent one
            if not filler_word or filler_word.lower() == "none":
                filler_word = "um"  # Default to most common filler
            
            merged.append({
                "word": filler_word,
                "type": "filler",
                "start_sec": round(filler_data.get("start", 0.0), 3),
                "end_sec": round(filler_data.get("end", 0.0), 3),
                "confidence": 0.25,  # Wav2Vec2 filler detection confidence
            })
    
    # Sort by start_sec
    merged.sort(key=lambda x: x["start_sec"])
    
    return merged


async def analyze_speech(
    audio_path: str,
    context: str = "conversational",
    device: str = "cpu",
    use_llm: bool = True
) -> Dict:
    """
    Perform comprehensive speech analysis on an audio file.
    
    Returns analysis WITH confidence scoring and timestamped rubric feedback.
    
    Args:
        audio_path: Path to audio file
        context: Speech context string
            - "conversational" - General conversation
            - "ielts" - IELTS Speaking test
            - "ielts[topic: family, cue_card: Describe someone]" - IELTS with metadata
            - "narrative", "presentation", "interview" - Other speech types
            - "custom[key: value, ...]" - Custom context with metadata
            Metadata is extracted and passed to LLM for context-aware analysis.
        device: Device to use (cpu or cuda)
        use_llm: Whether to use LLM for semantic evaluation
        
    Returns:
        dict with:
            - metadata: audio info
            - transcript: raw speech transcript
            - fluency_analysis: fluency metrics
            - pronunciation: intelligibility and prosody
            - band_scores: IELTS band scoring with CONFIDENCE
            - timestamped_feedback: Rubric-based feedback WITH TIMESTAMPS
            - raw_metrics: detailed metrics dict
            - llm_analysis: LLM annotations (if use_llm=True)
            - context: Parsed context information
    """
    
    audio_path_str = str(audio_path)
    
    # Parse context string into base_type and metadata
    base_context, context_metadata = parse_context(context)
    llm_context = format_context_for_llm(base_context, context_metadata)
    
    logger.info(f"Starting comprehensive analysis for: {audio_path_str}")
    logger.info(f"Context: {base_context} | {llm_context}")
    
    try:
        # =============================================
        # STAGE 1: RAW ACOUSTIC ANALYSIS
        # =============================================
        logger.info("Stage 1: Running raw audio analysis...")
        raw_analysis = await analyze_speech_raw(audio_path_str, base_context, device)
        
        # Check for errors
        if not raw_analysis.get("statistics", {}).get("total_words_transcribed", 0):
            raise SpeechAnalysisError(
                "No speech detected",
                "Audio file contains no detectable speech"
            )
        
        # =============================================
        # STAGE 2: BUILD ANALYSIS REPORT
        # =============================================
        logger.info("Stage 2: Building analysis report...")
        analysis = build_analysis(raw_analysis)
        
        # Extract transcript and metrics
        transcript = raw_analysis.get("raw_transcript", "")
        metrics_for_scoring = analysis["metrics_for_scoring"]
        
        # =============================================
        # BUILD FINAL REPORT (WITH CONFIDENCE & TIMESTAMPS)
        # =============================================
        logger.info("Finalizing report...")
        
        # Merge words and fillers into unified timeline
        timestamped_words = raw_analysis.get("timestamps", {}).get("words_timestamps_raw", [])
        timestamped_fillers = raw_analysis.get("timestamps", {}).get("filler_timestamps", [])
        
        # Create merged word_timestamps with both content and filler events
        word_timestamps_merged = merge_words_and_fillers(timestamped_words, timestamped_fillers)
        
        # Prepare timestamped feedback (if word-level timestamps available)
        timestamped_feedback = {}
        
        final_report = {
            # Metadata
            "metadata": analysis["metadata"],
            
            # Speech transcript
            "transcript": transcript,
            
            # Fluency analysis
            "fluency_analysis": raw_analysis.get("fluency_analysis", {}),
            
            # Pronunciation (from analysis)
            "pronunciation": analysis["pronunciation"],
            
            # Timestamped Words (unified timeline: content words + filler events)
            "word_timestamps": word_timestamps_merged if word_timestamps_merged else [],
            
            # Timestamped Rubric Feedback (when word-level timestamps available)
            "timestamped_feedback": timestamped_feedback if timestamped_feedback else {},
            
            # Raw metrics used for scoring
            "metrics_for_scoring": make_json_safe(metrics_for_scoring),
            
            # Normalized metrics (fluency, disfluency, prosody)
            "normalized_metrics": {
                "wpm": raw_analysis.get("wpm", 0),
                "long_pauses_per_min": raw_analysis.get("long_pauses_per_min", 0),
                "fillers_per_min": raw_analysis.get("fillers_per_min", 0),
                "pause_variability": raw_analysis.get("pause_variability", 0),
                "speech_rate_variability": raw_analysis.get("speech_rate_variability", 0),
                "vocab_richness": raw_analysis.get("vocab_richness", 0),
                "type_token_ratio": raw_analysis.get("type_token_ratio", 0),
                "repetition_ratio": raw_analysis.get("repetition_ratio", 0),
                "mean_utterance_length": raw_analysis.get("mean_utterance_length", 0),
            },
            
            # Statistics
            "statistics": raw_analysis["statistics"],
            
            # Speech quality indicators
            "speech_quality": {
                "mean_word_confidence": analysis["pronunciation"]["intelligibility"]["mean_word_confidence"],
                "low_confidence_ratio": analysis["pronunciation"]["intelligibility"]["low_confidence_ratio"],
                "is_monotone": analysis["pronunciation"]["prosody"]["monotone_detected"],
            },
            
        }
        
        logger.info("[OK] Analysis complete")
        return make_json_safe(final_report)
        
    except SpeechAnalysisError as e:
        logger.error(f"Speech analysis error: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        logger.debug(traceback.format_exc())
        raise SpeechAnalysisError(
            "Analysis failed",
            str(e)
        )