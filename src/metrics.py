# src/metrics.py
"""Fluency metrics calculation and scoring."""
import pandas as pd
import numpy as np
from .config import STOPWORDS

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
    
def rolling_wpm(df_words, window_sec=10.0):
    wpms = []
    start_times = df_words["start"].values

    for t in start_times:
        window = df_words[
            (df_words["start"] >= t) &
            (df_words["start"] < t + window_sec)
        ]
        if len(window) > 0:
            wpms.append(len(window) * 60 / window_sec)

    return wpms



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

def utterance_lengths(df_words_raw, pause_threshold=0.5):
    lengths = []
    count = 0

    for i in range(len(df_words_raw)):
        count += 1
        if i == len(df_words_raw) - 1:
            lengths.append(count)
        else:
            gap = (
                df_words_raw.iloc[i+1]["start"]
                - df_words_raw.iloc[i]["end"]
            )
            if gap > pause_threshold:
                lengths.append(count)
                count = 0

    return lengths

def build_raw_transcript(df_words_raw: pd.DataFrame) -> str:
        """
        Build a raw transcript string from word-level timestamps.
        Preserves original word order and surface forms.
        """
        if df_words_raw.empty or "word" not in df_words_raw.columns:
            return ""

        df_sorted = df_words_raw.sort_values("start")
        words = df_sorted["word"].astype(str).tolist()

        return " ".join(words)


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

    # Unique word count - use CONTENT words only
    unique_word_count = df_words_cleaned["word"].str.lower().nunique()
    
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

    pause_frequency = len(pause_durations) / duration_min
    
    # Lexical metrics - use CONTENT words only
    if len(df_words_cleaned) == 0:
        vocab_richness = 0.0
        repetition_ratio = 0.0
    else:
        words_clean = df_words_cleaned["word"].str.lower()
        
        vocab_richness = words_clean.nunique() / len(words_clean)


    words_clean_nostopwords = (
        df_words_cleaned["word"]
        .str.lower()
        .loc[~df_words_cleaned["word"].isin(STOPWORDS)]
    )
    # what ratio of words are the most common word - higher means more repetition (speakers tend to repeat safe words)
    repetition_ratio = (
        words_clean_nostopwords.value_counts().iloc[0] / len(words_clean_nostopwords)
        if len(words_clean_nostopwords) > 0
        else 0.0
    )

    wpm_rolling = rolling_wpm(df_words_cleaned)

    # compared to mean wpm (rolling), how much does the speech rate deviate? low = consistent pacing
    # < 0.2 very steady, 0.2-0.4 moderate, >0.4 highly variable
    speech_rate_variability = (
        np.std(wpm_rolling) / np.mean(wpm_rolling) if len(wpm_rolling) > 3 else 0.0
    )

    # avg words spoken per utterance (between pauses)
    utt_lengths = utterance_lengths(df_words_raw)
    mean_utterance_length = np.mean(utt_lengths) if utt_lengths else 0.0

    pause_after_filler = 0
    total_fillers = len(filler_events)

    for _, f in filler_events.iterrows():
        for gap in pause_durations:
            if gap > 0.3 and abs(f["end"] - gap_start) < 0.2:
                pause_after_filler += 1
                break

    pause_after_filler_rate = (
        pause_after_filler / total_fillers if total_fillers > 0 else 0.0
    )

    mean_word_confidence = (
        df_words_raw["confidence"].mean()
        if "confidence" in df_words_raw.columns and len(df_words_raw) > 0
        else 0.0
    )

    low_confidence_ratio = (
        (df_words_raw["confidence"] < 0.7).sum() / len(df_words_raw)
        if "confidence" in df_words_raw.columns and len(df_words_raw) > 0
        else 0.0
    )

    lexical_density = (
        len(words_clean_nostopwords) / len(df_words_raw)
        if len(df_words_raw) > 0
        else 0.0
    )

    raw_transcript = build_raw_transcript(df_words_raw)
    
    return {
        "raw_transcript": raw_transcript,
        "wpm": words_per_minute,
        "unique_word_count": unique_word_count,
        "fillers_per_min": fillers_per_min,
        "stutters_per_min": stutters_per_min,
        "long_pauses_per_min": long_pauses_per_min,
        "very_long_pauses_per_min": very_long_pauses_per_min,
        "pause_frequency": pause_frequency,
        "pause_time_ratio": pause_time_ratio,
        "pause_variability": pause_variability,
        "vocab_richness": vocab_richness,
        "repetition_ratio": repetition_ratio,
        "speech_rate_variability": speech_rate_variability,
        "mean_utterance_length": mean_utterance_length,
        "pause_after_filler_rate": pause_after_filler_rate,
        "mean_word_confidence": mean_word_confidence,
        "low_confidence_ratio": low_confidence_ratio,
        "lexical_density": lexical_density,
    }
