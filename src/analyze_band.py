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
    llm_metrics: dict,
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
        "fluency_coherence": {
            "pauses": {
                "pause_frequency_per_min": result.get("pause_frequency"),
                "long_pause_rate": result["long_pauses_per_min"],
                "pause_variability": float(result["pause_variability"]),
            },
            "rate": {
                "speech_rate_wpm": float(result["wpm"]),
                "speech_rate_variability": float(result["speech_rate_variability"]),
            },
            "disfluency": {
                "filler_frequency_per_min": float(result["fillers_per_min"]),
                "stutter_frequency_per_min": float(result["stutters_per_min"]),
                "repetition_rate": float(result["repetition_ratio"]),
            },
            "coherence": {
                "coherence_breaks": llm_metrics["coherence_breaks"],
                "topic_relevance": llm_metrics["topic_relevance"],
            },
        },
        "lexical_resource": {
            "breadth": {
                "unique_word_count": int(
                    round(result["vocab_richness"] * content_words)
                ),
                "lexical_diversity": float(result["vocab_richness"]),
                "lexical_density": round(result["lexical_density"], 3),
                "most_frequent_word_ratio": float(result["repetition_ratio"]),
            },
            "quality": {
                "word_choice_errors": llm_metrics["word_choice_errors"],
                "advanced_vocabulary_count": llm_metrics["advanced_vocabulary_count"],
            },
        },
        "grammatical_range_accuracy": {
            "complexity": {
                "mean_utterance_length": float(result["mean_utterance_length"]),
                "complex_structures_attempted": llm_metrics["complex_structures_attempted"],
                "complex_structures_accurate": llm_metrics["complex_structures_accurate"],
            },
            "accuracy": {
                "grammar_errors": llm_metrics["grammar_errors"],
                "meaning_blocking_error_ratio": llm_metrics["meaning_blocking_error_ratio"],
            },
        },
        "pronunciation": {
            "intelligibility": {
                "mean_word_confidence": round(mean_word_confidence, 3),
                "low_confidence_ratio": round(low_confidence_ratio, 3),
            },
            "prosody": {
                "monotone_detected": result["statistics"]["is_monotone"],
            },
        },
        "raw_data": {
            "word_timestamps": result["timestamps"]["words_timestamps_raw"],
            "pause_events": result.get("pause_events", []),
            "filler_events": result["timestamps"]["filler_timestamps"],
            "stutter_events": result.get("stutter_events", []),
        },
    }

async def analyze_band_from_audio(audio_path: str) -> dict:
    """Analyze speech and score IELTS band."""
    result = await analyze_speech(audio_path)
    llm_result = extract_llm_annotations(result["raw_transcript"])
    llm_metrics = aggregate_llm_metrics(llm_result)
    scorer = IELTSBandScorer()
    analysis = build_analysis(result, llm_metrics)
    band_scores = scorer.score(analysis)
    report = {"band_scores": band_scores, "analysis": analysis}
    return report


async def analyze_band_from_analysis(raw_analysis: dict, llm_metrics: dict) -> dict:
    """Analyze speech and score IELTS band."""
    scorer = IELTSBandScorer()
    analysis = build_analysis(raw_analysis, llm_metrics)
    band_scores = scorer.score(analysis)
    report = {"band_scores": band_scores, "analysis": analysis}
    return report

