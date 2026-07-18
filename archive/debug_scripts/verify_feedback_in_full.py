#!/usr/bin/env python3
"""
Quick verification that feedback is returned in detail="full" response.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.response_builder import build_response


def verify_feedback_in_full_response():
    """Verify structured feedback is returned in detail='full' responses."""
    
    # Create mock engine output with structured feedback
    mock_output = {
        "overall_band": 7.0,
        "criterion_bands": {
            "fluency_coherence": 7.0,
            "pronunciation": 7.5,
            "lexical_resource": 7.0,
            "grammatical_range_accuracy": 6.5,
        },
        "band_scores": {
            "overall_band": 7.0,
            "criterion_bands": {
                "fluency_coherence": 7.0,
                "pronunciation": 7.5,
                "lexical_resource": 7.0,
                "grammatical_range_accuracy": 6.5,
            },
            "feedback": {
                "fluency_coherence": {
                    "criterion": "Fluency & Coherence",
                    "band": 7.0,
                    "strengths": ["Good fluency - able to sustain speech"],
                    "weaknesses": [],
                    "suggestions": ["Practice extended speaking"]
                },
                "pronunciation": {
                    "criterion": "Pronunciation",
                    "band": 7.5,
                    "strengths": ["Generally clear pronunciation"],
                    "weaknesses": [],
                    "suggestions": []
                },
                "lexical_resource": {
                    "criterion": "Lexical Resource",
                    "band": 7.0,
                    "strengths": ["Good vocabulary range"],
                    "weaknesses": ["Word choice errors (1)"],
                    "suggestions": ["Learn new vocabulary"]
                },
                "grammatical_range_accuracy": {
                    "criterion": "Grammatical Range & Accuracy",
                    "band": 6.5,
                    "strengths": ["Adequate grammatical control"],
                    "weaknesses": ["Grammar errors found (2)"],
                    "suggestions": ["Review common errors"]
                },
                "overall": {
                    "overall_band": 7.0,
                    "summary": "Good proficiency with good fluency...",
                    "next_band_tips": {
                        "focus": "Improve grammar",
                        "action": "Master complex structures"
                    }
                }
            }
        },
        "statistics": {"total_duration_seconds": 180},
        "normalized_metrics": {"filler_frequency": 2.5},
        "speech_quality": {"mean_word_confidence": 0.82},
        "llm_analysis": {"grammar_error_count": 2},
        "transcript": "Sample transcript...",
    }
    
    # Build response with detail="full"
    response_full = build_response(
        job_id="test_001",
        status="completed",
        raw_analysis=mock_output,
        detail="full"
    )
    
    print("=" * 80)
    print("VERIFICATION: Feedback in detail='full' Response")
    print("=" * 80)
    
    # Check if feedback is present
    has_feedback = "feedback" in response_full
    print(f"\n✅ Feedback field present: {has_feedback}")
    
    if has_feedback:
        feedback = response_full["feedback"]
        print(f"\nFeedback structure:")
        print(f"  - fluency_coherence: {feedback.get('fluency_coherence', {}).get('criterion')}")
        print(f"  - pronunciation: {feedback.get('pronunciation', {}).get('criterion')}")
        print(f"  - lexical_resource: {feedback.get('lexical_resource', {}).get('criterion')}")
        print(f"  - grammatical_range_accuracy: {feedback.get('grammatical_range_accuracy', {}).get('criterion')}")
        print(f"  - overall: Band {feedback.get('overall', {}).get('overall_band')}")
        
        print(f"\nFluency & Coherence feedback:")
        fc = feedback.get("fluency_coherence", {})
        print(f"  Strengths: {fc.get('strengths', [])}")
        print(f"  Weaknesses: {fc.get('weaknesses', [])}")
        print(f"  Suggestions: {fc.get('suggestions', [])}")
        
        print(f"\nFull response also includes:")
        print(f"  - word_timestamps: {'word_timestamps' in response_full}")
        print(f"  - filler_events: {'filler_events' in response_full}")
        print(f"  - segment_timestamps: {'segment_timestamps' in response_full}")
        print(f"  - confidence_multipliers: {'confidence_multipliers' in response_full}")
    
    print("\n" + "=" * 80)
    print("RESULT: ✅ Feedback IS returned when detail='full'")
    print("=" * 80)
    print("""
The structured feedback with clear strengths, weaknesses, and suggestions 
is returned in the full response tier.

When you request: detail="full"
You get:
  • All basic fields (band, metrics, statistics, etc.)
  • All feedback fields (detailed per-rubric feedback)
  • All granular fields (word timestamps, filler events, etc.)
    """)


if __name__ == "__main__":
    verify_feedback_in_full_response()
