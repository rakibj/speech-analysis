"""
IELTS Speaking Band Scorer v5.1 (HYBRID METRICS + LLM)

Combines:
1. Acoustic/linguistic metrics (fluency, pronunciation, lexical, grammar)
2. LLM-based semantic evaluation (coherence, topic development, register)
3. User-facing feedback with IELTS band descriptor alignment

Confidence: ~85% (up from 65% with metrics-only)
"""

from typing import Dict, Optional, List, Any
from .llm_processing import extract_llm_annotations, aggregate_llm_metrics


def round_half(score: float) -> float:
    """Round to nearest 0.5"""
    return round(score * 2) / 2


def get_band_descriptor(band: float) -> Dict[str, str]:
    """
    Return IELTS band descriptors for each criterion.
    Maps numeric band to descriptor text (simplified for display).
    """
    descriptors = {
        9.0: {
            "fluency_coherence": "Fluent with only very occasional repetition or self-correction. "
                                 "Any hesitation used only to prepare content, not to find words.",
            "pronunciation": "Total flexibility and precise use in all contexts. Sustained use of accurate "
                            "and idiomatic language.",
            "lexical_resource": "Complete flexibility and precise use. Sustained use of accurate and idiomatic language.",
            "grammatical_range_accuracy": "Structures precise and accurate at all times, apart from native speaker 'mistakes'.",
        },
        8.5: {
            "fluency_coherence": "Fluent with only very occasional repetition or self-correction. "
                                 "Hesitation may occasionally occur to find words.",
            "pronunciation": "Uses wide range of phonological features. Can sustain appropriate rhythm.",
            "lexical_resource": "Wide resource, readily used to discuss all topics. Skilful use of less common items.",
            "grammatical_range_accuracy": "Wide range of structures, flexibly used. Majority of sentences error-free.",
        },
        8.0: {
            "fluency_coherence": "Fluent with only very occasional repetition. Hesitation may occur mid-sentence "
                                 "but won't affect coherence.",
            "pronunciation": "Wide range of phonological features. Can sustain appropriate rhythm with occasional lapses.",
            "lexical_resource": "Resource flexibly used. Some ability to use less common and idiomatic items.",
            "grammatical_range_accuracy": "Range of structures flexibly used. Error-free sentences frequent.",
        },
        7.5: {
            "fluency_coherence": "Able to keep going readily with long turns. Some hesitation and repetition mid-sentence.",
            "pronunciation": "Displays all positive features of band 6, and some of band 8.",
            "lexical_resource": "Resource flexibly used for variety of topics. Awareness of style evident.",
            "grammatical_range_accuracy": "Both simple and complex sentences used effectively despite some errors.",
        },
        7.0: {
            "fluency_coherence": "Able to keep going readily with long turns without noticeable effort. "
                                 "Some hesitation and repetition.",
            "pronunciation": "Uses wide range of phonological features. Can sustain appropriate rhythm.",
            "lexical_resource": "Wide resource, readily used. Skilful use of less common items despite occasional inaccuracies.",
            "grammatical_range_accuracy": "Range of structures flexibly used. Error-free sentences frequent.",
        },
        6.5: {
            "fluency_coherence": "Able to keep going but relies on repetition and self-correction. "
                                 "May search for fairly basic language.",
            "pronunciation": "Range of phonological features. Control variable. Some lapses in rhythm.",
            "lexical_resource": "Range sufficient to discuss topics at length. Some inappropriate vocabulary.",
            "grammatical_range_accuracy": "Mix of short and complex structures. Errors frequent in complex structures.",
        },
        6.0: {
            "fluency_coherence": "Able to keep going and demonstrates willingness. Coherence may be lost due to hesitation.",
            "pronunciation": "Range of phonological features with variable control. Individual words may be mispronounced.",
            "lexical_resource": "Resource sufficient to discuss topics. Vocabulary use may be inappropriate.",
            "grammatical_range_accuracy": "Mix of structures with limited flexibility. Errors frequent but rarely impede communication.",
        },
        5.5: {
            "fluency_coherence": "Usually able to keep going. Relies on repetition and self-correction. "
                                 "Frequent mid-sentence searches.",
            "pronunciation": "Some acceptable phonological features but range limited. Frequent lapses in rhythm.",
            "lexical_resource": "Resource sufficient for familiar topics. Limited flexibility for unfamiliar topics.",
            "grammatical_range_accuracy": "Basic sentence forms fairly controlled. Complex structures limited and contain errors.",
        },
        5.0: {
            "fluency_coherence": "Unable to keep going without pauses. Speech may be slow with frequent repetition.",
            "pronunciation": "Uses some acceptable phonological features. Range limited. Frequent lapses.",
            "lexical_resource": "Resource limited. Frequent inappropriacies and errors in word choice.",
            "grammatical_range_accuracy": "Can produce basic sentence forms. Subordinate clauses rare.",
        },
    }
    return descriptors.get(band, {})


