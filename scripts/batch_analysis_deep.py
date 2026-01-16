# uv run python scripts/batch_analysis_deep.py

import sys
import json
import csv
from pathlib import Path
from tqdm import tqdm

# --- path fix ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analyzer_old import analyze_speech


AUDIO_DIR = Path("data/l2arctic_spontaneous")
OUT_DIR = Path("outputs/l2arctic_deep")
OUT_DIR.mkdir(parents=True, exist_ok=True)

INDEX_CSV = Path("outputs/l2arctic_deep_index.csv")


def build_deep_record(audio_path: Path, result: dict) -> dict:
    """Build a deep, LLM-friendly analysis record."""

    verdict = result.get("verdict", {})
    metrics = result.get("normalized_metrics", {})
    benchmarking = result.get("benchmarking", {})
    opinions = result.get("opinions", {})

    words = result.get("word_timestamps", [])
    segments = result.get("segment_timestamps", [])
    fillers = result.get("filler_events", [])

    # Build readable transcript with timestamps
    transcript = " ".join(w["word"] for w in words)

    filler_summary = [
        {
            "type": f["type"],
            "text": f["text"],
            "style": f.get("style", "unknown"),
            "start": round(f["start"], 3),
            "end": round(f["end"], 3),
            "duration": round(f["duration"], 3),
            "count": f.get("count", 1),
        }
        for f in fillers
    ]

    return {
        "meta": {
            "sample_id": audio_path.stem,
            "filename": audio_path.name,
            "duration_sec": round(
                segments[-1]["end"], 2
            ) if segments else None,
            "word_count": len(words),
            "filler_event_count": len(fillers),
        },

        "verdict": verdict,
        "benchmarking": benchmarking,

        "metrics": metrics,

        "sub_analysis": {
            "primary_issues": opinions.get("primary_issues", []),
            "action_plan": opinions.get("action_plan", []),
        },

        "transcript": {
            "text": transcript,
            "segments": [
                {
                    "text": s["text"],
                    "start": round(s["start"], 3),
                    "end": round(s["end"], 3),
                }
                for s in segments
            ],
            "words": [
                {
                    "word": w["word"],
                    "start": round(w["start"], 3),
                    "end": round(w["end"], 3),
                }
                for w in words
            ],
        },

        "disfluency_events": filler_summary,
    }


def main():
    audio_files = sorted(AUDIO_DIR.glob("*.wav"))

    if not audio_files:
        raise RuntimeError("No audio files found")

    index_rows = []

    for audio_path in tqdm(audio_files, desc="Deep analysis"):
        try:
            result = analyze_speech(
                audio_path=str(audio_path),
                speech_context="conversational",
                device="cpu",
            )

            if result["verdict"]["fluency_score"] is None:
                continue

            record = build_deep_record(audio_path, result)

            out_json = OUT_DIR / f"{audio_path.stem}.json"
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)

            index_rows.append({
                "sample_id": audio_path.stem,
                "filename": audio_path.name,
                "fluency_score": record["verdict"]["fluency_score"],
                "readiness": record["verdict"]["readiness"],
                "wpm": record["metrics"].get("wpm"),
                "fillers_per_min": record["metrics"].get("fillers_per_min"),
                "pause_variability": record["metrics"].get("pause_variability"),
                "json_path": str(out_json),
            })

        except Exception as e:
            print(f"[ERROR] {audio_path.name}: {e}")

    # write index CSV
    with open(INDEX_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=index_rows[0].keys())
        writer.writeheader()
        writer.writerows(index_rows)

    print(f"\n✓ Deep analysis complete")
    print(f"✓ JSON files → {OUT_DIR}")
    print(f"✓ Index CSV → {INDEX_CSV}")


if __name__ == "__main__":
    main()
