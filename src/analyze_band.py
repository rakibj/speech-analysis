# analyze_band.py
import sys
from pathlib import Path
from src.analyzer_raw import analyze_speech
from src.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.ielts_band_scorer import IELTSBandScorer
from datetime import datetime

PROJECT_ROOT = Path.cwd().parent
sys.path.insert(0, str(PROJECT_ROOT))


def build_analysis(
    result: dict,
) -> dict:
    # ---- Lexical density ----
    total_words = result["statistics"]["total_words_transcribed"]
    content_words = result["statistics"]["content_words"]

    # ---- Word confidence metrics ----
    confidences = [
        w["confidence"]
        for w in result["timestamps"]["words_timestamps_raw"]
        if w.get("confidence") is not None
    ]

    mean_word_confidence = (
        sum(confidences) / len(confidences) if confidences else 0.0
    )

    low_confidence_ratio = (
        sum(1 for c in confidences if c < 0.7) / len(confidences)
        if confidences else 0.0
    )

    return {
        "metadata": {
            "audio_duration_sec": round(result["audio_duration_sec"], 2),
            "speaking_time_sec": round(result["speaking_time_sec"], 2),
            "total_words_transcribed": total_words,
            "content_word_count": content_words,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "fluency_analysis": result.get("fluency_analysis", {}),
        # ==================================================
        # PRONUNCIATION
        # ==================================================
        "pronunciation": {
            "intelligibility": {
                "mean_word_confidence": round(mean_word_confidence, 3),
                "low_confidence_ratio": round(low_confidence_ratio, 3),
            },
            "prosody": {
                "monotone_detected": result["statistics"]["is_monotone"],
            },
        },

        # ==================================================
        # RAW DATA (unchanged)
        # ==================================================
        "raw_data": {
            "word_timestamps": result["timestamps"]["words_timestamps_raw"],
            "pause_events": result.get("pause_events", []),
            "filler_events": result["timestamps"]["filler_timestamps"],
            "stutter_events": result.get("stutter_events", []),
        },
    }


async def analyze_band_from_audio(audio_path: str) -> dict:
    result = await analyze_speech(audio_path)
    scorer = IELTSBandScorer()
    analysis = build_analysis(result)
    band_scores = scorer.score_overall(analysis)
    return {"band_scores": band_scores, "analysis": analysis}


async def analyze_band_from_analysis(raw_analysis: dict) -> dict:
    scorer = IELTSBandScorer()
    analysis = build_analysis(raw_analysis)
    band_scores = scorer.score_overall(analysis)
    return {"band_scores": band_scores, "analysis": analysis}
