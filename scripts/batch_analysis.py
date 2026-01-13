import csv
import json
from pathlib import Path
from tqdm import tqdm
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analyzer import analyze_speech


AUDIO_DIR = Path("data/l2arctic_spontaneous")
OUT_CSV = Path("outputs/l2arctic_fluency_results.csv")
OUT_CSV.parent.mkdir(exist_ok=True)


def flatten_result(audio_path: Path, result: dict) -> dict:
    """Flatten analysis output into a single CSV row."""
    verdict = result.get("verdict", {})
    metrics = result.get("normalized_metrics", {})
    benchmarking = result.get("benchmarking", {})

    return {
        "sample_id": audio_path.stem,
        "filename": audio_path.name,

        # verdict
        "fluency_score": verdict.get("fluency_score"),
        "readiness": verdict.get("readiness"),

        # core metrics
        "wpm": metrics.get("wpm"),
        "fillers_per_min": metrics.get("fillers_per_min"),
        "stutters_per_min": metrics.get("stutters_per_min"),
        "pause_variability": metrics.get("pause_variability"),
        "long_pauses_per_min": metrics.get("long_pauses_per_min"),

        # benchmarking
        "percentile": benchmarking.get("percentile"),
        "score_gap": benchmarking.get("score_gap"),
    }


def main():
    audio_files = sorted(AUDIO_DIR.glob("*.wav"))

    if not audio_files:
        raise RuntimeError("No audio files found")

    rows = []

    for audio_path in tqdm(audio_files, desc="Analyzing audio"):
        try:
            result = analyze_speech(
                audio_path=str(audio_path),
                speech_context="conversational",
                device="cpu"
            )

            # skip insufficient samples
            if result["verdict"]["fluency_score"] is None:
                continue

            rows.append(flatten_result(audio_path, result))

        except Exception as e:
            print(f"[ERROR] {audio_path.name}: {e}")

    # write CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Saved {len(rows)} results → {OUT_CSV}")


if __name__ == "__main__":
    main()
