"""
Check exact metrics for pronunciation scoring
"""
import json
from pathlib import Path

band_results = Path("outputs/band_results_fixed")

for file in sorted(band_results.glob("*.json")):
    with open(file) as f:
        data = json.load(f)
    
    mean_conf = data["metrics"]["mean_word_confidence"]
    low_conf = data["metrics"]["low_confidence_ratio"]
    pron_score = data["band_scores"]["criterion_bands"]["pronunciation"]
    
    print(f"{file.stem:<15} | Mean: {mean_conf:.3f} | Low: {low_conf:.3f} ({low_conf*100:>5.1f}%) | Score: {pron_score:.1f}")
