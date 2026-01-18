import sys
import json
import traceback
import asyncio
from pathlib import Path
import gc
import numpy as np

# --- Project root setup ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rubric_from_metrics import generate_constraints
from src.analyzer_raw import analyze_speech
from src.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.analyze_band import analyze_band_from_audio, analyze_band_from_analysis
from src.logging_config import setup_logging
from src.exceptions import SpeechAnalysisError

# Setup logging
logger = setup_logging(level="INFO")

INPUT_DIR = PROJECT_ROOT / "data" / "ielts_part_2"
OUTPUT_DIR_ANALYSIS = PROJECT_ROOT / "outputs" / "audio_analysis"
OUTPUT_DIR_RESULT = PROJECT_ROOT / "outputs" / "band_results"


# =========================================================
# STAGE 1: RAW + LLM ANALYSIS
# =========================================================
ANALYSIS_SEMAPHORE = asyncio.Semaphore(1)


def make_json_safe(obj):
    """Convert numpy types to native Python types for JSON serialization."""
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

async def run_analysis(limit: int = None):
    """Run speech analysis on all audio files with error handling."""
    wav_files = sorted(INPUT_DIR.rglob("*.wav"))
    OUTPUT_DIR_ANALYSIS.mkdir(parents=True, exist_ok=True)

    total = len(wav_files)
    failures = []

    logger.info(f"Found {total} wav files")

    for idx, wav_path in enumerate(wav_files, start=1):
        if limit is not None and idx > limit:
            break
        out_path = OUTPUT_DIR_ANALYSIS / f"{wav_path.stem}.json"
        logger.info(f"[{idx}/{total}] analyzing {wav_path.name}")

        try:
            async with ANALYSIS_SEMAPHORE:
                result = await analyze_speech(wav_path)

            # llm_result = extract_llm_annotations(result["raw_transcript"])
            # llm_metrics = aggregate_llm_metrics(llm_result)
            rubric_estimations = generate_constraints(result)

            analysis = {
                "raw_analysis": result,
                "rubric_estimations": rubric_estimations,
                # "llm_metrics": llm_metrics,
            }

            with out_path.open("w", encoding="utf-8") as f:
                json.dump(make_json_safe(analysis), f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved analysis to {out_path}")

            # Let the system breathe
            await asyncio.sleep(0.3)
            gc.collect()

        except SpeechAnalysisError as e:
            failures.append((wav_path.name, str(e)))
            logger.error(f"❌ Analysis failed for {wav_path.name}: {e.message}")

            # Extra cooldown after failure
            await asyncio.sleep(1.0)
            gc.collect()
        except Exception as e:
            failures.append((wav_path.name, str(e)))
            logger.error(f"❌ Unexpected error for {wav_path.name}: {str(e)}")
            logger.debug(traceback.format_exc())

            # Extra cooldown after failure
            await asyncio.sleep(1.0)
            gc.collect()

    logger.info("\n=== Analysis complete ===")
    logger.info(f"Total files: {total}")
    logger.info(f"Successes: {total - len(failures)}")
    logger.info(f"Failures: {len(failures)}")
    
    if failures:
        logger.warning("Failed files:")
        for filename, error in failures:
            logger.warning(f"  - {filename}: {error}")

# =========================================================
# STAGE 2: IELTS BAND SCORING
# =========================================================
# Semaphore for LLM rate limiting (OpenAI has rate limits)
LLM_SEMAPHORE = asyncio.Semaphore(3)


async def score_single_file(idx: int, total: int, path: Path, out_path: Path) -> tuple:
    """Score a single analysis file asynchronously with LLM rate limiting.
    
    Returns:
        (success: bool, filename: str, error: str or None)
    """
    try:
        # Rate limit LLM calls to 3 concurrent requests
        async with LLM_SEMAPHORE:
            with path.open("r", encoding="utf-8") as f:
                analysis_json = json.load(f)

            # Explicit unpacking
            raw_analysis = analysis_json["raw_analysis"]
            
            logger.info(f"[{idx}/{total}] scoring {path.name}")

            # Call the correct analyze_band signature
            report = await analyze_band_from_analysis(raw_analysis)

            # Write results
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved band results to {out_path}")
            return (True, path.name, None)

    except KeyError as e:
        error_msg = f"Missing key: {str(e)}"
        logger.error(f"❌ Missing data key in {path.name}: {error_msg}")
        return (False, path.name, error_msg)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Scoring failed for {path.name}: {error_msg}")
        logger.debug(traceback.format_exc())
        return (False, path.name, error_msg)


async def run_result():
    """Score all analysis results in parallel with LLM rate limiting."""
    OUTPUT_DIR_RESULT.mkdir(parents=True, exist_ok=True)

    analysis_files = sorted(OUTPUT_DIR_ANALYSIS.glob("*.json"))
    total = len(analysis_files)

    logger.info(f"\nScoring {total} analysis files (parallel with LLM rate limiting)")

    # Create all scoring tasks
    tasks = []
    for idx, path in enumerate(analysis_files, start=1):
        out_path = OUTPUT_DIR_RESULT / path.name
        tasks.append(score_single_file(idx, total, path, out_path))

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Aggregate results
    successes = sum(1 for success, _, _ in results if success)
    failures = [(filename, error) for success, filename, error in results if not success]

    logger.info("\n=== Band scoring complete ===")
    logger.info(f"Total files: {total}")
    logger.info(f"Successes: {successes}")
    logger.info(f"Failures: {len(failures)}")

    if failures:
        logger.warning("Failed files:")
        for filename, error in failures:
            logger.warning(f"  - {filename}: {error}")



# =========================================================
# OPTIONAL: MERGE RESULTS
# =========================================================
def merge_band_results(input_dir: Path, output_path: Path):
    """Merge individual band results into single JSON file."""
    merged = {}
    failures = []

    json_files = sorted(
        p for p in input_dir.glob("*.json")
        if p.name != output_path.name
    )

    logger.info(f"Merging {len(json_files)} json files")

    for path in json_files:
        key = path.stem

        try:
            with path.open("r", encoding="utf-8") as f:
                merged[key] = json.load(f)
        except Exception as e:
            failures.append((path.name, str(e)))
            logger.error(f"❌ Failed to read {path.name}: {str(e)}")

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    logger.info("\n=== Merge complete ===")
    logger.info(f"Total merged: {len(merged)}")
    logger.info(f"Failures: {len(failures)}")
    
    if failures:
        logger.warning("Failed files:")
        for filename, error in failures:
            logger.warning(f"  - {filename}: {error}")


# =========================================================
# ENTRY POINT
# =========================================================
async def main():
    await run_analysis(1)
    await run_result()

    # Optional merge
    # merge_band_results(
    #     input_dir=OUTPUT_DIR_RESULT,
    #     output_path=OUTPUT_DIR_RESULT / "merged_band_analysis.txt",
    # )


if __name__ == "__main__":
    asyncio.run(main())
