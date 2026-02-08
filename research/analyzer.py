#!/usr/bin/env python3
"""
Analyzer Script - Generate organized analysis data from audio files

Takes an audio file and generates raw input data for fluency analysis,
saving results to /research/analysis/{filename}.json for use with scorer.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.analyzer_raw import analyze_speech


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def reorganize_analysis_data(raw_result: dict) -> dict:
    """
    Reorganize raw analysis output into clean input data for fluency scoring.

    Keeps all the raw input metrics and data, removes fluency_analysis
    (which will be calculated by the scorer).
    """
    return {
        "metadata": {
            # Audio file information
            "filename": raw_result.get("metadata", {}).get("filename", ""),
            "duration_seconds": raw_result.get("statistics", {}).get("duration_seconds", 0),
            "total_words_transcribed": raw_result.get("statistics", {}).get("total_words_transcribed", 0),
            "content_words": raw_result.get("statistics", {}).get("content_words", 0),
            "filler_words_detected": raw_result.get("statistics", {}).get("filler_words_detected", 0),
            "is_monotone": raw_result.get("statistics", {}).get("is_monotone", False),
        },

        # Transcript
        "transcript": raw_result.get("raw_transcript", ""),

        # Raw input metrics for fluency scoring (NOT computed fluency scores)
        "input_metrics": {
            "wpm": raw_result.get("wpm", 0),
            "long_pauses_per_min": raw_result.get("long_pauses_per_min", 0),
            "fillers_per_min": raw_result.get("fillers_per_min", 0),
            "pause_variability": raw_result.get("pause_variability", 0),
            "speech_rate_variability": raw_result.get("speech_rate_variability", 0),
            "vocab_richness": raw_result.get("vocab_richness", 0),
            "type_token_ratio": raw_result.get("type_token_ratio", 0),
            "repetition_ratio": raw_result.get("repetition_ratio", 0),
            "mean_utterance_length": raw_result.get("mean_utterance_length", 0),
            "mean_word_confidence": raw_result.get("mean_word_confidence", 0),
        },

        # Timestamped data for detailed analysis
        "timestamps": raw_result.get("timestamps", {}),
    }


async def analyze_audio(
    audio_path: str,
    context: str = "conversational",
    device: str = "cpu"
) -> Dict:
    """
    Analyze audio file and return raw analysis data.

    Args:
        audio_path: Path to audio file
        context: Speech context (conversational, ielts, narrative, etc.)
        device: Device to use (cpu or cuda)

    Returns:
        Dictionary with raw analysis data
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"Analyzing: {audio_path.name}")
    print(f"Context: {context} | Device: {device}")
    print("-" * 60)

    # Run analyzer_raw to get raw input metrics
    result = await analyze_speech(
        audio_path=str(audio_path),
        speech_context=context,
        device=device
    )

    return result


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run analyzer.py <audio_file> [context] [device]")
        print("\nExamples:")
        print("  uv run analyzer.py data/S01.wav")
        print("  uv run analyzer.py data/S01.wav ielts")
        print("  uv run analyzer.py data/S01.wav conversational cuda")
        sys.exit(1)

    # Parse arguments
    audio_path = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    device = sys.argv[3] if len(sys.argv) > 3 else "cpu"

    # Resolve paths relative to research directory
    if not Path(audio_path).is_absolute():
        audio_path_obj = Path(audio_path)
        # If path doesn't exist, try relative to research directory
        if not audio_path_obj.exists():
            audio_path = str(Path(__file__).parent / audio_path)
        else:
            audio_path = str(audio_path_obj)

    try:
        # Run analysis
        raw_result = await analyze_audio(
            audio_path=audio_path,
            context=context,
            device=device
        )

        # Reorganize data into clean structure (remove fluency_analysis)
        analysis_data = reorganize_analysis_data(raw_result)

        # Prepare output directory
        research_dir = Path(__file__).parent
        output_dir = research_dir / "analysis"
        output_dir.mkdir(exist_ok=True)

        # Generate output filename
        audio_filename = Path(audio_path).stem
        output_file = output_dir / f"{audio_filename}.json"

        # Save analysis to JSON
        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, cls=NumpyEncoder)

        print(f"\n[SUCCESS] Analysis saved to: {output_file}")
        print(f"\nOutput structure:")
        print(f"  - metadata (audio info)")
        print(f"  - transcript")
        print(f"  - input_metrics (raw input for fluency scoring)")
        print(f"  - timestamps (detailed word/filler/segment data)")

        # Print summary statistics
        metadata = analysis_data.get("metadata", {})
        print(f"\nAudio Info:")
        print(f"  Duration: {metadata.get('duration_seconds', 'N/A')}s")
        print(f"  Total Words: {metadata.get('total_words_transcribed', 'N/A')}")
        print(f"  Content Words: {metadata.get('content_words', 'N/A')}")
        print(f"  Filler Words: {metadata.get('filler_words_detected', 'N/A')}")
        print(f"  Monotone: {metadata.get('is_monotone', False)}")

        # Show input metrics
        metrics = analysis_data.get("input_metrics", {})
        if metrics:
            print(f"\nInput Metrics (for fluency scoring):")
            print(f"  WPM: {metrics.get('wpm', 'N/A'):.1f}")
            print(f"  Fillers/min: {metrics.get('fillers_per_min', 'N/A'):.2f}")
            print(f"  Long Pauses/min: {metrics.get('long_pauses_per_min', 'N/A'):.2f}")
            print(f"  Vocab Richness: {metrics.get('vocab_richness', 'N/A'):.3f}")
            print(f"  Repetition Ratio: {metrics.get('repetition_ratio', 'N/A'):.3f}")

        return 0

    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
