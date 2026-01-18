# src/metrics.py
"""Fluency metrics calculation and scoring."""
import pandas as pd
from typing import Tuple, Dict, List

from .metrics import calculate_normalized_metrics

from src.utils.config import (
    WPM_TOO_SLOW,
    WPM_SLOW_THRESHOLD,
    WPM_OPTIMAL_MAX,
    WPM_FAST_DECAY_RANGE,
    MAX_LONG_PAUSES_PER_MIN,
    MAX_FILLERS_PER_MIN,
    BASE_PAUSE_VARIABILITY,
    PAUSE_SCORE_BLOCK_THRESHOLD,
    FILLER_SCORE_BLOCK_THRESHOLD,
    STABILITY_SCORE_WARN_THRESHOLD,
    LEXICAL_LOW_THRESHOLD,
    WEIGHT_PAUSE,
    WEIGHT_FILLER,
    WEIGHT_STABILITY,
    WEIGHT_SPEECH_RATE,
    WEIGHT_LEXICAL,
    MIN_ANALYSIS_DURATION_SEC,
    CONTEXT_CONFIG,
    INSTRUCTIONS,
)

def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, x))


def calculate_subscores(
    metrics: dict,
    context_config: dict
) -> Tuple[dict, dict]:
    """
    Calculate fluency subscores.
    
    Args:
        metrics: Normalized metrics dictionary
        context_config: Context-specific tolerance settings
        
    Returns:
        Tuple of (subscores dict, context dict)
    """
    wpm = metrics["wpm"]
    
    # Speech rate score
    if wpm < WPM_SLOW_THRESHOLD:
        speech_rate_score = clamp01(
            (wpm - WPM_TOO_SLOW) / (WPM_SLOW_THRESHOLD - WPM_TOO_SLOW)
        )
    elif wpm <= WPM_OPTIMAL_MAX:
        speech_rate_score = 1.0
    else:
        speech_rate_score = clamp01(
            1 - (wpm - WPM_OPTIMAL_MAX) / WPM_FAST_DECAY_RANGE
        )
    
    # Pause structure score
    pause_score = clamp01(
        1 - (
            metrics["long_pauses_per_min"]
            / (MAX_LONG_PAUSES_PER_MIN * context_config["pause_tolerance"])
        )
    )
    
    # Filler dependency score
    filler_score = clamp01(
        1 - (metrics["fillers_per_min"] / MAX_FILLERS_PER_MIN)
    )
    
    # Rhythmic stability score
    stability_score = clamp01(
        1 - (
            metrics["pause_variability"]
            / (BASE_PAUSE_VARIABILITY * context_config["pause_variability_tolerance"])
        )
    )
    
    # Lexical quality score
    lexical_score = clamp01(
        0.65 * metrics["vocab_richness"]
        + 0.35 * (1 - metrics["repetition_ratio"])
    )
    
    subscores = {
        "speech_rate": speech_rate_score,
        "pause": pause_score,
        "filler": filler_score,
        "stability": stability_score,
        "lexical": lexical_score,
    }
    
    return subscores, context_config

def apply_compound_penalties(subscores: dict, metrics: dict) -> float:
    """
    Penalize combinations of issues that humans perceive
    as 'loss of control', even if each metric alone is acceptable.
    """
    penalty = 0.0

    # Lost-control pattern: hesitation + instability + repetition
    if (
        subscores["filler"] < 0.75 and
        subscores["stability"] < 0.75 and
        metrics["repetition_ratio"] > 0.06
    ):
        penalty += 0.12  # ≈12 points

    # Fluent-but-annoying: smooth but filler-heavy
    if (
        subscores["pause"] > 0.8 and
        metrics["fillers_per_min"] > 3.0
    ):
        penalty += 0.08

    return penalty

def calculate_fluency_score(
    subscores: dict, metrics: dict
) -> int:
    """
    Calculate overall fluency score (0-100).
    
    Args:
        subscores: Dictionary of individual subscores
        
    Returns:
        Fluency score as integer
    """
    raw_score = (
        WEIGHT_PAUSE * subscores["pause"] +
        WEIGHT_FILLER * subscores["filler"] +
        WEIGHT_STABILITY * subscores["stability"] +
        WEIGHT_SPEECH_RATE * subscores["speech_rate"] +
        WEIGHT_LEXICAL * subscores["lexical"]
    )

    penalty = apply_compound_penalties(subscores, metrics)
    raw_score = max(0.0, raw_score - penalty)
    
    return int(round(100 * clamp01(raw_score)))

