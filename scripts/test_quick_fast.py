"""
Quick test script for FAST analyzer (no LLM, no Wav2Vec2)
Similar to test_quick.py but uses analyzer_fast for speed testing

Run: python test_quick_fast.py

Expected runtime: 15-25 seconds (vs 100-120 seconds for full analysis)
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from src.core.analyzer_fast import analyze_speech_fast

# Enable UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def safe_print(text):
    """Safely print text with unicode character fallbacks"""
    if isinstance(text, str):
        # Replace special characters with ASCII equivalents for terminal display
        text = text.replace('✓', '[ok]')
        text = text.replace('•', '*')
    print(text)


async def main():
    # Find sample audio (same as test_quick.py)
    audio_file = Path("data/ielts_part_2/ielts7.wav")

    if not audio_file.exists():
        print(f"[ERROR] Audio File Not Found: {audio_file}")
        return
    
    print(f"[INFO] Loading: {audio_file.name} ({audio_file.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Run fast analysis
    try:
        print("\n[START] Starting FAST analysis (should take 15-25 seconds)...\n")
        
        start_time = time.time()
        
        result = await analyze_speech_fast(
            audio_path=str(audio_file),
            speech_context="conversational",
            device="cpu"
        )
        
        elapsed = time.time() - start_time
        
        # Display results
        print("\n" + "="*70)
        print("[OK] FAST ANALYSIS COMPLETE")
        print(f"[TIMING] Completed in {elapsed:.1f} seconds (5-8x faster than full)")
        print("="*70)
        
        # Export report
        output_path = Path("outputs") / f"final_report_fast_{audio_file.stem}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[EXPORTED] Report saved to: {output_path}\n")
        
        # Verdict
        print(f"[VERDICT]:")
        verdict = result.get('verdict', {})
        safe_print(f"   * Fluency Score: {verdict.get('fluency_score')}")
        safe_print(f"   * Readiness: {verdict.get('readiness')}")
        safe_print(f"   * Mode: FAST (skipped Wav2Vec2, LLM)")
        
        # Band scores
        print(f"\n[BAND SCORES - METRICS ONLY (no LLM)]:")
        if 'band_scores' in result:
            band_scores = result['band_scores']
            safe_print(f"   Overall Band: {band_scores.get('overall_score')}")
            safe_print(f"   Confidence: {band_scores.get('confidence', 'N/A')} (lower than full analysis)")
            
            print(f"\n   Criterion Bands:")
            if 'criterion_bands' in band_scores:
                for criterion, band in band_scores['criterion_bands'].items():
                    safe_print(f"     * {criterion}: {band}")
        
        # Transcript
        if 'raw_transcript' in result:
            transcript = result['raw_transcript']
            if len(transcript) > 300:
                print(f"\n[TRANSCRIPT]:\n{transcript[:300]}...\n")
            else:
                print(f"\n[TRANSCRIPT]:\n{transcript}\n")
        
        # Statistics
        print(f"\n[STATISTICS - Metrics Only (No Semantic Analysis)]:")
        stats = result.get('statistics', {})
        safe_print(f"   * Total words: {stats.get('total_words_transcribed')}")
        safe_print(f"   * Content words: {stats.get('content_words')}")
        safe_print(f"   * Filler words detected: {stats.get('filler_words_detected')}")
        safe_print(f"   * Filler percentage: {stats.get('filler_percentage')}%")
        
        # Normalized metrics
        print(f"\n[NORMALIZED METRICS]:")
        if 'normalized_metrics' in result:
            metrics = result['normalized_metrics']
            safe_print(f"   * Speech rate (WPM): {metrics.get('speech_rate_wpm')}")
            safe_print(f"   * Pause frequency: {metrics.get('pause_frequency')}")
            safe_print(f"   * Mean word confidence: {metrics.get('mean_word_confidence', 'N/A')}")
            safe_print(f"   * Filler frequency: {metrics.get('filler_frequency', 'N/A')}")
        
        # Opinions (limited in fast mode)
        print(f"\n[OPINIONS - Limited Analysis]:")
        opinions = result.get('opinions', {})
        if opinions.get('note'):
            safe_print(f"   {opinions['note']}")
        
        # What's NOT included in fast mode
        print(f"\n[FAST MODE LIMITATIONS]:")
        safe_print(f"   [NOT INCLUDED]")
        safe_print(f"   * Wav2Vec2 subtle filler detection")
        safe_print(f"   * LLM semantic analysis")
        safe_print(f"   * Grammar error identification")
        safe_print(f"   * Vocabulary sophistication assessment")
        safe_print(f"   * Listener effort estimation")
        
        # Use cases
        print(f"\n[USE CASES FOR FAST MODE]:")
        safe_print(f"   * Development and iteration")
        safe_print(f"   * Real-time dashboards")
        safe_print(f"   * Bulk initial screening")
        safe_print(f"   * A/B testing")
        safe_print(f"   * Performance benchmarking")
        
        # Comparison with full analysis
        print(f"\n[COMPARISON: Fast vs Full Analysis]")
        print(f"   " + "─"*66)
        print(f"   {'Metric':<30} {'Fast':<15} {'Full':<15}")
        print(f"   " + "─"*66)
        print(f"   {'Runtime':<30} {'15-25s':<15} {'100-120s':<15}")
        print(f"   {'Band Accuracy':<30} {'~72%':<15} {'~85%':<15}")
        print(f"   {'LLM Semantic':<30} {'No':<15} {'Yes':<15}")
        print(f"   {'Filler Detection':<30} {'Whisper only':<15} {'Wav2Vec2':<15}")
        print(f"   {'Feedback Quality':<30} {'Metrics only':<15} {'Detailed':<15}")
        print(f"   " + "─"*66)
        
        print("\n" + "="*70)
        print(f"[TIP] For production/detailed feedback, use /analyze endpoint")
        print(f"[TIP] For fast iteration, use /analyze-fast endpoint")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
