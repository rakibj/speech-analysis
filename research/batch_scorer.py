#!/usr/bin/env python3
"""
Batch Scorer Script - Score all analysis files in /research/analysis

Processes all JSON analysis files and generates fluency scores using the scoring logic from scorer.py.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import csv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scorer import calculate_fluency


def remap_score_to_band(score: int) -> float:
    """
    Remap fluency score (0-100) to band scale (1-9).

    Linear mapping: 0 -> 1, 100 -> 9
    """
    return round((score / 100) * 8 + 1, 1)


def get_unique_csv_filename(results_dir: Path) -> Path:
    """Generate unique CSV filename with date and increment counter."""
    today = datetime.now().strftime("%Y-%m-%d")
    base_name = f"batch_scoring_{today}"

    # Check for existing files with same date
    counter = 1
    while True:
        filename = f"{base_name}_{counter:03d}.csv"
        filepath = results_dir / filename
        if not filepath.exists():
            return filepath
        counter += 1


def save_results_to_csv(results: dict, csv_path: Path):
    """Save batch scoring results to CSV file."""
    successful = [
        (fname, r) for fname, r in results["results"].items() if r.get("status") == "success"
    ]
    successful.sort(key=lambda x: x[0])

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            'File',
            'Score (0-100)',
            'Band (1-9)',
            'Speech Rate',
            'Pause Structure',
            'Filler Dependency',
            'Rhythmic Stability',
            'Lexical Quality',
            'Issues Count'
        ])

        # Write data rows
        for filename, result in successful:
            score = result.get("fluency_score", 0)
            band = remap_score_to_band(score)
            subscores = result.get("subscores", {})
            issues_count = len(result.get("issues", []))

            writer.writerow([
                filename,
                score,
                band,
                f"{subscores.get('speech_rate', 0):.2f}",
                f"{subscores.get('pause', 0):.2f}",
                f"{subscores.get('filler', 0):.2f}",
                f"{subscores.get('stability', 0):.2f}",
                f"{subscores.get('lexical', 0):.2f}",
                issues_count
            ])

        # Add summary rows
        if successful:
            writer.writerow([])  # Empty row for spacing
            scores = [r.get("fluency_score", 0) for fname, r in successful]
            avg_score = sum(scores) / len(scores) if scores else 0
            min_score = min(scores) if scores else 0
            max_score = max(scores) if scores else 0

            writer.writerow(['SUMMARY', '', '', '', '', '', '', '', ''])
            writer.writerow([f'Average Score', f"{avg_score:.1f}", f"{remap_score_to_band(int(avg_score)):.1f}"])
            writer.writerow([f'Min Score', f"{min_score}", f"{remap_score_to_band(int(min_score)):.1f}"])
            writer.writerow([f'Max Score', f"{max_score}", f"{remap_score_to_band(int(max_score)):.1f}"])


def load_analysis_files(analysis_dir: Path) -> Dict[str, dict]:
    """Load all JSON analysis files."""
    json_files = sorted(analysis_dir.glob("*.json"))

    if not json_files:
        return {}

    analyses = {}
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                analyses[json_file.stem] = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {json_file.name}: {str(e)}")

    return analyses


def batch_score(analysis_dir: Path) -> dict:
    """Score all analysis files in directory."""
    print(f"Loading analysis files from: {analysis_dir}")
    analyses = load_analysis_files(analysis_dir)

    if not analyses:
        print("No analysis files found")
        return {"total": 0, "scored": 0, "failed": 0, "results": {}}

    print(f"Found {len(analyses)} analysis files")
    print("=" * 70)

    results = {
        "total": len(analyses),
        "scored": 0,
        "failed": 0,
        "results": {}
    }

    for idx, (filename, analysis_data) in enumerate(analyses.items(), 1):
        print(f"\n[{idx}/{len(analyses)}] Scoring: {filename}")

        try:
            # Calculate fluency score
            score_result = calculate_fluency(analysis_data)

            fluency_score = score_result.get("fluency_score", 0)
            subscores = score_result.get("subscores", {})
            issues = score_result.get("issues", [])

            print(f"  [OK] Fluency Score: {fluency_score}/100")
            print(f"    - Speech Rate: {subscores.get('speech_rate', 0):.2f}")
            print(f"    - Pause Structure: {subscores.get('pause', 0):.2f}")
            print(f"    - Filler Dependency: {subscores.get('filler', 0):.2f}")
            print(f"    - Rhythmic Stability: {subscores.get('stability', 0):.2f}")
            print(f"    - Lexical Quality: {subscores.get('lexical', 0):.2f}")

            if issues:
                print(f"    - Issues: {len(issues)} detected")

            results["scored"] += 1
            results["results"][filename] = {
                "status": "success",
                "fluency_score": fluency_score,
                "subscores": subscores,
                "issues_count": len(issues),
            }

        except Exception as e:
            print(f"  [ERROR] Failed: {str(e)}")
            results["failed"] += 1
            results["results"][filename] = {"status": "failed", "error": str(e)}

    return results


def print_summary(results: dict):
    """Print scoring summary."""
    print("\n" + "=" * 70)
    print("BATCH SCORING SUMMARY")
    print("=" * 70)

    print(f"\nTotal files scored: {results['scored']}/{results['total']}")
    print(f"Failed: {results['failed']}")

    if results["failed"] == 0:
        print(f"\n[OK] All files scored successfully!")
    else:
        print(f"\n[WARNING] {results['failed']} file(s) failed")
        for filename, result in results["results"].items():
            if result.get("status") == "failed":
                print(f"  - {filename}: {result.get('error')}")

    # Show scored files summary
    successful = [
        (fname, r) for fname, r in results["results"].items() if r.get("status") == "success"
    ]
    # Sort by filename (S01, S02, ..., S30)
    successful.sort(key=lambda x: x[0])

    if successful:
        print(f"\nScores by File (S01-S30):")
        print(f"  {'File':<10} {'Score':<10} {'Band':<8} {'Speech Rate':<15} {'Pause':<10} {'Filler':<10}")
        print(f"  {'-'*10} {'-'*10} {'-'*8} {'-'*15} {'-'*10} {'-'*10}")

        for filename, result in successful:
            score = result.get("fluency_score", 0)
            band = remap_score_to_band(score)
            subscores = result.get("subscores", {})
            sr = subscores.get("speech_rate", 0)
            pause = subscores.get("pause", 0)
            filler = subscores.get("filler", 0)
            print(f"  {filename:<10} {score:<10} {band:<8.1f} {sr:<15.2f} {pause:<10.2f} {filler:<10.2f}")

        # Statistics
        scores = [r.get("fluency_score", 0) for fname, r in successful]
        avg_score = sum(scores) / len(scores) if scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0

        print(f"\nStatistics:")
        print(f"  Average Score: {avg_score:.1f}/100 (Band {remap_score_to_band(int(avg_score)):.1f})")
        print(f"  Min Score: {min_score}/100 (Band {remap_score_to_band(int(min_score)):.1f})")
        print(f"  Max Score: {max_score}/100 (Band {remap_score_to_band(int(max_score)):.1f})")

    print(f"\n" + "=" * 70)


def main():
    """Main entry point."""
    # Get analysis directory
    research_dir = Path(__file__).parent
    analysis_dir = research_dir / "analysis"

    if not analysis_dir.exists():
        print(f"Error: Analysis directory not found: {analysis_dir}")
        sys.exit(1)

    try:
        # Run batch scoring
        results = batch_score(analysis_dir)

        # Print summary
        print_summary(results)

        # Save results to CSV
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)

        csv_path = get_unique_csv_filename(results_dir)
        save_results_to_csv(results, csv_path)

        print(f"\nResults saved to: {csv_path}")

        return 0 if results["failed"] == 0 else 1

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
