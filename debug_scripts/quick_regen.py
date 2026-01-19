"""
Quick regeneration script for band results
"""
import json
from pathlib import Path
from src.core.analyze_band import build_analysis
from src.core.ielts_band_scorer import score_ielts_speaking

audio_dir = Path("outputs/audio_analysis")
output_dir = Path("outputs/band_results_fixed")
output_dir.mkdir(exist_ok=True)

for file in sorted(audio_dir.glob("*.json")):
    with open(file) as f:
        data = json.load(f)
    
    raw = data["raw_analysis"]
    analysis = build_analysis(raw)
    scores = score_ielts_speaking(
        analysis["metrics_for_scoring"],
        raw.get("raw_transcript", ""),
        use_llm=True
    )
    
    result = {
        "band_scores": {
            "overall_band": scores["overall_band"],
            "criterion_bands": scores["criterion_bands"],
            "descriptors": scores["descriptors"],
            "feedback": scores["feedback"],
        },
        "analysis": {
            "metadata": analysis["metadata"],
            "fluency_analysis": raw.get("fluency_analysis", {}),
            "pronunciation": analysis["pronunciation"],
        },
        "metrics": analysis["metrics_for_scoring"],
    }
    
    with open(output_dir / file.name, "w") as f:
        json.dump(result, f, indent=2)
    
    pron = scores["criterion_bands"]["pronunciation"]
    overall = scores["overall_band"]
    print(f"{file.stem}: Overall {overall}, Pronunciation {pron}")
