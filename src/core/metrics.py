# src/metrics.py
"""Fluency metrics calculation and scoring."""
import pandas as pd
import numpy as np
from src.utils.config import STOPWORDS


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
    if df_words.empty:
        return wpms
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
    if fillers.empty:
        return False
    for _, f in fillers.iterrows():
        if start < f["end"] + tol and end > f["start"] - tol:
            return True
    return False


def utterance_lengths(df_words_asr, pause_threshold=0.5):
    """Compute utterance lengths using clean ASR word timeline."""
    if df_words_asr.empty:
        return []
    lengths = []
    count = 0
    n = len(df_words_asr)
    for i in range(n):
        count += 1
        if i == n - 1:
            lengths.append(count)
        else:
            gap = df_words_asr.iloc[i + 1]["start"] - df_words_asr.iloc[i]["end"]
            if gap > pause_threshold:
                lengths.append(count)
                count = 0
    return lengths


def calculate_normalized_metrics(
    df_words_asr: pd.DataFrame,
    df_words_content: pd.DataFrame,
    df_segments: pd.DataFrame,
    df_fillers: pd.DataFrame,
    total_duration: float,
    df_tokens_enriched: pd.DataFrame = None  # Optional: for future use only
) -> dict:
    """
    Calculate normalized fluency metrics.
    
    Args:
        df_words_asr: Full ASR word timeline (includes transcribed fillers like 'um', 'uh').
                      Used for pause detection, utterance segmentation, and confidence metrics.
        df_words_content: Content words only (fillers removed).
                          Used for lexical and rate metrics.
        df_segments: Segment-level timestamps from ASR.
        df_fillers: Unified disfluency events (fillers + stutters from all sources).
        total_duration: Total audio duration in seconds.
        df_tokens_enriched: Optional enriched token stream (ASR + acoustic fillers).
                            Currently unused — reserved for future advanced metrics.
        
    Returns:
        Dictionary of normalized metrics
    """
    if total_duration <= 0:
        total_duration = 0.1  # avoid division by zero

    duration_min = max(total_duration / 60.0, 0.5)

    # === Lexical & Rate Metrics (use content words only) ===
    words_per_minute = (len(df_words_content) * 60) / total_duration

    if len(df_words_content) == 0:
        vocab_richness = 0.0
        type_token_ratio = 0.0
        repetition_ratio = 0.0
        words_clean_nostopwords = pd.Series([], dtype="object")
    else:
        words_clean = df_words_content["word"].str.lower()
        vocab_richness = words_clean.nunique() / len(words_clean)
        type_token_ratio = vocab_richness  # TTR = unique_words / total_words
        
        words_clean_nostopwords = words_clean[~words_clean.isin(STOPWORDS)]
        if len(words_clean_nostopwords) > 0:
            repetition_ratio = (
                words_clean_nostopwords.value_counts().iloc[0] / len(words_clean_nostopwords)
            )
        else:
            repetition_ratio = 0.0

    # === Disfluency Metrics (use df_fillers) ===
    filler_events = df_fillers[df_fillers["type"] == "filler"]
    stutter_events = df_fillers[df_fillers["type"] == "stutter"]

    fillers_per_min = (
        filler_events["duration"].apply(filler_weight).sum() / duration_min
        if not filler_events.empty else 0.0
    )

    stutters_per_min = len(stutter_events) / duration_min

    # === Pause & Prosody Metrics (use df_words_asr + df_fillers) ===
    pause_durations = []
    if not df_words_asr.empty:
        for i in range(1, len(df_words_asr)):
            gap_start = df_words_asr.iloc[i - 1]["end"]
            gap_end = df_words_asr.iloc[i]["start"]
            gap = gap_end - gap_start
            if gap > 0.3 and not overlaps_filler(gap_start, gap_end, df_fillers):
                pause_durations.append(gap)

    pause_durations = pd.Series(pause_durations, dtype="float")

    long_pauses = pause_durations[pause_durations > 1.0]
    very_long_pauses = pause_durations[pause_durations > 2.0]

    long_pauses_per_min = len(long_pauses) / duration_min
    very_long_pauses_per_min = len(very_long_pauses) / duration_min
    pause_time_ratio = pause_durations.sum() / total_duration if not pause_durations.empty else 0.0
    pause_variability = pause_durations.std() if len(pause_durations) > 5 else 0.0
    pause_frequency = len(pause_durations) / duration_min

    # === Utterance Metrics ===
    utt_lengths = utterance_lengths(df_words_asr)
    mean_utterance_length = np.mean(utt_lengths) if utt_lengths else 0.0

    # === Confidence Metrics (use df_words_asr) ===
    if "confidence" in df_words_asr.columns and not df_words_asr.empty:
        valid_confs = df_words_asr["confidence"].dropna()
        if len(valid_confs) > 0:
            mean_word_confidence = valid_confs.mean()
            low_confidence_ratio = (valid_confs < 0.7).sum() / len(valid_confs)
        else:
            mean_word_confidence = 0.0
            low_confidence_ratio = 0.0
    else:
        mean_word_confidence = 0.0
        low_confidence_ratio = 0.0

    # === Derived Metrics ===
    lexical_density = (
        len(words_clean_nostopwords) / len(df_words_asr)
        if len(df_words_asr) > 0 else 0.0
    )

    wpm_rolling = rolling_wpm(df_words_content)
    speech_rate_variability = (
        np.std(wpm_rolling) / np.mean(wpm_rolling) if len(wpm_rolling) > 3 else 0.0
    )

    # Note: pause_after_filler_rate is buggy (uses undefined gap_start) — disabled for now
    pause_after_filler_rate = 0.0

    speaking_time_sec = total_duration - pause_durations.sum()

    return {
        "wpm": round(words_per_minute, 2),
        "unique_word_count": int(round(vocab_richness * len(df_words_content))) if len(df_words_content) > 0 else 0,
        "fillers_per_min": round(fillers_per_min, 2),
        "stutters_per_min": round(stutters_per_min, 2),
        "long_pauses_per_min": round(long_pauses_per_min, 2),
        "very_long_pauses_per_min": round(very_long_pauses_per_min, 2),
        "pause_frequency": round(pause_frequency, 2),
        "pause_time_ratio": round(pause_time_ratio, 3),
        "pause_variability": round(pause_variability, 3) if not np.isnan(pause_variability) else 0.0,
        "vocab_richness": round(vocab_richness, 3),
        "type_token_ratio": round(type_token_ratio, 3),
        "repetition_ratio": round(repetition_ratio, 3),
        "speech_rate_variability": round(speech_rate_variability, 3),
        "mean_utterance_length": round(mean_utterance_length, 2),
        "pause_after_filler_rate": round(pause_after_filler_rate, 3),
        "mean_word_confidence": round(mean_word_confidence, 3),
        "low_confidence_ratio": round(low_confidence_ratio, 3),
        "lexical_density": round(lexical_density, 3),
        "audio_duration_sec": round(total_duration, 2),
        "speaking_time_sec": round(speaking_time_sec, 2),
    }