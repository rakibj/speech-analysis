#!/usr/bin/env python3
"""
Command-line tool for analyzing single audio file fluency.

Usage:
    python -m src.cli.analyze_audio sample.flac
    python -m src.cli.analyze_audio sample.flac conversational
    python -m src.cli.analyze_audio sample.flac conversational output.json
"""
import sys
import json
import asyncio
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    # Import here to ensure proper path setup
    from src.services import AnalysisService
    
    audio_path = sys.argv[1]
    speech_context = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    output_json = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Validate audio file exists
    if not Path(audio_path).exists():
        print(f"Error: Audio file not found: {audio_path}")
        sys.exit(1)
    
    # Run analysis
    result = asyncio.run(AnalysisService.analyze_speech(audio_path, speech_context))
    
    # Save to JSON if requested
    if output_json:
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Results saved to: {output_json}")
    
    return result


if __name__ == "__main__":
    main()
