# analyze_band.py
import sys
from pathlib import Path
from src.analyzer_raw import analyze_speech
from src.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.ielts_band_scorer import IELTSBandScorer
from datetime import datetime

PROJECT_ROOT = Path.cwd().parent
sys.path.insert(0, str(PROJECT_ROOT))


def build_analysis(raw_analysis: dict) -> dict:
    """
    Build analysis report with band scoring.
    
    Now takes the raw_analysis dict directly and extracts metrics
    needed for the scorer.
    """
    
    # ---- Extract basic metrics ----
    total_words = raw_analysis["statistics"]["total_words_transcribed"]
    content_words = raw_analysis["statistics"]["content_words"]

    # ---- Extract word confidence metrics ----
    confidences = [
        w["confidence"]
        for w in raw_analysis["timestamps"]["words_timestamps_raw"]
        if w.get("confidence") is not None
    ]

    mean_word_confidence = (
        sum(confidences) / len(confidences) if confidences else 0.0
    )

    low_confidence_ratio = (
        sum(1 for c in confidences if c < 0.7) / len(confidences)
        if confidences else 0.0
    )

    # ---- Build metrics dict for scorer ----
    # Use the actual metrics from raw_analysis
    metrics_for_scoring = {
        # Fluency metrics
        "wpm": raw_analysis.get("wpm", 0),
        "long_pauses_per_min": raw_analysis.get("long_pauses_per_min", 0),
        "pause_variability": raw_analysis.get("pause_variability", 0),
        "repetition_ratio": raw_analysis.get("repetition_ratio", 0),
        
        # Pronunciation metrics
        "mean_word_confidence": mean_word_confidence,
        "low_confidence_ratio": low_confidence_ratio,
        
        # Lexical metrics
        "vocab_richness": raw_analysis.get("vocab_richness", 0),
        "lexical_density": raw_analysis.get("lexical_density", 0),
        
        # Grammar metrics
        "mean_utterance_length": raw_analysis.get("mean_utterance_length", 0),
        "speech_rate_variability": raw_analysis.get("speech_rate_variability", 0),
    }

    return {
        "metadata": {
            "audio_duration_sec": round(raw_analysis.get("audio_duration_sec", 0), 2),
            "speaking_time_sec": round(raw_analysis.get("speaking_time_sec", 0), 2),
            "total_words_transcribed": total_words,
            "content_word_count": content_words,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "fluency_analysis": raw_analysis.get("fluency_analysis", {}),
        
        # ==================================================
        # PRONUNCIATION
        # ==================================================
        "pronunciation": {
            "intelligibility": {
                "mean_word_confidence": round(mean_word_confidence, 3),
                "low_confidence_ratio": round(low_confidence_ratio, 3),
            },
            "prosody": {
                "monotone_detected": raw_analysis["statistics"].get("is_monotone", False),
            },
        },

        # ==================================================
        # RAW DATA (unchanged)
        # ==================================================
        "raw_data": {
            "word_timestamps": raw_analysis["timestamps"]["words_timestamps_raw"],
            "pause_events": raw_analysis.get("pause_events", []),
            "filler_events": raw_analysis["timestamps"].get("filler_timestamps", []),
            "stutter_events": raw_analysis.get("stutter_events", []),
        },
        
        # ==================================================
        # METRICS FOR SCORER (new)
        # ==================================================
        "metrics_for_scoring": metrics_for_scoring,
    }


async def analyze_band_from_audio(audio_path: str) -> dict:
    result = await analyze_speech(audio_path)
    analysis = build_analysis(result)
    
    # Score using the extracted metrics
    scorer = IELTSBandScorer()
    band_scores = scorer.score_overall(analysis["metrics_for_scoring"])
    
    return {"band_scores": band_scores, "analysis": analysis}


async def analyze_band_from_analysis(raw_analysis: dict) -> dict:
    analysis = build_analysis(raw_analysis)
    
    # Get raw transcript for LLM
    transcript = raw_analysis.get("raw_transcript", "")
    
    # Score using extracted metrics + LLM for semantic evaluation
    from src.ielts_band_scorer import score_ielts_speaking
    band_scores = score_ielts_speaking(
        metrics=analysis["metrics_for_scoring"],
        transcript=transcript,
        use_llm=True,  # Enable LLM for semantic evaluation
    )
    
    return {"band_scores": band_scores, "analysis": analysis}