def detect_issues(
    subscores: dict,
    metrics: dict
) -> List[dict]:
    """
    Detect and categorize fluency issues.
    
    Args:
        subscores: Dictionary of subscores
        metrics: Normalized metrics
        
    Returns:
        List of issue dictionaries sorted by score impact
    """
    issues = []
    
    def issue(severity: str, issue_id: str, root_cause: str, score_impact: int):
        return {
            "issue": issue_id,
            "severity": severity,
            "root_cause": root_cause,
            "score_impact": score_impact,
        }
    
    # Structural blockers
    if subscores["pause"] < PAUSE_SCORE_BLOCK_THRESHOLD:
        issues.append(issue(
            "high",
            "hesitation_structure",
            "Pauses frequently interrupt sentence flow.",
            int((1 - subscores["pause"]) * 30),
        ))
    
    if subscores["filler"] < FILLER_SCORE_BLOCK_THRESHOLD:
        issues.append(issue(
            "high",
            "filler_dependency",
            "Fillers replace silent planning pauses.",
            int((1 - subscores["filler"]) * 25),
        ))
    
    if subscores["stability"] < STABILITY_SCORE_WARN_THRESHOLD:
        issues.append(issue(
            "medium",
            "delivery_instability",
            "Speech rhythm varies unpredictably.",
            int((1 - subscores["stability"]) * 20),
        ))
    
    # Style issues
    if subscores["speech_rate"] < 0.7:
        issues.append(issue(
            "medium",
            "delivery_pacing",
            "Speech rate deviates from optimal clarity range.",
            int((1 - subscores["speech_rate"]) * 15),
        ))
    
    if subscores["lexical"] < LEXICAL_LOW_THRESHOLD:
        issues.append(issue(
            "low",
            "lexical_simplicity",
            "Frequent reuse of common vocabulary.",
            int((1 - subscores["lexical"]) * 10),
        ))
    
    return sorted(issues, key=lambda x: x["score_impact"], reverse=True)

def determine_readiness(
    fluency_score: int,
    issues: List[dict]
) -> str:
    """
    Determine speaker readiness based on score and issues.
    
    Args:
        fluency_score: Overall fluency score
        issues: List of detected issues
        
    Returns:
        Readiness status: 'ready', 'borderline', or 'not_ready'
    """
    high_issues = [i for i in issues if i["severity"] == "high"]
    medium_issues = [i for i in issues if i["severity"] == "medium"]
    
    if len(high_issues) >= 2:
        return "not_ready"
    elif len(high_issues) == 1:
        return "borderline"
    elif len(medium_issues) >= 2:
        return "borderline"
    elif fluency_score >= 80:
        return "ready"
    else:
        return "borderline"

def calculate_benchmarking(
    fluency_score: int,
    readiness: str
) -> dict:
    """
    Calculate benchmarking metrics and practice estimates.
    
    Args:
        fluency_score: Overall fluency score
        readiness: Readiness status
        
    Returns:
        Dictionary with percentile, target, and practice hours
    """
    # Estimate percentile
    if fluency_score >= 85:
        percentile = 80
    elif fluency_score >= 75:
        percentile = 65
    elif fluency_score >= 65:
        percentile = 50
    else:
        percentile = 30
    
    # Calculate score gap
    score_gap = (
        max(0, 80 - fluency_score)
        if readiness != "ready"
        else 0
    )
    
    return {
        "percentile": percentile,
        "target_score": 80,
        "score_gap": score_gap,
        "estimated_guided_practice_hours": score_gap * 0.6,
    }

