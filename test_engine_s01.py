#!/usr/bin/env python3
"""Test script to run the research engine on S01.wav"""

import asyncio
import sys
from pathlib import Path

# Add research to path
research_dir = Path(__file__).parent / "research"
sys.path.insert(0, str(research_dir))

from engine import analyze_speech

async def main():
    audio_path = Path(__file__).parent / "research" / "data" / "S29.wav"

    print(f"Testing engine on: {audio_path}")
    print(f"File exists: {audio_path.exists()}")

    if not audio_path.exists():
        print(f"ERROR: Audio file not found at {audio_path}")
        return

    try:
        result = await analyze_speech(
            audio_path=str(audio_path),
            context="conversational",
            device="cpu",
            use_llm=False  # Disable LLM for faster testing
        )

        print("\n[SUCCESS] Analysis completed successfully!")
        print(f"\nResult keys: {list(result.keys())}")

        # Print some key statistics
        print(f"\n{result}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
