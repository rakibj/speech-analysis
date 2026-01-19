#!/usr/bin/env python3
"""Debug why regeneration isn't picking up the coupling fix."""
import json
import os
from src.core.ielts_band_scorer import IELTSBandScorer

audio_path = 'outputs/audio_analysis/ielts5-5.5.json'

with open(audio_path) as f:
    audio_data = json.load(f)

raw = audio_data['raw_analysis']

print("Metrics being loaded:")
print(f"  vocab_richness: {raw.get('vocab_richness', 0)}")
print(f"  lexical_density: {raw.get('lexical_density', 0)}")
print(f"  wpm: {raw.get('wpm', 0)}")

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
result = scorer.score_overall_with_feedback(metrics, transcript)

print(f"\nResult:")
print(f"  Overall: {result['overall_band']}")
print(f"  Criterion bands:")
for key, value in result['criterion_bands'].items():
    print(f"    {key}: {value}")
