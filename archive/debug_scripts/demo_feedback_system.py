#!/usr/bin/env python3
"""
Comprehensive demonstration of the per-rubric feedback system.
Shows actual feedback for Band 5.5, Band 7.0, and Band 8.5 speakers.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.ielts_band_scorer import IELTSBandScorer


def demo_feedback_system():
    """Demonstrate the per-rubric feedback system with realistic examples."""
    
    scorer = IELTSBandScorer()
    
    print("=" * 100)
    print("PER-RUBRIC FEEDBACK SYSTEM DEMONSTRATION")
    print("=" * 100)
    
    # ============================================================================
    # SCENARIO 1: BAND 5.5 - PASS LEVEL (LEARNER NEEDS SIGNIFICANT IMPROVEMENT)
    # ============================================================================
    
    print("\n\n" + "▓" * 100)
    print("SCENARIO 1: BAND 5.5 SPEAKER - PASS LEVEL")
    print("▓" * 100)
    print("\nProfile: Learner who can handle basic conversation but needs improvement in multiple areas\n")
    
    subscores_5_5 = {
        "fluency_coherence": 5.5,
        "pronunciation": 5.0,
        "lexical_resource": 5.5,
        "grammatical_range_accuracy": 5.5,
    }
    
    metrics_5_5 = {
        "wpm": 95,
        "mean_word_confidence": 0.62,
        "low_confidence_ratio": 0.40,
        "is_monotone": True,
        "vocab_richness": 0.35,
        "long_pauses_per_min": 3.2,
        "repetition_ratio": 0.15,
    }
    
    llm_metrics_5_5 = {
        "coherence_break_count": 3,
        "flow_instability_present": True,
        "advanced_vocabulary_count": 1,
        "idiomatic_collocation_count": 0,
        "word_choice_error_count": 6,
        "grammar_error_count": 7,
        "complex_structures_attempted": 1,
        "complex_structure_accuracy_ratio": 0.2,
        "cascading_grammar_failure": True,
    }
    
    feedback_5_5 = scorer._build_feedback(
        subscores=subscores_5_5,
        metrics=metrics_5_5,
        llm_metrics=llm_metrics_5_5,
        transcript="Sample 5.5 speaker transcript"
    )
    
    print("FLUENCY & COHERENCE - Band 5.5")
    print("-" * 100)
    fc = feedback_5_5["fluency_coherence"]
    print(f"Criterion: {fc['criterion']}")
    print(f"Band: {fc['band']}")
    print(f"\nWhat's Working ({len(fc['strengths'])} items):")
    for item in fc['strengths']:
        print(f"  ✓ {item}")
    if not fc['strengths']:
        print("  (No clear strengths identified)")
    print(f"\nAreas for Improvement ({len(fc['weaknesses'])} items):")
    for item in fc['weaknesses']:
        print(f"  ✗ {item}")
    print(f"\nHow to Improve ({len(fc['suggestions'])} items):")
    for i, item in enumerate(fc['suggestions'][:3], 1):
        print(f"  {i}. {item}")
    
    print("\nPRONUNCIATION - Band 5.0")
    print("-" * 100)
    pr = feedback_5_5["pronunciation"]
    print(f"Criterion: {pr['criterion']}")
    print(f"Band: {pr['band']}")
    print(f"\nWhat's Working ({len(pr['strengths'])} items):")
    for item in pr['strengths']:
        print(f"  ✓ {item}")
    if not pr['strengths']:
        print("  (No clear strengths identified)")
    print(f"\nAreas for Improvement ({len(pr['weaknesses'])} items):")
    for item in pr['weaknesses'][:4]:
        print(f"  ✗ {item}")
    print(f"\nHow to Improve ({len(pr['suggestions'])} items):")
    for i, item in enumerate(pr['suggestions'][:3], 1):
        print(f"  {i}. {item}")
    
    print("\n" + "=" * 100)
    print("OVERALL ASSESSMENT")
    print("=" * 100)
    overall = feedback_5_5["overall"]
    print(f"\nBand: {overall['overall_band']}")
    print(f"\nSummary:\n{overall['summary']}")
    print(f"\nNext Band Tips:")
    print(f"  Focus: {overall['next_band_tips']['focus']}")
    print(f"  Action: {overall['next_band_tips']['action']}")
    
    # ============================================================================
    # SCENARIO 2: BAND 7.0 - GOOD LEVEL (SOLID SPEAKER)
    # ============================================================================
    
    print("\n\n" + "▓" * 100)
    print("SCENARIO 2: BAND 7.0 SPEAKER - GOOD LEVEL")
    print("▓" * 100)
    print("\nProfile: Solid speaker with good fluency and vocabulary, minor areas for refinement\n")
    
    subscores_7_0 = {
        "fluency_coherence": 7.0,
        "pronunciation": 7.5,
        "lexical_resource": 7.0,
        "grammatical_range_accuracy": 6.5,
    }
    
    metrics_7_0 = {
        "wpm": 140,
        "mean_word_confidence": 0.82,
        "low_confidence_ratio": 0.15,
        "is_monotone": False,
        "vocab_richness": 0.52,
        "long_pauses_per_min": 1.2,
        "repetition_ratio": 0.05,
    }
    
    llm_metrics_7_0 = {
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
    
    feedback_7_0 = scorer._build_feedback(
        subscores=subscores_7_0,
        metrics=metrics_7_0,
        llm_metrics=llm_metrics_7_0,
        transcript="Sample 7.0 speaker transcript"
    )
    
    print("LEXICAL RESOURCE - Band 7.0")
    print("-" * 100)
    lr = feedback_7_0["lexical_resource"]
    print(f"Criterion: {lr['criterion']}")
    print(f"Band: {lr['band']}")
    print(f"\nWhat's Working ({len(lr['strengths'])} items):")
    for item in lr['strengths']:
        print(f"  ✓ {item}")
    print(f"\nAreas for Improvement ({len(lr['weaknesses'])} items):")
    for item in lr['weaknesses']:
        print(f"  ✗ {item}")
    print(f"\nHow to Improve ({len(lr['suggestions'])} items):")
    for i, item in enumerate(lr['suggestions'][:3], 1):
        print(f"  {i}. {item}")
    
    print("\nGRAMMATICAL RANGE & ACCURACY - Band 6.5")
    print("-" * 100)
    gr = feedback_7_0["grammatical_range_accuracy"]
    print(f"Criterion: {gr['criterion']}")
    print(f"Band: {gr['band']}")
    print(f"\nWhat's Working ({len(gr['strengths'])} items):")
    for item in gr['strengths']:
        print(f"  ✓ {item}")
    print(f"\nAreas for Improvement ({len(gr['weaknesses'])} items):")
    for item in gr['weaknesses']:
        print(f"  ✗ {item}")
    print(f"\nHow to Improve ({len(gr['suggestions'])} items):")
    for i, item in enumerate(gr['suggestions'][:3], 1):
        print(f"  {i}. {item}")
    
    print("\n" + "=" * 100)
    print("OVERALL ASSESSMENT")
    print("=" * 100)
    overall = feedback_7_0["overall"]
    print(f"\nBand: {overall['overall_band']}")
    print(f"\nSummary:\n{overall['summary']}")
    print(f"\nNext Band Tips:")
    print(f"  Focus: {overall['next_band_tips']['focus']}")
    print(f"  Action: {overall['next_band_tips']['action']}")
    
    # ============================================================================
    # SCENARIO 3: BAND 8.5 - EXCELLENT LEVEL (NEAR-NATIVE SPEAKER)
    # ============================================================================
    
    print("\n\n" + "▓" * 100)
    print("SCENARIO 3: BAND 8.5 SPEAKER - EXCELLENT LEVEL")
    print("▓" * 100)
    print("\nProfile: Excellent speaker with near-native fluency, vocabulary, and grammar\n")
    
    subscores_8_5 = {
        "fluency_coherence": 8.5,
        "pronunciation": 8.0,
        "lexical_resource": 8.5,
        "grammatical_range_accuracy": 8.5,
    }
    
    metrics_8_5 = {
        "wpm": 165,
        "mean_word_confidence": 0.92,
        "low_confidence_ratio": 0.05,
        "is_monotone": False,
        "vocab_richness": 0.68,
        "long_pauses_per_min": 0.3,
        "repetition_ratio": 0.02,
    }
    
    llm_metrics_8_5 = {
        "coherence_break_count": 0,
        "flow_instability_present": False,
        "advanced_vocabulary_count": 18,
        "idiomatic_collocation_count": 7,
        "word_choice_error_count": 0,
        "grammar_error_count": 0,
        "complex_structures_attempted": 12,
        "complex_structure_accuracy_ratio": 1.0,
        "cascading_grammar_failure": False,
    }
    
    feedback_8_5 = scorer._build_feedback(
        subscores=subscores_8_5,
        metrics=metrics_8_5,
        llm_metrics=llm_metrics_8_5,
        transcript="Sample 8.5 speaker transcript"
    )
    
    print("FLUENCY & COHERENCE - Band 8.5")
    print("-" * 100)
    fc = feedback_8_5["fluency_coherence"]
    print(f"Criterion: {fc['criterion']}")
    print(f"Band: {fc['band']}")
    print(f"\nWhat's Working ({len(fc['strengths'])} items):")
    for item in fc['strengths']:
        print(f"  ✓ {item}")
    print(f"\nAreas for Improvement ({len(fc['weaknesses'])} items):")
    if fc['weaknesses']:
        for item in fc['weaknesses']:
            print(f"  ✗ {item}")
    else:
        print("  (No areas identified - excellent performance)")
    
    print("\nLEXICAL RESOURCE - Band 8.5")
    print("-" * 100)
    lr = feedback_8_5["lexical_resource"]
    print(f"Criterion: {lr['criterion']}")
    print(f"Band: {lr['band']}")
    print(f"\nWhat's Working ({len(lr['strengths'])} items):")
    for item in lr['strengths']:
        print(f"  ✓ {item}")
    print(f"\nAreas for Improvement ({len(lr['weaknesses'])} items):")
    if lr['weaknesses']:
        for item in lr['weaknesses']:
            print(f"  ✗ {item}")
    else:
        print("  (No areas identified - excellent performance)")
    
    print("\n" + "=" * 100)
    print("OVERALL ASSESSMENT")
    print("=" * 100)
    overall = feedback_8_5["overall"]
    print(f"\nBand: {overall['overall_band']}")
    print(f"\nSummary:\n{overall['summary']}")
    print(f"\nNext Band Tips:")
    tips = overall['next_band_tips']
    if tips:
        print(f"  Focus: {tips.get('focus', 'Already at highest level')}")
        print(f"  Action: {tips.get('action', 'Continue refining skills')}")
    else:
        print("  (Already at highest level - continue maintaining excellence)")
    
    # ============================================================================
    # SUMMARY & KEY INSIGHTS
    # ============================================================================
    
    print("\n\n" + "=" * 100)
    print("SYSTEM SUMMARY")
    print("=" * 100)
    
    print("\n✅ FEEDBACK GENERATION FEATURES:")
    print("""
