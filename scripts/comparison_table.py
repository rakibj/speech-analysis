#!/usr/bin/env python3
"""Generate comprehensive comparison table of current scoring"""
import json
from pathlib import Path
from src.core.ielts_band_scorer import IELTSBandScorer

analysis_dir = Path("outputs/audio_analysis")
scorer = IELTSBandScorer()

# Mapping of filenames to expected bands
expected_map = {
    'ielts5-5.5': 5.5,
    'ielts5.5': 5.5,
    'ielts7-7.5': 7.5,
    'ielts7': 7.0,
    'ielts8-8.5': 8.0,
    'ielts8.5': 8.5,
    'ielts9': 9.0,
}

# Original scores from Jan 19 (before any changes)
original_scores = {
    'ielts5-5.5': 6.5,
    'ielts5.5': 6.0,
    'ielts7-7.5': 7.5,
    'ielts7': 7.0,
    'ielts8-8.5': 8.0,
    'ielts8.5': 8.0,
    'ielts9': 8.0,
    'test_circular_reasoning': None,
    'test_good_speech_control': None,
    'test_off_topic_rambling': None,
    'test_random_idioms': None,
    'test_sophisticated_speech': None,
}

results = []

for analysis_file in sorted(analysis_dir.glob("*.json")):
    with open(analysis_file) as f:
        data = json.load(f)
    
    metrics = data['raw_analysis']
    stem = analysis_file.stem
    
    # Score acoustically
    fc = scorer.score_fluency(metrics)
    pr = scorer.score_pronunciation(metrics)
    lr = scorer.score_lexical(metrics, None)
    gr = scorer.score_grammar(metrics, None)
    
    weighted_avg = fc * 0.3 + pr * 0.2 + lr * 0.25 + gr * 0.25
    current = round(weighted_avg * 2) / 2
    
    expected = expected_map.get(stem)
    original = original_scores.get(stem)
    
    if expected:
        error_from_expected = current - expected
        status = "✓ MATCH" if abs(error_from_expected) < 0.1 else f"{error_from_expected:+.1f}"
    else:
        error_from_expected = None
        status = "N/A (test)"
    
    results.append({
        'file': stem,
        'expected': expected,
        'original': original,
        'current': current,
        'status': status,
        'fc': fc,
        'pr': pr,
        'lr': lr,
        'gr': gr,
    })

print("\n" + "=" * 130)
print("IELTS BAND SCORING - COMPREHENSIVE COMPARISON")
print("=" * 130)
print()
print(f"{'File':<30} {'Expected':<12} {'Original':<12} {'Current':<12} {'Status':<20} {'Criteria (FC/PR/LR/GR)':<40}")
print("-" * 130)

for r in results:
    criteria = f"{r['fc']}/{r['pr']}/{r['lr']}/{r['gr']}"
    expected_str = f"{r['expected']}" if r['expected'] else "—"
    original_str = f"{r['original']}" if r['original'] else "—"
    current_str = f"{r['current']}"
    
    print(f"{r['file']:<30} {expected_str:<12} {original_str:<12} {current_str:<12} {r['status']:<20} {criteria:<40}")

print()
print("=" * 130)
print("SUMMARY STATISTICS")
print("=" * 130)

# Only look at named tests (with expected values)
named_tests = [r for r in results if r['expected']]

if named_tests:
    avg_expected = sum(r['expected'] for r in named_tests) / len(named_tests)
    avg_original = sum(r['original'] for r in named_tests if r['original']) / len([r for r in named_tests if r['original']])
    avg_current = sum(r['current'] for r in named_tests) / len(named_tests)
    
    print(f"Named Tests (with expected bands): {len(named_tests)}")
    print(f"  Expected average:  {avg_expected:.2f}")
    print(f"  Original average:  {avg_original:.2f}")
    print(f"  Current average:   {avg_current:.2f}")
    print()
    
    # Count accuracy
    exact_matches = sum(1 for r in named_tests if abs(r['current'] - r['expected']) < 0.1)
    within_half = sum(1 for r in named_tests if abs(r['current'] - r['expected']) < 0.5)
    within_one = sum(1 for r in named_tests if abs(r['current'] - r['expected']) < 1.0)
    
    print(f"Accuracy Breakdown:")
    print(f"  Exact matches (±0.0):     {exact_matches}/{len(named_tests)} ({100*exact_matches/len(named_tests):.0f}%)")
    print(f"  Within ±0.5:              {within_half}/{len(named_tests)} ({100*within_half/len(named_tests):.0f}%)")
    print(f"  Within ±1.0:              {within_one}/{len(named_tests)} ({100*within_one/len(named_tests):.0f}%)")
    
    # Error analysis
    errors = [r['current'] - r['expected'] for r in named_tests]
    avg_error = sum(errors) / len(errors)
    print()
    print(f"Error Analysis:")
    print(f"  Average error: {avg_error:+.2f} (tendency to over-score if positive)")
    print(f"  Error range:   {min(errors):+.1f} to {max(errors):+.1f}")
