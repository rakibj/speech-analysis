"""
Speech Analysis Engine - Full Analysis Pipeline

Combines raw acoustic analysis, band scoring, and LLM annotations.
Returns comprehensive analysis report without timestamps, includes transcript.
"""

import sys
import json
import asyncio
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import traceback

# --- Project root setup ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.analyzer_raw import analyze_speech as analyze_speech_raw
from src.core.analyze_band import build_analysis
from src.core.ielts_band_scorer import score_ielts_speaking
from src.core.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.utils.logging_config import setup_logging
from src.utils.exceptions import SpeechAnalysisError

# Setup logging
logger = setup_logging(level="INFO")


def make_json_safe(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    else:
        return obj


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
        context: Speech context (conversational, narrative, presentation, interview)
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
    """
    
    audio_path_str = str(audio_path)
    logger.info(f"Starting comprehensive analysis for: {audio_path_str}")
    
    try:
        # =============================================
        # STAGE 1: RAW ACOUSTIC ANALYSIS
        # =============================================
        logger.info("Stage 1: Running raw audio analysis...")
        raw_analysis = await analyze_speech_raw(audio_path_str, context, device)
        
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
        # STAGE 3: BAND SCORING (WITH OPTIONAL LLM)
        # =============================================
        logger.info("Stage 3: Scoring IELTS bands...")
        band_scores = score_ielts_speaking(
            metrics=metrics_for_scoring,
            transcript=transcript,
            use_llm=use_llm
        )
        
        # =============================================
        # STAGE 4: LLM ANNOTATIONS (OPTIONAL)
        # =============================================
        llm_analysis = None
        llm_annotations = None
        if use_llm and transcript:
            try:
                logger.info("Stage 4: Running LLM annotation analysis...")
                llm_annotations = extract_llm_annotations(transcript)
                llm_analysis = aggregate_llm_metrics(llm_annotations)
                logger.info("[OK] LLM analysis complete")
            except Exception as e:
                logger.warning(f"LLM analysis failed (continuing): {str(e)}")
                llm_analysis = None
                llm_annotations = None
        
        # =============================================
        # BUILD FINAL REPORT (WITH CONFIDENCE & TIMESTAMPS)
        # =============================================
        logger.info("Finalizing report...")
        
        # Prepare timestamped feedback (if word-level timestamps available)
        timestamped_feedback = {}
        word_timestamps = raw_analysis.get("timestamps", {}).get("words_timestamps_raw", [])
        
        if word_timestamps and use_llm and llm_annotations and transcript:
            try:
                from src.core.llm_processing import map_spans_to_timestamps
                
                # Map grammar errors to timestamps
                if llm_annotations.grammar_errors:
                    timestamped_issues = map_spans_to_timestamps(transcript, llm_annotations.grammar_errors, word_timestamps)
                    timestamped_feedback["grammar_errors"] = [
                        {
                            "text": span.text,
                            "label": span.label,
                            "start_sec": span.start_sec,
                            "end_sec": span.end_sec,
                            "timestamp_mmss": span.timestamp_mmss,
                        }
                        for span in timestamped_issues
                    ]
                
                # Map word choice errors to timestamps
                if llm_annotations.word_choice_errors:
                    timestamped_issues = map_spans_to_timestamps(transcript, llm_annotations.word_choice_errors, word_timestamps)
                    timestamped_feedback["word_choice_errors"] = [
                        {
                            "text": span.text,
                            "label": span.label,
                            "start_sec": span.start_sec,
                            "end_sec": span.end_sec,
                            "timestamp_mmss": span.timestamp_mmss,
                        }
                        for span in timestamped_issues
                    ]
                
                # Map coherence breaks to timestamps
                if llm_annotations.coherence_breaks:
                    timestamped_issues = map_spans_to_timestamps(transcript, llm_annotations.coherence_breaks, word_timestamps)
                    timestamped_feedback["coherence_breaks"] = [
                        {
                            "text": span.text,
                            "label": span.label,
                            "start_sec": span.start_sec,
                            "end_sec": span.end_sec,
                            "timestamp_mmss": span.timestamp_mmss,
                        }
                        for span in timestamped_issues
                    ]
                
                if timestamped_feedback:
                    logger.info(f"[OK] Timestamped feedback mapped ({len(timestamped_feedback)} issue types)")
            except Exception as e:
                logger.warning(f"Could not generate timestamped feedback: {str(e)}")
                # Continue without timestamped feedback
        
        # Extract timestamped words and fillers from raw_analysis
        timestamped_words = raw_analysis.get("timestamps", {}).get("words_timestamps_raw", [])
        timestamped_fillers = raw_analysis.get("timestamps", {}).get("filler_timestamps", [])
        
        # Format words with timestamp_mmss
        formatted_words = []
        for word_data in timestamped_words:
            if isinstance(word_data, dict):
                start = word_data.get("start", 0.0)
                end = word_data.get("end", 0.0)
                word = word_data.get("word", "")
                # Calculate MM:SS format
                start_min = int(start // 60)
                start_sec = int(start % 60)
                end_min = int(end // 60)
                end_sec = int(end % 60)
                timestamp_mmss = f"{start_min}:{start_sec:02d}-{end_min}:{end_sec:02d}"
                
                formatted_words.append({
                    "word": word,
                    "start_sec": round(start, 2),
                    "end_sec": round(end, 2),
                    "timestamp_mmss": timestamp_mmss,
                    "confidence": round(word_data.get("confidence", 0.0), 3),
                })
        
        # Format fillers with timestamp_mmss
        formatted_fillers = []
        for filler_data in timestamped_fillers:
            if isinstance(filler_data, dict):
                start = filler_data.get("start", 0.0)
                end = filler_data.get("end", 0.0)
                filler_type = filler_data.get("type", "filler")
                filler_word = filler_data.get("word", "")
                # Calculate MM:SS format
                start_min = int(start // 60)
                start_sec = int(start % 60)
                end_min = int(end // 60)
                end_sec = int(end % 60)
                timestamp_mmss = f"{start_min}:{start_sec:02d}-{end_min}:{end_sec:02d}"
                
                formatted_fillers.append({
                    "word": filler_word,
                    "type": filler_type,
                    "start_sec": round(start, 2),
                    "end_sec": round(end, 2),
                    "timestamp_mmss": timestamp_mmss,
                })
        
        final_report = {
            # Metadata
            "metadata": analysis["metadata"],
            
            # Speech transcript
            "transcript": transcript,
            
            # Fluency analysis
            "fluency_analysis": raw_analysis.get("fluency_analysis", {}),
            
            # Pronunciation (from analysis)
            "pronunciation": analysis["pronunciation"],
            
            # IELTS Band Scores WITH CONFIDENCE
            "band_scores": {
                "overall_band": band_scores["overall_band"],
                "criterion_bands": band_scores["criterion_bands"],
                "confidence": band_scores.get("confidence"),  # ✅ CONFIDENCE INCLUDED
                "descriptors": band_scores["descriptors"],
                "feedback": band_scores["feedback"],
            },
            
            # Timestamped Words (word-level timeline with confidence)
            "timestamped_words": formatted_words if formatted_words else None,
            
            # Timestamped Fillers (all detected fillers and stutters)
            "timestamped_fillers": formatted_fillers if formatted_fillers else None,
            
            # Timestamped Rubric Feedback (when word-level timestamps available)
            "timestamped_feedback": timestamped_feedback if timestamped_feedback else None,
            
            # Raw metrics used for scoring
            "metrics_for_scoring": make_json_safe(metrics_for_scoring),
            
            # Statistics
            "statistics": raw_analysis["statistics"],
            
            # Speech quality indicators
            "speech_quality": {
                "mean_word_confidence": analysis["pronunciation"]["intelligibility"]["mean_word_confidence"],
                "low_confidence_ratio": analysis["pronunciation"]["intelligibility"]["low_confidence_ratio"],
                "is_monotone": analysis["pronunciation"]["prosody"]["monotone_detected"],
            },
            
            # LLM analysis (if available)
            "llm_analysis": llm_analysis,
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