1. CLEAR STRUCTURE
   - Strengths: What's working well (motivation)
   - Weaknesses: What needs improvement (clarity)
   - Suggestions: How to improve (actionable advice)

2. DATA-DRIVEN
   - Uses actual metrics (WPM, word confidence, error counts)
   - Specific numbers and observations
   - Evidence-based feedback

3. BAND-AWARE
   - Different feedback for each band level
   - Tone matches performance level
   - Expectations align with IELTS criteria

4. ACTIONABLE
   - Clear next steps for improvement
   - Specific focus for next band level
   - Prioritized by weakest criterion

5. COMPLETE COVERAGE
   - All 4 criteria covered separately
   - Overall assessment included
   - Next band roadmap provided
    """)
    
    print("✅ KEY METRICS USED:")
    print("""
   Fluency:     WPM, pause frequency, coherence breaks, flow stability
   Pronunciation: Word confidence, low-confidence ratio, monotone, clarity
   Lexicon:     Advanced vocabulary count, idioms, word choice errors, richness
   Grammar:     Error count, complex structure accuracy, cascading failures, range
    """)
    
    print("✅ RESPONSE TIERS:")
    print("""
   Default:     No feedback (privacy)
   Feedback:    Detailed per-criterion feedback
   Full:        Complete analysis + feedback
    """)
    
    print("\n" + "=" * 100)
    print("DEMONSTRATION COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    demo_feedback_system()
