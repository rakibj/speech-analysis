#!/usr/bin/env python3
"""
Test the EXACT code path that Modal uses
This mimics the API endpoint processing
"""
import sys
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.engine_runner import run_engine
from src.utils.logging_config import setup_logging

logger = setup_logging(level="INFO")

async def test_modal_code_path():
    """Test using the exact code path Modal uses"""
    
    # Read an audio file
    audio_file = Path("data/ielts_part_2/ielts5.5.wav")
    
    if not audio_file.exists():
        # Try ielts5-5.5 instead
        audio_file = Path("data/ielts_part_2/ielts5-5.5.wav")
    
    if not audio_file.exists():
        print(f"ERROR: No audio file found")
        return
    
    print("=" * 80)
    print("TESTING MODAL CODE PATH")
    print("=" * 80)
    print(f"\nAudio file: {audio_file}")
    
    # Read audio bytes (THIS IS WHAT THE API DOES)
    audio_bytes = audio_file.read_bytes()
    print(f"Audio size: {len(audio_bytes)} bytes")
    
    # Call run_engine with use_llm=True (THIS IS WHAT THE API DOES)
    result = await run_engine(
        audio_bytes=audio_bytes,
        context="conversational",
        device="cpu",
        use_llm=True,  # <-- THIS ENABLES LLM
        filename=audio_file.name
    )
    
    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    
    if "band_scores" in result:
        bs = result["band_scores"]
        cb = bs.get("criterion_bands", {})
        print(f"\nCriterion Bands:")
        print(f"  Fluency:       {cb.get('fluency_coherence')}")
        print(f"  Pronunciation: {cb.get('pronunciation')}")
        print(f"  Lexical:       {cb.get('lexical_resource')}")
        print(f"  Grammar:       {cb.get('grammatical_range_accuracy')}")
        print(f"  ──────────────────────────────────")
        print(f"  OVERALL:       {bs.get('overall_band')}")
    else:
        print("\nNo band_scores in result!")
        print(f"Keys in result: {list(result.keys())}")
    
    print("\n" + "=" * 80)
    print("COMPARISON WITH MODAL")
    print("=" * 80)
    print("\nModal returned (for ielts5.5 or ielts5-5.5):")
    print("  Fluency:       6.5")
    print("  Pronunciation: 5.5")
    print("  Lexical:       8")
    print("  Grammar:       7")
    print("  OVERALL:       7")

if __name__ == "__main__":
    asyncio.run(test_modal_code_path())
