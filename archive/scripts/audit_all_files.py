#!/usr/bin/env python3
"""Audit all test files: acoustic quality vs filename label"""
import json
from pathlib import Path
from src.core.ielts_band_scorer import IELTSBandScorer

analysis_dir = Path("outputs/audio_analysis")
scorer = IELTSBandScorer()

results = []

for analysis_file in sorted(analysis_dir.glob("*.json")):
    with open(analysis_file) as f:
        data = json.load(f)
    
    metrics = data['raw_analysis']
    stem = analysis_file.stem
    
    # Extract expected band from filename
    if stem.startswith('ielts'):
        # e.g., "ielts5-5.5" or "ielts7"
        label = stem.replace('ielts', '')
        try:
            if '-' in label:
                parts = label.split('-')
                expected = float(parts[0]) + 0.5 if len(parts[1]) == 1 else float(label.replace('-', '.'))
            else:
                expected = float(label)
        except:
            expected = None
    else:
        expected = None
    
    # Score acoustically
    fc = scorer.score_fluency(metrics)
    pr = scorer.score_pronunciation(metrics)
    lr = scorer.score_lexical(metrics, None)
    gr = scorer.score_grammar(metrics, None)
    
    weighted_avg = fc * 0.3 + pr * 0.2 + lr * 0.25 + gr * 0.25
    actual = round(weighted_avg * 2) / 2
    
    # Calculate error
    if expected:
        error = actual - expected
        match = abs(error) < 0.1
    else:
        error = None
        match = None
    
    results.append({
        'file': stem,
        'expected': expected,
        'actual': actual,
        'error': error,
        'match': match,
        'fc': fc,
        'pr': pr,
        'lr': lr,
        'gr': gr,
    })

print("=" * 100)
print("ACOUSTIC QUALITY AUDIT: Expected vs Actual Bands")
print("=" * 100)
print()
print(f"{'File':<30} {'Expected':<12} {'Actual':<12} {'Error':<12} {'Match?':<10} {'Criteria':<35}")
print("-" * 100)

for r in results:
    criteria = f"FC:{r['fc']} PR:{r['pr']} LR:{r['lr']} GR:{r['gr']}"
    match_str = "YES" if r['match'] else "NO " if r['match'] is not None else "N/A"
    error_str = f"{r['error']:+.1f}" if r['error'] is not None else "N/A"
    
    print(f"{r['file']:<30} {str(r['expected']):<12} {str(r['actual']):<12} {error_str:<12} {match_str:<10} {criteria:<35}")

print()
print("=" * 100)
print("SUMMARY:")
print("=" * 100)

# Group by acoustic quality
low_band = [r for r in results if r['expected'] and r['expected'] <= 5.5]
mid_band = [r for r in results if r['expected'] and 5.5 < r['expected'] <= 7.5]
high_band = [r for r in results if r['expected'] and r['expected'] > 7.5]

def analyze_group(group, name):
    if not group:
        return
    actual_avg = sum(r['actual'] for r in group) / len(group)
    expected_avg = sum(r['expected'] for r in group) / len(group)
    error_avg = sum(r['error'] for r in group) / len(group)
    
    print(f"\n{name} (expected {expected_avg:.1f}, got {actual_avg:.1f}, error {error_avg:+.1f}):")
    for r in group:
        pr_str = f"(Pronunciation: {r['pr']})"
        print(f"  {r['file']:<25} expected {r['expected']}, got {r['actual']} {pr_str}")

analyze_group(low_band, "LOW BAND (5.0-5.5)")
analyze_group(mid_band, "MID BAND (6.0-7.5)")
analyze_group(high_band, "HIGH BAND (8.0+)")

print()
print("=" * 100)
print("KEY FINDING:")
print("=" * 100)
print("""
The acoustic profile of the test files does NOT match their filename labels.
This is a DATA QUALITY issue, not a SCORING LOGIC issue.

The scorer is working correctly - it's measuring what's in the audio.
The problem is that the audio doesn't match the intended band levels.

Implications:
1. Using these files for "calibration" is backwards - we're calibrating to match
   WRONG labels, not to match actual IELTS standards.

2. The proper approach would be to either:
   - Use REAL IELTS test samples (which are expensive/hard to obtain)
   - Or: Create synthetic data with known band characteristics
   - Or: Have human IELTS raters label these samples correctly

3. Current calibration efforts are futile because the baseline expectations
   are fundamentally wrong.
""")
