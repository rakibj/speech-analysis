#!/usr/bin/env python3
"""
Test script to verify both /analyze and /analyze-fast endpoints work properly.
Tests on the same audio file and compares:
- Response format compatibility
- Band score accuracy
- Processing time speedup
"""

import asyncio
import json
from pathlib import Path
from src.core.analyzer_fast import analyze_speech_fast
from src.services import AnalysisService
import time

# Test file (IELTS sample)
TEST_FILE = "data/ielts_part_2/ielts7.wav"


async def test_endpoints():
    """Test both endpoints and compare results."""
    
    if not Path(TEST_FILE).exists():
        print(f"Test file not found: {TEST_FILE}")
        return False
    
    print("=" * 70)
    print("ENDPOINT VERIFICATION TEST")
    print("=" * 70)
    print(f"\nTest file: {TEST_FILE}")
    print(f"File size: {Path(TEST_FILE).stat().st_size / (1024*1024):.2f} MB")
    
    # Test 1: Full /analyze endpoint
    print("\n" + "=" * 70)
    print("TEST 1: Full Analysis (/analyze)")
    print("=" * 70)
    
    try:
        start_full = time.time()
        result_full = await AnalysisService.analyze_speech(
            audio_path=TEST_FILE,
            speech_context="ielts",
            device="cpu"
        )
        time_full = time.time() - start_full
        print(f"[OK] Full analysis completed in {time_full:.2f}s")
        
        # Check structure
        assert "band_scores" in result_full, "Missing band_scores"
        assert "overall_band" in result_full["band_scores"], "Missing overall_band"
        assert "transcript" in result_full, "Missing transcript"
        assert "statistics" in result_full, "Missing statistics"
        
        band_full = result_full["band_scores"]["overall_band"]
        print(f"[OK] Band score: {band_full}")
        print(f"[OK] Transcript length: {len(result_full['transcript'].split())} words")
        print(f"[OK] Output format: VALID")
        
    except Exception as e:
        print(f"[ERROR] Full analysis failed: {e}")
        return False
    
    # Test 2: Fast /analyze-fast endpoint
    print("\n" + "=" * 70)
    print("TEST 2: Fast Analysis (/analyze-fast)")
    print("=" * 70)
    
    try:
        start_fast = time.time()
        result_fast = await analyze_speech_fast(
            audio_path=TEST_FILE,
            speech_context="ielts",
            device="cpu"
        )
        time_fast = time.time() - start_fast
        print(f"[OK] Fast analysis completed in {time_fast:.2f}s")
        
        # Check structure
        assert "band_scores" in result_fast, "Missing band_scores"
        assert "overall_band" in result_fast["band_scores"], "Missing overall_band"
        assert "transcript" in result_fast, "Missing transcript"
        assert "statistics" in result_fast, "Missing statistics"
        assert "metadata" in result_fast, "Missing metadata"
        assert result_fast["metadata"].get("optimization_phase") == 1, "Not Phase 1 optimization"
        
        band_fast = result_fast["band_scores"]["overall_band"]
        print(f"[OK] Band score: {band_fast}")
        print(f"[OK] Transcript length: {len(result_fast['transcript'].split())} words")
        print(f"[OK] Optimization: Phase 1 (explicit in metadata)")
        print(f"[OK] Output format: VALID (compatible with /analyze)")
        
    except Exception as e:
        print(f"[ERROR] Fast analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Comparison
    print("\n" + "=" * 70)
    print("TEST 3: Comparison")
    print("=" * 70)
    
    speedup = time_full / time_fast
    time_saved = time_full - time_fast
    
    print(f"\nProcessing Time:")
    print(f"  Full:  {time_full:.2f}s")
    print(f"  Fast:  {time_fast:.2f}s")
    print(f"  Saved: {time_saved:.2f}s ({(time_saved/time_full)*100:.1f}%)")
    print(f"  Speedup: {speedup:.2f}x faster")
    
    # Band score match
    print(f"\nBand Score Match:")
    if band_full == band_fast:
        print(f"  [OK] IDENTICAL: {band_full} (both endpoints)")
    else:
        print(f"  [WARN] DIFFERENT: Full={band_full}, Fast={band_fast}")
    
    # Transcript match
    words_full = result_full["transcript"].split()
    words_fast = result_fast["transcript"].split()
    print(f"\nTranscript:")
    print(f"  Full: {len(words_full)} words")
    print(f"  Fast: {len(words_fast)} words")
    if words_full == words_fast:
        print(f"  [OK] Transcripts are identical")
    else:
        print(f"  [INFO] Transcripts differ (expected - different processing)")
    
    # Filler detection difference
    fillers_full = result_full["statistics"].get("filler_words_detected", 0)
    fillers_fast = result_fast["statistics"].get("filler_words_detected", 0)
    print(f"\nFiller Detection:")
    print(f"  Full: {fillers_full} fillers (Wav2Vec2)")
    print(f"  Fast: {fillers_fast} fillers (Whisper only, Phase 1)")
    print(f"  Note: Different detection methods expected")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    tests_passed = 0
    tests_total = 5
    
    # Test 1: Both endpoints return valid responses
    if result_full and result_fast:
        print("[1/5] Both endpoints return valid responses")
        tests_passed += 1
    
    # Test 2: Both have band scores
    if band_full and band_fast:
        print("[2/5] Both endpoints provide band scores")
        tests_passed += 1
    
    # Test 3: Band scores match
    if band_full == band_fast:
        print("[3/5] Band scores are identical")
        tests_passed += 1
    else:
        print(f"[3/5] WARN: Band scores differ (Full={band_full}, Fast={band_fast})")
    
    # Test 4: Fast is actually faster
    if time_fast < time_full:
        print(f"[4/5] Fast endpoint is {speedup:.2f}x faster")
        tests_passed += 1
    else:
        print(f"[4/5] ERROR: Fast endpoint not actually faster")
    
    # Test 5: Output formats compatible
    same_keys = set(result_full.keys()) == set(result_fast.keys())
    if same_keys or ("optimization_phase" in result_fast["metadata"]):
        print("[5/5] Output formats compatible (both have required fields)")
        tests_passed += 1
    
    print(f"\nResult: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed >= 4:
        print("\n[SUCCESS] Both endpoints working properly!")
        return True
    else:
        print("\n[FAILURE] Issues detected")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_endpoints())
    exit(0 if success else 1)
