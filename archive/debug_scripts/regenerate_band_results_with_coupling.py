#!/usr/bin/env python3
"""Regenerate all band_results with inter-criterion coupling applied."""
import json
import os
from src.core.ielts_band_scorer import IELTSBandScorer

audio_dir = 'outputs/audio_analysis'
band_dir = 'outputs/band_results'

files = [f for f in os.listdir(audio_dir) if f.endswith('.json')]
files.sort()

print("=" * 80)
print("REGENERATING ALL BAND RESULTS WITH INTER-CRITERION COUPLING")
print("=" * 80)

scorer = IELTSBandScorer()
old_vs_new = []

for filename in files:
    audio_path = os.path.join(audio_dir, filename)
    band_path = os.path.join(band_dir, filename)
    
    # Load audio analysis
    with open(audio_path) as f:
        audio_data = json.load(f)
    
    # Extract metrics from raw_analysis  
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
    
    # Load existing band result to get old score
    old_score = None
    if os.path.exists(band_path):
        with open(band_path) as f:
            old_data = json.load(f)
            old_score = old_data.get('overall_band')
    
    # Score with new coupling
    result = scorer.score_overall_with_feedback(metrics, transcript)
    new_score = result['overall_band']
    
    # Save updated band result
    result['filename'] = filename
    with open(band_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    change = "=" if old_score == new_score else f"({old_score:.1f} -> {new_score:.1f})" if old_score else f"(NEW: {new_score:.1f})"
    old_vs_new.append({
        'file': filename,
        'old': old_score,
        'new': new_score,
        'change': new_score - old_score if old_score else None
    })
    
    print(f"  {filename:25} OLD: {old_score} → NEW: {new_score:.1f} {change}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

changed = [x for x in old_vs_new if x['change'] is not None and x['change'] != 0]
print(f"\nTotal files regenerated: {len(old_vs_new)}")
print(f"Files with score changes: {len(changed)}")

if changed:
    print("\nBand changes:")
    for item in changed:
        change = item['change']
        direction = "↓" if change < 0 else "↑"
        print(f"  {direction} {item['file']:25} {item['old']:.1f} → {item['new']:.1f} (Δ {change:+.1f})")
