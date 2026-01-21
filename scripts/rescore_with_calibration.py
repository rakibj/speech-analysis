"""
Re-score existing analysis files with the calibrated scoring logic.
Compares old scores vs new scores to verify calibration effectiveness.
"""

import json
import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR_ANALYSIS = Path("outputs/audio_analysis")
OUTPUT_DIR_RESULT = Path("outputs/band_results")
OUTPUT_DIR_RESULT_CALIBRATED = Path("outputs/band_results_calibrated")


async def rescore_single_file(idx: int, total: int, path: Path, out_path: Path):
    """Re-score a single analysis file with new calibrated logic."""
    try:
        from src.core.analyze_band import analyze_band_from_analysis
        
        with path.open("r", encoding="utf-8") as f:
            analysis_json = json.load(f)

        raw_analysis = analysis_json["raw_analysis"]
        
        print(f"[{idx}/{total}] {path.stem}...", end=" ", flush=True)

        # Call scoring with new calibrated logic
        report = await analyze_band_from_analysis(raw_analysis)

        # Write results
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Extract band from nested structure (new format)
        band = report.get('band_scores', {}).get('overall_band')
        print(f"OK {band}")
        return (True, path.stem, band)

    except Exception as e:
        print(f"ER Error: {str(e)[:40]}")
        return (False, path.stem, None)


async def rescore_all():
    """Re-score all analysis files."""
    print("\n" + "="*80)
    print("RE-SCORING WITH CALIBRATED LOGIC")
    print("="*80 + "\n")
    
    OUTPUT_DIR_RESULT_CALIBRATED.mkdir(parents=True, exist_ok=True)
    
    analysis_files = sorted(OUTPUT_DIR_ANALYSIS.glob("*.json"))
    total = len(analysis_files)
    
    tasks = []
    for idx, path in enumerate(analysis_files, start=1):
        out_path = OUTPUT_DIR_RESULT_CALIBRATED / path.name
        tasks.append(rescore_single_file(idx, total, path, out_path))
    
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    # Gather results
    new_scores = {}
    for success, filename, score in results:
        if success:
            new_scores[filename] = score
    
    # Load old scores for comparison
    old_scores = {}
    for result_file in OUTPUT_DIR_RESULT.glob("*.json"):
        try:
            with result_file.open("r") as f:
                data = json.load(f)
            old_scores[result_file.stem] = data.get("overall_band")
        except:
            pass
    
    # Compare and print summary
    print("\n" + "="*80)
    print("CALIBRATION RESULTS")
    print("="*80 + "\n")
    
    print(f"{'File':30} {'Old':8} {'New':8} {'Change':10} {'Match Expected':15}")
    print("-" * 80)
    
    improvements = 0
    for filename in sorted(new_scores.keys()):
        new = new_scores[filename]
        old = old_scores.get(filename)
        
        # Extract expected band
        if "ielts" in filename:
            try:
                parts = filename.replace("ielts", "").split("-")
                expected = float(parts[0]) if parts[0] else None
            except:
                expected = None
        else:
            expected = None
        
        if old and new:
            change = new - old
            change_str = f"{change:+.1f}"
            match_expected = ""
            if expected:
                match_expected = "[Match]" if abs(new - expected) < 0.1 else f"(Exp:{expected:.1f})"
            
            print(
                f"{filename:30} {old:8.1f} {new:8.1f} {change_str:>10} {match_expected:>15}"
            )
            
            if change < 0 and expected and abs(new - expected) < abs(old - expected):
                improvements += 1
    
    print(f"\nTotal improvements toward expected: {improvements}/{len(new_scores)}")
    
    return new_scores, old_scores


if __name__ == "__main__":
    new_scores, old_scores = asyncio.run(rescore_all())
