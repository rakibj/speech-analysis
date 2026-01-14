# src/metrics.py
"""Fluency metrics calculation and scoring."""
import pandas as pd

def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, x))


def filler_weight(duration: float) -> float:
    """Weight fillers by perceptual impact."""
    if duration < 0.08:
        return 0.2      # micro hesitation
    elif duration < 0.3:
        return 0.6      # subtle filler
    else:
        return 1.0      # real filler


def overlaps_filler(
    start: float,
    end: float,
    fillers: pd.DataFrame,
    tol: float = 0.05
) -> bool:
    """Check if time range overlaps any filler event."""
    for _, f in fillers.iterrows():
        if start < f["end"] + tol and end > f["start"] - tol:
            return True
    return False


def calculate_normalized_metrics(
    df_words_raw: pd.DataFrame,      # CHANGED: Full timeline
    df_words_cleaned: pd.DataFrame,   # NEW: Content words only
    df_segments: pd.DataFrame,
    df_fillers: pd.DataFrame,
    total_duration: float
) -> dict:
    """
    Calculate normalized fluency metrics.
    
    Args:
        df_words_full: Complete word timeline (includes fillers with is_filler flag)
        df_words_content: Content words only (fillers removed)
        df_segments: Segment-level timestamps
        df_fillers: Filler/stutter events
        total_duration: Total audio duration in seconds
        
    Returns:
        Dictionary of normalized metrics
    """
    duration_min = max(total_duration / 60.0, 0.5)
    
    # Words per minute - use CONTENT words only
    words_per_minute = (len(df_words_cleaned) * 60) / total_duration
    
    # Filler metrics
    filler_events = df_fillers[df_fillers["type"] == "filler"]
    stutter_events = df_fillers[df_fillers["type"] == "stutter"]
    
    fillers_per_min = (
        filler_events["duration"]
        .apply(filler_weight)
        .sum()
        / duration_min
    )
    
    stutters_per_min = len(stutter_events) / duration_min
    
    # Pause detection - use FULL timeline to get accurate gaps
    pause_durations = []
    
    for i in range(1, len(df_words_raw)):
        gap_start = df_words_raw.iloc[i - 1]["end"]
        gap_end = df_words_raw.iloc[i]["start"]
        gap = gap_end - gap_start
        
        # Only count as pause if:
        # 1. Gap is significant (>0.3s)
        # 2. Gap doesn't overlap with detected filler events
        if gap > 0.3 and not overlaps_filler(gap_start, gap_end, df_fillers):
            pause_durations.append(gap)
    
    pause_durations = pd.Series(pause_durations, dtype="float")
    
    # Pause metrics
    long_pauses = pause_durations[pause_durations > 1.0]
    very_long_pauses = pause_durations[pause_durations > 2.0]
    
    long_pauses_per_min = len(long_pauses) / duration_min
    very_long_pauses_per_min = len(very_long_pauses) / duration_min
    
    pause_time_ratio = (
        pause_durations.sum() / total_duration
        if pause_durations.size > 0
        else 0.0
    )
    
    # standard deviation of puse durations, small deviation means more consistent pacing
    pause_variability = (
        pause_durations.std()
        if pause_durations.size > 5
        else 0.0
    )
    
    # Lexical metrics - use CONTENT words only
    if len(df_words_cleaned) == 0:
        vocab_richness = 0.0
        repetition_ratio = 0.0
    else:
        words_clean = df_words_cleaned["word"].str.lower()
        
        vocab_richness = words_clean.nunique() / len(words_clean)

        # what ratio of words are the most common word - higher means more repetition (speakers tend to repeat safe words)
        repetition_ratio = (
            words_clean.value_counts().iloc[0] / len(words_clean)
            if len(words_clean) > 0
            else 0.0
        )
    
    return {
        "wpm": words_per_minute,
        "fillers_per_min": fillers_per_min,
        "stutters_per_min": stutters_per_min,
        "long_pauses_per_min": long_pauses_per_min,
        "very_long_pauses_per_min": very_long_pauses_per_min,
        "pause_time_ratio": pause_time_ratio,
        "pause_variability": pause_variability,
        "vocab_richness": vocab_richness,
        "repetition_ratio": repetition_ratio,
    }
