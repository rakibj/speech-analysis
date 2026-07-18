#!/usr/bin/env python3
"""
Extract Pure Duration-Weighted Disfluency Metric

Preregistered hypothesis:
  Duration-weighted disfluency (pause structure + filler dependency)
  correlates MORE STRONGLY with human fluency judgments
  than baseline WPM alone.

This script extracts ONLY the disfluency components:
  - Pause Structure (with variability weighting)
  - Filler Dependency

And computes correlation against human ratings,
compared to WPM baseline.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List

# ============================================================
# CONFIGURATION: Disfluency Scoring Constants
# ============================================================

# Pause and filler limits (from scorer)
MAX_LONG_PAUSES_PER_MIN = 4.0
MAX_FILLERS_PER_MIN = 6.0
BASE_PAUSE_VARIABILITY = 0.7

# Disfluency weights (ONLY temporal/fluency factors)
WEIGHT_PAUSE = 0.55      # Pauses are primary disfluency indicator
WEIGHT_FILLER = 0.45     # Fillers are secondary disfluency indicator


def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, x))


def compute_disfluency_score(metrics: dict) -> float:
    """
    Compute PURE duration-weighted disfluency score.

    Includes ONLY:
    - Pause Structure (weighted by variability)
    - Filler Dependency

    Excludes:
    - Speech Rate
    - Lexical Quality
    - Rhythmic Stability (even though it involves variability)
    - Compound penalties

    Returns: Disfluency score (0-1, where 0=fluent, 1=disfluent)
    """

    # ===== COMPONENT 1: Pause Structure =====
    # Weight by variability: high variability indicates long pauses
    pause_variability = metrics.get("pause_variability", 0)
    long_pauses = metrics.get("long_pauses_per_min", 0)

    # Variability amplifier: 1.0 (consistent) to 2.0 (erratic)
    variability_amplifier = 1.0 + clamp01(pause_variability / BASE_PAUSE_VARIABILITY)

    # Pause disfluency score: 0=fluent, 1=disfluent
    pause_disfluency = clamp01(
        (long_pauses * variability_amplifier) / (MAX_LONG_PAUSES_PER_MIN)
    )

    # ===== COMPONENT 2: Filler Dependency =====
    # Raw filler count: 0=fluent, high=disfluent
    fillers_per_min = metrics.get("fillers_per_min", 0)
    filler_disfluency = clamp01(fillers_per_min / MAX_FILLERS_PER_MIN)

    # ===== COMBINE: Weighted Disfluency =====
    disfluency_score = (
        WEIGHT_PAUSE * pause_disfluency +
        WEIGHT_FILLER * filler_disfluency
    )

    # Invert to match convention: 0=disfluent, 1=fluent (like other scores)
    fluency_score = 1.0 - clamp01(disfluency_score)

    return fluency_score


def load_analysis_data(analysis_dir: Path) -> Dict[str, dict]:
    """Load all analysis JSON files."""
    analyses = {}

    for json_file in sorted(analysis_dir.glob("*.json")):
        sample_id = json_file.stem
        try:
            with open(json_file) as f:
                analyses[sample_id] = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {json_file.name}: {e}")

    return analyses


def extract_metrics_csv(analysis_dir: Path, output_file: Path):
    """Extract disfluency and baseline metrics to CSV."""

    analyses = load_analysis_data(analysis_dir)

    if not analyses:
        print("No analysis files found")
        return

    print(f"Processing {len(analyses)} analysis files...")

    # Collect results
    results = []

    for sample_id in sorted(analyses.keys()):
        data = analyses[sample_id]
        metrics = data.get("input_metrics", {})

        if not metrics:
            print(f"  [SKIP] {sample_id}: No input_metrics")
            continue

        # Extract WPM (baseline)
        wpm = metrics.get("wpm", 0)

        # Compute duration-weighted disfluency
        disfluency = compute_disfluency_score(metrics)

        results.append({
            "sample_id": sample_id,
            "wpm": round(wpm, 1),
            "duration_weighted_disfluency": round(disfluency, 3),
        })

        print(f"  {sample_id}: WPM={wpm:.1f}, Disfluency={disfluency:.3f}")

    # Write to CSV
    if results:
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "wpm", "duration_weighted_disfluency"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\nMetrics saved to: {output_file}")
        print(f"Total samples: {len(results)}")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    analysis_dir = script_dir / "analysis"
    output_file = script_dir / "disfluency_metrics.csv"

    if not analysis_dir.exists():
        print(f"Error: Analysis directory not found: {analysis_dir}")
        return 1

    extract_metrics_csv(analysis_dir, output_file)
    return 0


if __name__ == "__main__":
    exit(main())
