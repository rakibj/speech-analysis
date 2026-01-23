#!/usr/bin/env python3
"""Quick validation of API response structure and data accuracy."""

response = {
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

checks = []

# 1. Band calculation
avg = sum(response['criterion_bands'].values()) / 4
rounded_avg = round(avg * 2) / 2
expected_band = 6.0
match = response['overall_band'] == rounded_avg
checks.append(('Band calculation', match, f"{response['overall_band']} == {rounded_avg} (avg={avg})"))

# 2. Filler percentage calculation  
total = response['statistics']['total_words_transcribed']
fillers = response['statistics']['filler_words_detected']
expected_pct = round(100 * fillers / total, 2)
actual_pct = response['statistics']['filler_percentage']
match = abs(actual_pct - expected_pct) < 0.01
checks.append(('Filler % calculation', match, f"{actual_pct} == {expected_pct} ({fillers}/{total})"))

# 3. No articulationrate field
has_artic = 'articulationrate' in response['normalized_metrics']
checks.append(('No articulationrate field', not has_artic, f"Present: {has_artic}"))

# 4. Confidence in valid range
conf = response['confidence']['overall_confidence']
match = 0 <= conf <= 1
checks.append(('Confidence in [0,1]', match, f"Value: {conf}"))

# 5. Required metrics present
required_metrics = ['wpm', 'long_pauses_per_min', 'fillers_per_min', 'pause_variability', 
                   'speech_rate_variability', 'vocab_richness', 'type_token_ratio', 
                   'repetition_ratio', 'mean_utterance_length']
for metric in required_metrics:
    has_it = metric in response['normalized_metrics']
    checks.append((f'Metric: {metric}', has_it, f"Present: {has_it}"))

# 6. Criterion bands in valid range
for criterion, band in response['criterion_bands'].items():
    match = 5.0 <= band <= 9.0
    checks.append((f'{criterion} in [5,9]', match, f"Value: {band}"))

# Print results
print('\n' + '='*80)
print('RESPONSE VALIDATION AUDIT')
print('='*80 + '\n')

passed = 0
for check, result, detail in checks:
    status = '✅ PASS' if result else '❌ FAIL'
    print(f'{status} | {check:35} | {detail}')
    if result:
        passed += 1

print(f'\n{passed}/{len(checks)} checks passed ({100*passed/len(checks):.0f}%)\n')

# Additional info
if passed == len(checks):
    print('✅ All validation checks passed!')
else:
    print('❌ Some checks failed - review above')
