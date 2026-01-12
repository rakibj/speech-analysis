# src/analyze_audio.py
#!/usr/bin/env python3
"""
Command-line tool for analyzing speech fluency.

Usage:
    python scripts/analyze_audio.py sample4.flac
    python scripts/analyze_audio.py sample4.flac conversational
    python scripts/analyze_audio.py sample4.flac presentation
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.analyzer import analyze_speech


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    audio_path = sys.argv[1]
    speech_context = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    output_json = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Validate audio file exists
    if not Path(audio_path).exists():
        print(f"Error: Audio file not found: {audio_path}")
        sys.exit(1)
    
    # Run analysis
    result = analyze_speech(audio_path, speech_context)
    
    # Save to JSON if requested
    if output_json:
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Results saved to: {output_json}")
    
    return result


if __name__ == "__main__":
    main()