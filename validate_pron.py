"""
Final pronunciation validation
"""
import json
from pathlib import Path

expected_ranges = {
    "ielts5-5.5": (5.0, 6.5),
    "ielts5.5": (5.0, 6.5),
    "ielts7-7.5": (6.5, 7.5),
    "ielts7": (6.5, 7.5),
    "ielts8-8.5": (7.5, 8.5),
    "ielts8.5": (8.0, 9.0),
    "ielts9": (8.0, 9.0),
}

band_results = Path("outputs/band_results_fixed")

print("\nPRONUNCIATION VALIDATION:\n")
print(f"{'File':<15} {'Expected':<15} {'Actual':<10} {'Status':<10}")
print("-" * 50)

passed = 0
for file in sorted(band_results.glob("*.json")):
    with open(file) as f:
        data = json.load(f)
    
    name = file.stem
    expected = expected_ranges[name]
    actual = data["band_scores"]["criterion_bands"]["pronunciation"]
    
    in_range = expected[0] <= actual <= expected[1]
    status = "PASS" if in_range else "FAIL"
    if in_range:
        passed += 1
    
    print(f"{name:<15} {str(expected):<15} {actual:<10.1f} {status:<10}")

print(f"\nResult: {passed}/7 passed")
