"""
config.py

Central configuration file for the speech fluency analysis system.

This file defines:
- Detection thresholds (fillers, pauses, stutters)
- Scoring weights and limits
- Context-specific tolerances (conversation vs presentation)
- Readiness criteria and benchmarking assumptions

⚠️ IMPORTANT:
- All numeric values here directly affect scores and verdicts.
- Changing values WILL change user-facing results.
- Treat this file as product policy, not just engineering config.
"""

# ============================================================
# FILLER & STUTTER DETECTION CONFIGURATION
# ============================================================

# Mapping from raw phoneme labels (from wav2vec / CTC output)
# to normalized human-readable filler text.
#
# Example:
#   raw phoneme "MM" or "NN" → perceived as "um"
FILLER_MAP = {
    "A": "uh",
    "E": "uh",
    "U": "uh",
    "M": "um",
    "N": "um",
    "MM": "um",
    "NN": "um",
}

# Maximum allowed gap (in seconds) between a filler/stutter
# and the next word start to still consider it word-initial.
#
# Used to avoid falsely classifying normal word onsets as fillers.
WORD_ONSET_WINDOW = 0.12  # seconds

# Minimum duration (in seconds) for a sound to be considered
# a meaningful filler rather than noise or articulation artifact.
MIN_FILLER_DURATION = 0.02  # seconds

# Set of consonants that can form stutters when rapidly repeated.
# Example: "t-t-today", "b-b-but"
STUTTER_CONSONANTS = set("BCDFGHJKLPQRSTVWXYZ")


# ============================================================
# MINIMUM ANALYSIS REQUIREMENTS
# ============================================================

# Minimum audio duration required to produce a valid fluency score.
# Shorter samples are rejected as statistically unreliable.
MIN_ANALYSIS_DURATION_SEC = 5.0


# ============================================================
# SPEECH RATE (WORDS PER MINUTE) THRESHOLDS
# ============================================================

# Below this WPM, speech is considered unnaturally slow.
WPM_TOO_SLOW = 70

# Below this WPM, speech begins to feel hesitant or labored.
WPM_SLOW_THRESHOLD = 110

# Upper bound of the optimal WPM range for clarity.
WPM_OPTIMAL_MAX = 170

# Range over which excessively fast speech is penalized.
# Beyond WPM_OPTIMAL_MAX, score decays linearly over this range.
WPM_FAST_DECAY_RANGE = 120


# ============================================================
# PAUSE BEHAVIOR LIMITS
# ============================================================

# Maximum acceptable number of long pauses (>1s) per minute
# before pause structure is penalized.
MAX_LONG_PAUSES_PER_MIN = 4.0

# If pause subscore drops below this threshold,
# it is treated as a structural fluency blocker.
PAUSE_SCORE_BLOCK_THRESHOLD = 0.6


# ============================================================
# FILLER DEPENDENCY LIMITS
# ============================================================

# Maximum acceptable number of fillers per minute (weighted by duration)
# before fluency is penalized.
MAX_FILLERS_PER_MIN = 6.0

# If filler subscore drops below this threshold,
# it is treated as a structural fluency blocker.
FILLER_SCORE_BLOCK_THRESHOLD = 0.6


# ============================================================
# RHYTHMIC STABILITY LIMITS
# ============================================================

# Baseline acceptable standard deviation of pause durations.
# Higher values indicate erratic speech rhythm.
BASE_PAUSE_VARIABILITY = 0.7

# Below this stability score, speech rhythm is flagged as unstable.
STABILITY_SCORE_WARN_THRESHOLD = 0.6


# ============================================================
# LEXICAL QUALITY LIMITS
# ============================================================

# Below this lexical subscore, vocabulary usage is considered weak
# (high repetition, low diversity).
LEXICAL_LOW_THRESHOLD = 0.5


# ============================================================
# SCORING WEIGHTS (MUST SUM TO 1.0)
# ============================================================

# Contribution of pause structure to final fluency score.
WEIGHT_PAUSE = 0.30

# Contribution of filler dependency to final fluency score.
WEIGHT_FILLER = 0.25

# Contribution of rhythmic stability to final fluency score.
WEIGHT_STABILITY = 0.20

# Contribution of speech rate (WPM) to final fluency score.
WEIGHT_SPEECH_RATE = 0.15

# Contribution of lexical richness and repetition avoidance.
WEIGHT_LEXICAL = 0.10


# ============================================================
# READINESS & DECISION THRESHOLDS
# ============================================================

# Minimum audio duration required to consider a speaker
# "ready" for high-stakes evaluation (e.g. IELTS simulation).
MIN_SAMPLE_DURATION_SEC = 30

# Minimum fluency score required to be classified as "ready".
READY_SCORE_THRESHOLD = 80


# ============================================================
# BENCHMARKING & PRACTICE ESTIMATION
# ============================================================

# Target fluency score representing strong readiness.
BENCHMARK_TARGET_SCORE = 80

# Estimated guided practice hours required to improve fluency
# by one point on the 0–100 scale.
PRACTICE_HOURS_PER_POINT = 0.6


# ============================================================
# CONTEXT-SPECIFIC TOLERANCE CONFIGURATION
# ============================================================

# Different speaking contexts tolerate pauses and rhythm
# differently. These multipliers adjust scoring sensitivity.
#
# Example:
#   Narrative speech allows longer pauses than interviews.
CONTEXT_CONFIG = {
    "conversational": {
        "pause_tolerance": 1.0,
        "pause_variability_tolerance": 1.0,
    },
    "narrative": {
        "pause_tolerance": 1.4,
        "pause_variability_tolerance": 1.3,
    },
    "presentation": {
        "pause_tolerance": 1.2,
        "pause_variability_tolerance": 1.1,
    },
    "interview": {
        "pause_tolerance": 0.9,
        "pause_variability_tolerance": 0.9,
    },
}


# ============================================================
# LOW-LEVEL DETECTION PARAMETERS
# ============================================================

# Maximum gap (in seconds) between repeated stutter sounds
# to be grouped into a single stutter event.
GROUP_GAP_SEC = 0.15

# Time resolution (in seconds) per wav2vec token frame.
# Used to convert token indices to timestamps.
FRAME_SEC = 0.02  # 20 ms per frame


# ============================================================
# ACTION PLAN INSTRUCTIONS
# ============================================================

# Mapping from detected issue identifiers to
# human-readable corrective instructions.
INSTRUCTIONS = {
    "hesitation_structure": (
        "Pause only after completing full clauses or ideas."
    ),
    "filler_dependency": (
        "Replace filler words with silent pauses under 300 ms."
    ),
    "delivery_instability": (
        "Practice steady pacing using metronome or rhythm drills."
    ),
    "delivery_pacing": (
        "Reduce speaking speed slightly while maintaining energy."
    ),
    "lexical_simplicity": (
        "Actively substitute repeated words during rehearsal."
    ),
}
