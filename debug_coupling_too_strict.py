#!/usr/bin/env python3
"""Debug why all files are scoring 6.0."""
import json
import os
from src.core.ielts_band_scorer import IELTSBandScorer

audio_dir = 'outputs/audio_analysis'

for filename in ['ielts5-5.5.json', 'ielts8.5.json', 'ielts9.json']:
    audio_path = os.path.join(audio_dir, filename)
    
    with open(audio_path) as f:
        audio_data = json.load(f)
    
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
        'repetition_ratio': raw.get('repetition_ratio', 0),
        'audio_duration_sec': raw.get('audio_duration_sec', 0),
        'stutters_per_min': raw.get('stutters_per_min', 0),
        'mean_utterance_length': raw.get('mean_utterance_length', 0),
    }
    transcript = raw.get('raw_transcript', '')
    
    scorer = IELTSBandScorer()
    
    # Score individually to see before coupling
    fc = scorer.score_fluency(metrics)
    pr = scorer.score_pronunciation(metrics)
    lr = scorer.score_lexical(metrics)
    gr = scorer.score_grammar(metrics)
    
    # Now score with full method
    result = scorer.score_overall_with_feedback(metrics, transcript)
    
    print(f"\n{filename}")
    print(f"  Before coupling: FC={fc:.1f}, PR={pr:.1f}, LR={lr:.1f}, GR={gr:.1f}")
    print(f"  After coupling:  FC={result['criterion_bands']['fluency_coherence']:.1f}, " +
          f"PR={result['criterion_bands']['pronunciation']:.1f}, " +
          f"LR={result['criterion_bands']['lexical_resource']:.1f}, " +
          f"GR={result['criterion_bands']['grammatical_range_accuracy']:.1f}")
    print(f"  Overall: {result['overall_band']:.1f}")
