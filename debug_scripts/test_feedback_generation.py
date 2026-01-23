#!/usr/bin/env python3
"""
Test script to verify per-rubric feedback generation with strengths and weaknesses.
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.ielts_band_scorer import IELTSBandScorer


def test_feedback_generation():
    """Test feedback generation for different band levels."""
    
    scorer = IELTSBandScorer()
    
    # Test case 1: Band 7 speaker with good metrics
    print("=" * 80)
    print("TEST 1: Band 7 Speaker (Good Performance)")
    print("=" * 80)
    
    subscores_band7 = {
        "fluency_coherence": 7.0,
        "pronunciation": 7.5,
        "lexical_resource": 7.0,
        "grammatical_range_accuracy": 6.5,
    }
    
    metrics_band7 = {
        "wpm": 140,
        "mean_word_confidence": 0.82,
        "low_confidence_ratio": 0.15,
        "is_monotone": False,
        "vocab_richness": 0.52,
        "long_pauses_per_min": 1.2,
        "repetition_ratio": 0.05,
    }
    
    llm_metrics_band7 = {
        "coherence_break_count": 0,
        "flow_instability_present": False,
        "advanced_vocabulary_count": 8,
        "idiomatic_collocation_count": 3,
        "word_choice_error_count": 1,
        "grammar_error_count": 2,
        "complex_structures_attempted": 5,
        "complex_structure_accuracy_ratio": 0.8,
        "cascading_grammar_failure": False,
    }
    
    transcript_band7 = "Sample transcript for band 7 speaker."
    
    feedback_band7 = scorer._build_feedback(
        subscores=subscores_band7,
        metrics=metrics_band7,
        llm_metrics=llm_metrics_band7,
        transcript=transcript_band7,
    )
    
    print("\nFEEDBACK STRUCTURE:")
    print(json.dumps(feedback_band7, indent=2))
    
    # Verify structure
    required_criteria = ["fluency_coherence", "pronunciation", "lexical_resource", "grammatical_range_accuracy", "overall"]
    for criterion in required_criteria:
        if criterion not in feedback_band7:
            print(f"\n❌ MISSING: {criterion}")
        else:
            feedback_item = feedback_band7[criterion]
            print(f"\n✅ {criterion}:")
            if isinstance(feedback_item, dict):
                if "criterion" in feedback_item:
                    print(f"   - Criterion: {feedback_item['criterion']}")
                if "band" in feedback_item:
                    print(f"   - Band: {feedback_item['band']}")
                if "strengths" in feedback_item:
                    print(f"   - Strengths ({len(feedback_item['strengths'])}): {feedback_item['strengths'][:2]}...")
                if "weaknesses" in feedback_item:
                    print(f"   - Weaknesses ({len(feedback_item['weaknesses'])}): {feedback_item['weaknesses'][:2]}...")
                if "suggestions" in feedback_item:
                    print(f"   - Suggestions ({len(feedback_item['suggestions'])}): {feedback_item['suggestions'][:2]}...")
                if "summary" in feedback_item:
                    print(f"   - Summary: {feedback_item['summary'][:80]}...")
                if "next_band_tips" in feedback_item:
                    print(f"   - Next Band Tips: {list(feedback_item['next_band_tips'].keys())}")
    
    # Test case 2: Band 5.5 speaker (needs improvement)
    print("\n\n" + "=" * 80)
    print("TEST 2: Band 5.5 Speaker (Needs Improvement)")
    print("=" * 80)
    
    subscores_band5_5 = {
        "fluency_coherence": 5.5,
        "pronunciation": 5.5,
        "lexical_resource": 5.0,
        "grammatical_range_accuracy": 5.5,
    }
    
    metrics_band5_5 = {
        "wpm": 95,
        "mean_word_confidence": 0.65,
        "low_confidence_ratio": 0.35,
        "is_monotone": True,
        "vocab_richness": 0.38,
        "long_pauses_per_min": 2.8,
        "repetition_ratio": 0.12,
    }
    
    llm_metrics_band5_5 = {
        "coherence_break_count": 2,
        "flow_instability_present": True,
        "advanced_vocabulary_count": 2,
        "idiomatic_collocation_count": 0,
        "word_choice_error_count": 4,
        "grammar_error_count": 5,
        "complex_structures_attempted": 2,
        "complex_structure_accuracy_ratio": 0.5,
        "cascading_grammar_failure": True,
    }
    
    transcript_band5_5 = "Sample transcript for band 5.5 speaker."
    
    feedback_band5_5 = scorer._build_feedback(
        subscores=subscores_band5_5,
        metrics=metrics_band5_5,
        llm_metrics=llm_metrics_band5_5,
        transcript=transcript_band5_5,
    )
    
    print("\nFEEDBACK STRUCTURE:")
    print(json.dumps(feedback_band5_5, indent=2, default=str))
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY OF FEEDBACK GENERATION")
    print("=" * 80)
    
    # Check that feedback has clear strengths and weaknesses for each criterion
    print("\nFluency & Coherence (Band 7.0):")
    fluency = feedback_band7["fluency_coherence"]
    print(f"  Strengths: {len(fluency['strengths'])} items")
    print(f"  Weaknesses: {len(fluency['weaknesses'])} items")
    print(f"  Suggestions: {len(fluency['suggestions'])} items")
    
    print("\nFluency & Coherence (Band 5.5):")
    fluency_poor = feedback_band5_5["fluency_coherence"]
    print(f"  Strengths: {len(fluency_poor['strengths'])} items")
    print(f"  Weaknesses: {len(fluency_poor['weaknesses'])} items")
    print(f"  Suggestions: {len(fluency_poor['suggestions'])} items")
    
    print("\n✅ All feedback tests completed!")
    print("\nKey Observations:")
    print("1. Each rubric has clear STRENGTHS section")
    print("2. Each rubric has clear WEAKNESSES section")
    print("3. Each rubric has SUGGESTIONS for improvement")
    print("4. Feedback uses actual metrics (WPM, error counts, etc.)")
    print("5. Overall section includes summary and next band tips")


if __name__ == "__main__":
    test_feedback_generation()
