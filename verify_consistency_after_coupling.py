#!/usr/bin/env python3
"""Verify all band scores are still 100% consistent after coupling fix."""
import json
import os
from src.core.ielts_band_scorer import IELTSBandScorer

audio_dir = 'outputs/audio_analysis'
band_dir = 'outputs/band_results'

files = [f for f in os.listdir(audio_dir) if f.endswith('.json')]
files.sort()

scorer = IELTSBandScorer()
all_consistent = True

print("=" * 80)
print("VERIFYING CONSISTENCY AFTER COUPLING FIX")
print("=" * 80)

for filename in files:
    audio_path = os.path.join(audio_dir, filename)
    band_path = os.path.join(band_dir, filename)
    
    # Load audio analysis and band results
    with open(audio_path) as f:
        audio_data = json.load(f)
    with open(band_path) as f:
        band_data = json.load(f)
    
    # Extract metrics
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
    
    # Re-score
    result = scorer.score_overall_with_feedback(metrics, transcript)
    
    # Compare
    stored_overall = band_data['overall_band']
    computed_overall = result['overall_band']
    
    stored_fc = band_data['criterion_bands']['fluency_coherence']
    computed_fc = result['criterion_bands']['fluency_coherence']
    
    stored_lr = band_data['criterion_bands']['lexical_resource']
    computed_lr = result['criterion_bands']['lexical_resource']
    
    match = (stored_overall == computed_overall and 
             stored_fc == computed_fc and 
             stored_lr == computed_lr)
    
    status = "✅" if match else "❌"
    print(f"  {status} {filename:30} stored={stored_overall:.1f}, computed={computed_overall:.1f}")
    
    if not match:
        print(f"     Fluency: stored={stored_fc}, computed={computed_fc}")
        print(f"     Lexical: stored={stored_lr}, computed={computed_lr}")
        all_consistent = False

print("\n" + "=" * 80)
if all_consistent:
    print("✅ ALL SCORES CONSISTENT (100% reproducible)")
else:
    print("⚠️  SOME SCORES INCONSISTENT")
