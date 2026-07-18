"""
Final summary display
"""
import json
from pathlib import Path

br = Path("outputs/band_results")
print("\n" + "="*90)
print("FINAL BAND RESULTS SUMMARY")
print("="*90 + "\n")
print(f"{'File':<15} {'Overall':<10} {'Fluency':<10} {'Pron':<8} {'Lexical':<10} {'Grammar':<10}")
print("-"*90)

for f in sorted(br.glob("*.json")):
    with open(f) as file:
        d = json.load(file)
    b = d["band_scores"]["criterion_bands"]
    overall = d["band_scores"]["overall_band"]
    fluency = b["fluency_coherence"]
    pron = b["pronunciation"]
    lexical = b["lexical_resource"]
    grammar = b["grammatical_range_accuracy"]
    
    print(f"{f.stem:<15} {overall:<10.1f} {fluency:<10.1f} {pron:<8.1f} {lexical:<10.1f} {grammar:<10.1f}")

print("\n" + "="*90 + "\n")
