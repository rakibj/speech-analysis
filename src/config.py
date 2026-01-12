# src/config.py
"""Configuration constants for fluency analysis."""

# ==============================
# FILLER DETECTION
# ==============================

FILLER_MAP = {
    "A": "uh",
    "E": "uh",
    "U": "uh",
    "M": "um",
    "N": "um",
    "MM": "um",
    "NN": "um",
}

WORD_ONSET_WINDOW = 0.12
MIN_FILLER_DURATION = 0.02
STUTTER_CONSONANTS = set("BCDFGHJKLPQRSTVWXYZ")

# ==============================
# ANALYSIS THRESHOLDS
# ==============================

MIN_ANALYSIS_DURATION_SEC = 5.0

# Speech rate
WPM_TOO_SLOW = 70
WPM_SLOW_THRESHOLD = 110
WPM_OPTIMAL_MAX = 170
WPM_FAST_DECAY_RANGE = 120

# Pauses
MAX_LONG_PAUSES_PER_MIN = 4.0
PAUSE_SCORE_BLOCK_THRESHOLD = 0.6

# Fillers
MAX_FILLERS_PER_MIN = 6.0
FILLER_SCORE_BLOCK_THRESHOLD = 0.6

# Stability
BASE_PAUSE_VARIABILITY = 0.7
STABILITY_SCORE_WARN_THRESHOLD = 0.6

# Lexical
LEXICAL_LOW_THRESHOLD = 0.5

# ==============================
# SCORING WEIGHTS (must sum to 1.0)
# ==============================

WEIGHT_PAUSE = 0.30
WEIGHT_FILLER = 0.25
WEIGHT_STABILITY = 0.20
WEIGHT_SPEECH_RATE = 0.15
WEIGHT_LEXICAL = 0.10

# ==============================
# READINESS
# ==============================

MIN_SAMPLE_DURATION_SEC = 30
READY_SCORE_THRESHOLD = 80

# ==============================
# BENCHMARKING
# ==============================

BENCHMARK_TARGET_SCORE = 80
PRACTICE_HOURS_PER_POINT = 0.6

# ==============================
# CONTEXT CONFIGURATIONS
# ==============================

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

# ==============================
# DETECTION PARAMETERS
# ==============================

GROUP_GAP_SEC = 0.15  # max gap between stutter repetitions
FRAME_SEC = 0.02      # 20ms per wav2vec token

# ==============================
# ISSUE INSTRUCTIONS
# ==============================

INSTRUCTIONS = {
    "hesitation_structure": "Pause only after completing full clauses.",
    "filler_dependency": "Replace fillers with silent pauses under 300ms.",
    "delivery_instability": "Practice steady pacing with metronome drills.",
    "delivery_pacing": "Reduce speed slightly while maintaining energy.",
    "lexical_simplicity": "Actively substitute repeated words during rehearsal.",
}