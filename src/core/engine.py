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
    
    Returns everything except timestamps, includes transcript.
    
    Args:
        audio_path: Path to audio file
        context: Speech context (conversational, narrative, presentation, interview)
        device: Device to use (cpu or cuda)
        use_llm: Whether to use LLM for semantic evaluation
        
    Returns:
        dict with:
            - metadata: audio info, timestamps
            - transcript: raw speech transcript
            - fluency_analysis: fluency metrics
            - pronunciation: intelligibility and prosody
            - band_scores: IELTS band scoring
            - feedback: user-facing feedback
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
        if use_llm and transcript:
            try:
                logger.info("Stage 4: Running LLM annotation analysis...")
                llm_annotations = extract_llm_annotations(transcript)
                llm_analysis = aggregate_llm_metrics(llm_annotations)
                logger.info("[OK] LLM analysis complete")
            except Exception as e:
                logger.warning(f"LLM analysis failed (continuing): {str(e)}")
                llm_analysis = None
        
        # =============================================
        # BUILD FINAL REPORT (NO TIMESTAMPS)
        # =============================================
        logger.info("Finalizing report...")
        
        final_report = {
            # Metadata
            "metadata": analysis["metadata"],
            
            # Speech transcript
            "transcript": transcript,
            
            # Fluency analysis
            "fluency_analysis": raw_analysis.get("fluency_analysis", {}),
            
            # Pronunciation (from analysis)
            "pronunciation": analysis["pronunciation"],
            
            # IELTS Band Scores
            "band_scores": {
                "overall_band": band_scores["overall_band"],
                "criterion_bands": band_scores["criterion_bands"],
                "descriptors": band_scores["descriptors"],
                "feedback": band_scores["feedback"],
            },
            
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