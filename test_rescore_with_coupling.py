#!/usr/bin/env python3
"""Re-score ielts5-5.5 with the new inter-criterion coupling to show the fix."""
import json
from src.core.ielts_band_scorer import IELTSBandScorer

# Load audio analysis
with open('outputs/audio_analysis/ielts5-5.5.json') as f:
    audio_data = json.load(f)

# Extract metrics from raw_analysis  
raw = audio_data['raw_analysis']
metrics = {
    'wpm': raw.get('wpm', 0),
    'mean_word_confidence': raw.get('mean_word_confidence', 0),
    'low_confidence_ratio': raw.get('low_confidence_ratio', 0),
    'fillers_per_min': raw.get('fillers_per_min', 0),
    'long_pauses_per_min': raw.get('long_pauses_per_min', 0),
    'pause_variability': raw.get('pause_variability', 0),
    'speech_rate_variability': raw.get('speech_rate_variability', 0),
    'vocab_richness': raw.get('vocab_richness', 0),
    'lexical_density': raw.get('lexical_density', 0),
    'repetition_ratio': raw.get('repetition_ratio', 0),
    'audio_duration_sec': raw.get('audio_duration_sec', 0),
    'stutters_per_min': raw.get('stutters_per_min', 0),
    'mean_utterance_length': raw.get('mean_utterance_length', 0),
    'unique_word_count': raw.get('unique_word_count', 0),
}
transcript = raw.get('raw_transcript', '')

print("=" * 80)
print("RE-SCORING IELTS5-5.5 WITH INTER-CRITERION COUPLING FIX")
print("=" * 80)

print(f"\n[METRICS EXTRACTED]")
print(f"  WPM: {metrics['wpm']:.2f}")
print(f"  Fillers/min: {metrics['fillers_per_min']:.2f}")
print(f"  Vocab richness: {metrics['vocab_richness']:.3f}")
print(f"  Audio duration: {metrics['audio_duration_sec']:.2f}s")

# Score with coupling applied
scorer = IELTSBandScorer()
result = scorer.score_overall_with_feedback(metrics, transcript)

print(f"\n[CRITERION SCORES (WITH COUPLING)]")
print(f"  Fluency/Coherence: {result['criterion_bands']['fluency_coherence']:.1f}")
print(f"  Pronunciation: {result['criterion_bands']['pronunciation']:.1f}")
print(f"  Lexical Resource: {result['criterion_bands']['lexical_resource']:.1f}")
print(f"  Grammar/Accuracy: {result['criterion_bands']['grammatical_range_accuracy']:.1f}")

print(f"\n[OVERALL BAND]")
print(f"  NEW Score: {result['overall_band']:.1f} (with coupling)")
print(f"  OLD Score: 7.0 (without coupling)")
print(f"  Improvement: {7.0 - result['overall_band']:.1f} bands")

print(f"\n[COUPLING ANALYSIS]")
fc = result['criterion_bands']['fluency_coherence']
pr = result['criterion_bands']['pronunciation']
lr = result['criterion_bands']['lexical_resource']
gr = result['criterion_bands']['grammatical_range_accuracy']

print(f"  Fluency: {fc:.1f}")
if fc < 6.5:
    print(f"    → Lexical/Grammar capped at fluency + 0.5 = {fc + 0.5:.1f}")
elif fc < 7.0:
    print(f"    → Lexical/Grammar capped at fluency + 1.0 = {fc + 1.0:.1f}")
else:
    print(f"    → No cap (fluency >= 7.0)")

print(f"  Pronunciation: {pr:.1f}")
if pr < 6.5:
    print(f"    → Lexical/Grammar capped at pronunciation + 1.0 = {pr + 1.0:.1f}")

print(f"  Lexical: {lr:.1f}")
print(f"  Grammar: {gr:.1f}")

print(f"\n[CONFIDENCE]")
print(f"  Confidence score: {result['confidence']['overall_confidence']:.2f}")
print(f"  Category: {result['confidence'].get('confidence_category', 'N/A')}")

print("\n" + "=" * 80)
