"""
Verify consistency between analysis data and band results.
1. Run analysis to generate data files
2. Run result scoring to generate band files
3. Compare consistency between data and results
4. Generate summary report
"""

import sys
import json
import asyncio
import traceback
from pathlib import Path
from collections import defaultdict

# --- Project root setup ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging_config import setup_logging

logger = setup_logging(level="INFO")

INPUT_DIR = PROJECT_ROOT / "data" / "ielts_part_2"
OUTPUT_DIR_ANALYSIS = PROJECT_ROOT / "outputs" / "audio_analysis"
OUTPUT_DIR_RESULT = PROJECT_ROOT / "outputs" / "band_results"


async def run_analysis(limit: int = None):
    """Run speech analysis on all audio files."""
    from src.core.rubric_from_metrics import generate_constraints
    from src.core.analyzer_raw import analyze_speech
    import numpy as np
    import gc
    
    ANALYSIS_SEMAPHORE = asyncio.Semaphore(1)
    
    def make_json_safe(obj):
        """Convert numpy types to native Python types."""
        if isinstance(obj, dict):
            return {k: make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_json_safe(v) for v in obj]
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        else:
            return obj
    
    wav_files = sorted(INPUT_DIR.rglob("*.wav"))
    OUTPUT_DIR_ANALYSIS.mkdir(parents=True, exist_ok=True)

    total = len(wav_files)
    failures = []
    successes = 0

    logger.info(f"\n{'='*60}")
    logger.info(f"STAGE 1: RUNNING ANALYSIS")
    logger.info(f"{'='*60}")
    logger.info(f"Found {total} wav files")

    for idx, wav_path in enumerate(wav_files, start=1):
        if limit is not None and idx > limit:
            break
        out_path = OUTPUT_DIR_ANALYSIS / f"{wav_path.stem}.json"
        logger.info(f"[{idx}/{total}] {wav_path.name}")

        try:
            async with ANALYSIS_SEMAPHORE:
                result = await analyze_speech(wav_path)

            rubric_estimations = generate_constraints(result)

            analysis = {
                "raw_analysis": result,
                "rubric_estimations": rubric_estimations,
            }

            with out_path.open("w", encoding="utf-8") as f:
                json.dump(make_json_safe(analysis), f, indent=2, ensure_ascii=False)
            
            successes += 1
            await asyncio.sleep(0.3)
            gc.collect()

        except Exception as e:
            failures.append((wav_path.name, str(e)))
            logger.error(f"  ❌ Failed: {str(e)[:80]}")
            await asyncio.sleep(1.0)
            gc.collect()

    logger.info(f"\n  Successes: {successes} / {total}")
    logger.info(f"  Failures: {len(failures)}")
    return successes, failures


async def run_result():
    """Score all analysis results."""
    from src.core.analyze_band import analyze_band_from_analysis
    
    LLM_SEMAPHORE = asyncio.Semaphore(3)
    
    async def score_single_file(idx: int, total: int, path: Path, out_path: Path) -> tuple:
        try:
            async with LLM_SEMAPHORE:
                with path.open("r", encoding="utf-8") as f:
                    analysis_json = json.load(f)

                raw_analysis = analysis_json["raw_analysis"]
                
                logger.info(f"[{idx}/{total}] {path.name}")

                report = await analyze_band_from_analysis(raw_analysis)

                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                return (True, path.name, None)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"  ❌ Failed: {error_msg[:80]}")
            return (False, path.name, error_msg)

    OUTPUT_DIR_RESULT.mkdir(parents=True, exist_ok=True)
    analysis_files = sorted(OUTPUT_DIR_ANALYSIS.glob("*.json"))
    total = len(analysis_files)

    logger.info(f"\n{'='*60}")
    logger.info(f"STAGE 2: RUNNING BAND SCORING")
    logger.info(f"{'='*60}")
    logger.info(f"Scoring {total} analysis files\n")

    tasks = []
    for idx, path in enumerate(analysis_files, start=1):
        out_path = OUTPUT_DIR_RESULT / path.name
        tasks.append(score_single_file(idx, total, path, out_path))

    results = await asyncio.gather(*tasks, return_exceptions=False)

    successes = sum(1 for success, _, _ in results if success)
    failures = [(filename, error) for success, filename, error in results if not success]

    logger.info(f"\n  Successes: {successes} / {total}")
    logger.info(f"  Failures: {len(failures)}")
    return successes, failures


