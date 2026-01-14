#!/usr/bin/env python3
"""Test 3 complex attempts, 0% accuracy, 6 errors."""

from scripts.ielts_band_scorer import IELTSBandScorer

sample_data = {
    'metadata': {
        'audio_duration_sec': 74.88,
        'speaking_time_sec': 69.8,
        'total_words_transcribed': 101,
        'content_word_count': 99
    },
    'fluency_coherence': {
        'pauses': {
            'pause_frequency_per_min': 5.61,
            'long_pause_rate': 1.60,
            'pause_variability': 0.27
        },
        'rate': {
            'speech_rate_wpm': 79.33,
            'speech_rate_variability': 0.28
        },
        'disfluency': {
            'filler_frequency_per_min': 2.88,
            'stutter_frequency_per_min': 0.0,
            'repetition_rate': 0.073
        },
        'coherence': {
            'coherence_breaks': 1,
            'topic_relevance': True
        }
    },
    'lexical_resource': {
        'breadth': {
            'unique_word_count': 63,
            'lexical_diversity': 0.636,
            'lexical_density': 0.545,
            'most_frequent_word_ratio': 0.073
        },
        'quality': {
            'word_choice_errors': 5,
            'advanced_vocabulary_count': 0
        }
    },
    'grammatical_range_accuracy': {
        'complexity': {
            'mean_utterance_length': 14.43,
            'complex_structures_attempted': 3,
            'complex_structures_accurate': 0  # 0% accuracy
        },
        'accuracy': {
            'grammar_errors': 6,
            'meaning_blocking_error_ratio': 0.0
        }
    },
    'pronunciation': {
        'intelligibility': {
            'mean_word_confidence': 0.819,
            'low_confidence_ratio': 0.267
        },
        'prosody': {
            'monotone_detected': False
        }
    }
}

scorer = IELTSBandScorer()
result = scorer.score(sample_data)

print(f"\n{'='*60}")
print(f"3 ATTEMPTS @ 0% WITH 6 ERRORS TEST")
print(f"{'='*60}")
print(f"\nSample: 3 complex attempts, 0 accurate (0%), 6 errors")
print(f"\nResults:")
print(f"  Fluency & Coherence:       {result['criterion_bands']['fluency_coherence']:.1f}")
print(f"  Lexical Resource:          {result['criterion_bands']['lexical_resource']:.1f}")
print(f"  Grammatical Range:         {result['criterion_bands']['grammatical_range_accuracy']:.1f}")
print(f"  Pronunciation:             {result['criterion_bands']['pronunciation']:.1f}")
print(f"\n  OVERALL BAND:              {result['overall_band']:.1f}")
print(f"\nExpected:")
print(f"  Grammar: 5.0 (9.0 - 3.0 for floor accuracy - 0.5 for errors = 5.5 → 5.0)")
print(f"  Lexical: 6.5 (no advanced vocab cap)")
print(f"  Overall: 5.0 (weak grammar balanced by moderate other criteria)")
print(f"\nFeedback: {result['feedback_summary']}")
print(f"{'='*60}\n")
