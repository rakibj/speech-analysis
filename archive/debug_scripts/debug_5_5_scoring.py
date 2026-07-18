"""Debug why ielts5-5.5 is scoring 7.0 overall."""
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
print("DEBUG: Why is ielts5-5.5 scoring 7.0 overall?")
print("="*80)

print("\n[METRICS]")
print(f"  WPM: {metrics['wpm']:.2f}")
print(f"  Mean word confidence: {metrics['mean_word_confidence']:.3f}")
print(f"  Low confidence ratio: {metrics['low_confidence_ratio']:.3f}")
print(f"  Fillers per min: {metrics['fillers_per_min']:.2f}")
print(f"  Long pauses per min: {metrics['long_pauses_per_min']:.2f}")
print(f"  Pause variability: {metrics['pause_variability']:.3f}")
print(f"  Speech rate variability: {metrics['speech_rate_variability']:.3f}")
print(f"  Vocab richness: {metrics['vocab_richness']:.3f}")
print(f"  Repetition ratio: {metrics['repetition_ratio']:.3f}")
print(f"  Audio duration: {metrics['audio_duration_sec']:.2f}s")

# Score individually
scorer = IELTSBandScorer()

fluency = scorer.score_fluency(metrics)
pronunciation = scorer.score_pronunciation(metrics)
lexical = scorer.score_lexical(metrics, None)
grammar = scorer.score_grammar(metrics, None)

print("\n[INDIVIDUAL CRITERION SCORES]")
print(f"  Fluency/Coherence: {fluency}")
print(f"  Pronunciation: {pronunciation}")
print(f"  Lexical Resource: {lexical}")
print(f"  Grammar/Accuracy: {grammar}")

# Calculate weighted average
weighted_avg = (fluency * 0.3 + pronunciation * 0.2 + lexical * 0.25 + grammar * 0.25)
print(f"\n[WEIGHTED CALCULATION]")
print(f"  Fluency × 0.3 = {fluency} × 0.3 = {fluency * 0.3:.3f}")
print(f"  Pronunciation × 0.2 = {pronunciation} × 0.2 = {pronunciation * 0.2:.3f}")
print(f"  Lexical × 0.25 = {lexical} × 0.25 = {lexical * 0.25:.3f}")
print(f"  Grammar × 0.25 = {grammar} × 0.25 = {grammar * 0.25:.3f}")
print(f"  Weighted avg = {weighted_avg:.3f}")

from src.core.ielts_band_scorer import round_half
overall_before_penalties = round_half(weighted_avg)
print(f"  After rounding to 0.5: {overall_before_penalties}")

# Check penalties
print(f"\n[PENALTY CHECKS]")
print(f"  Min criterion score: {min([fluency, pronunciation, lexical, grammar])}")
if min([fluency, pronunciation, lexical, grammar]) <= 5.5:
    print(f"  → Should apply hard cap at 6.0")
else:
    print(f"  → No cap (min >= 5.5)")

high_bands = sum(1 for s in [fluency, pronunciation, lexical, grammar] if s >= 8.0)
print(f"  High bands (>=8.0): {high_bands}")
if high_bands >= 3 and min([fluency, pronunciation, lexical, grammar]) >= 7.5:
    print(f"  → Boost to 8.5 (3+ high bands & min >= 7.5)")
elif high_bands >= 2 and min([fluency, pronunciation, lexical, grammar]) >= 7.0:
    print(f"  → Boost to 8.0 (2+ high bands & min >= 7.0)")
else:
    print(f"  → No boost applied")

# Full score
result = scorer.score_overall_with_feedback(metrics, "", None)
overall = result["overall_band"]

print(f"\n[FINAL RESULT]")
print(f"  Overall band: {overall}")
print(f"  Confidence: {result['confidence']['overall_confidence']}")

print("\n[ANALYSIS]")
if fluency >= 6.5 and pronunciation >= 6.5 and lexical >= 7.0:
    print("  ⚠️  Lexical is high (7.0) - this is boosting the overall score!")
    print("  This speaker may have decent vocabulary but poor fluency/pronunciation")
    print(f"     - Fluency: {fluency} (low for score of 7.0)")
    print(f"     - Pronunciation: {pronunciation} (acceptable)")
    print(f"     - Lexical: {lexical} (HIGH - why?)")
    print(f"     - Grammar: {grammar}")

print("\n[RECOMMENDATION]")
print("Check:")
print("  1. Why is lexical so high for a 5-5.5 band speaker?")
print("  2. Are LLM metrics being used? (advanced_vocabulary count)")
print("  3. Should there be tighter coupling between criteria?")
