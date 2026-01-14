import numpy as np
from scripts.ielts_band_scorer import IELTSBandScorer

# Your sample data
analysis_data = {
    'metadata': {
        'audio_duration_sec': 74.98,
        'speaking_time_sec': 74.32,
        'total_words_transcribed': 121,
        'content_word_count': 117,
        'analysis_timestamp': '2026-01-14T17:03:14.388811Z'
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
            'coherence_breaks': 3,
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
            'word_choice_errors': 2,
            'advanced_vocabulary_count': 0
        }
    },
    'grammatical_range_accuracy': {
        'complexity': {
            'mean_utterance_length': 13.444444444444445,
            'complex_structures_attempted': 3,
            'complex_structures_accurate': 0
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
print("IELTS BAND SCORING - FIXED VERSION")
print("=" * 70)
print(f"\nOverall Band: {result['overall_band']}")
print(f"\nCriterion Bands:")
for criterion, band in result['criterion_bands'].items():
    print(f"  {criterion.replace('_', ' ').title()}: {band}")
print(f"\nFeedback: {result['feedback_summary']}")
print(f"Duration Factor Applied: {result['duration_factor_applied']}")
print("\n" + "=" * 70)
print("EXPLANATION OF CHANGES:")
print("=" * 70)
print("""
1. Grammar (was 7.0 → now ~5.5-6.0):
   - 0% accuracy on 3 complex structures now gets -3.0 (harsh penalty)
   - Grammar error rate: 2.56% (3/117) is fine, but combined with 0% complex accuracy = major issue

2. Fluency (was 7.0 → now ~6.0-6.5):
   - Filler frequency lowered from band6=6.0 to 4.5 (stricter)
   - Coherence breaks threshold lowered from 3 to 2 (stricter)
   - Current: 3.52 fillers/min, 3 coherence breaks
   - Duration-adjusted: Sample is 75 seconds (short), stricter thresholds apply

3. Lexical (was 8.0 → now ~6.5):
   - NO advanced vocabulary count = hard cap at 6.5 max
   - Diversity is good (0.564) but without advanced vocab, can't exceed 6.5

4. Overall Band (was 7.5 → now ~6.0-6.5):
   - Weakness gap reduced from 2.5→2.0 and 2.0→1.5 (stricter enforcement)
   - If any criterion ≤4.5, overall ≤5.0 (not 5.5)
   - Grammar weakness pulls everything down
""")
