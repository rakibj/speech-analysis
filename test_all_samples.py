#!/usr/bin/env python
"""
Verification of Fixed IELTS Band Scorer - All samples
Tests to confirm realistic scoring across multiple scenarios
"""

import numpy as np
from scripts.ielts_band_scorer import IELTSBandScorer

def test_sample_0_percent_accuracy():
    """Sample with 0% grammar accuracy - should score ~5.0"""
    analysis_data = {
        'metadata': {
            'audio_duration_sec': 74.98,
            'speaking_time_sec': 74.32,
            'total_words_transcribed': 121,
            'content_word_count': 117,
        },
        'fluency_coherence': {
            'pauses': {'pause_frequency_per_min': 0.80, 'long_pause_rate': 0.0, 'pause_variability': 0.0},
            'rate': {'speech_rate_wpm': 93.6, 'speech_rate_variability': 0.33},
            'disfluency': {'filler_frequency_per_min': 3.52, 'stutter_frequency_per_min': 0.80, 'repetition_rate': 0.039},
            'coherence': {'coherence_breaks': 3, 'topic_relevance': True}
        },
        'lexical_resource': {
            'breadth': {'unique_word_count': 66, 'lexical_diversity': 0.564, 'lexical_density': 0.421, 'most_frequent_word_ratio': 0.039},
            'quality': {'word_choice_errors': 2, 'advanced_vocabulary_count': 0}
        },
        'grammatical_range_accuracy': {
            'complexity': {'mean_utterance_length': 13.4, 'complex_structures_attempted': 3, 'complex_structures_accurate': 0},
            'accuracy': {'grammar_errors': 3, 'meaning_blocking_error_ratio': 0.0}
        },
        'pronunciation': {
            'intelligibility': {'mean_word_confidence': 0.864, 'low_confidence_ratio': 0.157},
            'prosody': {'monotone_detected': True}
        },
        'raw_transcript': 'test'
    }
    scorer = IELTSBandScorer()
    result = scorer.score(analysis_data)
    
    print("\n" + "="*70)
    print("SAMPLE 1: 0% Grammar Accuracy (0/3 complex structures)")
    print("="*70)
    print(f"Overall: {result['overall_band']} ✓ (Expected ~5.0)")
    print(f"  Fluency: {result['criterion_bands']['fluency_coherence']} (3 coherence breaks penalized)")
    print(f"  Lexical: {result['criterion_bands']['lexical_resource']} (no advanced vocab cap)")
    print(f"  Grammar: {result['criterion_bands']['grammatical_range_accuracy']} (0% accuracy = harsh penalty)")
    print(f"  Pronunciation: {result['criterion_bands']['pronunciation']} (low confidence + monotone)")
    return result['overall_band'] == 5.0

def test_sample_66_percent_accuracy():
    """Sample with 66% grammar accuracy - should score ~6.5"""
    analysis_data = {
        'metadata': {
            'audio_duration_sec': 74.98,
            'speaking_time_sec': 74.32,
            'total_words_transcribed': 121,
            'content_word_count': 117,
        },
        'fluency_coherence': {
            'pauses': {'pause_frequency_per_min': 0.80, 'long_pause_rate': 0.0, 'pause_variability': 0.0},
            'rate': {'speech_rate_wpm': 93.6, 'speech_rate_variability': 0.33},
            'disfluency': {'filler_frequency_per_min': 3.52, 'stutter_frequency_per_min': 0.80, 'repetition_rate': 0.039},
            'coherence': {'coherence_breaks': 1, 'topic_relevance': True}
        },
        'lexical_resource': {
            'breadth': {'unique_word_count': 66, 'lexical_diversity': 0.564, 'lexical_density': 0.421, 'most_frequent_word_ratio': 0.039},
            'quality': {'word_choice_errors': 1, 'advanced_vocabulary_count': 0}
        },
        'grammatical_range_accuracy': {
            'complexity': {'mean_utterance_length': 13.4, 'complex_structures_attempted': 3, 'complex_structures_accurate': 2},
            'accuracy': {'grammar_errors': 3, 'meaning_blocking_error_ratio': 0.0}
        },
        'pronunciation': {
            'intelligibility': {'mean_word_confidence': 0.864, 'low_confidence_ratio': 0.157},
            'prosody': {'monotone_detected': True}
        },
        'raw_transcript': 'test'
    }
    scorer = IELTSBandScorer()
    result = scorer.score(analysis_data)
    
    print("\n" + "="*70)
    print("SAMPLE 2: 66% Grammar Accuracy (2/3 complex structures)")
    print("="*70)
    print(f"Overall: {result['overall_band']} ✓ (Expected ~6.5)")
    print(f"  Fluency: {result['criterion_bands']['fluency_coherence']} (1 coherence break is good)")
    print(f"  Lexical: {result['criterion_bands']['lexical_resource']} (no advanced vocab cap)")
    print(f"  Grammar: {result['criterion_bands']['grammatical_range_accuracy']} (66% < 72% threshold = penalty)")
    print(f"  Pronunciation: {result['criterion_bands']['pronunciation']} (low confidence + monotone)")
    return result['overall_band'] == 6.5

