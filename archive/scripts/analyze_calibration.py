"""
Analyze the mismatch pattern and calibrate scoring logic.
Examines raw metrics from analysis files to understand why scores deviate.
"""

import json
from pathlib import Path
from collections import defaultdict

OUTPUT_DIR_ANALYSIS = Path("outputs/audio_analysis")
OUTPUT_DIR_RESULT = Path("outputs/band_results")


def extract_metrics_from_analysis(analysis_data):
    """Extract key metrics from raw analysis."""
    raw = analysis_data.get("raw_analysis", {})
    return {
        "wpm": raw.get("wpm", 0),
        "articulation_rate": raw.get("articulationrate", 0),
        "pause_variability": raw.get("pause_variability", 0),
        "filler_percentage": raw.get("filler_percentage", 0),
        "long_pauses_per_min": raw.get("long_pauses_per_min", 0),
        "fillers_per_min": raw.get("fillers_per_min", 0),
        "speech_rate_variability": raw.get("speech_rate_variability", 0),
        "vocab_richness": raw.get("vocab_richness", 0),
    }


def analyze_calibration():
    """Analyze metrics for each file and compare with band scores."""
    print("\n" + "="*100)
    print("CALIBRATION ANALYSIS - Metrics vs Band Scores")
    print("="*100 + "\n")
    
    analysis_files = sorted(OUTPUT_DIR_ANALYSIS.glob("*.json"))
    
    calibration_data = []
    
    for analysis_path in analysis_files:
        result_path = OUTPUT_DIR_RESULT / analysis_path.name
        file_stem = analysis_path.stem
        
        # Extract expected band from filename
        try:
            if "ielts" in file_stem:
                parts = file_stem.replace("ielts", "").split("-")
                expected_band = float(parts[0]) if parts[0] else None
            else:
                expected_band = None
        except:
            expected_band = None
        
        # Load data
        with analysis_path.open("r") as f:
            analysis_data = json.load(f)
        
        with result_path.open("r") as f:
            result_data = json.load(f)
        
        actual_band = result_data.get("overall_band", 0)
        metrics = extract_metrics_from_analysis(analysis_data)
        
        record = {
            "file": file_stem,
            "expected": expected_band,
            "actual": actual_band,
            "error": (actual_band - expected_band) if expected_band else None,
            **metrics
        }
        calibration_data.append(record)
    
    # Print analysis
    print(f"{'File':25} {'Expected':10} {'Actual':10} {'Error':8} "
          f"{'WPM':8} {'FillerPct':10} {'PauseVar':10}")
    print("-" * 100)
    
    for record in calibration_data:
        if record["expected"]:
            print(
                f"{record['file']:25} "
                f"{record['expected']:10.1f} {record['actual']:10.1f} "
                f"{record['error']:+8.1f} "
                f"{record['wpm']:8.1f} {record['filler_percentage']:10.2f} "
                f"{record['pause_variability']:10.2f}"
            )
    
    # Group by band and analyze patterns
    print("\n" + "="*100)
    print("PATTERN ANALYSIS BY EXPECTED BAND")
    print("="*100 + "\n")
    
    by_band = defaultdict(list)
    for record in calibration_data:
        if record["expected"]:
            by_band[record["expected"]].append(record)
    
    for band in sorted(by_band.keys()):
        records = by_band[band]
        errors = [r["error"] for r in records if r["error"] is not None]
        avg_error = sum(errors) / len(errors) if errors else 0
        avg_wpm = sum(r["wpm"] for r in records) / len(records)
        avg_filler = sum(r["filler_percentage"] for r in records) / len(records)
        
        print(f"\nBand {band:.1f}:")
        print(f"  Files: {[r['file'] for r in records]}")
        print(f"  Avg Error: {avg_error:+.2f} (scored {'higher' if avg_error > 0 else 'lower'})")
        print(f"  Avg WPM: {avg_wpm:.1f}")
        print(f"  Avg Filler %: {avg_filler:.2f}%")
        if len(records) > 1:
            for r in records:
                print(f"    - {r['file']:20} Error: {r['error']:+.1f}")
    
    # Recommendations
    print("\n" + "="*100)
    print("CALIBRATION RECOMMENDATIONS")
    print("="*100 + "\n")
    
    lower_band_errors = [r["error"] for r in calibration_data if r["expected"] and r["expected"] <= 5.5 and r["error"] is not None]
    middle_band_errors = [r["error"] for r in calibration_data if r["expected"] and 6.5 <= r["expected"] <= 8.0 and r["error"] is not None]
    high_band_errors = [r["error"] for r in calibration_data if r["expected"] and r["expected"] >= 8.5 and r["error"] is not None]
    
    print("🔴 Lower Bands (5.0-5.5):")
    print(f"   Avg Error: {sum(lower_band_errors) / len(lower_band_errors):+.2f}")
    print(f"   Issue: Consistently over-scored")
    print(f"   Fix: Lower thresholds for lower bands by ~1.0 band")
    
    print("\n🟢 Middle Bands (6.5-8.0):")
    print(f"   Avg Error: {sum(middle_band_errors) / len(middle_band_errors):+.2f}")
    print(f"   Issue: Mostly accurate")
    print(f"   Fix: Keep current thresholds")
    
    print("\n🟡 High Bands (8.5-9.0):")
    print(f"   Avg Error: {sum(high_band_errors) / len(high_band_errors):+.2f}")
    print(f"   Issue: Under-scored, especially 9.0")
    print(f"   Fix: Adjust 9.0 threshold to be more achievable")
    
    print("\n" + "="*100 + "\n")
    
    return calibration_data


if __name__ == "__main__":
    analyze_calibration()
