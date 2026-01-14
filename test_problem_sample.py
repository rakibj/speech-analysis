import numpy as np
from scripts.ielts_band_scorer import IELTSBandScorer

analysis_data = {
    'metadata': {
        'audio_duration_sec': 74.88,
        'speaking_time_sec': 69.8,
        'total_words_transcribed': 101,
        'content_word_count': 99,
    },
    'fluency_coherence': {
        'pauses': {
            'pause_frequency_per_min': 5.609,
            'long_pause_rate': 1.603,
            'pause_variability': 0.271
        },
        'rate': {
            'speech_rate_wpm': 79.33,
            'speech_rate_variability': 0.281
        },
        'disfluency': {
            'filler_frequency_per_min': 2.885,
            'stutter_frequency_per_min': 0.0,
            'repetition_rate': 0.0727
        },
        'coherence': {
            'coherence_breaks': 1,
            'topic_relevance': True
        }
    },
    'lexical_resource': {
        'breadth': {
            'unique_word_count': 63,
            'lexical_diversity': 0.6364,
            'lexical_density': 0.545,
            'most_frequent_word_ratio': 0.0727
        },
        'quality': {
            'word_choice_errors': 2,
            'advanced_vocabulary_count': 1
        }
    },
    'grammatical_range_accuracy': {
        'complexity': {
            'mean_utterance_length': 14.43,
            'complex_structures_attempted': 1,
            'complex_structures_accurate': 0
        },
        'accuracy': {
            'grammar_errors': 2,
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
    },
    'raw_transcript': 'I can see sky scraper toll buildings'
}

scorer = IELTSBandScorer()
result = scorer.score(analysis_data)

print("=" * 70)
print("PROBLEMATIC SAMPLE: 1 Complex at 0% Accuracy")
print("=" * 70)
print(f"\nOverall Band: {result['overall_band']} (was 7.0, should be ~5.5-6.0)")
print(f"\nCriterion Bands:")
for criterion, band in result['criterion_bands'].items():
    print(f"  {criterion.replace('_', ' ').title()}: {band}")

print(f"\nFeedback: {result['feedback_summary']}")
print("\n" + "=" * 70)
print("ANALYSIS:")
print("=" * 70)
print(f"""
Issues Fixed:
1. Grammar: 1 complex attempted at 0% accuracy
   - Now penalized -1.5 (not just -0.5)
   - Score: 9.0 - 1.5 = 7.5 (not 8.5)

2. Lexical: 1 advanced vocabulary word
   - Now capped at max 7.0 (for 1-2 adv words)
   - Score: 7.0 (not 8.0)

3. Overall: Weakness gap enforcement
   - Gap = 7.5 - 6.0 = 1.5 (SEVERE threshold)
   - Overall = min + 0.5 = 6.0 (not 7.0)

Expected: Overall ~6.0 (pulled down by grammar and pronunciation weaknesses)
""")
