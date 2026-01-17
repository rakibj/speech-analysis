"""
IELTS Speaking Band Scorer v5.0 (METRICS-BASED)

Uses actual acoustic and linguistic metrics instead of LLM annotations:
- Fluency: WPM, pause variability, repetition, long pauses
- Pronunciation: word confidence, intelligibility ratio
- Lexical: vocabulary richness, lexical density
- Grammar: derived from fluency metrics

Calibrated to match IELTS band reference samples.
"""

from typing import Dict


def round_half(score: float) -> float:
    """Round to nearest 0.5"""
    return round(score * 2) / 2


class IELTSBandScorer:
    """
    Metrics-based IELTS band scorer using actual speech metrics.
    
    Calibration based on reference samples:
    - Band 5-5.5: wpm~89, long_pauses~2.1, pause_var~0.9
    - Band 7: wpm~109, long_pauses~1.4, pause_var~0.66
    - Band 8-8.5: wpm~198, long_pauses~0, pause_var~0.14
    """

    # ===============================
    # FLUENCY & COHERENCE
    # ===============================

    def score_fluency(self, metrics: Dict) -> float:
        """
        Score fluency based on:
        - WPM (speech rate)
        - Long pauses per minute
        - Pause variability
        - Repetition ratio
        """
        wpm = metrics.get("wpm", 0)
        long_pauses = metrics.get("long_pauses_per_min", 0)
        pause_var = metrics.get("pause_variability", 0)
        repetition = metrics.get("repetition_ratio", 0)

        # Band 8-9: Excellent fluency
        # Slightly relaxed thresholds to include ielts8.5 (wpm=133, pause_var=0.25)
        # and ielts9 (wpm=158, pause_var=0.55)
        if wpm >= 130 and long_pauses <= 1.0 and pause_var <= 0.60 and repetition <= 0.050:
            return 8.5

        # Band 7-8: Very good fluency
        if wpm >= 100 and long_pauses <= 1.8 and pause_var <= 0.75 and repetition <= 0.065:
            return 7.5

        # Band 6-7: Moderate fluency with some hesitation
        if wpm >= 80 and long_pauses <= 2.5 and pause_var <= 1.2:
            return 6.5

        # Band 5-6: Noticeable fluency issues
        if long_pauses >= 2.0 or pause_var >= 0.9:
            return 5.5

        # Default: Band 6
        return 6.0


    # ===============================
    # PRONUNCIATION
    # ===============================

    def score_pronunciation(self, metrics: Dict) -> float:
        """
        Score pronunciation based on:
        - Mean word confidence
        - Low confidence ratio (words with confidence < 0.7)
        """
        mean_conf = metrics.get("mean_word_confidence", 0)
        low_conf_ratio = metrics.get("low_confidence_ratio", 0)

        # Band 8-9: Excellent clarity
        if mean_conf >= 0.89 and low_conf_ratio <= 0.12:
            return 8.5

        # Band 7-8: Very good clarity
        if mean_conf >= 0.85 and low_conf_ratio <= 0.20:
            return 7.5

        # Band 6-7: Generally clear
        if mean_conf >= 0.82 and low_conf_ratio <= 0.30:
            return 6.5

        # Band 5-6: Intelligibility issues
        if low_conf_ratio >= 0.35:
            return 5.5

        # Default: Band 6
        return 6.0


    # ===============================
    # LEXICAL RESOURCE
    # ===============================

    def score_lexical(self, metrics: Dict) -> float:
        """
        Score lexical resource based on:
        - Vocabulary richness
        - Lexical density (content words / total words)
        """
        vocab_richness = metrics.get("vocab_richness", 0)
        lexical_density = metrics.get("lexical_density", 0)

        # Band 8+: High vocabulary range
        if vocab_richness >= 0.55 and lexical_density >= 0.48:
            return 8.0

        # Band 7-8: Good vocabulary
        if vocab_richness >= 0.50 and lexical_density >= 0.45:
            return 7.5

        # Band 6-7: Adequate vocabulary
        if vocab_richness >= 0.45 and lexical_density >= 0.40:
            return 6.5

        # Band 5-6: Limited vocabulary
        if vocab_richness < 0.40 or lexical_density < 0.35:
            return 5.5

        # Default: Band 6
        return 6.0


    # ===============================
    # GRAMMATICAL RANGE & ACCURACY
    # ===============================

    def score_grammar(self, metrics: Dict) -> float:
        """
        Score grammar based on:
        - Mean utterance length (proxy for complex sentence use)
        - Speech rate variability (proxy for confident control)
        - Repetition ratio (indicates uncertainty/repair)
        """
        mean_utt_len = metrics.get("mean_utterance_length", 0)
        speech_rate_var = metrics.get("speech_rate_variability", 0)
        repetition = metrics.get("repetition_ratio", 0)

        # Band 8+: Complex structures, good control
        if mean_utt_len >= 35 and speech_rate_var <= 0.25 and repetition <= 0.035:
            return 8.0

        # Band 7-8: Some complexity
        if mean_utt_len >= 20 and speech_rate_var <= 0.40 and repetition <= 0.065:
            return 7.5

        # Band 6-7: Basic-to-moderate structures
        if mean_utt_len >= 10 and repetition <= 0.10:
            return 6.5

        # Band 5-6: Limited control or heavy repetition
        if repetition >= 0.12 or mean_utt_len < 8:
            return 5.5

        # Default: Band 6
        return 6.0


    # ===============================
    # OVERALL BAND
    # ===============================

    def score_overall(self, metrics: Dict) -> Dict:
        """
        Compute overall band from four criteria.
        
        Input metrics should include:
        - wpm, long_pauses_per_min, pause_variability, repetition_ratio
        - mean_word_confidence, low_confidence_ratio
        - vocab_richness, lexical_density
        - mean_utterance_length, speech_rate_variability
        """
        fc = self.score_fluency(metrics)
        pr = self.score_pronunciation(metrics)
        lr = self.score_lexical(metrics)
        gr = self.score_grammar(metrics)

        subscores = {
            "fluency_coherence": fc,
            "pronunciation": pr,
            "lexical_resource": lr,
            "grammatical_range_accuracy": gr,
        }

        # Overall = average of 4 criteria
        avg = sum(subscores.values()) / 4
        overall = round_half(avg)

        # Hard cap: if any criterion is weak (5.5), cap overall at 6.0
        if min(subscores.values()) <= 5.5:
            overall = min(overall, 6.0)

        # Ensure reasonable range
        overall = max(5.0, min(9.0, overall))

        return {
            "overall_band": overall,
            "criterion_bands": subscores,
        }


# ===============================================
# PUBLIC ENTRY POINT
# ===============================================

def score_ielts_speaking(metrics: Dict) -> Dict:
    """
    Score IELTS speaking from raw metrics.
    
    Args:
        metrics: dict with keys like wpm, long_pauses_per_min, etc.
    
    Returns:
        dict with overall_band and criterion_bands
    """
    scorer = IELTSBandScorer()
    return scorer.score_overall(metrics)
