#!/usr/bin/env python
"""Test response mapping to identify any remaining issues."""
import json
from src.services.response_builder import build_response, transform_engine_output


# Simulate what your engine ACTUALLY returns (from engine.py final_report)
SAMPLE_ENGINE_OUTPUT = {
    'metadata': {'filename': 'test.wav', 'duration': 30},
    'transcript': 'The identity from flick and quite honestly, what did we see from Madrid?',
    'fluency_analysis': {},
    'pronunciation': {'intelligibility': {}, 'prosody': {}},
    'band_scores': {
        'overall_band': 7.5,
        'criterion_bands': {'fluency': 7.5, 'accuracy': 7.0},
        'confidence': {'category': 'high', 'score': 0.95},
        'descriptors': [],
        'feedback': {}
    },
    'timestamped_words': [
        {'word': 'The', 'start': 0.0, 'end': 0.5, 'confidence': 0.99},
        {'word': 'identity', 'start': 0.5, 'end': 1.2, 'confidence': 0.98}
    ],
    'timestamped_fillers': [
        {'type': 'filler', 'text': 'um', 'start': 2.0, 'end': 2.3}
    ],
    'timestamped_feedback': None,
    'metrics_for_scoring': {},
    'statistics': {
        'total_words_transcribed': 120,
        'content_words': 119,
        'filler_words_detected': 1,
        'filler_percentage': 0.83,
        'speech_rate': 120,
        'articulation_rate': 115,
        'pause_frequency': 0.05
    },
    'speech_quality': {
        'mean_word_confidence': 0.96,
        'low_confidence_ratio': 0.02,
        'is_monotone': False
    },
    'llm_analysis': {
        'topic_relevance': True,
        'listener_effort_high': False,
        'flow_instability_present': False,
        'overall_clarity_score': 3,
        'coherence_break_count': 0,
        'word_choice_error_count': 0,
        'advanced_vocabulary_count': 2,
        'grammar_error_count': 0,
    }
}


def test_transform():
    """Test the transformation function."""
    print("=" * 70)
    print("TEST 1: Data Transformation")
    print("=" * 70)
    
    transformed = transform_engine_output(SAMPLE_ENGINE_OUTPUT)
    
    print("\n[CHECK] Fields that were NULL before transformation:")
    null_fields = ['grammar_errors', 'word_choice_errors', 'examiner_descriptors', 
                   'fluency_notes', 'normalized_metrics']
    
    for field in null_fields:
        original = SAMPLE_ENGINE_OUTPUT.get(field)
        transformed_val = transformed.get(field)
        status = "[OK] GENERATED" if transformed_val is not None else "[ERROR] STILL NULL"
        print(f"  {field}: {status}")
        if transformed_val is not None:
            print(f"    -> {transformed_val}")
    
    return transformed


def test_default_response(transformed):
    """Test default tier (minimal)."""
    print("\n" + "=" * 70)
    print("TEST 2: Default Response Tier (Minimal)")
    print("=" * 70)
    
    response = build_response(
        job_id="test-job-1",
        status="completed",
        raw_analysis=transformed,
        detail=None  # Default tier
    )
    
    expected_keys = {'job_id', 'status', 'engine_version', 'scoring_config', 
                     'overall_band', 'criterion_bands', 'confidence'}
    
    actual_keys = set(response.keys())
    
    print(f"\nExpected keys: {expected_keys}")
    print(f"Actual keys:   {actual_keys}")
    
    if expected_keys == actual_keys:
        print("[OK] Default tier has correct fields")
    else:
        print("[ERROR] Field mismatch!")
        print(f"  Missing: {expected_keys - actual_keys}")
        print(f"  Extra: {actual_keys - expected_keys}")
    
    print(f"\nResponse size: {len(json.dumps(response))} bytes")
    return response


def test_feedback_response(transformed):
    """Test feedback tier."""
    print("\n" + "=" * 70)
    print("TEST 3: Feedback Response Tier")
    print("=" * 70)
    
    response = build_response(
        job_id="test-job-1",
        status="completed",
        raw_analysis=transformed,
        detail="feedback"
    )
    
    feedback_fields = {'transcript', 'grammar_errors', 'word_choice_errors',
                       'examiner_descriptors', 'fluency_notes'}
    
    print("\n[CHECK] Feedback-tier specific fields:")
    for field in feedback_fields:
        if field in response:
            value = response[field]
            is_null = value is None
            status = "[OK] PRESENT" if not is_null else "[!] NULL"
            print(f"  {field}: {status}")
            if not is_null and len(str(value)) < 60:
                print(f"    -> {value}")
        else:
            print(f"  {field}: [ERROR] MISSING")
    
    print(f"\nResponse size: {len(json.dumps(response))} bytes")
    return response


def test_full_response(transformed):
    """Test full tier."""
    print("\n" + "=" * 70)
    print("TEST 4: Full Response Tier")
    print("=" * 70)
    
    response = build_response(
        job_id="test-job-1",
        status="completed",
        raw_analysis=transformed,
        detail="full"
    )
    
    full_fields = {'word_timestamps', 'content_words', 'segment_timestamps',
                   'filler_events', 'statistics', 'normalized_metrics',
                   'opinions', 'benchmarking', 'llm_analysis',
                   'confidence_multipliers', 'timestamped_feedback', 'speech_quality'}
    
    print("\n[CHECK] Full-tier specific fields:")
    for field in full_fields:
        if field in response:
            value = response[field]
            is_null = value is None
            status = "[OK] PRESENT" if not is_null else "[!] NULL"
            print(f"  {field}: {status}")
            if not is_null and field in ['statistics', 'normalized_metrics', 'llm_analysis', 'speech_quality']:
                print(f"    -> {type(value).__name__}")
        else:
            print(f"  {field}: [ERROR] MISSING")
    
    print(f"\nResponse size: {len(json.dumps(response))} bytes")
    return response


def test_completeness():
    """Check that no field is unexpectedly NULL in feedback/full tiers."""
    print("\n" + "=" * 70)
    print("TEST 5: Completeness Check")
    print("=" * 70)
    
    transformed = transform_engine_output(SAMPLE_ENGINE_OUTPUT)
    response = build_response(
        job_id="test-job-1",
        status="completed",
        raw_analysis=transformed,
        detail="full"
    )
    
    null_count = 0
    for key, value in response.items():
        if value is None and key not in ['overall_band', 'criterion_bands', 'confidence']:
            # These are expected to be None based on sample data
            null_count += 1
            print(f"  [!] {key} is NULL (may be expected)")
        elif value is None:
            print(f"  [OK] {key} is NULL (expected for scoring fields)")
    
    if null_count == 0:
        print("\n[OK] No unexpected NULL values!")
    else:
        print(f"\n[!] Found {null_count} potentially problematic NULL values")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RESPONSE MAPPING TEST SUITE")
    print("=" * 70)
    
    # Run tests
    transformed = test_transform()
    default_resp = test_default_response(transformed)
    feedback_resp = test_feedback_response(transformed)
    full_resp = test_full_response(transformed)
    test_completeness()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\n[OK] If all fields show [OK], mapping is working correctly!")