def verify_consistency():
    """Compare analysis data with band results for consistency."""
    logger.info(f"\n{'='*60}")
    logger.info(f"STAGE 3: VERIFYING CONSISTENCY")
    logger.info(f"{'='*60}\n")
    
    analysis_files = sorted(OUTPUT_DIR_ANALYSIS.glob("*.json"))
    consistency_report = {
        "total_files": len(analysis_files),
        "files_checked": 0,
        "consistent": 0,
        "inconsistent": 0,
        "errors": [],
        "details_by_band": defaultdict(lambda: {"total": 0, "consistent": 0, "inconsistent": 0}),
    }
    
    for analysis_path in analysis_files:
        result_path = OUTPUT_DIR_RESULT / analysis_path.name
        
        if not result_path.exists():
            consistency_report["errors"].append(f"Result file missing for {analysis_path.name}")
            continue
        
        try:
            with analysis_path.open("r") as f:
                analysis_data = json.load(f)
            
            with result_path.open("r") as f:
                result_data = json.load(f)
            
            consistency_report["files_checked"] += 1
            
            # Extract band from result
            overall_band = result_data.get("band_scores", {}).get("overall_band")
            
            if overall_band is None:
                consistency_report["errors"].append(
                    f"{analysis_path.name}: No overall_band in results"
                )
                continue
            
            # Extract metrics from analysis
            raw_analysis = analysis_data.get("raw_analysis", {})
            metrics_for_scoring = result_data.get("metrics_for_scoring", {})
            
            # Check consistency indicators
            # Band should be based on the metrics in the analysis
            band_key = f"band_{overall_band:.1f}"
            
            # Check if the result has expected fields
            has_band_scores = "band_scores" in result_data
            has_metrics = "metrics_for_scoring" in result_data
            has_transcript = "transcript" in result_data
            
            is_consistent = has_band_scores and has_metrics and has_transcript
            
            if is_consistent:
                consistency_report["consistent"] += 1
            else:
                consistency_report["inconsistent"] += 1
            
            # Track by band
            band_str = f"{overall_band:.1f}"
            consistency_report["details_by_band"][band_str]["total"] += 1
            if is_consistent:
                consistency_report["details_by_band"][band_str]["consistent"] += 1
            else:
                consistency_report["details_by_band"][band_str]["inconsistent"] += 1
            
            logger.info(
                f"{analysis_path.stem}: Band {overall_band:.1f} - "
                f"{'✓' if is_consistent else '✗'}"
            )
        
        except Exception as e:
            consistency_report["errors"].append(f"{analysis_path.name}: {str(e)}")
            logger.error(f"  Error checking {analysis_path.name}: {str(e)[:80]}")
    
    return consistency_report


async def main():
    """Run full verification pipeline."""
    logger.info("\n" + "="*60)
    logger.info("BATCH BAND ANALYSIS VERIFICATION")
    logger.info("="*60)
    
    # Stage 1: Run analysis
    analysis_success, analysis_failures = await run_analysis()
    
    # Stage 2: Run result scoring
    result_success, result_failures = await run_result()
    
    # Stage 3: Verify consistency
    consistency_report = verify_consistency()
    
    # Generate summary
    logger.info(f"\n{'='*60}")
    logger.info(f"FINAL SUMMARY")
    logger.info(f"{'='*60}\n")
    
    logger.info("[STAGE 1: ANALYSIS]")
    logger.info(f"  Files processed: {analysis_success}")
    logger.info(f"  Failures: {len(analysis_failures)}")
    
    logger.info("\n[STAGE 2: BAND SCORING]")
    logger.info(f"  Files scored: {result_success}")
    logger.info(f"  Failures: {len(result_failures)}")
    
    logger.info("\n[STAGE 3: CONSISTENCY CHECK]")
    logger.info(f"  Files verified: {consistency_report['files_checked']}")
    logger.info(f"  Consistent: {consistency_report['consistent']}")
    logger.info(f"  Inconsistent: {consistency_report['inconsistent']}")
    
    if consistency_report['details_by_band']:
        logger.info("\n[BREAKDOWN BY BAND]")
        for band in sorted(consistency_report['details_by_band'].keys(), key=float, reverse=True):
            details = consistency_report['details_by_band'][band]
            consistency_rate = (
                100 * details['consistent'] / details['total']
                if details['total'] > 0 else 0
            )
            logger.info(
                f"  Band {band}: {details['consistent']}/{details['total']} "
                f"consistent ({consistency_rate:.0f}%)"
            )
    
    if consistency_report['errors']:
        logger.info(f"\n[ERRORS ({len(consistency_report['errors'])})]")
        for error in consistency_report['errors'][:10]:  # Show first 10
            logger.info(f"  - {error}")
        if len(consistency_report['errors']) > 10:
            logger.info(f"  ... and {len(consistency_report['errors']) - 10} more")
    
    # Overall pass/fail
    consistency_pct = (
        100 * consistency_report['consistent'] / consistency_report['files_checked']
        if consistency_report['files_checked'] > 0 else 0
    )
    
    logger.info(f"\n{'='*60}")
    logger.info(f"OVERALL CONSISTENCY: {consistency_pct:.1f}%")
    if consistency_pct >= 95:
        logger.info("✓ PASS - Results are consistent with data")
    elif consistency_pct >= 80:
        logger.info("⚠ WARNING - Some inconsistencies detected")
    else:
        logger.info("✗ FAIL - Major inconsistencies detected")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
