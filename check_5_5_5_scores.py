#!/usr/bin/env python3
"""Check actual criterion scores for ielts5-5.5."""
import json
from src.core.ielts_band_scorer import IELTSBandScorer

with open('outputs/audio_analysis/ielts5-5.5.json') as f:
    audio_data = json.load(f)

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

scorer = IELTSBandScorer()

# Score each criterion
print("Scoring ielts5-5.5.json:")
print(f"\nMetrics:")
print(f"  WPM: {metrics['wpm']:.2f}")
print(f"  Vocab richness: {metrics['vocab_richness']:.3f}")
print(f"  Lexical density: {metrics['lexical_density']:.3f}")
print(f"  Mean utterance length: {metrics['mean_utterance_length']:.2f}")

fc = scorer.score_fluency(metrics)
pr = scorer.score_pronunciation(metrics)
lr = scorer.score_lexical(metrics)
gr = scorer.score_grammar(metrics)

print(f"\nCriteria before coupling:")
print(f"  Fluency/Coherence: {fc:.1f}")
print(f"  Pronunciation: {pr:.1f}")
print(f"  Lexical Resource: {lr:.1f}")
print(f"  Grammar/Accuracy: {gr:.1f}")

print(f"\nWeighted calculation:")
print(f"  Fluency × 0.3 = {fc:.1f} × 0.3 = {fc * 0.3:.3f}")
print(f"  Pronunciation × 0.2 = {pr:.1f} × 0.2 = {pr * 0.2:.3f}")
print(f"  Lexical × 0.25 = {lr:.1f} × 0.25 = {lr * 0.25:.3f}")
print(f"  Grammar × 0.25 = {gr:.1f} × 0.25 = {gr * 0.25:.3f}")
weighted = fc * 0.3 + pr * 0.2 + lr * 0.25 + gr * 0.25
print(f"  Weighted avg: {weighted:.3f} → {round(weighted * 2) / 2:.1f}")

result = scorer.score_overall_with_feedback(metrics, transcript)
print(f"\nFull scoring result: {result['overall_band']:.1f}")
