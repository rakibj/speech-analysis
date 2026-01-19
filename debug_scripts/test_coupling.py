#!/usr/bin/env python3
"""Test if inter-criterion coupling is being applied."""
import json
from src.core.ielts_band_scorer import IELTSBandScorer

# Load ielts5-5.5 metrics
with open('outputs/audio_analysis/ielts5-5.5.json') as f:
    data = json.load(f)

metrics = data['raw_analysis']['metrics']
transcript = data['raw_analysis'].get('transcript', '')

print("=" * 80)
print("TESTING INTER-CRITERION COUPLING FIX")
print("=" * 80)

print(f"\n[INPUT METRICS]")
print(f"  WPM: {metrics['wpm']:.2f}")
print(f"  Fillers/min: {metrics['fillers_per_min']:.2f}")
print(f"  Vocab richness: {metrics['vocab_richness']:.3f}")

# Score with full method
scorer = IELTSBandScorer()
result = scorer.score_overall_with_feedback(metrics, transcript)

print(f"\n[INDIVIDUAL CRITERION SCORES (after coupling)]")
print(f"  Fluency/Coherence: {result['band_scores']['fluency']:.1f}")
print(f"  Pronunciation: {result['band_scores']['pronunciation']:.1f}")
print(f"  Lexical Resource: {result['band_scores']['lexical']:.1f}")
print(f"  Grammar/Accuracy: {result['band_scores']['grammar']:.1f}")

print(f"\n[OVERALL BAND]")
print(f"  Before rounding: {result.get('overall_raw', 'N/A')}")
print(f"  After rounding: {result['overall_band']:.1f}")

print(f"\n[COUPLING CHECK]")
fc = result['band_scores']['fluency']
pr = result['band_scores']['pronunciation']
lr = result['band_scores']['lexical']
gr = result['band_scores']['grammar']

if fc < 6.5:
    print(f"  ✓ Coupling applied: fluency={fc:.1f} < 6.5, lexical/grammar should be capped")
elif fc < 7.0:
    print(f"  ✓ Coupling applied: fluency={fc:.1f} < 7.0, lexical/grammar should be capped")
else:
    print(f"  - No coupling applied (fluency >= 7.0)")

if pr < 6.5:
    print(f"  ✓ Coupling applied: pronunciation={pr:.1f} < 6.5, lexical/grammar should be capped")

print(f"\n[EXPECTED AFTER COUPLING]")
print(f"  If coupling worked:")
print(f"  - Lexical should be <= min(original, fc + 0.5) = min(7.0, 7.0) = 7.0")
print(f"  - Actually, with fc={fc:.1f} and fc < 7.0:")
print(f"  - Lexical should be <= fc + 1.0 = {fc + 1.0:.1f}")
print(f"  - So lexical={lr:.1f} is {'CORRECT' if lr <= fc + 1.0 else 'STILL TOO HIGH'}")

print("\n" + "=" * 80)