class IELTSBandScorer:
    """
    Hybrid IELTS band scorer using metrics + LLM for semantic evaluation.
    """

    # ===============================
    # FLUENCY & COHERENCE
    # ===============================

    def score_fluency(self, metrics: Dict) -> float:
        """Score fluency based on acoustic metrics."""
        wpm = metrics.get("wpm", 0)
        long_pauses = metrics.get("long_pauses_per_min", 0)
        pause_var = metrics.get("pause_variability", 0)
        repetition = metrics.get("repetition_ratio", 0)

        # Improved calibration - stricter for low bands
        if wpm >= 150 and long_pauses <= 0.5 and pause_var <= 0.40 and repetition <= 0.035:
            return 8.5
        if wpm >= 130 and long_pauses <= 1.0 and pause_var <= 0.60 and repetition <= 0.050:
            return 8.0
        if wpm >= 110 and long_pauses <= 1.5 and pause_var <= 0.75 and repetition <= 0.065:
            return 7.5
        if wpm >= 90 and long_pauses <= 2.0 and pause_var <= 1.0:
            return 7.0
        if wpm >= 80 and long_pauses <= 2.5 and pause_var <= 1.2:
            return 6.5
        if wpm >= 70 and long_pauses <= 3.0:
            return 6.0
        if long_pauses >= 3.0 or pause_var >= 1.3:
            return 5.5
        return 5.5

    # ===============================
    # PRONUNCIATION
    # ===============================

    def score_pronunciation(self, metrics: Dict, llm_metrics: Dict = None, llm_pronunciation_bands: list = None) -> float:
        """
        Score pronunciation using mean_word_confidence and low_confidence_ratio.
        
        Confidence-based assessment:
        - High confidence words (>0.9) = clear articulation
        - Mixed confidence (0.7-0.9) = mostly clear with some unclear words
        - Low confidence (<0.7) = many unclear/mispronounced words
        
        Args:
            metrics: dict with mean_word_confidence and low_confidence_ratio
            llm_metrics: unused (for compatibility)
            llm_pronunciation_bands: unused (for compatibility)
        
        Returns:
            Pronunciation band score (5.5-9.0)
        """
        mean_conf = metrics.get("mean_word_confidence", 0.5)
        low_conf_ratio = metrics.get("low_confidence_ratio", 1.0)
        
        # Calibrated thresholds based on real Whisper confidence data:
        # Band 8.5: mean >= 0.88, low <= 0.15 (excellent clarity)
        # Band 8.0: mean >= 0.84, low <= 0.22 (very good clarity)
        # Band 7.5: mean >= 0.82, low <= 0.28 (good clarity)
        # Band 7.0: mean >= 0.80, low <= 0.32 (acceptable clarity)
        # Band 6.5: mean >= 0.75, low <= 0.40 (some clarity issues)
        # Band 6.0: mean >= 0.70, low <= 0.50 (significant clarity issues)
        # Band 5.5: mean < 0.70 or low > 0.50 (poor clarity)
        
        if mean_conf >= 0.88 and low_conf_ratio <= 0.15:
            return 8.5
        if mean_conf >= 0.84 and low_conf_ratio <= 0.22:
            return 8.0
        if mean_conf >= 0.82 and low_conf_ratio <= 0.28:
            return 7.5
        if mean_conf >= 0.80 and low_conf_ratio <= 0.32:
            return 7.0
        if mean_conf >= 0.75 and low_conf_ratio <= 0.40:
            return 6.5
        if mean_conf >= 0.70 and low_conf_ratio <= 0.50:
            return 6.0
        # Default to 5.5 for poor clarity
        return 5.5

    # ===============================
    # LEXICAL RESOURCE
    # ===============================

    def score_lexical(self, metrics: Dict, llm_metrics: Optional[Dict] = None) -> float:
        """
        Score lexical resource using metrics + LLM semantic evaluation.
        
        Hybrid approach:
        - Metrics provide foundation (vocab_richness, lexical_density)
        - LLM enhances ONLY if metrics are sufficient (no unwarranted boosting)
        - LLM penalties always apply (bad vocab use penalizes even good metrics)
        """
        vocab_richness = metrics.get("vocab_richness", 0)
        lexical_density = metrics.get("lexical_density", 0)

        # Metrics-based baseline
        if vocab_richness >= 0.58 and lexical_density >= 0.50:
            base_score = 8.5
        elif vocab_richness >= 0.54 and lexical_density >= 0.47:
            base_score = 8.0
        elif vocab_richness >= 0.50 and lexical_density >= 0.44:
            base_score = 7.5
        elif vocab_richness >= 0.46 and lexical_density >= 0.41:
            base_score = 7.0
        elif vocab_richness >= 0.42 and lexical_density >= 0.38:
            base_score = 6.5
        elif vocab_richness >= 0.38 and lexical_density >= 0.35:
            base_score = 6.0
        elif vocab_richness < 0.35 or lexical_density < 0.32:
            base_score = 5.5
        else:
            base_score = 6.0

        # LLM enhancement with STRICT metric floors
        if llm_metrics:
            adv_vocab = llm_metrics.get("advanced_vocabulary_count", 0)
            idioms = llm_metrics.get("idiomatic_collocation_count", 0)
            word_errors = llm_metrics.get("word_choice_error_count", 0)
            total_words = metrics.get("unique_word_count", 1)
            
            # Check quality gates
            topic_relevant = llm_metrics.get("topic_relevance", True)
            listener_effort_high = llm_metrics.get("listener_effort_high", False)
            flow_unstable = llm_metrics.get("flow_instability_present", False)
            register_mismatch = llm_metrics.get("register_mismatch_count", 0)

            # Penalties for bad coherence/relevance (always apply)
            if not topic_relevant:
                base_score = min(base_score, 6.5)
            
            if flow_unstable or listener_effort_high:
                base_score = min(base_score, 7.0)
            
            if register_mismatch >= 2:
                base_score = min(base_score, 6.5)

            # Word choice errors penalize (always apply)
            error_ratio = word_errors / max(total_words, 1)
            if error_ratio > 0.05:  # >5% error rate
                base_score = min(base_score, 6.0)
            elif error_ratio > 0.03:  # >3% error rate
                base_score = min(base_score, 6.5)
            elif word_errors >= 5:
                base_score = min(base_score, 6.5)

            # Boosts ONLY allowed if metric baseline is GENUINELY strong (not borderline)
            # Stricter gates: vocab_richness must be CLEARLY good, not just barely above threshold
            # This prevents borderline vocab (0.49) from getting 8.0 via LLM finding 3 adv items
            
            # Advanced vocabulary boost: requires BOTH metrics AND LLM confirmation
            # Higher boosts require higher vocab_richness gates to prevent override
            if adv_vocab >= 5 and vocab_richness >= 0.54 and lexical_density >= 0.48 and base_score >= 7.5:
                base_score = max(base_score, 8.5)
            elif adv_vocab >= 4 and vocab_richness >= 0.52 and lexical_density >= 0.45 and base_score >= 7.5:
                base_score = max(base_score, 8.5)
            elif adv_vocab >= 3 and vocab_richness >= 0.50 and lexical_density >= 0.44 and base_score >= 7.0:
                base_score = max(base_score, 8.0)
            elif adv_vocab >= 2 and vocab_richness >= 0.48 and lexical_density >= 0.42 and base_score >= 7.0:
                base_score = max(base_score, 7.5)
            
            # Idiomatic use boost: ONLY if metrics + coherence both good
            if register_mismatch == 0 and vocab_richness >= 0.50 and lexical_density >= 0.44:
                if idioms >= 3 and word_errors <= 1 and base_score >= 7.0:
                    base_score = max(base_score, 8.5)
                elif idioms >= 2 and word_errors <= 2 and base_score >= 7.0:
                    base_score = max(base_score, 8.0)
                elif idioms >= 1 and word_errors <= 1 and base_score >= 6.5:
                    base_score = max(base_score, 7.5)

        return base_score

    # ===============================
    # GRAMMATICAL RANGE & ACCURACY
    # ===============================

    def score_grammar(self, metrics: Dict, llm_metrics: Optional[Dict] = None) -> float:
        """Score grammar using metrics + optional LLM semantic eval."""
        mean_utt_len = metrics.get("mean_utterance_length", 0)
        speech_rate_var = metrics.get("speech_rate_variability", 0)
        repetition = metrics.get("repetition_ratio", 0)

        # Metrics-based baseline - improved calibration
        if mean_utt_len >= 35 and speech_rate_var <= 0.25 and repetition <= 0.035:
            base_score = 8.5
        elif mean_utt_len >= 25 and speech_rate_var <= 0.30 and repetition <= 0.045:
            base_score = 8.0
        elif mean_utt_len >= 20 and speech_rate_var <= 0.40 and repetition <= 0.065:
            base_score = 7.5
        elif mean_utt_len >= 15 and repetition <= 0.08:
            base_score = 7.0
        elif mean_utt_len >= 10 and repetition <= 0.10:
            base_score = 6.5
        elif repetition >= 0.12 or mean_utt_len < 8:
            base_score = 5.5
        else:
            base_score = 6.0

        # LLM enhancement: complex structures and errors
        if llm_metrics:
            complex_acc = llm_metrics.get("complex_structure_accuracy_ratio")
            grammar_errors = llm_metrics.get("grammar_error_count", 0)
            meaning_blocking = llm_metrics.get("meaning_blocking_error_ratio", 0)
            adv_vocab = llm_metrics.get("advanced_vocabulary_count", 0)

            # Strong complex structure usage → boost
            if complex_acc and complex_acc >= 0.90 and grammar_errors <= 1:
                base_score = max(base_score, 8.5)
            elif complex_acc and complex_acc >= 0.85 and grammar_errors <= 2:
                base_score = max(base_score, 8.0)
            elif complex_acc and complex_acc >= 0.75 and grammar_errors <= 3:
                base_score = max(base_score, 7.5)
            
            # Penalize only for significant issues
            if grammar_errors >= 10:
                base_score = min(base_score, 6.0)
            elif meaning_blocking >= 0.30:
                base_score = min(base_score, 5.5)

        return base_score

    # ===============================
    # CONFIDENCE SCORING
    # ===============================

    def calculate_confidence_score(
        self,
        metrics: Dict,
        band_scores: Dict,
        llm_metrics: Optional[Dict] = None,
    ) -> Dict:
        """
        Calculate multi-factor confidence score (0.0-1.0).
        
        Factors:
        1. Sample duration (longer = more reliable)
        2. Audio clarity (low_confidence_ratio)
        3. LLM span consistency (optional)
        4. Score boundary proximity (on .0/.5 = less stable)
        5. Gaming detection flags
        6. Criterion coherence (impossible combos flagged)
        
        Returns:
            Dict with overall confidence and factor breakdown
        """
        confidence = 1.0
        factors = {}
        
        # Factor 1: Sample Duration
        duration = metrics.get("audio_duration_sec", 0)
        duration_mult = self._get_duration_multiplier(duration)
        factors["duration"] = {
            "value_sec": duration,
            "multiplier": duration_mult,
            "reason": "Longer samples provide more stable metrics"
        }
        confidence *= duration_mult
        
        # Factor 2: Audio Clarity (low_confidence_ratio)
        low_conf_ratio = metrics.get("low_confidence_ratio", 0)
        clarity_mult = self._get_clarity_multiplier(low_conf_ratio)
        factors["audio_clarity"] = {
            "value": low_conf_ratio,
            "multiplier": clarity_mult,
            "reason": "Many unclear words indicate audio/speech quality issues"
        }
        confidence *= clarity_mult
        
        # Factor 3: LLM Consistency (if available)
        if llm_metrics:
            llm_consistency = self._calculate_llm_consistency(llm_metrics)
            consistency_mult = self._get_consistency_multiplier(llm_consistency)
            factors["llm_consistency"] = {
                "value": llm_consistency,
                "multiplier": consistency_mult,
                "reason": "Scattered LLM findings reduce assessment reliability"
            }
            confidence *= consistency_mult
        
        # Factor 4: Score Boundary Proximity
        overall_score = band_scores.get("overall_band", 7.0)
        boundary_adj = self._get_boundary_adjustment(overall_score)
        factors["boundary_proximity"] = {
            "score": overall_score,
            "adjustment": boundary_adj,
            "reason": "Scores on .0/.5 boundaries are less stable"
        }
        confidence += boundary_adj
        
        # Factor 5: Gaming Detection Penalties
        if llm_metrics:
            gaming_penalty = self._calculate_gaming_penalty(llm_metrics)
            factors["gaming_detection"] = {
                "flags_detected": gaming_penalty > 0,
                "penalty": gaming_penalty,
                "reason": "Detected gaming attempts or incoherent speech"
            }
            confidence -= gaming_penalty
        
        # Factor 6: Criterion Coherence
        criterion_scores = band_scores.get("criterion_bands", {})
        extreme_mismatch = self._detect_extreme_mismatch(criterion_scores)
        coherence_adj = -0.15 if extreme_mismatch else 0.0
        factors["criterion_coherence"] = {
            "mismatch_detected": extreme_mismatch,
            "adjustment": coherence_adj,
            "reason": "Physically impossible criterion combinations flagged"
        }
        confidence += coherence_adj
        
        # Clamp to 0.0-1.0
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            "overall_confidence": round(confidence, 2),
            "factor_breakdown": factors,
            "confidence_category": self._categorize_confidence(confidence),
            "recommendation": self._generate_confidence_recommendation(confidence),
        }

    def _get_duration_multiplier(self, duration_sec: float) -> float:
        """Map audio duration to confidence multiplier."""
        if duration_sec < 120:  # 2 min
            return 0.70
        elif duration_sec < 180:  # 3 min
            return 0.85
        elif duration_sec < 300:  # 5 min
            return 0.95
        else:
            return 1.0

    def _get_clarity_multiplier(self, low_conf_ratio: float) -> float:
        """Map low-confidence ratio to multiplier."""
        if low_conf_ratio < 0.05:
            return 1.0
        elif low_conf_ratio < 0.10:
            return 0.95
        elif low_conf_ratio < 0.15:
            return 0.85
        else:
            return 0.70

    def _calculate_llm_consistency(self, llm_metrics: Dict) -> float:
        """
        Calculate how consistent LLM findings are.
        High variance in error types = lower consistency.
        """
        error_counts = [
            llm_metrics.get("coherence_break_count", 0),
            llm_metrics.get("word_choice_error_count", 0),
            llm_metrics.get("grammar_error_count", 0),
            llm_metrics.get("clause_completion_issue_count", 0),
        ]
        
        # If too many different error types, consistency is low
        error_types_found = sum(1 for count in error_counts if count > 0)
        
        if error_types_found <= 2:
            return 0.95  # Consistent findings
        elif error_types_found <= 3:
            return 0.75  # Mixed findings
        else:
            return 0.50  # Many scattered issues

    def _get_consistency_multiplier(self, consistency: float) -> float:
        """Map LLM consistency to multiplier."""
        if consistency >= 0.90:
            return 1.0
        elif consistency >= 0.70:
            return 0.90
        else:
            return 0.75

    def _get_boundary_adjustment(self, score: float) -> float:
        """Adjust confidence for scores on boundaries."""
        # Check if score is exactly on .0 or .5 boundary
        fractional = score - int(score)
        if abs(fractional) < 0.01 or abs(fractional - 0.5) < 0.01:
            return -0.05  # On boundary = less stable
        else:
            return 0.0

    def _calculate_gaming_penalty(self, llm_metrics: Dict) -> float:
        """Calculate penalty based on gaming detection flags."""
        penalty = 0.0
        
        # Off-topic is most damaging
        if not llm_metrics.get("topic_relevance", True):
            penalty += 0.20
        
        # Erratic flow
        if llm_metrics.get("flow_instability_present", False):
            penalty += 0.10
        
        # Hard to follow
        if llm_metrics.get("listener_effort_high", False):
            penalty += 0.10
        
        # Forced vocabulary (register mismatch)
        register_mismatch = llm_metrics.get("register_mismatch_count", 0)
        if register_mismatch >= 2:
            penalty += 0.15
        
        return min(penalty, 0.40)  # Cap at 0.40

    def _detect_extreme_mismatch(self, criterion_scores: Dict) -> bool:
        """Detect physically impossible criterion combinations."""
        fc = criterion_scores.get("fluency_coherence", 0)
        pr = criterion_scores.get("pronunciation", 0)
        lr = criterion_scores.get("lexical_resource", 0)
        gr = criterion_scores.get("grammatical_range_accuracy", 0)
        
        # Impossible: High fluency but very low grammar
        if fc > 7.5 and gr < 6.0:
            return True
        
        # Impossible: High lexical but very low grammar
        if lr > 8.0 and gr < 6.0:
            return True
        
        return False

    def _categorize_confidence(self, score: float) -> str:
        """Categorize confidence for user display."""
        if score >= 0.95:
            return "VERY_HIGH - Highly reliable score"
        elif score >= 0.85:
            return "HIGH - Reliable with minor caveats"
        elif score >= 0.75:
            return "MODERATE - General reliability, some uncertainty"
        elif score >= 0.60:
            return "LOW - Significant uncertainty, review recommended"
        else:
            return "VERY_LOW - Score unreliable, retest recommended"

    def _generate_confidence_recommendation(self, score: float) -> str:
        """Generate actionable recommendation."""
        if score >= 0.90:
            return "No action needed. Score is reliable."
        elif score >= 0.80:
            return "Score is generally reliable. Consider longer sample for verification."
        elif score >= 0.70:
            return "Score has moderate reliability. Audio quality or duration may be affecting results."
        elif score >= 0.60:
            return "Low confidence. Recommend retesting with 5+ minutes of clear audio."
        else:
            return "Very low confidence. Score unreliable. Retest required with better audio conditions."

    # ===============================
    # OVERALL BAND WITH FEEDBACK
    # ===============================

    def score_overall_with_feedback(
        self,
        metrics: Dict,
        transcript: str,
        llm_metrics: Optional[Dict] = None,
    ) -> Dict:
        """
        Compute overall band with IELTS descriptor alignment and user feedback.
        
        If llm_metrics provided, uses LLM insights for richer feedback.
        Uses weighted average with emphasis on consistent high performance.
        Applies topic relevance and coherence penalties.
        """
        fc = self.score_fluency(metrics)
        pr = self.score_pronunciation(metrics)
        lr = self.score_lexical(metrics, llm_metrics)
        gr = self.score_grammar(metrics, llm_metrics)

        subscores = {
            "fluency_coherence": fc,
            "pronunciation": pr,
            "lexical_resource": lr,
            "grammatical_range_accuracy": gr,
        }

        # Overall calculation: Official IELTS formula (equal weight to all criteria)
        # Overall Band = (FC + PR + LR + GR) / 4
        overall = round_half((fc + pr + lr + gr) / 4.0)

        # Clamp to valid IELTS range [5.0, 9.0]
        overall = max(5.0, min(9.0, overall))

        # Get descriptors for overall band AND individual criteria
        descriptor = get_band_descriptor(overall)
        
        # Build criterion-specific descriptors from the actual criterion scores
        criterion_descriptors = {
            "fluency_coherence": get_band_descriptor(fc).get("fluency_coherence", ""),
            "pronunciation": get_band_descriptor(pr).get("pronunciation", ""),
            "lexical_resource": get_band_descriptor(lr).get("lexical_resource", ""),
            "grammatical_range_accuracy": get_band_descriptor(gr).get("grammatical_range_accuracy", ""),
        }
        
        # Enhance descriptors with actual LLM findings if available
        if llm_metrics:
            # Fluency enhancements
            if llm_metrics.get("coherence_break_count", 0) > 0:
                criterion_descriptors["fluency_coherence"] += f" {llm_metrics['coherence_break_count']} coherence breaks detected."
            if llm_metrics.get("flow_instability_present"):
                criterion_descriptors["fluency_coherence"] += " Speech flow shows instability."
            
            # Grammar enhancements
            grammar_errors = llm_metrics.get("grammar_error_count", 0)
            if grammar_errors > 0:
                criterion_descriptors["grammatical_range_accuracy"] += f" {grammar_errors} grammar error(s) identified."
            if llm_metrics.get("cascading_grammar_failure"):
                criterion_descriptors["grammatical_range_accuracy"] += " Grammar errors cascade affecting meaning."
            
            # Lexical enhancements
            word_errors = llm_metrics.get("word_choice_error_count", 0)
            adv_vocab = llm_metrics.get("advanced_vocabulary_count", 0)
            if word_errors > 0:
                criterion_descriptors["lexical_resource"] += f" {word_errors} word choice issue(s) detected."
            if adv_vocab > 0:
                criterion_descriptors["lexical_resource"] += f" {adv_vocab} advanced vocabulary use noted."
        
        # Enhance with speech quality metrics if available
        if "mean_word_confidence" in metrics or "low_confidence_ratio" in metrics:
            low_conf_ratio = metrics.get("low_confidence_ratio", 0)
            if low_conf_ratio > 0.3:
                criterion_descriptors["pronunciation"] += f" {round(low_conf_ratio*100)}% of words show low confidence."
        
        # Calculate confidence score
        band_scores = {
            "overall_band": overall,
            "criterion_bands": subscores
        }
        confidence_result = self.calculate_confidence_score(
            metrics,
            band_scores,
            llm_metrics
        )

        # Build feedback
        feedback = self._build_feedback(
            subscores, metrics, llm_metrics, transcript
        )

        return {
            "overall_band": overall,
            "criterion_bands": subscores,
            "confidence": confidence_result,
            "descriptors": descriptor,
            "criterion_descriptors": criterion_descriptors,
            "feedback": feedback,
        }

    def _build_feedback(
        self,
        subscores: Dict,
        metrics: Dict,
        llm_metrics: Optional[Dict],
        transcript: str,
    ) -> Dict[str, Any]:
        """
        Generate detailed user-facing feedback with clear strengths and weaknesses.
        
        Returns feedback for each criterion with:
        - What is good (strengths)
        - What needs improvement (weaknesses)
        - Actionable suggestions
        """
        feedback = {}

        # ============================================================
        # FLUENCY & COHERENCE FEEDBACK
        # ============================================================
        fc = subscores["fluency_coherence"]
        fluency_feedback = {
            "criterion": "Fluency & Coherence",
            "band": fc,
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }
        
        if llm_metrics:
            coherence_breaks = llm_metrics.get("coherence_break_count", 0)
            flow_unstable = llm_metrics.get("flow_instability_present", False)
            
            # Strengths
            if fc >= 8.0:
                fluency_feedback["strengths"].append("Excellent fluency - speech flows naturally")
                fluency_feedback["strengths"].append("Minimal hesitation and repetition")
            elif fc >= 7.0:
                fluency_feedback["strengths"].append("Good fluency - able to sustain speech")
                fluency_feedback["strengths"].append("Generally smooth delivery with minor pauses")
            elif fc >= 6.0:
                fluency_feedback["strengths"].append("Able to produce extended speech")
                if coherence_breaks == 0:
                    fluency_feedback["strengths"].append("Ideas are logically connected")
            else:
                if coherence_breaks == 0:
                    fluency_feedback["strengths"].append("Speech stays on topic")
            
            # Weaknesses
            if coherence_breaks > 0:
                fluency_feedback["weaknesses"].append(f"Coherence breaks detected ({coherence_breaks}) - ideas not always clearly connected")
            if flow_unstable:
                fluency_feedback["weaknesses"].append("Speech flow is inconsistent - difficulty finding words")
            if fc < 7.0:
                wpm = metrics.get("wpm", 0)
                if wpm < 80:
                    fluency_feedback["weaknesses"].append(f"Speech rate is slow ({wpm} WPM) - consider speaking at natural pace")
            if fc < 6.0:
                long_pauses = metrics.get("long_pauses_per_min", 0)
                repetition = metrics.get("repetition_ratio", 0)
                if long_pauses > 2.5:
                    fluency_feedback["weaknesses"].append(f"Frequent long pauses ({long_pauses}/min) - prepare answers more thoroughly")
                if repetition > 0.1:
                    fluency_feedback["weaknesses"].append(f"Excessive repetition (ratio: {repetition}) - vary your vocabulary and structures")
            
            # Suggestions
            if coherence_breaks > 0:
                fluency_feedback["suggestions"].append("Use transition words (furthermore, in addition, however) to connect ideas")
                fluency_feedback["suggestions"].append("Practice organizing thoughts before speaking")
            if flow_unstable:
                fluency_feedback["suggestions"].append("Take pauses to think, but avoid very long silences")
                fluency_feedback["suggestions"].append("Record yourself and listen for natural flow")
            if fc < 7.5:
                fluency_feedback["suggestions"].append("Practice extended speaking (2-3 minutes) on various topics")
        
        feedback["fluency_coherence"] = fluency_feedback

        # ============================================================
        # PRONUNCIATION FEEDBACK
        # ============================================================
        pr = subscores["pronunciation"]
        pronunciation_feedback = {
            "criterion": "Pronunciation",
            "band": pr,
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }
        
        mean_conf = metrics.get("mean_word_confidence", 0.7)
        low_conf_ratio = metrics.get("low_confidence_ratio", 0)
        
        # Strengths
        if pr >= 8.0:
            pronunciation_feedback["strengths"].append("Clear pronunciation - easily understood")
            pronunciation_feedback["strengths"].append("Consistent phonological control")
            pronunciation_feedback["strengths"].append("Natural stress and intonation patterns")
        elif pr >= 7.0:
            pronunciation_feedback["strengths"].append("Generally clear pronunciation")
            pronunciation_feedback["strengths"].append("Minor accent variations don't affect understanding")
        elif pr >= 6.0:
            pronunciation_feedback["strengths"].append("Understandable pronunciation")
            if mean_conf > 0.75:
                pronunciation_feedback["strengths"].append("Most words are clearly articulated")
        else:
            if low_conf_ratio < 0.4:
                pronunciation_feedback["strengths"].append("Some words are clearly pronounced")
        
        # Weaknesses
        if pr < 8.0 and low_conf_ratio > 0.3:
            pronunciation_feedback["weaknesses"].append(f"Low word clarity ({round(low_conf_ratio*100)}% unclear words)")
            pronunciation_feedback["weaknesses"].append("Mispronunciation of certain words affects understanding")
        if pr < 7.0 and mean_conf < 0.75:
            pronunciation_feedback["weaknesses"].append(f"Average word clarity is low ({round(mean_conf*100)}%) - enunciation needs work")
        if pr < 6.0:
            pronunciation_feedback["weaknesses"].append("Pronunciation issues make speech difficult to understand")
            pronunciation_feedback["weaknesses"].append("Inconsistent control over phonological features")
        if metrics.get("is_monotone", False):
            pronunciation_feedback["weaknesses"].append("Lack of intonation variation - speech sounds monotone")
        
        # Suggestions
        if low_conf_ratio > 0.2:
            pronunciation_feedback["suggestions"].append("Focus on articulation - speak more clearly and deliberately")
            pronunciation_feedback["suggestions"].append("Record yourself and compare with native speaker pronunciation")
        if metrics.get("is_monotone", False):
            pronunciation_feedback["suggestions"].append("Practice varying pitch and stress - listen to English music and podcasts")
            pronunciation_feedback["suggestions"].append("Mark stress patterns in words you struggle with")
        if pr < 7.0:
            pronunciation_feedback["suggestions"].append("Use a pronunciation app (Forvo, Google Translate) to check individual words")
            pronunciation_feedback["suggestions"].append("Watch English movies and imitate natural pronunciation patterns")
        
        feedback["pronunciation"] = pronunciation_feedback

        # ============================================================
        # LEXICAL RESOURCE FEEDBACK
        # ============================================================
        lr = subscores["lexical_resource"]
        lexical_feedback = {
            "criterion": "Lexical Resource",
            "band": lr,
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }
        
        if llm_metrics:
            adv_vocab = llm_metrics.get("advanced_vocabulary_count", 0)
            idioms = llm_metrics.get("idiomatic_collocation_count", 0)
            word_errors = llm_metrics.get("word_choice_error_count", 0)
            vocab_richness = metrics.get("vocab_richness", 0)
            
            # Strengths
            if lr >= 8.0:
                lexical_feedback["strengths"].append("Wide and flexible vocabulary range")
                if adv_vocab > 0:
                    lexical_feedback["strengths"].append(f"Uses {adv_vocab} advanced vocabulary items effectively")
                if idioms > 0:
                    lexical_feedback["strengths"].append(f"Employs {idioms} idiomatic expressions naturally")
            elif lr >= 7.0:
                lexical_feedback["strengths"].append("Good vocabulary range")
                if adv_vocab > 0:
                    lexical_feedback["strengths"].append(f"Uses {adv_vocab} advanced items to show sophistication")
                if idioms > 0:
                    lexical_feedback["strengths"].append(f"Includes {idioms} idiomatic expressions")
            elif lr >= 6.0:
                lexical_feedback["strengths"].append("Adequate vocabulary for topic discussion")
                if vocab_richness > 0.45:
                    lexical_feedback["strengths"].append("Good vocabulary diversity")
            else:
                if vocab_richness > 0.35:
                    lexical_feedback["strengths"].append("Attempts varied vocabulary")
            
            # Weaknesses
            if word_errors > 0:
                lexical_feedback["weaknesses"].append(f"Word choice errors ({word_errors}) - using wrong words or wrong connotation")
            if lr < 7.0 and adv_vocab == 0:
                lexical_feedback["weaknesses"].append("Limited use of advanced vocabulary")
            if lr < 6.0:
                lexical_feedback["weaknesses"].append("Limited vocabulary range")
                lexical_feedback["weaknesses"].append("Difficulty expressing ideas on unfamiliar topics")
                if vocab_richness < 0.4:
                    lexical_feedback["weaknesses"].append("Excessive repetition of the same words")
            if idioms == 0 and lr >= 6.0:
                lexical_feedback["weaknesses"].append("Does not use idiomatic expressions or collocations")
            
            # Suggestions
            if word_errors > 0:
                lexical_feedback["suggestions"].append("Learn precise word meanings and usage contexts")
                lexical_feedback["suggestions"].append("Use a thesaurus and corpus (e.g., English Corpora) to check word usage")
            if lr < 7.5:
                lexical_feedback["suggestions"].append("Learn 10-15 new advanced words/phrases per week")
                lexical_feedback["suggestions"].append("Study idiomatic expressions in context")
            if vocab_richness < 0.45:
                lexical_feedback["suggestions"].append("Paraphrase - express the same idea using different words")
                lexical_feedback["suggestions"].append("Practice describing topics using synonyms")
        else:
            # Without LLM metrics
            if lr >= 8.0:
                lexical_feedback["strengths"].append("Excellent vocabulary range and flexibility")
            elif lr >= 7.0:
                lexical_feedback["strengths"].append("Good vocabulary with variety")
            elif lr >= 6.0:
                lexical_feedback["strengths"].append("Adequate vocabulary for discussion")
            else:
                lexical_feedback["strengths"].append("Some vocabulary use shown")
                lexical_feedback["weaknesses"].append("Limited vocabulary range needs expansion")
        
        feedback["lexical_resource"] = lexical_feedback

        # ============================================================
        # GRAMMATICAL RANGE & ACCURACY FEEDBACK
        # ============================================================
        gr = subscores["grammatical_range_accuracy"]
        grammar_feedback = {
            "criterion": "Grammatical Range & Accuracy",
            "band": gr,
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }
        
        if llm_metrics:
            grammar_errors = llm_metrics.get("grammar_error_count", 0)
            complex_structures = llm_metrics.get("complex_structures_attempted", 0)
            complex_accuracy = llm_metrics.get("complex_structure_accuracy_ratio")
            cascading_failure = llm_metrics.get("cascading_grammar_failure", False)
            
            # Strengths
            if gr >= 8.0:
                grammar_feedback["strengths"].append("Excellent grammatical control")
                grammar_feedback["strengths"].append("Wide range of structures used accurately")
                if complex_structures > 0 and complex_accuracy == 1.0:
                    grammar_feedback["strengths"].append("Complex structures handled accurately")
            elif gr >= 7.0:
                grammar_feedback["strengths"].append("Good grammatical control")
                grammar_feedback["strengths"].append("Mostly accurate sentence structures")
                if complex_structures > 0:
                    grammar_feedback["strengths"].append("Attempts complex structures")
            elif gr >= 6.0:
                grammar_feedback["strengths"].append("Adequate grammatical control")
                if grammar_errors <= 2:
                    grammar_feedback["strengths"].append("Manages basic and some complex structures")
            else:
                if grammar_errors < 5:
                    grammar_feedback["strengths"].append("Basic sentence formation demonstrated")
            
            # Weaknesses
            if grammar_errors > 0:
                grammar_feedback["weaknesses"].append(f"Grammar errors found ({grammar_errors}) - affects clarity at times")
            if cascading_failure:
                grammar_feedback["weaknesses"].append("Grammar errors compound - meaning becomes unclear")
            if gr < 7.0 and complex_structures > 0 and complex_accuracy and complex_accuracy < 0.7:
                grammar_feedback["weaknesses"].append("Complex structures attempted but often inaccurate")
            if gr < 6.0:
                grammar_feedback["weaknesses"].append("Limited range of grammatical structures")
                grammar_feedback["weaknesses"].append("Frequent grammatical errors affect meaning")
            if gr < 7.0 and complex_structures == 0:
                grammar_feedback["weaknesses"].append("Primarily uses simple sentences - limited complexity")
            
            # Suggestions
            if grammar_errors > 0:
                grammar_feedback["suggestions"].append("Review common grammar errors identified in your speech")
                grammar_feedback["suggestions"].append(f"Focus on tense consistency and subject-verb agreement")
            if complex_structures == 0 or (complex_accuracy and complex_accuracy < 0.7):
                grammar_feedback["suggestions"].append("Practice using complex structures (relative clauses, conditionals, etc.)")
                grammar_feedback["suggestions"].append("Start with written practice, then transfer to speaking")
            if gr < 7.0:
                grammar_feedback["suggestions"].append("Study one complex structure per week (e.g., subordinate clauses)")
                grammar_feedback["suggestions"].append("Record yourself and check for grammatical accuracy")
                grammar_feedback["suggestions"].append("Practice combining simple sentences into complex ones")
        else:
            # Without LLM metrics
            if gr >= 8.0:
                grammar_feedback["strengths"].append("Excellent range and accuracy of grammatical structures")
            elif gr >= 7.0:
                grammar_feedback["strengths"].append("Good control of various grammatical structures")
            elif gr >= 6.0:
                grammar_feedback["strengths"].append("Adequate grammatical control with some range")
            else:
                grammar_feedback["strengths"].append("Basic grammatical control shown")
                grammar_feedback["weaknesses"].append("Limited range and accuracy needs development")
        
        feedback["grammatical_range_accuracy"] = grammar_feedback

        # ============================================================
        # OVERALL ASSESSMENT
        # ============================================================
        overall = round_half(
            (subscores["fluency_coherence"]
            + subscores["pronunciation"]
            + subscores["lexical_resource"]
            + subscores["grammatical_range_accuracy"]) / 4
        )
        
        overall_feedback = {
            "overall_band": overall,
            "summary": self._get_overall_summary(overall),
            "next_band_tips": self._get_next_band_tips(overall, subscores)
        }
        
        feedback["overall"] = overall_feedback
        
        return feedback
    
    def _get_overall_summary(self, overall: float) -> str:
        """Get summary text for overall band."""
        if overall >= 8.0:
            return "You demonstrate strong command of English with fluent delivery, varied vocabulary, and excellent grammatical control. Continue refining your pronunciation and exploring more advanced expressions."
        elif overall >= 7.0:
            return "You show good English proficiency with generally fluent speech, adequate range of vocabulary and structures. Focus on expanding lexical range and reducing grammatical errors."
        elif overall >= 6.0:
            return "You have adequate English skills to discuss topics with some range and generally clear communication. Work on fluency, vocabulary diversity, and grammatical accuracy to progress further."
        elif overall >= 5.5:
            return "You can manage basic conversation but need improvement in fluency, vocabulary range, and grammatical accuracy. Consistent practice in all areas will help you advance."
        else:
            return "You have some English ability but need significant improvement in fluency, vocabulary, and grammar. Consider focused practice on foundational skills."
    
    def _get_next_band_tips(self, current: float, subscores: Dict) -> Dict[str, str]:
        """Get specific tips to reach the next band level."""
        tips = {}
        
        if current < 9.0:
            next_band = round_half(current + 0.5)
            
            # Find weakest criterion
            weakest_criterion = min(subscores.items(), key=lambda x: x[1])[0]
            
            if weakest_criterion == "fluency_coherence":
                tips["focus"] = "Improve fluency and coherence to reach band " + str(next_band)
                tips["action"] = "Practice extended speaking on various topics. Use transition words and plan your responses."
            elif weakest_criterion == "pronunciation":
                tips["focus"] = "Improve pronunciation clarity to reach band " + str(next_band)
                tips["action"] = "Work on articulation and intonation. Use pronunciation apps and compare with native speakers."
            elif weakest_criterion == "lexical_resource":
                tips["focus"] = "Expand vocabulary and use advanced words to reach band " + str(next_band)
                tips["action"] = "Learn new words in context, practice using synonyms, and study idiomatic expressions."
            else:  # grammatical_range_accuracy
                tips["focus"] = "Improve grammar range and accuracy to reach band " + str(next_band)
                tips["action"] = "Master complex sentence structures and ensure accurate tense and agreement."
        
        return tips

    def build_timestamped_rubric_feedback(
        self,
        subscores: Dict,
        metrics: Dict,
        word_timestamps: List[Dict],
        llm_annotations: Optional[Any] = None,
    ) -> Dict:
        """
        Build feedback grouped by IELTS rubric with timestamped segments.
        
        Args:
            subscores: Band scores for each criterion
            metrics: Raw metrics dictionary
            word_timestamps: List of word timestamp dicts from audio_analysis
            llm_annotations: Optional LLMSpeechAnnotations object
            
        Returns:
            Dict with timestamped feedback grouped by rubric category
        """
        from .llm_processing import map_spans_to_timestamps
        
        timestamped_spans = []
        if llm_annotations:
            # Collect all spans from LLM annotations
            all_spans = []
            all_spans.extend(llm_annotations.coherence_breaks)
            all_spans.extend(llm_annotations.word_choice_errors)
            all_spans.extend(llm_annotations.grammar_errors)
            all_spans.extend(llm_annotations.meaning_blocking_grammar_errors)
            all_spans.extend(llm_annotations.advanced_vocabulary)
            all_spans.extend(llm_annotations.idiomatic_or_collocational_use)
            all_spans.extend(llm_annotations.clause_completion_issues)
            all_spans.extend(llm_annotations.complex_structures_attempted)
            all_spans.extend(llm_annotations.complex_structures_accurate)
            all_spans.extend(llm_annotations.register_mismatch)
            all_spans.extend(llm_annotations.successful_paraphrase)
            all_spans.extend(llm_annotations.failed_paraphrase)
            
            # Map to timestamps (need raw_transcript from metrics)
            transcript = metrics.get("raw_transcript", "")
            if transcript and word_timestamps:
                timestamped_spans = map_spans_to_timestamps(
                    transcript,
                    all_spans,
                    word_timestamps
                )
        
        # Extract pronunciation issues from low-confidence words
        pronunciation_issues = []
        for word_data in word_timestamps:
            if word_data.get("confidence", 1.0) < 0.70:
                pronunciation_issues.append({
                    "word": word_data.get("word", ""),
                    "start_sec": word_data.get("start", 0.0),
                    "end_sec": word_data.get("end", 0.0),
                    "confidence": word_data.get("confidence", 0.0),
                })
        
        # Group timestamped spans by category
        grammar_issues = [s for s in timestamped_spans if s.label in [
            "grammar_error", "meaning_blocking_grammar_error", "clause_completion_issue"
        ]]
        
        lexical_issues = [s for s in timestamped_spans if s.label in [
            "word_choice_error"
        ]]
        
        lexical_highlights = [s for s in timestamped_spans if s.label in [
            "advanced_vocabulary", "idiomatic_or_collocational_use", "successful_paraphrase"
        ]]
        
        fluency_issues = [s for s in timestamped_spans if s.label in [
            "coherence_break"
        ]]
        
        return {
            "fluency_coherence": {
                "band": subscores.get("fluency_coherence", 7.0),
                "issues": [
                    {
                        "type": issue.label,
                        "segment": issue.text,
                        "timestamps": {
                            "start_sec": issue.start_sec,
                            "end_sec": issue.end_sec,
                            "display": issue.timestamp_mmss,
                        },
                        "feedback": f"Coherence break detected. Connect ideas more smoothly."
                    }
                    for issue in fluency_issues
                ]
            },
            "pronunciation": {
                "band": subscores.get("pronunciation", 7.0),
                "unclear_words": [
                    {
                        "word": issue["word"],
                        "timestamps": {
                            "start_sec": issue["start_sec"],
                            "end_sec": issue["end_sec"],
                            "display": f"{int(issue['start_sec'])//60}:{int(issue['start_sec'])%60:02d}",
                        },
                        "confidence": round(issue["confidence"], 2),
                        "feedback": "Enunciate more clearly"
                    }
                    for issue in pronunciation_issues
                ]
            },
            "lexical_resource": {
                "band": subscores.get("lexical_resource", 7.0),
                "issues": [
                    {
                        "type": issue.label,
                        "word": issue.text,
                        "timestamps": {
                            "start_sec": issue.start_sec,
                            "end_sec": issue.end_sec,
                            "display": issue.timestamp_mmss,
                        },
                        "feedback": "Word choice could be improved"
                    }
                    for issue in lexical_issues
                ],
                "highlights": [
                    {
                        "type": highlight.label,
                        "phrase": highlight.text,
                        "timestamps": {
                            "start_sec": highlight.start_sec,
                            "end_sec": highlight.end_sec,
                            "display": highlight.timestamp_mmss,
                        },
                        "feedback": "Excellent vocabulary use"
                    }
                    for highlight in lexical_highlights
                ]
            },
            "grammatical_accuracy": {
                "band": subscores.get("grammatical_range_accuracy", 7.0),
                "issues": [
                    {
                        "type": issue.label,
                        "segment": issue.text,
                        "timestamps": {
                            "start_sec": issue.start_sec,
                            "end_sec": issue.end_sec,
                            "display": issue.timestamp_mmss,
                        },
                        "severity": "high" if "meaning_blocking" in issue.label else "low",
                        "feedback": "Grammar error - see feedback for correction"
                    }
                    for issue in grammar_issues
                ]
            }
        }

    def score_overall(self, metrics: Dict) -> Dict:
        """Legacy method for backwards compatibility."""
        return self.score_overall_with_feedback(metrics, "", None)


