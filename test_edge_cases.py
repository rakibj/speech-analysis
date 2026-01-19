#!/usr/bin/env python3
"""
Test runner for edge-case and rigging-attempt datasets.

Tests the system's ability to:
1. Detect and penalize random idiom insertion
2. Detect and penalize off-topic rambling
3. Detect and penalize circular reasoning
4. Accept legitimate sophisticated speech
5. Score legitimate good speech appropriately

Run: uv run python test_edge_cases.py
"""

import json
import asyncio
from pathlib import Path
from src.core.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.core.ielts_band_scorer import IELTSBandScorer

# Test dataset definitions
TEST_CASES = {
    "test_random_idioms": {
        "description": "Random idiom insertion - should be penalized",
        "expected_max_overall": 6.5,
        "expected_max_lexical": 7.0,
        "expected_topic_relevant": True,
        "expected_flow_stable": False,
        "fail_if_overall_above": 7.0,  # Should NOT reach 7.0+
        "fail_if_lexical_above": 7.5,  # Should NOT reach 7.5+
    },
    "test_off_topic_rambling": {
        "description": "Off-topic rambling - hard cap at 6.5",
        "expected_max_overall": 6.5,
        "expected_max_lexical": 6.5,
        "expected_topic_relevant": False,
        "fail_if_overall_above": 6.5,
        "note": "Topic relevance should trigger hard cap",
    },
    "test_circular_reasoning": {
        "description": "Circular reasoning with chain association - penalize for low coherence",
        "expected_max_overall": 6.0,
        "expected_max_lexical": 5.5,
        "expected_topic_relevant": True,
        "expected_flow_stable": False,
        "fail_if_overall_above": 6.0,
        "note": "Flow unstable and high repetition should penalize",
    },
    "test_sophisticated_speech": {
        "description": "Legitimate sophisticated speech - should score HIGH",
        "expected_min_overall": 8.0,
        "expected_min_lexical": 8.0,
        "expected_topic_relevant": True,
        "expected_flow_stable": True,
        "fail_if_overall_below": 8.0,  # Should reach 8.0+
        "fail_if_lexical_below": 8.0,  # Should reach 8.0+
        "note": "Sophisticated vocab used contextually should NOT be penalized",
    },
    "test_good_speech_control": {
        "description": "Legitimate good speech - control case",
        "expected_min_overall": 6.5,
        "expected_min_lexical": 6.0,
        "expected_topic_relevant": True,
        "expected_flow_stable": True,
        "fail_if_overall_below": 6.5,
        "note": "Solid B-level performance",
    },
}


async def run_test(test_name: str, test_config: dict):
    """Run a single edge-case test."""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"Description: {test_config['description']}")
    print(f"{'='*70}")

    # Load test data
    test_file = Path(f"outputs/audio_analysis/{test_name}.json")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return None

    with open(test_file) as f:
        test_data = json.load(f)

    transcript = test_data["raw_analysis"]["raw_transcript"]
    metrics = test_data["raw_analysis"]
    
    # Run analysis
    try:
        # Get LLM annotations for the transcript
        llm_annotations = await extract_llm_annotations(transcript)
        llm_metrics = aggregate_llm_metrics(llm_annotations)
        
        # Score using IELTS band scorer
        scorer = IELTSBandScorer()
        result = scorer.score_overall_with_feedback(metrics, transcript, llm_metrics)
        
        band_scores = result["criterion_bands"]
        overall = result["overall_band"]
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Extract LLM insights
    topic_relevant = llm_metrics.get("topic_relevance", True)
    flow_stable = not llm_metrics.get("flow_instability_present", False)
    listener_effort_high = llm_metrics.get("listener_effort_high", False)
    clarity = llm_metrics.get("overall_clarity_score", 3)
    register_mismatch = llm_metrics.get("register_mismatch_count", 0)
    adv_vocab = llm_metrics.get("advanced_vocabulary_count", 0)
    idioms = llm_metrics.get("idiomatic_collocation_count", 0)

    # Display results
    print(f"\n[SCORES]")
    print(f"  Overall:            {overall}")
    print(f"  Fluency/Coherence:  {band_scores['fluency_coherence']}")
    print(f"  Pronunciation:      {band_scores['pronunciation']}")
    print(f"  Lexical Resource:   {band_scores['lexical_resource']}")
    print(f"  Grammar/Accuracy:   {band_scores['grammatical_range_accuracy']}")

    # Test assertions
    passed = True
    failures = []

    # Check max/min thresholds
    if "fail_if_overall_above" in test_config:
        if overall > test_config["fail_if_overall_above"]:
            failures.append(
                f"Overall {overall} exceeds max {test_config['fail_if_overall_above']}"
            )
            passed = False

    if "fail_if_overall_below" in test_config:
        if overall < test_config["fail_if_overall_below"]:
            failures.append(
                f"Overall {overall} below min {test_config['fail_if_overall_below']}"
            )
            passed = False

    if "fail_if_lexical_above" in test_config:
        if band_scores["lexical_resource"] > test_config["fail_if_lexical_above"]:
            failures.append(
                f"Lexical {band_scores['lexical_resource']} exceeds max {test_config['fail_if_lexical_above']}"
            )
            passed = False

    if "fail_if_lexical_below" in test_config:
        if band_scores["lexical_resource"] < test_config["fail_if_lexical_below"]:
            failures.append(
                f"Lexical {band_scores['lexical_resource']} below min {test_config['fail_if_lexical_below']}"
            )
            passed = False

    # Check LLM expectation flags
    if "expected_topic_relevant" in test_config:
        if topic_relevant != test_config["expected_topic_relevant"]:
            failures.append(
                f"Topic relevance {topic_relevant}, expected {test_config['expected_topic_relevant']}"
            )

    if "expected_flow_stable" in test_config:
        if flow_stable != test_config["expected_flow_stable"]:
            failures.append(
                f"Flow stable {flow_stable}, expected {test_config['expected_flow_stable']}"
            )

    # Report
    print(f"\n{'[PASS]' if passed else '[FAIL]'}")
    if failures:
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")
    if "note" in test_config:
        print(f"Note: {test_config['note']}")

    return passed


async def main():
    """Run all edge-case tests."""
    print("[TEST] IELTS SPEECH ANALYZER - EDGE CASE TEST SUITE")
    print("Testing system's ability to detect gaming/rigging attempts\n")

    results = {}
    for test_name, test_config in TEST_CASES.items():
        result = await run_test(test_name, test_config)
        results[test_name] = result

    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    passed_count = sum(1 for v in results.values() if v is True)
    total_count = len(results)
    
    print(f"\nTests Passed: {passed_count}/{total_count}")
    
    for test_name, result in results.items():
        status = "[PASS]" if result is True else "[FAIL]" if result is False else "[SKIP]"
        print(f"  {status}  {test_name}")

    if passed_count == total_count:
        print("\n[SUCCESS] All tests passed! System successfully detects gaming attempts.")
    else:
        print(f"\n[WARNING] {total_count - passed_count} tests failed. System needs adjustment.")


if __name__ == "__main__":
    asyncio.run(main())
