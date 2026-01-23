#!/usr/bin/env python3
"""Check existing band results"""
import json
from pathlib import Path

print("=" * 80)
print("BAND RESULTS FOR ielts5-5.5")
print("=" * 80)

band_file = Path("outputs/band_results/ielts5-5.5.json")

with open(band_file) as f:
    band_data = json.load(f)

cb = band_data['band_scores']['criterion_bands']
print(f"\nFluency:       {cb['fluency_coherence']}")
print(f"Pronunciation: {cb['pronunciation']}")
print(f"Lexical:       {cb['lexical_resource']}")
print(f"Grammar:       {cb['grammatical_range_accuracy']}")
print(f"──────────────────────────────────")
overall = band_data['band_scores']['overall_band']
print(f"OVERALL:       {overall}")

print("\n" + "=" * 80)
print("BAND RESULTS FOR ielts5.5 (CALIBRATED)")
print("=" * 80)

band_file_cal = Path("outputs/band_results_calibrated/ielts5.5.json")
if band_file_cal.exists():
    with open(band_file_cal) as f:
        band_data_cal = json.load(f)
    cb = band_data_cal['band_scores']['criterion_bands']
    print(f"\nFluency:       {cb['fluency_coherence']}")
    print(f"Pronunciation: {cb['pronunciation']}")
    print(f"Lexical:       {cb['lexical_resource']}")
    print(f"Grammar:       {cb['grammatical_range_accuracy']}")
    print(f"──────────────────────────────────")
    overall = band_data_cal['band_scores']['overall_band']
    print(f"OVERALL:       {overall}")

print("\n" + "=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print("\nThe MODAL response showed:")
print("  Fluency:       6.5")
print("  Pronunciation: 5.5")
print("  Lexical:       8")
print("  Grammar:       7")
print("  OVERALL:       7")
print("\nWhich LOCAL ielts5-5.5 file matches this?")
print("Checking all files...")

from pathlib import Path
import re

for json_file in sorted(Path("outputs").rglob("*.json")):
    if "ielts5" not in json_file.name:
        continue
    try:
        with open(json_file) as f:
            data = json.load(f)
        if 'band_scores' in data:
            cb = data.get('band_scores', {}).get('criterion_bands', {})
            if cb.get('fluency_coherence') == 6.5 and cb.get('grammatical_range_accuracy') == 7:
                print(f"\n✓ MATCH FOUND: {json_file}")
                print(f"  Fluency:       {cb['fluency_coherence']}")
                print(f"  Pronunciation: {cb['pronunciation']}")
                print(f"  Lexical:       {cb['lexical_resource']}")
                print(f"  Grammar:       {cb['grammatical_range_accuracy']}")
                print(f"  Overall:       {data['band_scores']['overall_band']}")
    except:
        pass
