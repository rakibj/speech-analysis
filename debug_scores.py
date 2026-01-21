#!/usr/bin/env python3
"""Debug: Check why all scores are 6.5"""
import json
from src.core.ielts_band_scorer import IELTSBandScorer

# Load analysis
with open('outputs/audio_analysis/ielts5-5.5.json') as f:
    data = json.load(f)

metrics = data['raw_analysis']

# Debug individual scores
scorer = IELTSBandScorer()

fc = scorer.score_fluency(metrics)
pr = scorer.score_pronunciation(metrics)
lr = scorer.score_lexical(metrics, None)
gr = scorer.score_grammar(metrics, None)

print("=" * 60)
print("METRIC VALUES:")
print("=" * 60)
print(f"wpm: {metrics.get('wpm')}")
print(f"long_pauses_per_min: {metrics.get('long_pauses_per_min')}")
print(f"pause_variability: {metrics.get('pause_variability')}")
print(f"mean_word_confidence: {metrics.get('mean_word_confidence')}")
print(f"low_confidence_ratio: {metrics.get('low_confidence_ratio')}")
print(f"vocab_richness: {metrics.get('vocab_richness')}")
print(f"lexical_density: {metrics.get('lexical_density')}")
print(f"repetition_ratio: {metrics.get('repetition_ratio')}")
print(f"mean_utterance_length: {metrics.get('mean_utterance_length')}")

print("\n" + "=" * 60)
print("SCORED VALUES:")
print("=" * 60)
print(f"Fluency: {fc}")
print(f"Pronunciation: {pr}")
print(f"Lexical: {lr}")
print(f"Grammar: {gr}")

# Full score
result = scorer.score_overall_with_feedback(metrics, "")
print("\n" + "=" * 60)
print("OVERALL RESULT:")
print("=" * 60)
print(json.dumps({
    "overall_band": result["overall_band"],
    "criterion_bands": result["criterion_bands"]
}, indent=2))
