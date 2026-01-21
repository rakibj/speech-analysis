"""
Quick consistency verification: compare existing analysis files with band results.
Does NOT re-run analysis or scoring, just checks if results align with data.
"""

import json
from pathlib import Path
from collections import defaultdict

OUTPUT_DIR_ANALYSIS = Path("outputs/audio_analysis")
OUTPUT_DIR_RESULT = Path("outputs/band_results")


def verify_consistency():
    """Compare analysis data with band results for consistency."""
    print("\n" + "="*70)
    print("CONSISTENCY VERIFICATION - Comparing Analysis Data with Band Results")
    print("="*70 + "\n")
    
    analysis_files = sorted(OUTPUT_DIR_ANALYSIS.glob("*.json"))
    consistency_report = {
        "total_files": len(analysis_files),
        "files_checked": 0,
        "consistent": 0,
        "inconsistent": 0,
        "missing_results": 0,
        "errors": [],
        "details_by_band": defaultdict(lambda: {"total": 0, "consistent": 0, "inconsistent": 0}),
        "detail_entries": []
    }
    
    for analysis_path in analysis_files:
        result_path = OUTPUT_DIR_RESULT / analysis_path.name
        file_stem = analysis_path.stem
        
        # Extract expected band from filename (e.g., "ielts7.5" -> 7.5)
        try:
            if "ielts" in file_stem:
                parts = file_stem.replace("ielts", "").split("-")
                if len(parts) >= 1 and parts[0]:
                    try:
                        expected_band = float(parts[0])
                    except:
                        expected_band = None
                else:
                    expected_band = None
            else:
                expected_band = None
        except:
            expected_band = None
        
        if not result_path.exists():
            consistency_report["missing_results"] += 1
            consistency_report["errors"].append(f"Result file missing for {analysis_path.name}")
            print(f"❌ {file_stem:30} - Result file missing")
            continue
        
        try:
            with analysis_path.open("r") as f:
                analysis_data = json.load(f)
            
            with result_path.open("r") as f:
                result_data = json.load(f)
            
            consistency_report["files_checked"] += 1
            
            # Extract band from result - check both top level and nested
            overall_band = result_data.get("band_scores", {}).get("overall_band")
            if overall_band is None:
                overall_band = result_data.get("overall_band")  # Try top level
            
            if overall_band is None:
                consistency_report["errors"].append(
                    f"{analysis_path.name}: No overall_band in results"
                )
                print(f"❌ {file_stem:30} - No overall_band in result")
                continue
            
            # Check if the result has expected fields (old format at top level)
            has_band_scores = "overall_band" in result_data or "band_scores" in result_data
            has_confidence = "confidence" in result_data or ("band_scores" in result_data and "confidence" in result_data.get("band_scores", {}))
            has_descriptors = "descriptors" in result_data
            has_feedback = "feedback" in result_data
            
            # For analysis data
            has_raw_analysis = "raw_analysis" in analysis_data
            has_rubric = "rubric_estimations" in analysis_data
            
            # Overall consistency check
            is_consistent = (
                has_band_scores and 
                (has_confidence or has_descriptors or has_feedback) and
                has_raw_analysis and 
                has_rubric
            )
            
            # Check if band matches filename
            band_match = False
            if expected_band is not None:
                band_match = abs(float(overall_band) - expected_band) < 0.1
            
            if is_consistent:
                consistency_report["consistent"] += 1
                status = "✓"
            else:
                consistency_report["inconsistent"] += 1
                status = "⚠"
            
            # Track by band
            band_str = f"{overall_band:.1f}"
            consistency_report["details_by_band"][band_str]["total"] += 1
            if is_consistent:
                consistency_report["details_by_band"][band_str]["consistent"] += 1
            else:
                consistency_report["details_by_band"][band_str]["inconsistent"] += 1
            
            # Record detail
            detail = {
                "file": file_stem,
                "expected_band": expected_band,
                "actual_band": overall_band,
                "band_match": band_match,
                "has_band_scores": has_band_scores,
                "has_confidence": has_confidence,
                "has_descriptors": has_descriptors,
                "has_feedback": has_feedback,
                "has_raw_analysis": has_raw_analysis,
                "has_rubric": has_rubric,
                "consistent": is_consistent
            }
            consistency_report["detail_entries"].append(detail)
            
            match_indicator = "✓" if band_match else "~" if expected_band else "?"
            print(
                f"{status} {file_stem:30} Band {overall_band:3.1f} "
                f"(Expected: {expected_band if expected_band else 'N/A':>3}) {match_indicator}"
            )
        
        except Exception as e:
            consistency_report["errors"].append(f"{analysis_path.name}: {str(e)}")
            print(f"❌ {file_stem:30} - Error: {str(e)[:50]}")
    
    return consistency_report


def print_summary(report):
    """Print detailed summary."""
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print(f"\nFiles checked: {report['files_checked']}")
    print(f"Missing results: {report['missing_results']}")
    print(f"Consistent: {report['consistent']}")
    print(f"Inconsistent: {report['inconsistent']}")
    
    if report['details_by_band']:
        print(f"\n--- Breakdown by Band ---")
        for band in sorted(report['details_by_band'].keys(), key=float, reverse=True):
            details = report['details_by_band'][band]
            consistency_rate = (
                100 * details['consistent'] / details['total']
                if details['total'] > 0 else 0
            )
            print(
                f"  Band {band}: {details['consistent']:2d}/{details['total']:2d} "
                f"({consistency_rate:5.1f}%) consistent"
            )
    
    if report['errors']:
        print(f"\n--- Errors ({len(report['errors'])}) ---")
        for error in report['errors'][:10]:
            print(f"  • {error}")
        if len(report['errors']) > 10:
            print(f"  ... and {len(report['errors']) - 10} more")
    
    # Overall pass/fail
    consistency_pct = (
        100 * report['consistent'] / report['files_checked']
        if report['files_checked'] > 0 else 0
    )
    
    print(f"\n" + "="*70)
    print(f"OVERALL CONSISTENCY: {consistency_pct:.1f}%")
    if consistency_pct >= 95:
        print("✅ PASS - Results are consistent with data")
    elif consistency_pct >= 80:
        print("⚠️ WARNING - Some inconsistencies detected")
    else:
        print("❌ FAIL - Major inconsistencies detected")
    print("="*70 + "\n")


if __name__ == "__main__":
    report = verify_consistency()
    print_summary(report)
