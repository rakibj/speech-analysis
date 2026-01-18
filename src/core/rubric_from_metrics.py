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
    Examiner logic:
    - High bands are lost only if listener effort is noticeable
    - Natural fillers and rhythm are acceptable
    - One dominant breakdown matters more than many small issues
    
    Calibrated thresholds based on actual IELTS band samples:
    - Band 5-5.5: wpm ~89, long_pauses ~2.1, pause_var ~0.9
    - Band 7: wpm ~109, long_pauses ~1.4, pause_var ~0.66
    - Band 8-8.5: wpm ~198, long_pauses ~0, pause_var ~0.14
    """

    reasons: List[str] = []

    wpm = a.get("wpm", 0)
    long_pauses = a.get("long_pauses_per_min", 0)
    fillers = a.get("fillers_per_min", 0)
    repetition = a.get("repetition_ratio", 0)
    pause_var = a.get("pause_variability", 0)

    # --------------------------------------------------
    # EXCELLENT FLUENCY → Band 8–9 possible
    # High WPM + minimal long pauses + low pause variability
    # --------------------------------------------------
    if (
        wpm >= 170
        and long_pauses <= 0.5
        and pause_var <= 0.25
        and repetition <= 0.035
    ):
        return {
            "allowed_bands": [8, 9],
            "confidence": "high",
            "reasons": [
                "fast, smooth delivery with excellent rhythm control"
            ],
        }

    # --------------------------------------------------
    # VERY GOOD FLUENCY → Band 7–8 possible
    # Good WPM + low long pauses + moderate pause consistency
    # --------------------------------------------------
    if (
        wpm >= 100
        and long_pauses <= 1.8
        and pause_var <= 0.75
        and repetition <= 0.065
    ):
        return {
            "allowed_bands": [7, 8],
            "confidence": "high",
            "reasons": [
                "fluent delivery with occasional natural pauses"
            ],
        }

    # --------------------------------------------------
    # MODERATE FLUENCY → Band 5–6 possible
    # Lower WPM + noticeable long pauses + high variability
    # --------------------------------------------------
    if (
        long_pauses >= 2.0
        or pause_var >= 0.9
        or (repetition >= 0.06 and pause_var >= 0.7)
    ):
        return {
            "allowed_bands": [5, 6],
            "confidence": "high",
            "reasons": [
                "noticeable fluency breakdown with listener effort required"
            ],
        }

    # --------------------------------------------------
    # DEFAULT IELTS ZONE → Band 6–7
    # --------------------------------------------------
    return {
        "allowed_bands": [6, 7],
        "confidence": "high",
        "reasons": [
            "generally fluent with some natural hesitation"
        ],
    }


# ======================================================
# Pronunciation (IELTS-style)
# ======================================================
def pronunciation_constraints(a: Dict) -> Dict:
    """
    Examiner logic:
    - Pronunciation only caps bands if intelligibility suffers
    - Accent and monotony do NOT cap bands
    
    Calibrated thresholds based on actual IELTS band samples:
    - Band 5-5.5: mean_conf ~0.839, low_conf_ratio ~0.223
    - Band 7: mean_conf ~0.871, low_conf_ratio ~0.169
    - Band 8-8.5: mean_conf ~0.905, low_conf_ratio ~0.101
    """

    mean_conf = a.get("mean_word_confidence", 0)
    low_conf_ratio = a.get("low_confidence_ratio", 0)

    # --------------------------------------------------
    # EXCELLENT PRONUNCIATION → Band 8–9 possible
    # High mean confidence + very few low-confidence words
    # --------------------------------------------------
    if mean_conf >= 0.89 and low_conf_ratio <= 0.12:
        return {
            "allowed_bands": [8, 9],
            "confidence": "high",
            "reasons": [
                "consistently clear and intelligible pronunciation"
            ],
        }

    # --------------------------------------------------
    # VERY GOOD PRONUNCIATION → Band 7–8 possible
    # Good mean confidence + moderate low-confidence ratio
    # --------------------------------------------------
    if mean_conf >= 0.85 and low_conf_ratio <= 0.20:
        return {
            "allowed_bands": [7, 8],
            "confidence": "high",
            "reasons": [
                "clear pronunciation with minor intelligibility lapses"
            ],
        }

    # --------------------------------------------------
    # INTELLIGIBILITY PROBLEMS → cannot exceed Band 6
    # Many unclear words impacting listener comprehension
    # --------------------------------------------------
    if low_conf_ratio >= 0.35:
        return {
            "allowed_bands": [5, 6],
            "confidence": "high",
            "reasons": [
                "frequent intelligibility issues require listener effort"
            ],
        }

    # --------------------------------------------------
    # DEFAULT IELTS ZONE → Band 6–7
    # --------------------------------------------------
    return {
        "allowed_bands": [6, 7],
        "confidence": "high",
        "reasons": [
            "generally clear with minor intelligibility lapses"
        ],
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
