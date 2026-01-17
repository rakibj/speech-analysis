"""
IELTS Speaking Band Scorer v4.2 (REVISED)

Fixes:
- Stronger low/high separation
- Less score clustering at 7.5
- Flow clarity rewarded properly
- Error density penalized
"""

from typing import Dict


# ------------------------------------------------------
# Utilities
# ------------------------------------------------------

def round_half(score: float) -> float:
    return round(score * 2) / 2


# ------------------------------------------------------
# V4.2 SCORER
# ------------------------------------------------------

class IELTSBandScorer:

    # ===============================
    # FLUENCY & COHERENCE
    # ===============================

    def score_fluency(self, m: Dict) -> float:
        if not m.get("topic_relevance", True):
            return 4.5

        if m.get("listener_effort_high", False):
            return 6.0

        coherence_breaks = m.get("coherence_break_count", 0)
        clause_issues = m.get("clause_completion_issue_count", 0)
        flow_instability = m.get("flow_instability_present", False)

        # Hard penalties
        if coherence_breaks >= 3:
            return 6.0

        if flow_instability:
            return 6.5

        # Mid control
        if coherence_breaks == 2:
            return 6.5

        if coherence_breaks == 1 or clause_issues > 0:
            return 7.0

        # High fluency requires zero strain
        if coherence_breaks == 0 and clause_issues == 0:
            return 8.0

        return 7.5


    # ===============================
    # LEXICAL RESOURCE
    # ===============================

    def score_lexical(self, m: Dict) -> float:
        word_choice_errors = m.get("word_choice_error_count", 0)
        adv_vocab = m.get("advanced_vocabulary_count", 0)
        idioms = m.get("idiomatic_collocation_count", 0)

        failed_para = m.get("failed_paraphrase_count", 0)
        success_para = m.get("successful_paraphrase_count", 0)
        para_ratio = m.get("paraphrase_success_ratio")

        # Clear low-band signal
        if word_choice_errors >= 7:
            return 6.0

        if failed_para > success_para:
            return 6.5

        # Baseline
        score = 7.0

        # Penalize lexical thinness
        if adv_vocab == 0 and word_choice_errors >= 3:
            score = 6.5

        # Band 7+ control
        if para_ratio is not None and para_ratio >= 0.6:
            score = 7.5

        # Precision > decoration
        if word_choice_errors <= 2 and adv_vocab >= 2:
            score = max(score, 7.5)

        # Idioms only unlock, never gate
        if idioms >= 1 and word_choice_errors <= 1:
            score = max(score, 8.0)

        return score


    # ===============================
    # GRAMMATICAL RANGE & ACCURACY
    # ===============================

    def score_grammar(self, m: Dict) -> float:
        if m.get("cascading_grammar_failure", False):
            return 6.0

        meaning_block_ratio = m.get("meaning_blocking_error_ratio", 0.0)
        grammar_errors = m.get("grammar_error_count", 0)

        # Meaning disruption
        if meaning_block_ratio >= 0.30:
            return 5.5

        # Error density matters
        if grammar_errors >= 7:
            return 6.5

        score = 7.0

        ratio = m.get("complex_structure_accuracy_ratio")

        if ratio is not None:
            if ratio >= 0.75:
                score = 7.5
            if ratio >= 0.85 and meaning_block_ratio < 0.10:
                score = 8.0

        return score


    # ===============================
    # PRONUNCIATION
    # ===============================

    def score_pronunciation(self, m: Dict) -> float:
        if m.get("listener_effort_high", False):
            return 6.0

        if m.get("flow_instability_present", False):
            return 6.5

        return 7.5


    # ===============================
    # OVERALL BAND
    # ===============================

    def score_overall(self, m: Dict) -> Dict:
        fc = self.score_fluency(m)
        lr = self.score_lexical(m)
        gr = self.score_grammar(m)
        pr = self.score_pronunciation(m)

        subscores = {
            "fluency_coherence": fc,
            "lexical_resource": lr,
            "grammatical_range_accuracy": gr,
            "pronunciation": pr,
        }

        avg = sum(subscores.values()) / 4
        overall = round_half(avg)

        # Hard cap if any criterion is weak
        if min(subscores.values()) <= 5.5:
            overall = min(overall, 6.0)

        # Band 9 remains extremely strict
        if overall >= 9.0 and not all(v >= 8.5 for v in subscores.values()):
            overall = 8.5

        return {
            "overall_band": overall,
            "criterion_bands": subscores,
        }


# ------------------------------------------------------
# PUBLIC ENTRY POINT
# ------------------------------------------------------

def score_ielts_speaking(llm_metrics: Dict) -> Dict:
    """
    llm_metrics = output of your LLM-only aggregation step
    """
    scorer = IELTSBandScorer()
    return scorer.score_overall(llm_metrics)
