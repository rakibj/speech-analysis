#!/usr/bin/env python3
"""Verify that coupling produces deterministic results."""
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
    'repetition_ratio': raw.get('repetition_ratio', 0),
    'audio_duration_sec': raw.get('audio_duration_sec', 0),
    'stutters_per_min': raw.get('stutters_per_min', 0),
    'mean_utterance_length': raw.get('mean_utterance_length', 0),
}
transcript = raw.get('raw_transcript', '')

print("Testing determinism of coupling fix (10 runs):")
scores = []
for i in range(10):
    scorer = IELTSBandScorer()
    result = scorer.score_overall_with_feedback(metrics, transcript)
    scores.append(result['overall_band'])
    print(f"  Run {i+1}: {result['overall_band']:.1f}")

if len(set(scores)) == 1:
    print(f"\n✅ DETERMINISTIC - All 10 runs produced {scores[0]:.1f}")
else:
    print(f"\n⚠️  INCONSISTENT - Got {set(scores)}")
