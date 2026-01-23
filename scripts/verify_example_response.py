#!/usr/bin/env python3
"""
Detailed verification of example API response structure.
Shows exactly what's in the response and validates each component.
"""

import json
from pathlib import Path

# Your example response
example_response = {
    'job_id': '3c6e75c6-de7d-49de-afbb-7de1452dde2c',
    'status': 'completed',
    'overall_band': 6,
    'criterion_bands': {
        'fluency_coherence': 6,
        'pronunciation': 7,
        'lexical_resource': 6,
        'grammatical_range_accuracy': 6
    },
    'statistics': {
        'total_words_transcribed': 163,
        'content_words': 162,
        'filler_words_detected': 1,
        'filler_percentage': 0.61,
        'is_monotone': False
    },
    'normalized_metrics': {
        'wpm': 88.73,
        'long_pauses_per_min': 2.19,
        'fillers_per_min': 2.74,
        'pause_variability': 1.472,
        'speech_rate_variability': 0.317,
        'vocab_richness': 0.537,
        'type_token_ratio': 0.537,
        'repetition_ratio': 0.072,
        'mean_utterance_length': 9.59
    },
    'confidence': {
        'overall_confidence': 0.44
    }
}

print("\n" + "="*100)
print("EXAMPLE API RESPONSE VERIFICATION")
print("="*100 + "\n")

# Verify structure
print("📋 RESPONSE STRUCTURE")
print("-"*100)
print(f"✅ job_id: {example_response['job_id']}")
print(f"✅ status: {example_response['status']}")
print(f"✅ overall_band: {example_response['overall_band']}")
print(f"\n✅ criterion_bands:")
for criterion, band in example_response['criterion_bands'].items():
    print(f"   • {criterion}: {band}")

print(f"\n✅ statistics ({len(example_response['statistics'])} fields):")
for stat, value in example_response['statistics'].items():
    print(f"   • {stat}: {value}")

print(f"\n✅ normalized_metrics ({len(example_response['normalized_metrics'])} fields):")
for metric, value in example_response['normalized_metrics'].items():
    print(f"   • {metric}: {value}")

print(f"\n✅ confidence:")
for key, value in example_response['confidence'].items():
    print(f"   • {key}: {value}")

# Verify calculations
print("\n" + "="*100)
print("✅ CALCULATION VERIFICATION")
print("="*100 + "\n")

# Band calculation
avg = sum(example_response['criterion_bands'].values()) / 4
rounded = round(avg * 2) / 2
print(f"Band Calculation:")
print(f"  (6 + 7 + 6 + 6) / 4 = {avg}")
print(f"  Rounded to 0.5: {rounded}")
print(f"  ✅ Matches overall_band ({example_response['overall_band']}) : {rounded == example_response['overall_band']}")

# Filler percentage
total = example_response['statistics']['total_words_transcribed']
fillers = example_response['statistics']['filler_words_detected']
expected_pct = round(100 * fillers / total, 2)
actual_pct = example_response['statistics']['filler_percentage']
print(f"\nFiller Percentage Calculation:")
print(f"  {fillers} fillers / {total} total words = {100*fillers/total:.4f}%")
print(f"  Rounded to 2 decimals: {expected_pct}%")
print(f"  ✅ Matches reported ({actual_pct}%) : {abs(expected_pct - actual_pct) < 0.01}")

# Confidence range
conf = example_response['confidence']['overall_confidence']
print(f"\nConfidence Range:")
print(f"  Value: {conf}")
print(f"  ✅ In valid range [0, 1]: {0 <= conf <= 1}")

# Criterion bands range
print(f"\nCriterion Bands Range:")
for criterion, band in example_response['criterion_bands'].items():
    in_range = 5.0 <= band <= 9.0
    print(f"  {criterion}: {band} ✅ {in_range}")

# Content vs total words
content = example_response['statistics']['content_words']
total = example_response['statistics']['total_words_transcribed']
fillers = example_response['statistics']['filler_words_detected']
expected_content = total - fillers
print(f"\nWord Count Consistency:")
print(f"  Total: {total}")
print(f"  Content: {content}")
print(f"  Fillers: {fillers}")
print(f"  Expected content (total - fillers): {expected_content}")
print(f"  ✅ Matches reported content: {content == expected_content}")

# Metrics value ranges
print(f"\n✅ Normalized Metrics Ranges:")
metrics_ranges = {
    'wpm': (40, 200),
    'long_pauses_per_min': (0, 20),
    'fillers_per_min': (0, 20),
    'pause_variability': (0, 5),
    'speech_rate_variability': (0, 2),
    'vocab_richness': (0, 1),
    'type_token_ratio': (0, 1),
    'repetition_ratio': (0, 1),
    'mean_utterance_length': (0, 50)
}

for metric, (min_val, max_val) in metrics_ranges.items():
    actual = example_response['normalized_metrics'][metric]
    in_range = min_val <= actual <= max_val
    status = "✅" if in_range else "⚠️"
    print(f"  {status} {metric:30} = {actual:8.3f} (expected: [{min_val}-{max_val}])")

# Summary
print("\n" + "="*100)
print("VALIDATION SUMMARY")
print("="*100 + "\n")

all_checks = [
    ("overall_band calculation", example_response['overall_band'] == 6.0),
    ("filler_percentage accuracy", abs(actual_pct - expected_pct) < 0.01),
    ("confidence in range", 0 <= conf <= 1),
    ("all criterion bands in range", all(5.0 <= v <= 9.0 for v in example_response['criterion_bands'].values())),
    ("content_words = total - fillers", content == expected_content),
    ("all metrics in expected ranges", all(min_val <= example_response['normalized_metrics'][m] <= max_val 
                                           for m, (min_val, max_val) in metrics_ranges.items())),
]

passed = sum(1 for _, result in all_checks if result)
total = len(all_checks)

for check, result in all_checks:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status} | {check}")

print(f"\n✅ Overall: {passed}/{total} checks passed ({100*passed/total:.0f}%)")

# Missing fields check (what SHOULD be there but in this minimal example)
print("\n" + "="*100)
print("ℹ️  OPTIONAL FIELDS (Not in this minimal example, but available in detail='feedback')")
print("="*100 + "\n")

optional_fields = [
    ("descriptor (overall band)", "IELTS band descriptor text"),
    ("criterion_descriptors", "Per-criterion IELTS descriptors with LLM findings"),
    ("llm_analysis", "LLM grammar/vocabulary/coherence findings"),
    ("speech_quality", "Word confidence and prosody metrics"),
    ("transcript (feedback tier)", "Full speech transcription"),
    ("grammar_errors (feedback tier)", "Identified grammar issues"),
    ("word_choice_errors (feedback tier)", "Vocabulary misuse examples"),
]

print("These fields appear when detail='feedback' or detail='full':\n")
for field, description in optional_fields:
    print(f"  • {field:40} - {description}")

print("\nFor full detail tier, also includes:")
print("  • word_timestamps - Timestamped word list")
print("  • filler_events - Timestamped fillers")
print("  • content_words - Non-filler word count")

print("\n" + "="*100 + "\n")
