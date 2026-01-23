#!/usr/bin/env python3
"""Test that scoring works after revert"""
from src.core.ielts_band_scorer import score_ielts_speaking

# Test metrics
metrics = {
    'wpm': 120,
    'long_pauses_per_min': 1.0,
    'pause_variability': 0.5,
    'repetition_ratio': 0.05,
    'mean_word_confidence': 0.90,
    'low_confidence_ratio': 0.10,
    'vocab_richness': 0.50,
    'lexical_density': 0.45,
    'mean_utterance_length': 20,
    'speech_rate_variability': 0.25,
}

result = score_ielts_speaking(metrics, use_llm=False)
print('Score test successful!')
print(f'Overall band: {result["overall_band"]}')
print('Criterion bands:')
for key, val in result["criterion_bands"].items():
    print(f'  {key}: {val}')
