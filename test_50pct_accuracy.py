#!/usr/bin/env python3
"""Test 50% accuracy on 2 complex attempts with 1 advanced word."""

from scripts.ielts_band_scorer import IELTSBandScorer

# Sample: 2 complex attempts, 1 accurate (50% accuracy), 1 advanced word
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
            'word_choice_errors': 2,
            'advanced_vocabulary_count': 1
        }
    },
    'grammatical_range_accuracy': {
        'complexity': {
            'mean_utterance_length': 14.43,
            'complex_structures_attempted': 2,
            'complex_structures_accurate': 1  # 50% accuracy
        },
        'accuracy': {
            'grammar_errors': 1,
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
print(f"50% ACCURACY TEST")
print(f"{'='*60}")
print(f"\nSample: 2 complex attempts, 1 accurate (50%), 1 advanced word")
print(f"\nResults:")
print(f"  Fluency & Coherence:       {result['criterion_bands']['fluency_coherence']:.1f}")
print(f"  Lexical Resource:          {result['criterion_bands']['lexical_resource']:.1f}")
print(f"  Grammatical Range:         {result['criterion_bands']['grammatical_range_accuracy']:.1f}")
print(f"  Pronunciation:             {result['criterion_bands']['pronunciation']:.1f}")
print(f"\n  OVERALL BAND:              {result['overall_band']:.1f}")
print(f"\nExpected:")
print(f"  Grammar: Should be 7.0-7.5 max (50% accuracy + 2 attempts = -1.0 for low attempts + -0.5 for 50% = 9.0-2.5 = 6.5→7.0)")
print(f"  Lexical: Should be 7.0 max (only 1 advanced word = capped at 7.0)")
print(f"  Overall: Should be 5.5-6.0 (weak fluency pulls down)")
print(f"\nFeedback: {result['feedback_summary']}")
print(f"{'='*60}\n")