# ===============================================
# PUBLIC ENTRY POINT (WITH OPTIONAL LLM)
# ===============================================

def score_ielts_speaking(
    metrics: Dict, transcript: str = "", use_llm: bool = False
) -> Dict:
    """
    Score IELTS speaking from metrics (and optionally LLM analysis).
    
    Args:
        metrics: dict with acoustic/linguistic metrics
        transcript: raw transcript (required if use_llm=True)
        use_llm: whether to use LLM for semantic evaluation
    
    Returns:
        dict with overall_band, criterion_bands, descriptors, and feedback
        
    Notes:
        LLM failures degrade gracefully - metrics-only scoring is used as fallback
    """
    from src.utils.logging_config import logger
    from src.utils.exceptions import LLMProcessingError
    
    scorer = IELTSBandScorer()
    llm_metrics = None

    if use_llm and transcript:
        try:
            from .llm_processing import extract_llm_annotations, aggregate_llm_metrics
            
            llm_annotations = extract_llm_annotations(transcript)
            llm_metrics = aggregate_llm_metrics(llm_annotations)
            logger.info("LLM scoring successful")
        except LLMProcessingError as e:
            logger.warning(f"LLM scoring failed, falling back to metrics-only: {e.message}")
        except Exception as e:
            logger.warning(f"Unexpected error during LLM scoring, using metrics-only: {str(e)}")

    result = scorer.score_overall_with_feedback(metrics, transcript, llm_metrics)
    
    # DEBUG: Log the actual criterion scores
    cb = result.get("criterion_bands", {})
    logger.info(f"[BAND_SCORES_DEBUG] Fluency={cb.get('fluency_coherence')} | Pron={cb.get('pronunciation')} | Lex={cb.get('lexical_resource')} | Gram={cb.get('grammatical_range_accuracy')} | Overall={result.get('overall_band')}")
    
    return result
