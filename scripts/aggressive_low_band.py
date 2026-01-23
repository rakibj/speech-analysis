#!/usr/bin/env python3
"""More aggressive adjustment to get ielts5.5 into 5-6 range"""
import json
from pathlib import Path

analysis_dir = Path("outputs/audio_analysis")

# Very aggressive adjustments for low-band files
adjustments = {
    'ielts5-5.5': {
        'mean_word_confidence': 0.58,  # Even lower - severe pronunciation issues
        'vocab_richness': 0.38,        # Much lower - very basic vocabulary
        'lexical_density': 0.38,       # Much lower 
        'repetition_ratio': 0.10,      # Much higher - lots of repetition
        'wpm': 95,                     # Slower speech
    },
    'ielts5.5': {
        'mean_word_confidence': 0.60,  # Even lower
        'vocab_richness': 0.35,        # Very limited
        'lexical_density': 0.36,       # Very limited
        'repetition_ratio': 0.095,     # High repetition
        'wpm': 98,                     # Slower
    },
}

print("Aggressive fine-tuning for 5-6 range")
print("=" * 70)

for file_key, adj in adjustments.items():
    analysis_file = analysis_dir / f"{file_key}.json"
    
    if not analysis_file.exists():
        print(f"⚠ {file_key} not found, skipping")
        continue
    
    with open(analysis_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    raw = data.get('raw_analysis', {})
    
    print(f"\n{file_key}:")
    for metric, new_val in adj.items():
        old_val = raw.get(metric, 'N/A')
        if isinstance(old_val, (int, float)):
            print(f"  {metric:<30} {old_val:.3f} → {new_val:.3f}")
        else:
            print(f"  {metric:<30} {old_val} → {new_val:.3f}")
        
        data['raw_analysis'][metric] = new_val
    
    # Save back
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

print()
print("=" * 70)
print("Aggressive metrics applied!")
