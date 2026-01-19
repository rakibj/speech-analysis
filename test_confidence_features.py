"""Test confidence and timestamped feedback features."""
import json
from src.core.ielts_band_scorer import IELTSBandScorer

# Load a test band_results file
with open("outputs/band_results/ielts9.json") as f:
    band_data = json.load(f)

# Load the corresponding audio analysis
with open("outputs/audio_analysis/ielts9.json") as f:
    audio_data = json.load(f)

# Extract metrics
raw_analysis = audio_data.get("raw_analysis", {})
metrics = {
    "wpm": raw_analysis.get("wpm", 0),
    "unique_word_count": raw_analysis.get("unique_word_count", 0),
    "fillers_per_min": raw_analysis.get("fillers_per_min", 0),
    "long_pauses_per_min": raw_analysis.get("long_pauses_per_min", 0),
    "pause_variability": raw_analysis.get("pause_variability", 0),
    "pause_frequency": raw_analysis.get("pause_frequency", 0),
    "pause_time_ratio": raw_analysis.get("pause_time_ratio", 0),
    "vocab_richness": raw_analysis.get("vocab_richness", 0),
    "repetition_ratio": raw_analysis.get("repetition_ratio", 0),
    "speech_rate_variability": raw_analysis.get("speech_rate_variability", 0),
    "mean_word_confidence": raw_analysis.get("mean_word_confidence", 0.9),
    "low_confidence_ratio": raw_analysis.get("low_confidence_ratio", 0),
    "audio_duration_sec": raw_analysis.get("audio_duration_sec", 0),
    "lexical_density": raw_analysis.get("lexical_density", 0),
}

# Test confidence calculation
scorer = IELTSBandScorer()

# Create mock band scores from existing results
existing_scores = band_data.get("band_scores", {})
band_scores = {
    "overall_band": band_data.get("overall_band", 8.0),
    "criterion_bands": {
        "fluency_coherence": existing_scores.get("fluency_coherence", 8.0),
        "pronunciation": existing_scores.get("pronunciation", 8.0),
        "lexical_resource": existing_scores.get("lexical_resource", 8.0),
        "grammatical_range_accuracy": existing_scores.get("grammatical_range_accuracy", 8.0),
    }
}

# Calculate confidence
confidence = scorer.calculate_confidence_score(metrics, band_scores, None)

print("\n=== CONFIDENCE ANALYSIS ===")
print(f"Overall Confidence: {confidence['overall_confidence']}")
print(f"Category: {confidence['confidence_category']}")
print(f"Recommendation: {confidence['recommendation']}")
print("\nFactor Breakdown:")
for factor_name, factor_data in confidence['factor_breakdown'].items():
    print(f"  {factor_name}:")
    for key, value in factor_data.items():
        if isinstance(value, float):
            print(f"    {key}: {value:.2f}")
        else:
            print(f"    {key}: {value}")

print("\n✓ Confidence calculation working!")
print("\nNote: Timestamped feedback requires LLM annotations (from full pipeline)")
