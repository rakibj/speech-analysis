#!/usr/bin/env python3
"""Check what the CURRENT code scores all files as"""
import json
from pathlib import Path
from src.core.ielts_band_scorer import IELTSBandScorer

analysis_dir = Path("outputs/audio_analysis")
scorer = IELTSBandScorer()

files_to_check = ['ielts5-5.5', 'ielts7', 'ielts8.5', 'ielts9']

print("CURRENT CODE SCORING (with calibrated thresholds):")
print("=" * 90)
print(f"{'File':<20} {'Overall':<12} {'Criteria':<50} {'Expected':<12}")
print("-" * 90)

expected_map = {'ielts5-5.5': '5.5', 'ielts7': '7.0', 'ielts8.5': '8.5', 'ielts9': '9.0'}

for fname in files_to_check:
    analysis_file = analysis_dir / f"{fname}.json"
    with open(analysis_file) as f:
        data = json.load(f)
    
    metrics = data['raw_analysis']
    
    fc = scorer.score_fluency(metrics)
    pr = scorer.score_pronunciation(metrics)
    lr = scorer.score_lexical(metrics, None)
    gr = scorer.score_grammar(metrics, None)
    
    weighted_avg = fc * 0.3 + pr * 0.2 + lr * 0.25 + gr * 0.25
    overall = round(weighted_avg * 2) / 2
    
    criteria_str = f"FC:{fc} PR:{pr} LR:{lr} GR:{gr}"
    expected = expected_map[fname]
    
    print(f"{fname:<20} {overall:<12} {criteria_str:<50} {expected:<12}")

print()
print("=" * 90)
print("COMPARISON TABLE:")
print("=" * 90)
print(f"{'File':<20} {'Expected':<12} {'Original':<12} {'Current':<12} {'Change':<12}")
print("-" * 90)

original_scores = {
    'ielts5-5.5': 6.5,
    'ielts7': 7.0,
    'ielts8.5': 8.0,
    'ielts9': 8.0
}

expected_scores = {
    'ielts5-5.5': 5.5,
    'ielts7': 7.0,
    'ielts8.5': 8.5,
    'ielts9': 9.0
}

for fname in files_to_check:
    analysis_file = analysis_dir / f"{fname}.json"
    with open(analysis_file) as f:
        data = json.load(f)
    
    metrics = data['raw_analysis']
    fc = scorer.score_fluency(metrics)
    pr = scorer.score_pronunciation(metrics)
    lr = scorer.score_lexical(metrics, None)
    gr = scorer.score_grammar(metrics, None)
    
    weighted_avg = fc * 0.3 + pr * 0.2 + lr * 0.25 + gr * 0.25
    current = round(weighted_avg * 2) / 2
    
    expected = expected_scores[fname]
    original = original_scores[fname]
    change = current - original
    
    print(f"{fname:<20} {expected:<12} {original:<12} {current:<12} {change:+.1f}")
