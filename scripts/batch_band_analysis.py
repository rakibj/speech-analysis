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

INPUT_DIR = PROJECT_ROOT / "data" / "ielts_part_2"
OUTPUT_DIR_ANALYSIS = PROJECT_ROOT / "outputs" / "audio_analysis"
OUTPUT_DIR_RESULT = PROJECT_ROOT / "outputs" / "band_results"


# =========================================================
# STAGE 1: RAW + LLM ANALYSIS
# =========================================================
ANALYSIS_SEMAPHORE = asyncio.Semaphore(1)


def make_json_safe(obj):
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
    wav_files = sorted(INPUT_DIR.rglob("*.wav"))
    OUTPUT_DIR_ANALYSIS.mkdir(parents=True, exist_ok=True)

    total = len(wav_files)
    failures = []

    print(f"Found {total} wav files")

    for idx, wav_path in enumerate(wav_files, start=1):
        if limit is not None and idx > limit:
            break
        out_path = OUTPUT_DIR_ANALYSIS / f"{wav_path.stem}.json"
        print(f"[{idx}/{total}] analyzing {wav_path.name}")

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

            # # 🔑 Let the system breathe
            await asyncio.sleep(0.3)
            gc.collect()

        except Exception:
            failures.append(wav_path.name)
            print(f"❌ FAILED: {wav_path.name}")
            traceback.print_exc()

            # Extra cooldown after failure
            await asyncio.sleep(1.0)
            gc.collect()

    print("\n=== Analysis complete ===")
    print(f"Total files: {total}")
    print(f"Failures: {len(failures)}")

# =========================================================
# STAGE 2: IELTS BAND SCORING
# =========================================================
async def run_result():
    OUTPUT_DIR_RESULT.mkdir(parents=True, exist_ok=True)

    analysis_files = sorted(OUTPUT_DIR_ANALYSIS.glob("*.json"))
    total = len(analysis_files)
    failures = []

    print(f"\nScoring {total} analysis files")

    for idx, path in enumerate(analysis_files, start=1):
        out_path = OUTPUT_DIR_RESULT / path.name
        print(f"[{idx}/{total}] scoring {path.name}")

        try:
            with path.open("r", encoding="utf-8") as f:
                analysis_json = json.load(f)

            # 🔑 EXPLICIT unpacking (this is the key fix)
            raw_analysis = analysis_json["raw_analysis"]
            llm_metrics = analysis_json["llm_metrics"]

            # 🔑 Call the correct analyze_band signature
            report = await analyze_band_from_analysis(raw_analysis, llm_metrics)

            with out_path.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        except Exception:
            failures.append(path.name)
            print(f"❌ FAILED: {path.name}")
            traceback.print_exc()

    print("\n=== Band scoring complete ===")
    print(f"Total files: {total}")
    print(f"Failures: {len(failures)}")

    if failures:
        print("Failed files:")
        for f in failures:
            print(" -", f)



# =========================================================
# OPTIONAL: MERGE RESULTS
# =========================================================
def merge_band_results(input_dir: Path, output_path: Path):
    merged = {}
    failures = []

    json_files = sorted(
        p for p in input_dir.glob("*.json")
        if p.name != output_path.name
    )

    print(f"Merging {len(json_files)} json files")

    for path in json_files:
        key = path.stem

        try:
            with path.open("r", encoding="utf-8") as f:
                merged[key] = json.load(f)
        except Exception:
            failures.append(path.name)
            print(f"❌ Failed to read {path.name}")
            traceback.print_exc()

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print("\n=== Merge complete ===")
    print(f"Total merged: {len(merged)}")
    print(f"Failures: {len(failures)}")


# =========================================================
# ENTRY POINT
# =========================================================
async def main():
    await run_analysis()
    # await run_result()

    # Optional merge
    # merge_band_results(
    #     input_dir=OUTPUT_DIR_RESULT,
    #     output_path=OUTPUT_DIR_RESULT / "merged_band_analysis.txt",
    # )


if __name__ == "__main__":
    asyncio.run(main())
