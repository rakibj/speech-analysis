# src/stage1_constraints.py

from typing import Dict, List


# ======================================================
# Utility
# ======================================================
def _confidence(reasons: List[str]) -> str:
    if len(reasons) >= 2:
        return "high"
    return "medium"


# ======================================================
# Fluency & Coherence (IELTS-style)
# ======================================================
def fluency_constraints(a: Dict) -> Dict:
    """
    Fluency rubric aligned with official scoring thresholds.
    Uses same logic as score_fluency() in ielts_band_scorer.py.
    """

    wpm = a.get("wpm", 0)
    long_pauses = a.get("long_pauses_per_min", 0)
    pause_var = a.get("pause_variability", 0)
    repetition = a.get("repetition_ratio", 0)

    # Band 8.5: wpm >= 150 and long_pauses <= 0.5 and pause_var <= 0.40 and repetition <= 0.035
    if wpm >= 150 and long_pauses <= 0.5 and pause_var <= 0.40 and repetition <= 0.035:
        return {
            "allowed_bands": [8, 9],
            "confidence": "high",
            "reasons": ["excellent fluency with minimal pauses and strong rhythm control"],
        }

    # Band 8.0: wpm >= 130 and long_pauses <= 1.0 and pause_var <= 0.60 and repetition <= 0.050
    if wpm >= 130 and long_pauses <= 1.0 and pause_var <= 0.60 and repetition <= 0.050:
        return {
            "allowed_bands": [8, 9],
            "confidence": "high",
            "reasons": ["very fluent with excellent pacing and minimal hesitation"],
        }

    # Band 7.5: wpm >= 110 and long_pauses <= 1.5 and pause_var <= 0.75 and repetition <= 0.065
    if wpm >= 110 and long_pauses <= 1.5 and pause_var <= 0.75 and repetition <= 0.065:
        return {
            "allowed_bands": [7, 8],
            "confidence": "high",
            "reasons": ["fluent delivery with occasional natural pauses"],
        }

    # Band 7.0: wpm >= 90 and long_pauses <= 2.0 and pause_var <= 1.0
    if wpm >= 90 and long_pauses <= 2.0 and pause_var <= 1.0:
        return {
            "allowed_bands": [7, 8],
            "confidence": "high",
            "reasons": ["generally fluent with some natural hesitation"],
        }

    # Band 6.5: wpm >= 80 and long_pauses <= 2.5 and pause_var <= 1.2
    if wpm >= 80 and long_pauses <= 2.5 and pause_var <= 1.2:
        return {
            "allowed_bands": [6, 7],
            "confidence": "high",
            "reasons": ["moderate fluency with noticeable pauses"],
        }

    # Band 6.0: wpm >= 70 and long_pauses <= 3.0
    if wpm >= 70 and long_pauses <= 3.0:
        return {
            "allowed_bands": [6, 7],
            "confidence": "high",
            "reasons": ["basic fluency with frequent hesitation"],
        }

    # Band 5.5: long_pauses >= 3.0 or pause_var >= 1.3
    # Note: pause_var = 0 is often a data issue, but long_pauses >= 3.0 is clear signal for 5.5
    if long_pauses >= 3.0 or pause_var >= 1.3:
        return {
            "allowed_bands": [5, 6],
            "confidence": "high",
            "reasons": ["notable fluency issues with significant pauses and variability"],
        }
    
    # Default to Band 5.5 for very low WPM or missing data
    if wpm < 70:
        return {
            "allowed_bands": [5, 6],
            "confidence": "high",
            "reasons": ["very slow speech rate indicates fluency issues"],
        }
    
    # Final fallback
    return {
        "allowed_bands": [5, 6],
        "confidence": "high",
        "reasons": ["minimal fluency indicators"],
    }


# ======================================================
# Pronunciation (IELTS-style)
# ======================================================
def pronunciation_constraints(a: Dict) -> Dict:
    """
    Pronunciation rubric aligned with official scoring thresholds.
    Uses same logic as score_pronunciation() in ielts_band_scorer.py.
    """

    mean_conf = a.get("mean_word_confidence", 0)
    low_conf_ratio = a.get("low_confidence_ratio", 0)

    # Band 8.5: mean_conf >= 0.92 and low_conf_ratio <= 0.08
    if mean_conf >= 0.92 and low_conf_ratio <= 0.08:
        return {
            "allowed_bands": [8, 9],
            "confidence": "high",
            "reasons": ["near-perfect pronunciation with excellent intelligibility"],
        }

    # Band 8.0: mean_conf >= 0.89 and low_conf_ratio <= 0.12
    if mean_conf >= 0.89 and low_conf_ratio <= 0.12:
        return {
            "allowed_bands": [8, 9],
            "confidence": "high",
            "reasons": ["consistently clear and intelligible pronunciation"],
        }

    # Band 7.5: mean_conf >= 0.87 and low_conf_ratio <= 0.17
    if mean_conf >= 0.87 and low_conf_ratio <= 0.17:
        return {
            "allowed_bands": [7, 8],
            "confidence": "high",
            "reasons": ["very clear pronunciation with rare intelligibility lapses"],
        }

    # Band 7.0: mean_conf >= 0.84 and low_conf_ratio <= 0.20
    if mean_conf >= 0.84 and low_conf_ratio <= 0.20:
        return {
            "allowed_bands": [7, 8],
            "confidence": "high",
            "reasons": ["clear pronunciation with occasional intelligibility lapses"],
        }

    # Band 6.5: mean_conf >= 0.80 and low_conf_ratio <= 0.25
    if mean_conf >= 0.80 and low_conf_ratio <= 0.25:
        return {
            "allowed_bands": [6, 7],
            "confidence": "high",
            "reasons": ["generally clear with noticeable intelligibility issues"],
        }

    # Band 6.0: mean_conf >= 0.75 and low_conf_ratio <= 0.32
    if mean_conf >= 0.75 and low_conf_ratio <= 0.32:
        return {
            "allowed_bands": [6, 7],
            "confidence": "high",
            "reasons": ["moderately clear with some intelligibility problems"],
        }

    # Band 5.5: low_conf_ratio > 0.32
    if low_conf_ratio > 0.32:
        return {
            "allowed_bands": [5, 6],
            "confidence": "high",
            "reasons": ["frequent intelligibility issues require listener effort"],
        }
    
    # Fallback for very low confidence (data issue or genuinely poor)
    if mean_conf < 0.75:
        return {
            "allowed_bands": [5, 6],
            "confidence": "high",
            "reasons": ["low average confidence indicates pronunciation issues"],
        }
    
    # Default fallback
    return {
        "allowed_bands": [6, 7],
        "confidence": "high",
        "reasons": ["generally clear with intelligibility lapses"],
    }


# ======================================================
# Public Entry Point
# ======================================================
def generate_constraints(analysis: Dict) -> Dict:
    """
    Stage-1 IELTS rubric constraints.
    Deterministic, examiner-faithful, LLM-safe.
    """

    return {
        "rubric_estimations": {
            "fluency_coherence": fluency_constraints(analysis),
            "pronunciation": pronunciation_constraints(analysis),
        }
    }
