#!/usr/bin/env python3
"""
Full end-to-end trace for ielts5.5.wav
Simulate the EXACT flow used by batch_band_analysis.py
"""
import sys
import json
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.analyzer_raw import analyze_speech
from src.core.ielts_band_scorer import score_ielts_speaking
from src.utils.logging_config import setup_logging

logger = setup_logging(level="INFO")

async def test_ielts5_5():
    """Test exact flow on ielts5.5.wav"""
    audio_file = Path("data/ielts_part_2/ielts5.5.wav")
    
    print("=" * 80)
    print("STAGE 1: RAW AUDIO ANALYSIS")
    print("=" * 80)
    
    # Stage 1: Analyze speech (gets metrics)
    result = await analyze_speech(audio_file)
    metrics = result['metrics_for_scoring']
    transcript = result.get('raw_transcript', '')
    
    print(f"\nAudio Duration: {result.get('audio_duration_sec')} sec")
    print(f"\nMetrics for scoring:")
    for k, v in sorted(metrics.items()):
        if isinstance(v, float):
            print(f"  {k:.<40} {v:.4f}")
        else:
            print(f"  {k:.<40} {v}")
    
    print("\n" + "=" * 80)
    print("STAGE 2: LLM SCORING")
    print("=" * 80)
    
    # Stage 2: Score with LLM
    band_scores = score_ielts_speaking(
        metrics=metrics,
        transcript=transcript,
        use_llm=True  # <-- THIS IS THE KEY
    )
    
    print(f"\nBand Scores:")
    print(f"  Fluency:      {band_scores['criterion_bands']['fluency_coherence']}")
    print(f"  Pronunciation: {band_scores['criterion_bands']['pronunciation']}")
    print(f"  Lexical:      {band_scores['criterion_bands']['lexical_resource']}")
    print(f"  Grammar:      {band_scores['criterion_bands']['grammatical_range_accuracy']}")
    print(f"  ───────────────────────────────────────────")
    print(f"  OVERALL:      {band_scores['overall_band']}")
    
    print("\n" + "=" * 80)
    print("STAGE 3: CONFIDENCE & FEEDBACK")
    print("=" * 80)
    
    print(f"\nConfidence: {band_scores.get('confidence', {}).get('overall_confidence')}")
    print(f"Recommendation: {band_scores.get('confidence', {}).get('confidence_category')}")
    
    return band_scores

if __name__ == "__main__":
    result = asyncio.run(test_ielts5_5())
    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2))
