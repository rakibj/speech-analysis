#!/usr/bin/env python3
"""Debug: test 3 attempts 0% with actual details from notebook."""

import sys
import importlib

# Force fresh import
if 'scripts.ielts_band_scorer' in sys.modules:
    del sys.modules['scripts.ielts_band_scorer']

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
            'pause_frequency_per_min': 5.608974358974359,
            'long_pause_rate': 1.6025641025641026,
            'pause_variability': 0.27122297978214244
        },
        'rate': {
            'speech_rate_wpm': 79.32692307692308,
            'speech_rate_variability': 0.2807944380799325
        },
        'disfluency': {
            'filler_frequency_per_min': 2.884615384615385,
            'stutter_frequency_per_min': 0.0,
            'repetition_rate': 0.07272727272727272
        },
        'coherence': {
            'coherence_breaks': 1,
            'topic_relevance': True
        }
    },
    'lexical_resource': {
        'breadth': {
            'unique_word_count': 63,
            'lexical_diversity': 0.6363636363636364,
            'lexical_density': 0.545,
            'most_frequent_word_ratio': 0.07272727272727272
        },
        'quality': {
            'word_choice_errors': 5,
            'advanced_vocabulary_count': 0
        }
    },
    'grammatical_range_accuracy': {
        'complexity': {
            'mean_utterance_length': 14.428571428571429,
            'complex_structures_attempted': 3,
            'complex_structures_accurate': 0
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

print("\nScoring breakdown:")
print(f"  Fluency: {result['criterion_bands']['fluency_coherence']}")
print(f"  Lexical: {result['criterion_bands']['lexical_resource']}")
print(f"  Grammar: {result['criterion_bands']['grammatical_range_accuracy']}")
print(f"  Pronunciation: {result['criterion_bands']['pronunciation']}")
print(f"  Overall: {result['overall_band']}")
