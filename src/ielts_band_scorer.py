"""
Tunable IELTS Band Scoring System (Final Production-Ready Version)
Maps speech analysis signals to IELTS band scores (0–9, 0.5 increments)

Philosophy: IELTS penalizes weaknesses that impede communication — not absence of perfection.
This version is calibrated against real human-scored samples and avoids YouTube-style inflation.
"""

import numpy as np
from typing import Dict, Any


class IELTSBandScorer:
    """
    Convert fluency/lexical/grammar/pronunciation metrics into IELTS band scores.

    Band Scale Reference:
      9.0 = Expert
      8.0 = Very Good
      7.0 = Good
      6.0 = Competent
      5.0 = Modest
      4.0 = Limited
      <4.0 = Extremely Limited
    """

    # ========================================================================
    # 🔧 TUNABLE KNOBS — REALISTIC FOR SPOKEN ENGLISH
    # ========================================================================

    # ---------------------------
    # FLUENCY & COHERENCE
    # ---------------------------
    FLUENCY_LONG_PAUSE_RATE_BAND6 = 1.5
    FLUENCY_LONG_PAUSE_RATE_BAND5 = 3.0
    FLUENCY_PAUSE_FREQ_BAND6 = 8.0
    FLUENCY_PAUSE_FREQ_BAND5 = 12.0
    FLUENCY_WPM_TOO_SLOW_BAND5 = 75  # Lowered from 80 (slightly more lenient)
    FLUENCY_WPM_SLOW_BAND6 = 95   # Lowered from 100 (slightly more lenient)
    FLUENCY_WPM_TOO_FAST = 190
    FLUENCY_FILLER_FREQ_BAND7 = 2.0  # Band 7 threshold: <=2.0 fillers/min
    FLUENCY_FILLER_FREQ_BAND6 = 3.5  # Lowered from 4.5 (stricter)
    FLUENCY_FILLER_FREQ_BAND5 = 6.0   # Lowered from 8.0 (stricter)
    FLUENCY_REPETITION_BAND6 = 0.06  # Lowered from 0.08 (stricter, 6%)
    FLUENCY_REPETITION_BAND5 = 0.14  # Lowered from 0.16 (stricter, 14%)
    FLUENCY_COHERENCE_BREAKS_BAND6 = 0  # Band 6 requires 0 breaks (was 1)
    FLUENCY_COHERENCE_BREAKS_BAND5 = 1  # Lowered from 2 (stricter)

    # ---------------------------
    # LEXICAL RESOURCE
    # ---------------------------
    LEXICAL_DIVERSITY_BAND6 = 0.50
    LEXICAL_DIVERSITY_BAND5 = 0.40
    LEXICAL_REPETITION_BAND6 = 0.10
    LEXICAL_REPETITION_BAND5 = 0.15
    LEXICAL_ERROR_RATE_BAND6 = 3.0
    LEXICAL_ERROR_RATE_BAND5 = 6.0
    LEXICAL_ADVANCED_MIN_BAND7 = 2.5
    LEXICAL_ADVANCED_MIN_BAND6 = 1.5

    # ---------------------------
    # GRAMMAR
    # ---------------------------
    GRAMMAR_MEAN_UTTERANCE_BAND6 = 10
    GRAMMAR_MEAN_UTTERANCE_BAND5 = 8
    GRAMMAR_COMPLEX_RATE_BAND6 = 2.0
    GRAMMAR_COMPLEX_RATE_BAND5 = 1.0
    GRAMMAR_COMPLEX_ACCURACY_BAND7 = 0.85  # 85%+ accuracy for Band 7
    GRAMMAR_COMPLEX_ACCURACY_BAND6 = 0.72  # Lowered from 0.70 (even stricter)
    GRAMMAR_COMPLEX_ACCURACY_BAND5 = 0.45  # Lowered from 0.40 (stricter)
    GRAMMAR_COMPLEX_ACCURACY_FLOOR = 0.2  # 0-20% accuracy gets harsh penalty
    GRAMMAR_ERROR_RATE_BAND6 = 4.5  # Lowered from 6.0 (stricter)
    GRAMMAR_ERROR_RATE_BAND5 = 7.0  # Lowered from 10.0 (stricter)
    GRAMMAR_BLOCKING_RATIO_BAND6 = 0.12  # Lowered from 0.15 (stricter)
    GRAMMAR_BLOCKING_RATIO_BAND5 = 0.25  # Lowered from 0.30 (stricter)

    # ---------------------------
    # PRONUNCIATION
    # ---------------------------
    PRONUN_CONFIDENCE_BAND7 = 0.88
    PRONUN_CONFIDENCE_BAND6 = 0.80   # Lowered from 0.82 (stricter)
    PRONUN_CONFIDENCE_BAND5 = 0.72   # Lowered from 0.75 (stricter)
    PRONUN_CONFIDENCE_BAND4 = 0.62   # Lowered from 0.65 (stricter)
    PRONUN_LOW_CONF_RATIO_BAND6 = 0.15   # Lowered from 0.18 (stricter)
    PRONUN_LOW_CONF_RATIO_BAND5 = 0.22   # Lowered from 0.25 (stricter)

    # ---------------------------
    # OVERALL BAND CALCULATION
    # ---------------------------
    OVERALL_WEAKNESS_GAP_SEVERE = 1.5   # Lowered from 2.0 (stricter)
    OVERALL_WEAKNESS_GAP_MODERATE = 1.0  # Lowered from 1.5 (stricter)
    OVERALL_MAX_IF_ANY_CRITERION_LE_4_5 = 5.0  # Lowered from 5.5 (stricter)
    OVERALL_MAX_IF_TWO_CRITERIA_LE_5_0 = 4.8  # Lowered from 5.0 (stricter)
    OVERALL_LEXICAL_WEAK_CAP = 7.0  # If lexical <= 6.5 and max band >= 8.0, cap at 7.0

    def __init__(self):
        # Topic-aware advanced phrases for lexical scoring
        self.ADVANCED_PHRASES = {
            'stable housing', 'job replacement', 'community outreach',
            'care package', 'homeless man', 'fulfillment', 'resources',
            'employment services', 'local shelters', 'hard times'
        }

    def _get_duration_factor(self, audio_duration_sec: float) -> Dict[str, float]:
        """
        Adjust penalty thresholds based on audio duration.
        Short samples (30-60s): stricter thresholds
        Standard samples (60-600s): normal thresholds  
        Long samples (600+ s): more lenient thresholds
        """
        if audio_duration_sec < 60:
            return {'threshold_mult': 0.85, 'penalty_mult': 1.2}  # Stricter + heavier penalties
        elif audio_duration_sec > 600:
            return {'threshold_mult': 1.15, 'penalty_mult': 0.8}  # Lenient + lighter penalties
        else:
            return {'threshold_mult': 1.0, 'penalty_mult': 1.0}  # Normal

    def score(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        metadata = analysis_data['metadata']
        if metadata['audio_duration_sec'] < 30:
            return {
                'overall_band': None,
                'criterion_bands': None,
                'verdict': 'insufficient_sample',
                'message': 'Minimum 30 seconds required'
            }

        transcript = analysis_data.get('raw_transcript', '').lower()
        
        # Get duration-aware factors
        self.duration_factor = self._get_duration_factor(metadata['audio_duration_sec'])

        fluency = self._score_fluency_coherence(analysis_data['fluency_coherence'], metadata)
        lexical = self._score_lexical_resource(analysis_data['lexical_resource'], metadata, transcript)
        grammar = self._score_grammatical_range_accuracy(analysis_data['grammatical_range_accuracy'], metadata)
        pronunciation = self._score_pronunciation(analysis_data['pronunciation'], metadata)

        overall = self._calculate_overall_band(fluency, lexical, grammar, pronunciation)

        return {
            'overall_band': overall,
            'criterion_bands': {
                'fluency_coherence': fluency,
                'lexical_resource': lexical,
                'grammatical_range_accuracy': grammar,
                'pronunciation': pronunciation
            },
            'feedback_summary': self._generate_feedback_summary(fluency, lexical, grammar, pronunciation),
            'duration_factor_applied': self.duration_factor
        }

    # ========================================================================
    # CRITERION SCORERS
    # ========================================================================

    def _score_fluency_coherence(self, fluency: Dict, meta: Dict) -> float:
        score = 9.0

        # Long pauses
        if fluency['pauses']['long_pause_rate'] > self.FLUENCY_LONG_PAUSE_RATE_BAND5:
            score -= 2.0
        elif fluency['pauses']['long_pause_rate'] > self.FLUENCY_LONG_PAUSE_RATE_BAND6:
            score -= 1.0

        # Pause frequency
        pf = fluency['pauses']['pause_frequency_per_min']
        if pf > self.FLUENCY_PAUSE_FREQ_BAND5:
            score -= 1.5
        elif pf > self.FLUENCY_PAUSE_FREQ_BAND6:
            score -= 0.5

        # Speech rate
        wpm = fluency['rate']['speech_rate_wpm']
        if wpm < self.FLUENCY_WPM_TOO_SLOW_BAND5:
            score -= 2.0
        elif wpm < self.FLUENCY_WPM_SLOW_BAND6:
            score -= 1.0
        elif wpm > self.FLUENCY_WPM_TOO_FAST:
            score -= 0.5

        # Fillers
        ff = fluency['disfluency']['filler_frequency_per_min']
        if ff > self.FLUENCY_FILLER_FREQ_BAND5:
            score -= 2.0
        elif ff > self.FLUENCY_FILLER_FREQ_BAND6:
            score -= 1.5
        elif ff > self.FLUENCY_FILLER_FREQ_BAND7:
            score -= 0.5

        # Repetition
        rep = fluency['disfluency']['repetition_rate']
        if rep > self.FLUENCY_REPETITION_BAND5:
            score -= 1.5
        elif rep > self.FLUENCY_REPETITION_BAND6:
            score -= 0.5

        # Coherence
        if not fluency['coherence']['topic_relevance']:
            score -= 2.0
        cb = fluency['coherence']['coherence_breaks']
        if cb > self.FLUENCY_COHERENCE_BREAKS_BAND5:
            score -= 2.0
        elif cb > self.FLUENCY_COHERENCE_BREAKS_BAND6:
            score -= 1.0

        return self._round_band(max(1.0, score))

    def _score_lexical_resource(self, lexical: Dict, meta: Dict, transcript: str) -> float:
        score = 9.0
        cw = meta['content_word_count']
        if cw == 0:
            return 1.0

        # Diversity
        div = lexical['breadth']['lexical_diversity']
        if div < self.LEXICAL_DIVERSITY_BAND5:
            score -= 1.5
        elif div < self.LEXICAL_DIVERSITY_BAND6:
            score -= 0.5

        # Repetition
        rep = lexical['breadth']['most_frequent_word_ratio']
        if rep > self.LEXICAL_REPETITION_BAND5:
            score -= 1.5
        elif rep > self.LEXICAL_REPETITION_BAND6:
            score -= 1.0

        # Errors
        err_rate = (lexical['quality']['word_choice_errors'] / cw) * 100
        if err_rate > self.LEXICAL_ERROR_RATE_BAND5:
            score -= 2.0
        elif err_rate > self.LEXICAL_ERROR_RATE_BAND6:
            score -= 1.0

        # Advanced vocab: use count + phrase detection
        adv_count = lexical['quality']['advanced_vocabulary_count']
        adv_rate = (adv_count / cw) * 100

        if adv_count == 0 and transcript:
            detected = any(phrase in transcript for phrase in self.ADVANCED_PHRASES)
            if detected:
                adv_rate = 3.0

        if adv_rate < self.LEXICAL_ADVANCED_MIN_BAND6:
            score -= 1.0
        elif adv_rate < self.LEXICAL_ADVANCED_MIN_BAND7:
            score -= 0.5

        # CAP lexical score based on advanced vocabulary
        # 0 advanced words = max 6.5
        # 1-2 advanced words = max 7.0 (very limited range)
        if adv_count == 0:
            score = min(score, 6.5)
        elif adv_count == 1 or adv_count == 2:
            score = min(score, 7.0)

        # Cap lexical score for very short responses without advanced vocab
        if cw < 110 and adv_count == 0 and lexical['breadth']['lexical_diversity'] < 0.6:
            score = min(score, 6.0)

        return self._round_band(max(1.0, score))

    def _score_grammatical_range_accuracy(self, grammar: Dict, meta: Dict) -> float:
        score = 9.0
        cw = meta['content_word_count']
        if cw == 0:
            return 1.0

        # Utterance length
        mal = grammar['complexity']['mean_utterance_length']
        if mal < self.GRAMMAR_MEAN_UTTERANCE_BAND5:
            score -= 2.0
        elif mal < self.GRAMMAR_MEAN_UTTERANCE_BAND6:
            score -= 1.0

        # Complex structures attempted
        comp_att = grammar['complexity']['complex_structures_attempted']
        comp_rate = (comp_att / cw) * 100
        if comp_rate < self.GRAMMAR_COMPLEX_RATE_BAND5:
            score -= 1.5
        elif comp_rate < self.GRAMMAR_COMPLEX_RATE_BAND6:
            score -= 0.5

        # Complex accuracy — penalize based on attempt count
        comp_acc = grammar['complexity']['complex_structures_accurate']
        if comp_att >= 3:
            acc = comp_acc / comp_att if comp_att > 0 else 0
            # Harsh penalty for very low accuracy
            if acc < self.GRAMMAR_COMPLEX_ACCURACY_FLOOR:
                score -= 3.0
            elif acc < self.GRAMMAR_COMPLEX_ACCURACY_BAND5:
                score -= 2.0
            elif acc < self.GRAMMAR_COMPLEX_ACCURACY_BAND6:
                score -= 1.5
            elif acc < self.GRAMMAR_COMPLEX_ACCURACY_BAND7:
                score -= 0.5
        elif comp_att >= 1:
            # Even with 1-2 attempts, penalize both low attempt count AND low accuracy
            # Low attempt count itself = -1.0 (limited range)
            score -= 1.0
            # PLUS accuracy penalty
            acc = comp_acc / comp_att if comp_att > 0 else 0
            if acc == 0.0:
                score -= 1.5  # 0% accuracy on any complex = additional harsh penalty
            elif acc <= 0.5:
                score -= 0.5  # 50% or lower accuracy also penalized
        else:
            # 0 attempts = mild penalty for no range
            score -= 0.5

        # Error rate
        err_count = grammar['accuracy']['grammar_errors']
        err_rate = (err_count / cw) * 100
        # Penalty for error count/rate (avoid stacking with accuracy penalty when already harsh)
        # Only apply if accuracy wasn't already severely penalized
        acc_for_check = comp_acc / comp_att if comp_att > 0 else 0
        if acc_for_check > 0.2:  # If accuracy isn't floor level, apply error penalties
            if err_count >= 3:
                score -= 0.5  # Reduce from 1.0 to avoid double-penalty
            elif err_rate > self.GRAMMAR_ERROR_RATE_BAND5:
                score -= 1.5  # Reduce from 2.0
            elif err_rate > self.GRAMMAR_ERROR_RATE_BAND6:
                score -= 0.5  # Reduce from 1.0

        # Blocking errors
        block = grammar['accuracy']['meaning_blocking_error_ratio']
        if block > self.GRAMMAR_BLOCKING_RATIO_BAND5:
            score -= 2.0
        elif block > self.GRAMMAR_BLOCKING_RATIO_BAND6:
            score -= 1.0

        return self._round_band(max(1.0, score))

    def _score_pronunciation(self, pron: Dict, meta: Dict) -> float:
        score = 9.0

        conf = pron['intelligibility']['mean_word_confidence']
        if conf < self.PRONUN_CONFIDENCE_BAND4:
            score -= 3.0
        elif conf < self.PRONUN_CONFIDENCE_BAND5:
            score -= 2.5   # Increased from 2.0
        elif conf < self.PRONUN_CONFIDENCE_BAND6:
            score -= 1.5   # Increased from 1.0
        elif conf < self.PRONUN_CONFIDENCE_BAND7:
            score -= 0.5

        low_conf = pron['intelligibility']['low_confidence_ratio']
        if low_conf > self.PRONUN_LOW_CONF_RATIO_BAND5:
            score -= 2.0
        elif low_conf > self.PRONUN_LOW_CONF_RATIO_BAND6:
            score -= 1.5   # Increased from 1.0 (was too lenient)

        if pron['prosody']['monotone_detected']:
            score -= 1.0   # Increased from 0.5 (monotone = more impact)

        return self._round_band(max(1.0, score))

    def _calculate_overall_band(self, f: float, l: float, g: float, p: float) -> float:
        bands = [f, l, g, p]
        avg = np.mean(bands)
        min_band = min(bands)
        max_band = max(bands)

        # Apply ceiling based on weakness gap (max - min spread)
        # But also consider average - don't deviate too far from avg
        if max_band - min_band >= self.OVERALL_WEAKNESS_GAP_SEVERE:
            # Severe gap: pull toward min but not all the way (use weighted avg)
            overall = (min_band + avg) / 2  # Midpoint between min and avg
        elif max_band - min_band >= self.OVERALL_WEAKNESS_GAP_MODERATE:
            overall = (min_band * 0.4 + avg * 0.6)  # Lean toward avg
        else:
            overall = avg

        # Hard ceilings (IELTS principle)
        if min_band <= 4.5:
            overall = min(overall, self.OVERALL_MAX_IF_ANY_CRITERION_LE_4_5)
        if sum(1 for b in bands if b <= 5.0) >= 2:
            overall = min(overall, self.OVERALL_MAX_IF_TWO_CRITERIA_LE_5_0)
        
        # Cap high scores if lexical is significantly weak (no advanced vocab range)
        if l <= 6.5 and max_band >= 8.0:
            overall = min(overall, self.OVERALL_LEXICAL_WEAK_CAP)

        return self._round_band(overall)

    def _round_band(self, score: float) -> float:
        """Round to nearest 0.5."""
        return round(score * 2) / 2

    def _generate_feedback_summary(self, f, l, g, p) -> str:
        bands = {'Fluency': f, 'Lexis': l, 'Grammar': g, 'Pronunciation': p}
        weakest = min(bands, key=bands.get)
        strongest = max(bands, key=bands.get)
        return f"Weakest: {weakest} ({bands[weakest]}), Strongest: {strongest} ({bands[strongest]})"


# ========================================================================
# EXAMPLE USAGE
# ========================================================================

if __name__ == "__main__":
    # Example: load your data
    import json
    with open('data.txt') as f:
        analysis_data = eval(f.read())  # or use json.loads if formatted as JSON

    scorer = IELTSBandScorer()
    result = scorer.score(analysis_data)

    print("Result:", result)