#!/usr/bin/env python3
"""
Batch Analyzer Script - Analyze all audio files in /research/data

Processes all WAV files in the data directory and generates analysis JSON files.
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research.analyzer import analyze_audio, reorganize_analysis_data
import json
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


async def batch_analyze(
    data_dir: Path,
    context: str = "conversational",
    device: str = "cpu",
    skip_existing: bool = False
) -> dict:
    """
    Analyze all WAV files in data directory.

    Args:
        data_dir: Directory containing WAV files
        context: Speech context (conversational, ielts, etc.)
        device: Device to use (cpu or cuda)
        skip_existing: Skip files that already have analysis

    Returns:
        Dictionary with results summary
    """
    # Find all WAV files
    wav_files = sorted(data_dir.glob("*.wav"))

    if not wav_files:
        print(f"No WAV files found in {data_dir}")
        return {
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "results": {}
        }

    print(f"Found {len(wav_files)} audio files")
    print("=" * 70)

    # Prepare output directory
    output_dir = Path(__file__).parent / "analysis"
    output_dir.mkdir(exist_ok=True)

    results = {
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "results": {}
    }

    for idx, wav_file in enumerate(wav_files, 1):
        filename = wav_file.stem
        output_file = output_dir / f"{filename}.json"

        print(f"\n[{idx}/{len(wav_files)}] Processing: {filename}")

        # Check if already analyzed
        if skip_existing and output_file.exists():
            print(f"  → Skipped (already analyzed)")
            results["skipped"] += 1
            results["results"][filename] = {"status": "skipped"}
            continue

        try:
            # Run analysis
            raw_result = await analyze_audio(
                audio_path=str(wav_file),
                context=context,
                device=device
            )

            # Reorganize data
            from research.analyzer import reorganize_analysis_data
            analysis_data = reorganize_analysis_data(raw_result)

            # Save to JSON
            with open(output_file, 'w') as f:
                json.dump(analysis_data, f, indent=2, cls=NumpyEncoder)

            # Extract summary stats
            metadata = analysis_data.get("metadata", {})
            metrics = analysis_data.get("input_metrics", {})

            print(f"  [OK] Success")
            print(f"    - Duration: {metadata.get('duration_seconds', 0):.1f}s")
            print(f"    - Words: {metadata.get('total_words_transcribed', 0)}")
            print(f"    - WPM: {metrics.get('wpm', 0):.1f}")
            print(f"    - Fillers/min: {metrics.get('fillers_per_min', 0):.2f}")

            results["processed"] += 1
            results["results"][filename] = {
                "status": "success",
                "duration": metadata.get('duration_seconds', 0),
                "words": metadata.get('total_words_transcribed', 0),
                "wpm": metrics.get('wpm', 0),
                "fillers_per_min": metrics.get('fillers_per_min', 0),
                "vocab_richness": metrics.get('vocab_richness', 0),
            }

        except Exception as e:
            print(f"  [ERROR] Failed: {str(e)}")
            results["failed"] += 1
            results["results"][filename] = {"status": "failed", "error": str(e)}

    return results


def print_summary(results: dict):
    """Print batch processing summary."""
    print("\n" + "=" * 70)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 70)

    print(f"\nTotal files processed: {results['processed']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Failed: {results['failed']}")

    if results["failed"] == 0:
        print(f"\n[OK] All files processed successfully!")
    else:
        print(f"\n[WARNING] {results['failed']} file(s) failed")
        for filename, result in results["results"].items():
            if result.get("status") == "failed":
                print(f"  - {filename}: {result.get('error')}")

    # Show processed files summary
    successful = [r for r in results["results"].values() if r.get("status") == "success"]
    if successful:
        print(f"\nProcessed Files Summary:")
        print(f"  {'File':<20} {'Duration':<12} {'Words':<10} {'WPM':<10} {'Fillers/min':<12}")
        print(f"  {'-'*20} {'-'*12} {'-'*10} {'-'*10} {'-'*12}")

        for filename, result in sorted(results["results"].items()):
            if result.get("status") == "success":
                duration = result.get("duration", 0)
                words = result.get("words", 0)
                wpm = result.get("wpm", 0)
                fillers = result.get("fillers_per_min", 0)
                print(f"  {filename:<20} {duration:<12.1f} {words:<10} {wpm:<10.1f} {fillers:<12.2f}")

    print(f"\n" + "=" * 70)


async def main():
    """Main entry point."""
    # Parse arguments
    context = sys.argv[1] if len(sys.argv) > 1 else "conversational"
    device = sys.argv[2] if len(sys.argv) > 2 else "cpu"
    skip_existing = "--skip" in sys.argv or "-skip" in sys.argv

    # Get data directory
    research_dir = Path(__file__).parent
    data_dir = research_dir / "data"

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    print(f"Batch Analyzing Audio Files")
    print(f"Data directory: {data_dir}")
    print(f"Context: {context}")
    print(f"Device: {device}")
    if skip_existing:
        print(f"Skip existing: Yes")

    try:
        # Run batch analysis
        results = await batch_analyze(
            data_dir=data_dir,
            context=context,
            device=device,
            skip_existing=skip_existing
        )

        # Print summary
        print_summary(results)

        return 0 if results["failed"] == 0 else 1

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