def generate_action_plan(
    issues: List[dict],
    score_gap: int
) -> List[dict]:
    """
    Generate prioritized action plan with expected gains.
    
    Args:
        issues: List of detected issues
        score_gap: Points needed to reach target
        
    Returns:
        List of action items with priorities and expected gains
    """
    action_plan = []
    
    # Normalize gains to match score gap
    max_gain = sum(i["score_impact"] for i in issues[:3]) or 1
    scale = score_gap / max_gain if score_gap > 0 else 1.0
    
    for idx, issue in enumerate(issues[:3]):
        action_plan.append({
            "priority": idx + 1,
            "focus": issue["issue"],
            "instruction": INSTRUCTIONS.get(
                issue["issue"],
                "Focus on improving this aspect."
            ),
            "expected_score_gain": int(issue["score_impact"] * scale),
        })
    
    return action_plan

def analyze_fluency(
    df_words_full: pd.DataFrame,      # CHANGED: Full timeline with is_filler column
    df_words_content: pd.DataFrame,   # NEW: Content words only (no fillers)
    df_segments: pd.DataFrame,
    df_fillers: pd.DataFrame,
    total_duration: float,
    speech_context: str = "conversational"
) -> dict:
    """
    Complete fluency analysis pipeline.
    
    Args:
        df_words_full: Complete word-level timestamps (includes fillers marked with is_filler)
        df_words_content: Content words only (fillers removed) for WPM calculation
        df_segments: Segment-level timestamps
        df_fillers: Filler/stutter events
        total_duration: Total audio duration in seconds
        speech_context: Type of speech context
        
    Returns:
        Complete analysis dictionary with verdict, metrics, and opinions
    """
    # Check minimum duration
    if total_duration < MIN_ANALYSIS_DURATION_SEC:
        return {
            "verdict": {
                "fluency_score": None,
                "readiness": "insufficient_sample",
            },
            "benchmarking": None,
            "normalized_metrics": None,
            "opinions": None,
        }
    
    # Validate context
    if speech_context not in CONTEXT_CONFIG:
        print(f"⚠️  Warning: Invalid context '{speech_context}'. Using 'conversational'.")
        speech_context = "conversational"
    
    # Get context configuration
    context_config = CONTEXT_CONFIG[speech_context]
    
    # Calculate metrics (CHANGED: pass both word DataFrames)
    metrics = calculate_normalized_metrics(
        df_words_full,      # For pause detection (full timeline)
        df_words_content,   # For WPM and lexical metrics
        df_segments,
        df_fillers,
        total_duration
    )
    
    # Calculate subscores
    subscores, _ = calculate_subscores(metrics, context_config)
    
    # Calculate fluency score
    fluency_score = calculate_fluency_score(subscores, metrics)
    
    # Detect issues
    issues = detect_issues(subscores, metrics)
    
    # Determine readiness
    readiness = determine_readiness(fluency_score, issues)
    
    # Calculate benchmarking
    benchmarking = calculate_benchmarking(fluency_score, readiness)
    
    # Generate action plan
    action_plan = generate_action_plan(issues, benchmarking["score_gap"])
    
    return {
        "verdict": {
            "fluency_score": fluency_score,
            "readiness": readiness,
        },
        "benchmarking": benchmarking,
        "opinions": {
            "primary_issues": issues,
            "action_plan": action_plan,
        },
    }

if __name__ == "__main__":
    # Quick test with dummy data
    import numpy as np
    
    # Create dummy data
    df_words = pd.DataFrame({
        "word": ["hello", "world", "this", "is", "test"],
        "start": [0.0, 0.5, 1.0, 1.5, 2.0],
        "end": [0.4, 0.9, 1.4, 1.9, 2.4],
        "duration": [0.4, 0.4, 0.4, 0.4, 0.4],
        "confidence": [0.9, 0.9, 0.9, 0.9, 0.9],
    })
    
    df_segments = pd.DataFrame({
        "text": ["hello world this is test"],
        "start": [0.0],
        "end": [2.4],
        "duration": [2.4],
        "avg_word_confidence": [0.9],
    })
    
    df_fillers = pd.DataFrame({
        "type": ["filler", "stutter"],
        "text": ["uh", "t"],
        "start": [0.45, 1.45],
        "end": [0.48, 1.48],
        "duration": [0.03, 0.03],
    })
    
    result = analyze_fluency(df_words, df_segments, df_fillers, 2.4)
    print(f"Fluency Score: {result['verdict']['fluency_score']}")
    print(f"Readiness: {result['verdict']['readiness']}")