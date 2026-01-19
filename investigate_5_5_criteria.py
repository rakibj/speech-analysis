"""Investigate lexical and grammar scoring for ielts5-5.5."""
import json
from src.core.ielts_band_scorer import IELTSBandScorer

# Load audio analysis
with open("outputs/audio_analysis/ielts5-5.5.json") as f:
    audio_data = json.load(f)

raw_analysis = audio_data.get("raw_analysis", {})

# Build metrics
metrics = {
    "wpm": raw_analysis.get("wpm", 0),
    "unique_word_count": raw_analysis.get("unique_word_count", 0),
    "fillers_per_min": raw_analysis.get("fillers_per_min", 0),
    "stutters_per_min": raw_analysis.get("stutters_per_min", 0),
    "long_pauses_per_min": raw_analysis.get("long_pauses_per_min", 0),
    "very_long_pauses_per_min": raw_analysis.get("very_long_pauses_per_min", 0),
    "pause_frequency": raw_analysis.get("pause_frequency", 0),
    "pause_time_ratio": raw_analysis.get("pause_time_ratio", 0),
    "pause_variability": raw_analysis.get("pause_variability", 0),
    "vocab_richness": raw_analysis.get("vocab_richness", 0),
    "repetition_ratio": raw_analysis.get("repetition_ratio", 0),
    "speech_rate_variability": raw_analysis.get("speech_rate_variability", 0),
    "mean_utterance_length": raw_analysis.get("mean_utterance_length", 0),
    "pause_after_filler_rate": raw_analysis.get("pause_after_filler_rate", 0),
    "mean_word_confidence": raw_analysis.get("mean_word_confidence", 0.9),
    "low_confidence_ratio": raw_analysis.get("low_confidence_ratio", 0),
    "lexical_density": raw_analysis.get("lexical_density", 0),
    "audio_duration_sec": raw_analysis.get("audio_duration_sec", 0),
}

print("="*80)
print("INVESTIGATING: Why Lexical=7.0 and Grammar=7.0 for 5-5.5 band?")
print("="*80)

scorer = IELTSBandScorer()

print("\n[LEXICAL RESOURCE SCORING]")
print(f"  vocab_richness: {metrics['vocab_richness']:.3f}")
print(f"  unique_word_count: {metrics['unique_word_count']}")
print(f"  lexical_density: {metrics['lexical_density']:.3f}")

# Read the source to understand thresholds
print("\n  Scoring logic:")
print(f"    - vocab_richness >= 0.5 → band 8.5")
print(f"    - vocab_richness >= 0.45 → band 8.0")
print(f"    - vocab_richness >= 0.40 → band 7.5")
print(f"    - vocab_richness >= 0.35 → band 7.0")
print(f"  Current vocab_richness: {metrics['vocab_richness']:.3f} ✓ >= 0.35 → 7.0")

print("\n  Issue: vocab_richness baseline (0.48) is naturally high!")
print("  This doesn't account for weak fluency/pronunciation")
print("  → Lexical should be LOWER if fluency/pronunciation are weak")

print("\n[GRAMMAR/ACCURACY SCORING]")
fluency = scorer.score_fluency(metrics)
print(f"  Fluency score: {fluency}")
print(f"  repetition_ratio: {metrics['repetition_ratio']:.3f}")
print(f"  pause_variability: {metrics['pause_variability']:.3f}")

print("\n  Scoring logic (when fluency < 7.0):")
print(f"    - Base score: {fluency}")
print(f"    - repetition_ratio >= 0.04 → no boost")
print(f"  Current repetition: {metrics['repetition_ratio']:.3f} (just below 0.04)")

print("\n  Issue: Grammar is just rounding fluency!")
print("  This doesn't evaluate actual grammatical structures")
print("  → Grammar is inflated because fluency is 6.5")

print("\n[ROOT CAUSE]")
print("  ❌ Lexical and Grammar are NOT dependent on low Fluency/Pronunciation")
print("  ❌ They should be penalized when other criteria are weak")
print("  ❌ Currently: vocab_richness alone drives lexical (0.48 → 7.0)")
print("  ❌ Grammar just copies fluency without real grammar analysis")

print("\n[SOLUTION]")
print("  Need to add INTER-CRITERION COUPLING:")
print("  1. If Fluency < 6.5, cap Lexical at max(lexical, fluency + 0.5)")
print("  2. If Fluency < 6.5, cap Grammar at max(grammar, fluency + 0.5)")
print("  3. Or: Use hard minimum - overall can't exceed (fluency + 1.0)")

print("\n[EXPECTED vs ACTUAL]")
print("  Expected for 5-5.5 band: Overall 5.5-6.5")
print("  Actual: 7.0 (too high by 0.5-1.5 bands!)")
