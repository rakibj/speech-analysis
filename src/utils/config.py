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

VALID_CONTEXTS = {"conversational", "narrative", "presentation", "interview"}

STOPWORDS = {
    # ------------------------------------------------------------------
    # Articles & determiners (no lexical choice signal)
    # ------------------------------------------------------------------
    "a", "an", "the",
    "this", "that", "these", "those",

    # ------------------------------------------------------------------
    # Personal pronouns (unavoidable repetition in speech)
    # ------------------------------------------------------------------
    "i", "me", "my", "mine", "myself",
    "you", "your", "yours", "yourself",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",

    # ------------------------------------------------------------------
    # Auxiliary & copular verbs (grammatical scaffolding)
    # ------------------------------------------------------------------
    "am", "is", "are", "was", "were",
    "be", "been", "being",

    # ------------------------------------------------------------------
    # Modal verbs (high frequency, low lexical information)
    # ------------------------------------------------------------------
    "can", "could", "may", "might",
    "must", "shall", "should",
    "will", "would",

    # ------------------------------------------------------------------
    # Function verbs (do/have — repetition is not lexical weakness)
    # ------------------------------------------------------------------
    "do", "does", "did", "done", "doing",
    "have", "has", "had", "having",

    # ------------------------------------------------------------------
    # Prepositions (mandatory grammar glue)
    # ------------------------------------------------------------------
    "to", "of", "in", "on", "at", "for", "with",
    "about", "from", "by", "into", "onto",
    "over", "under", "after", "before",
    "between", "among", "through", "during",
    "without", "within", "against", "around",
    "towards", "upon",

    # ------------------------------------------------------------------
    # Conjunctions & subordinators (structural, not lexical)
    # ------------------------------------------------------------------
    "and", "but", "or", "so", "yet",
    "because", "although", "though", "while",
    "if", "unless", "until", "since",

    # ------------------------------------------------------------------
    # Relative & complementizers (clause formation)
    # ------------------------------------------------------------------
    "that", "which", "who", "whom", "whose",
    "where", "when",

    # ------------------------------------------------------------------
    # Quantifiers & generalizers (very common, vague)
    # ------------------------------------------------------------------
    "some", "any", "many", "much",
    "few", "little", "more", "most",
    "less", "least", "all", "both",
    "either", "neither", "each", "every",
    "enough",

    # ------------------------------------------------------------------
    # Negation & polarity (grammatical necessity)
    # ------------------------------------------------------------------
    "not", "no", "nor", "never",
    "none", "nothing", "nobody", "nowhere",

    # ------------------------------------------------------------------
    # Existentials & placeholders (low semantic value)
    # ------------------------------------------------------------------
    "there", "here",
    "something", "anything", "everything",
    "someone", "anyone", "everyone",
    "somewhere", "anywhere", "everywhere",

    # ------------------------------------------------------------------
    # Spoken fillers & discourse glue (NOT lexical choice)
    # ------------------------------------------------------------------
    "uh", "um", "erm", "ah", "eh", "hmm",
    "like",           # filler usage (IELTS-relevant)
    "well", "okay", "ok", "right",
    "you know", "i mean",
    "kind of", "sort of",
    "basically", "actually", "literally",

    # ------------------------------------------------------------------
    # Temporal / sequencing glue (narrative structure, not vocabulary)
    # ------------------------------------------------------------------
    "then", "now", "today", "yesterday", "tomorrow",
    "later", "first", "second", "third", "next", "finally",
}

# ============================================================
# FILLER & STUTTER DETECTION CONFIGURATION
# ============================================================

FILLER_PATTERNS = {
    # Basic fillers
    'um', 'umm', 'ummm', 'uhm', 'uhhmm',
    'uh', 'uhh', 'uhhh', 'er', 'err', 'errr',
    'ah', 'ahh', 'ahhh', 'eh', 'ehh', 'ehhh',
    
    # British/formal variants
    'erm', 'errm', 'errmm',
    
    # Elongated versions
    'uuuh', 'uuum', 'aaah', 'mmm', 'hmm', 'hmmm',
    
}
FILLER_REGEX = r"^(um+|uh+|erm+|er+|ah+|eh+|mmm+|hmm+)$"
FILLER_IGNORE_MAX = 0.10     # <100ms → ignore
FILLER_LIGHT_MAX = 0.30      # 100–300ms → light
# More conservative set (exclude discourse markers)
CORE_FILLERS = {
    'um', 'umm', 'ummm', 'uhm', 'uhhmm',
    'uh', 'uhh', 'uhhh', 'er', 'err', 'errr',
    'ah', 'ahh', 'ahhh', 'eh', 'ehh', 'ehhh',
    'erm', 'errm', 'errmm',
    'uuuh', 'uuum', 'aaah', 'mmm', 'hmm', 'hmmm',
}


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
# Context format:
#   "conversational" - General conversation
#   "ielts" - IELTS Speaking (topic-based, may include off-topic tolerance)
#   "ielts[topic: ..., cue_card: ...]" - IELTS with specific context
#
# The system parses context to extract:
#   - base_context: conversational | ielts | custom
#   - metadata: topic, cue_card, etc. (passed to LLM for relevance checks)
#
# Example:
#   Narrative speech allows longer pauses than interviews.
CONTEXT_CONFIG = {
    "conversational": {
        "pause_tolerance": 1.0,
        "pause_variability_tolerance": 1.0,
        "base_type": "conversational",
    },
    "ielts": {
        "pause_tolerance": 1.0,
        "pause_variability_tolerance": 1.0,
        "base_type": "ielts",
        # IELTS speaking has specific relevance expectations
        "topic_relevance_threshold": 0.65,  # Soft relevance check
    },
    "narrative": {
        "pause_tolerance": 1.4,
        "pause_variability_tolerance": 1.3,
        "base_type": "narrative",
    },
    "presentation": {
        "pause_tolerance": 1.2,
        "pause_variability_tolerance": 1.1,
        "base_type": "presentation",
    },
    "interview": {
        "pause_tolerance": 0.9,
        "pause_variability_tolerance": 0.9,
        "base_type": "interview",
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
