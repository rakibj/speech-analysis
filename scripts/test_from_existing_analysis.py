#!/usr/bin/env python3
"""
Full trace using existing audio_analysis files
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.ielts_band_scorer import score_ielts_speaking
from src.utils.logging_config import setup_logging

logger = setup_logging(level="INFO")

def test_from_analysis():
    """Test using existing audio_analysis files"""
    
    audio_analysis_file = Path("outputs/audio_analysis/ielts5.5.json")
    
    if not audio_analysis_file.exists():
        print(f"ERROR: {audio_analysis_file} not found!")
        return
    
    print("=" * 80)
    print("LOADING FROM AUDIO ANALYSIS FILE")
    print("=" * 80)
    
    with open(audio_analysis_file) as f:
        analysis_data = json.load(f)
    
    raw = analysis_data['raw_analysis']
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
        'mean_utterance_length': raw.get('mean_utterance_length', 0),
        'unique_word_count': raw.get('unique_word_count', 0),
        'stutters_per_min': raw.get('stutters_per_min', 0),
        'repetition_ratio': raw.get('repetition_ratio', 0),
        'audio_duration_sec': raw.get('audio_duration_sec', 0),
    }
    
    transcript = raw.get('raw_transcript', '')
    
    print(f"\nAudio Duration: {metrics['audio_duration_sec']} sec")
    print(f"Transcript length: {len(transcript)} chars")
    
    print(f"\nMetrics for scoring:")
    for k, v in sorted(metrics.items()):
        if isinstance(v, float):
            print(f"  {k:.<40} {v:.4f}")
        else:
            print(f"  {k:.<40} {v}")
    
    print("\n" + "=" * 80)
    print("STAGE 1: SCORE WITHOUT LLM")
    print("=" * 80)
    
    # Score WITHOUT LLM (metrics only)
    band_scores_no_llm = score_ielts_speaking(
        metrics=metrics,
        transcript=transcript,
        use_llm=False
    )
    
    print(f"\nBand Scores (NO LLM):")
    cb = band_scores_no_llm['criterion_bands']
    print(f"  Fluency:       {cb['fluency_coherence']}")
    print(f"  Pronunciation: {cb['pronunciation']}")
    print(f"  Lexical:       {cb['lexical_resource']}")
    print(f"  Grammar:       {cb['grammatical_range_accuracy']}")
    print(f"  ──────────────────────────────────────────")
    avg_no_llm = (cb['fluency_coherence'] + cb['pronunciation'] + cb['lexical_resource'] + cb['grammatical_range_accuracy']) / 4
    print(f"  Average:       {avg_no_llm}")
    print(f"  OVERALL:       {band_scores_no_llm['overall_band']}")
    
    print("\n" + "=" * 80)
    print("STAGE 2: SCORE WITH LLM")
    print("=" * 80)
    
    # Score WITH LLM
    band_scores_with_llm = score_ielts_speaking(
        metrics=metrics,
        transcript=transcript,
        use_llm=True
    )
    
    print(f"\nBand Scores (WITH LLM):")
    cb = band_scores_with_llm['criterion_bands']
    print(f"  Fluency:       {cb['fluency_coherence']}")
    print(f"  Pronunciation: {cb['pronunciation']}")
    print(f"  Lexical:       {cb['lexical_resource']}")
    print(f"  Grammar:       {cb['grammatical_range_accuracy']}")
    print(f"  ──────────────────────────────────────────")
    avg_with_llm = (cb['fluency_coherence'] + cb['pronunciation'] + cb['lexical_resource'] + cb['grammatical_range_accuracy']) / 4
    print(f"  Average:       {avg_with_llm}")
    print(f"  OVERALL:       {band_scores_with_llm['overall_band']}")
    
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"\nMetrics-only:  {band_scores_no_llm['overall_band']}")
    print(f"With LLM:      {band_scores_with_llm['overall_band']}")
    print(f"\nDifference: {band_scores_with_llm['overall_band'] - band_scores_no_llm['overall_band']}")
    
    # Check what Modal returned
    print("\n" + "=" * 80)
    print("MODAL RESPONSE vs LOCAL")
    print("=" * 80)
    print("\nMODAL returned:")
    print("  Fluency:       6.5")
    print("  Pronunciation: 5.5")
    print("  Lexical:       8")
    print("  Grammar:       7")
    print("  OVERALL:       7")
    
    print("\nLOCAL (WITH LLM) returned:")
    print(f"  Fluency:       {band_scores_with_llm['criterion_bands']['fluency_coherence']}")
    print(f"  Pronunciation: {band_scores_with_llm['criterion_bands']['pronunciation']}")
    print(f"  Lexical:       {band_scores_with_llm['criterion_bands']['lexical_resource']}")
    print(f"  Grammar:       {band_scores_with_llm['criterion_bands']['grammatical_range_accuracy']}")
    print(f"  OVERALL:       {band_scores_with_llm['overall_band']}")

if __name__ == "__main__":
    test_from_analysis()