def test_sample_excellent():
    """Sample with high performance - should score ~7.5-8.0"""
    analysis_data = {
        'metadata': {
            'audio_duration_sec': 120.0,
            'speaking_time_sec': 118.0,
            'total_words_transcribed': 300,
            'content_word_count': 260,
        },
        'fluency_coherence': {
            'pauses': {'pause_frequency_per_min': 1.5, 'long_pause_rate': 0.0, 'pause_variability': 0.1},
            'rate': {'speech_rate_wpm': 130.0, 'speech_rate_variability': 0.2},
            'disfluency': {'filler_frequency_per_min': 1.0, 'stutter_frequency_per_min': 0.1, 'repetition_rate': 0.02},
            'coherence': {'coherence_breaks': 0, 'topic_relevance': True}
        },
        'lexical_resource': {
            'breadth': {'unique_word_count': 150, 'lexical_diversity': 0.75, 'lexical_density': 0.62, 'most_frequent_word_ratio': 0.02},
            'quality': {'word_choice_errors': 0, 'advanced_vocabulary_count': 8}
        },
        'grammatical_range_accuracy': {
            'complexity': {'mean_utterance_length': 18.0, 'complex_structures_attempted': 6, 'complex_structures_accurate': 5},
            'accuracy': {'grammar_errors': 1, 'meaning_blocking_error_ratio': 0.0}
        },
        'pronunciation': {
            'intelligibility': {'mean_word_confidence': 0.92, 'low_confidence_ratio': 0.05},
            'prosody': {'monotone_detected': False}
        },
        'raw_transcript': 'test'
    }
    scorer = IELTSBandScorer()
    result = scorer.score(analysis_data)
    
    print("\n" + "="*70)
    print("SAMPLE 3: Excellent Performance")
    print("="*70)
    print(f"Overall: {result['overall_band']} ✓ (Expected ~7.5-8.0)")
    print(f"  Fluency: {result['criterion_bands']['fluency_coherence']} (excellent)")
    print(f"  Lexical: {result['criterion_bands']['lexical_resource']} (advanced vocab present)")
    print(f"  Grammar: {result['criterion_bands']['grammatical_range_accuracy']} (83% accuracy, good range)")
    print(f"  Pronunciation: {result['criterion_bands']['pronunciation']} (high confidence)")
    return result['overall_band'] >= 7.5

if __name__ == "__main__":
    print("\n" + "="*70)
    print("IELTS BAND SCORER - VERIFICATION TESTS")
    print("="*70)
    
    results = []
    results.append(("0% Accuracy", test_sample_0_percent_accuracy()))
    results.append(("66% Accuracy", test_sample_66_percent_accuracy()))
    results.append(("Excellent", test_sample_excellent()))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("✓ All tests passed!" if all_passed else "✗ Some tests failed!"))
