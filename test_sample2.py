import numpy as np
from scripts.ielts_band_scorer import IELTSBandScorer

# Second sample - the one showing 8.0 overall (3 complex, 2 accurate)
analysis_data = {
    'metadata': {
        'audio_duration_sec': 74.98,
        'speaking_time_sec': 74.32,
        'total_words_transcribed': 121,
        'content_word_count': 117,
        'analysis_timestamp': '2026-01-14T17:24:25.656414Z'
    },
    'fluency_coherence': {
        'pauses': {
            'pause_frequency_per_min': 0.8002133902373966,
            'long_pause_rate': 0.0,
            'pause_variability': 0.0
        },
        'rate': {
            'speech_rate_wpm': 93.6249666577754,
            'speech_rate_variability': 0.3293183958234518
        },
        'disfluency': {
            'filler_frequency_per_min': 3.5209389170445453,
            'stutter_frequency_per_min': 0.8002133902373966,
            'repetition_rate': 0.0392156862745098
        },
        'coherence': {
            'coherence_breaks': 1,  # BETTER (was 3)
            'topic_relevance': True
        }
    },
    'lexical_resource': {
        'breadth': {
            'unique_word_count': 66,
            'lexical_diversity': 0.5641025641025641,
            'lexical_density': 0.421,
            'most_frequent_word_ratio': 0.0392156862745098
        },
        'quality': {
            'word_choice_errors': 1,  # BETTER (was 2)
            'advanced_vocabulary_count': 0
        }
    },
    'grammatical_range_accuracy': {
        'complexity': {
            'mean_utterance_length': 13.444444444444445,
            'complex_structures_attempted': 3,
            'complex_structures_accurate': 2  # BETTER (was 0)
        },
        'accuracy': {
            'grammar_errors': 3,
            'meaning_blocking_error_ratio': 0.0
        }
    },
    'pronunciation': {
        'intelligibility': {
            'mean_word_confidence': 0.864,
            'low_confidence_ratio': 0.157
        },
        'prosody': {
            'monotone_detected': True
        }
    },
    'raw_transcript': 'in a large city building there was two people who were carrying similar suitcases'
}

scorer = IELTSBandScorer()
result = scorer.score(analysis_data)

print("=" * 70)
print("SAMPLE 2: 3 Complex, 2 Accurate (66% success)")
print("=" * 70)
print(f"\nOverall Band: {result['overall_band']}")
print(f"\nCriterion Bands:")
for criterion, band in result['criterion_bands'].items():
    print(f"  {criterion.replace('_', ' ').title()}: {band}")
print(f"\nFeedback: {result['feedback_summary']}")
print("\n" + "=" * 70)
print("ANALYSIS:")
print("=" * 70)
print("""
This sample should score ~6.0-6.5 overall because:
- Grammar: 66% accuracy on 3 complex structures = Band 6 (not Band 9!)
- Fluency: 3.52 fillers/min, 1 coherence break = Band 6-7 (no longer Band 8)
- Lexical: 6.5 (no advanced vocab cap)
- Pronunciation: Should be reduced due to low confidence + monotone
- Overall: Pulled down by multiple criteria at Band 6-6.5
""")
