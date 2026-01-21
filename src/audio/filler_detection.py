# src/audio/filler_detection.py
"""Filler and disfluency detection using multiple methods."""
import re
import os
import soundfile as sf
import pandas as pd
from typing import Tuple, Set

from src.utils.config import (
    CORE_FILLERS,
    FILLER_MAP,
    FILLER_REGEX,
    WORD_ONSET_WINDOW,
    MIN_FILLER_DURATION,
    STUTTER_CONSONANTS,
    GROUP_GAP_SEC,
    FRAME_SEC,
)


# ==============================
# WORD-LEVEL FILLER DETECTION
# ==============================

def normalize_word(word: str) -> str:
    """
    Normalize a word for filler detection.
    
    - Strips punctuation
    - Converts to lowercase
    - Removes extra whitespace
    
    Args:
        word: Raw word string from transcription
        
    Returns:
        Normalized word string
    """
    word = re.sub(r'^[^\w]+|[^\w]+$', '', word.lower().strip())
    word = re.sub(r'\s+', ' ', word)
    return word


def is_filler_word(
    word: str,
    filler_set: Set[str] = CORE_FILLERS,
    include_pattern_match: bool = True
) -> bool:
    """
    Determine if a word is a filler with high confidence.
    
    Args:
        word: Word to check
        filler_set: Set of known filler words
        include_pattern_match: Also check regex patterns for variations
        
    Returns:
        True if word is a filler
    """
    normalized = normalize_word(word)
    
    if not normalized:
        return False
    
    # Direct lookup in filler set
    if normalized in filler_set:
        return True
    
    # Pattern matching for variations
    if include_pattern_match:
        # Repeated vowels: uhhhhh, ummmm, ahhhhh
        if re.fullmatch(r'[uea]h{2,}', normalized):
            return True
        if re.fullmatch(r'[ume]{2,}', normalized):
            return True
        
        # Elongated nasals: mmmmm, nnnn
        if re.fullmatch(r'[mn]{2,}', normalized):
            return True
        
        # Um/uh variants with extra letters
        if re.fullmatch(r'u+h*m+', normalized):
            return True
        if re.fullmatch(r'u+h+', normalized):
            return True
        if re.fullmatch(r'e+r+m*', normalized):
            return True
    
    return False


def mark_filler_words(
    df_words: pd.DataFrame,
    filler_set: Set[str] = CORE_FILLERS,
    word_column: str = 'word'
) -> pd.DataFrame:
    """
    Add 'is_filler' column to word DataFrame.
    
    Args:
        df_words: DataFrame with word timestamps
        filler_set: Set of filler words to detect
        word_column: Name of column containing words
        
    Returns:
        DataFrame with added 'is_filler' column
    """
    df = df_words.copy()
    
    df['is_filler'] = df[word_column].apply(
        lambda w: is_filler_word(w, filler_set)
    )
    
    return df


def get_content_words(df_words: pd.DataFrame) -> pd.DataFrame:
    """
    Extract only content words (non-fillers).
    
    Args:
        df_words: DataFrame with 'is_filler' column
        
    Returns:
        Filtered DataFrame with only content words
    """
    if 'is_filler' not in df_words.columns:
        raise ValueError("DataFrame must have 'is_filler' column. Run mark_filler_words() first.")
    
    return df_words[~df_words['is_filler']].copy().reset_index(drop=True)


def segment_contains_filler(segment_text: str, filler_set: Set[str] = CORE_FILLERS) -> bool:
    """
    Check if a segment contains any filler words.
    
    Args:
        segment_text: Full segment text
        filler_set: Set of filler words
        
    Returns:
        True if segment contains fillers
    """
    words = segment_text.lower().split()
    return any(is_filler_word(w, filler_set) for w in words)


def mark_filler_segments(
    df_segments: pd.DataFrame,
    filler_set: Set[str] = CORE_FILLERS,
    text_column: str = 'text'
) -> pd.DataFrame:
    """
    Add 'contains_filler' column to segment DataFrame.
    
    Args:
        df_segments: DataFrame with segment timestamps
        filler_set: Set of filler words to detect
        text_column: Name of column containing segment text
        
    Returns:
        DataFrame with added 'contains_filler' column
    """
    df = df_segments.copy()
    
    df['contains_filler'] = df[text_column].apply(
        lambda text: segment_contains_filler(text, filler_set)
    )
    
    return df


# ==============================
# WAV2VEC2 PHONEME DETECTION
# ==============================

def detect_phonemes_wav2vec(audio_path: str) -> pd.DataFrame:
    """
    Detect phoneme-level events using Wav2Vec2.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        DataFrame with phoneme events (label, start, end, duration)
    """
    from transformers.models.wav2vec2 import Wav2Vec2Processor, Wav2Vec2ForCTC
    import shutil
    
    # Use HF_HOME from environment (set by Modal) for model caching
    cache_dir = os.getenv("HF_HOME", None)
    
    def load_wav2vec_models():
        """Load models with automatic cache recovery on corruption."""
        try:
            processor = Wav2Vec2Processor.from_pretrained(
                "facebook/wav2vec2-large-960h",
                cache_dir=cache_dir
            )
            wav2vec = Wav2Vec2ForCTC.from_pretrained(
                "facebook/wav2vec2-large-960h",
                cache_dir=cache_dir
            )
            wav2vec.eval()
            return processor, wav2vec
        except (OSError, UnicodeDecodeError) as e:
            # Cache corrupted - try to clear it and retry
            if "Invalid argument" in str(e) or "UnicodeDecodeError" in str(type(e).__name__):
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Wav2Vec2 cache corrupted, rebuilding...")
                
                # Clear the corrupted cache
                if cache_dir:
                    wav2vec_cache = os.path.join(cache_dir, "models--facebook--wav2vec2-large-960h")
                    if os.path.exists(wav2vec_cache):
                        try:
                            shutil.rmtree(wav2vec_cache)
                            logger.info(f"Cleared corrupted cache: {wav2vec_cache}")
                        except Exception as cleanup_err:
                            logger.error(f"Failed to clear cache: {cleanup_err}")
                
                # Retry with fresh download
                processor = Wav2Vec2Processor.from_pretrained(
                    "facebook/wav2vec2-large-960h",
                    cache_dir=cache_dir
                )
                wav2vec = Wav2Vec2ForCTC.from_pretrained(
                    "facebook/wav2vec2-large-960h",
                    cache_dir=cache_dir
                )
                wav2vec.eval()
                logger.info("Wav2Vec2 models loaded successfully after cache rebuild")
                return processor, wav2vec
            else:
                raise
    
    processor, wav2vec = load_wav2vec_models()
    
    # Load audio
    waveform, sr = sf.read(audio_path, dtype="float32")
    
    # Convert stereo to mono
    if waveform.ndim == 2:
        waveform = waveform.mean(axis=1)
    
    import torch
    import torchaudio
    waveform = torch.from_numpy(waveform)
    
    # Resample to 16kHz if needed
    if sr != 16000:
        waveform = torchaudio.functional.resample(waveform, sr, 16000)
        sr = 16000
    
    # Prepare input
    inputs = processor(
        waveform.squeeze(),
        sampling_rate=16000,
        return_tensors="pt",
    )
    
    # Forward pass
    with torch.no_grad():
        logits = wav2vec(**inputs).logits
    
    # Get predicted tokens
    predicted_ids = torch.argmax(logits, dim=-1)[0]
    tokens = processor.tokenizer.convert_ids_to_tokens(predicted_ids.tolist())
    
    # Convert tokens to events
    events = []
    current = None
    
    for i, tok in enumerate(tokens):
        t = i * FRAME_SEC
        
        if tok == '<pad>':
            if current:
                current["end"] = t
                events.append(current)
                current = None
            continue
        
        if current and current["label"] == tok:
            continue
        
        if current:
            current["end"] = t
            events.append(current)
        
        current = {"label": tok, "start": t}
    
    if current:
        current["end"] = t
        events.append(current)
    
    df = pd.DataFrame(events)
    if df.empty:
        return df
    
    df["duration"] = df["end"] - df["start"]
    df["labels"] = df["label"]
    
    # Merge adjacent same-label events
    df = merge_adjacent_events(df)
    
    return df


def merge_adjacent_events(df: pd.DataFrame, max_gap: float = 0.05) -> pd.DataFrame:
    """Merge adjacent events with the same label."""
    if df.empty:
        return df
    
    merged = []
    current = None
    
    for _, row in df.sort_values("start").iterrows():
        if current is None:
            current = row.to_dict()
            continue
        
        same_label = row["labels"] == current["labels"]
        close = row["start"] - current["end"] <= max_gap
        
        if same_label and close:
            current["end"] = row["end"]
            current["duration"] = current["end"] - current["start"]
        else:
            merged.append(current)
            current = row.to_dict()
    
    if current:
        merged.append(current)
    
    return pd.DataFrame(merged)


# ==============================
# FILLER/STUTTER CLASSIFICATION
# ==============================

def overlaps_any_word_relaxed(
    start: float,
    end: float,
    words: pd.DataFrame,
    tol_before: float = 0.02,
    tol_after: float = 0.02
) -> bool:
    """Check if time range overlaps any word."""
    for _, w in words.iterrows():
        if start < w["end"] + tol_after and end > w["start"] - tol_before:
            return True
    return False


def is_word_initial_candidate(
    row: pd.Series,
    word_starts: pd.DataFrame,
    max_lead: float = WORD_ONSET_WINDOW
) -> bool:
    """Check if event is immediately before a word start."""
    end = row["end"]
    upcoming = word_starts[
        (word_starts["start"] >= end) &
        ((word_starts["start"] - end) <= max_lead)
    ]
    return not upcoming.empty


def looks_like_filler(norm: str, duration: float) -> bool:
    """Check if normalized label looks like a filler sound."""
    if duration < MIN_FILLER_DURATION:
        return False
    
    # Vowel hesitations (uh, ah, eh)
    if re.fullmatch(r"[AEIOUH]+", norm):
        return True
    
    # Nasal hums (mm, nn)
    if re.fullmatch(r"M+|N+", norm):
        return True
    
    return False


def should_suppress_word_initial(row: pd.Series) -> bool:
    """Check if word-initial sound should be suppressed."""
    label = row["labels"].upper()
    norm = re.sub(r"(.)\1+", r"\1", label)
    
    # Never suppress filler-shaped sounds
    if looks_like_filler(norm, row["duration"]):
        return False
    
    # Suppress only ultra-short junk
    return row["duration"] < 0.03


def classify_non_word_event(row: pd.Series) -> dict:
    """Classify a non-word phoneme event as filler or stutter."""
    label = row["labels"].upper()
    duration = row["duration"]
    norm = re.sub(r"(.)\1+", r"\1", label)
    
    # Fillers
    if looks_like_filler(norm, duration):
        return {
            "type": "filler",
            "raw_label": label,
            "text": FILLER_MAP.get(norm, "uh"),
        }
    
    # Stutters
    if (
        norm in STUTTER_CONSONANTS
        and norm not in FILLER_MAP
        and duration < 0.15
    ):
        return {
            "type": "stutter",
            "raw_label": label,
            "text": norm.lower(),
        }
    
    return None


def detect_fillers_wav2vec(
    audio_path: str,
    df_aligned_words: pd.DataFrame
) -> pd.DataFrame:
    """
    Detect fillers and stutters using Wav2Vec2 phoneme detection.
    
    Args:
        audio_path: Path to audio file
        df_aligned_words: DataFrame with aligned word timestamps
        
    Returns:
        DataFrame with detected filler/stutter events
    """
    # Get phoneme-level events
    df_wav2vec = detect_phonemes_wav2vec(audio_path)
    
    if df_wav2vec.empty:
        return pd.DataFrame()
    
    # Filter out word overlaps
    df_wav2vec["overlaps_word"] = df_wav2vec.apply(
        lambda r: overlaps_any_word_relaxed(r["start"], r["end"], df_aligned_words),
        axis=1
    )
    
    df_non_word = df_wav2vec.loc[~df_wav2vec["overlaps_word"]].copy()
    
    # Handle word-initial sounds
    word_starts = df_aligned_words[["start"]].copy()
    
    df_non_word["is_word_initial"] = df_non_word.apply(
        lambda r: is_word_initial_candidate(r, word_starts),
        axis=1
    )
    
    df_non_word["suppress"] = df_non_word.apply(
        lambda r: r["is_word_initial"] and should_suppress_word_initial(r),
        axis=1
    )
    
    df_non_word = df_non_word.loc[~df_non_word["suppress"]].reset_index(drop=True)
    
    # Merge micro events
    df_non_word = merge_adjacent_events(df_non_word, max_gap=0.05)
    
    # Classify events
    converted = []
    for _, row in df_non_word.iterrows():
        result = classify_non_word_event(row)
        if result:
            converted.append({
                "type": result["type"],
                "text": result["text"],
                "raw_label": result["raw_label"],
                "start": row["start"],
                "end": row["end"],
                "duration": row["duration"],
            })
    
    return pd.DataFrame(converted)


# ==============================
# WHISPER FILLER DETECTION
# ==============================

def detect_fillers_whisper(verbatim_result: dict) -> pd.DataFrame:
    """
    Extract filler words from verbatim Whisper transcription.
    
    Args:
        verbatim_result: Whisper transcription result with verbatim prompt
        
    Returns:
        DataFrame with detected filler words
    """
    
    def normalize_whisper_token(token: str) -> str:
        token = token.lower().strip()
        return re.sub(r"^[^\w]+|[^\w]+$", "", token)
    
    whisper_fillers = []
    
    for seg in verbatim_result.get("segments", []):
        for w in seg.get("words", []):
            norm = normalize_whisper_token(w["word"])
            if norm and FILLER_REGEX.match(norm):
                whisper_fillers.append({
                    "style": "clear",
                    "type": "filler",
                    "text": norm,
                    "raw_label": w["word"],
                    "start": float(w["start"]),
                    "end": float(w["end"]),
                    "duration": float(w["end"] - w["start"]),
                    "confidence": float(w["probability"]),
                })
    
    return pd.DataFrame(whisper_fillers)


# ==============================
# MERGE & GROUP DETECTIONS
# ==============================

def overlaps_time(
    a_start: float,
    a_end: float,
    b_start: float,
    b_end: float,
    tol: float = 0.05
) -> bool:
    """Check if two time ranges overlap."""
    return (a_start < b_end + tol) and (a_end > b_start - tol)


def merge_filler_detections(
    df_whisper: pd.DataFrame,
    df_wav2vec: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge Whisper and Wav2Vec2 filler detections.
    Prioritizes Whisper (clear speech), backfills with Wav2Vec2 (subtle).
    
    Args:
        df_whisper: Fillers detected by Whisper
        df_wav2vec: Fillers detected by Wav2Vec2
        
    Returns:
        Combined DataFrame with all filler events
    """
    final_fillers = []
    
    # Add all Whisper detections first
    for _, wf in df_whisper.iterrows():
        final_fillers.append(wf.to_dict())
    
    # Add Wav2Vec2 detections that don't overlap
    for _, row in df_wav2vec.iterrows():
        duplicate = False
        
        for af in final_fillers:
            if overlaps_time(row["start"], row["end"], af["start"], af["end"]):
                duplicate = True
                break
        
        if not duplicate:
            entry = row.to_dict()
            entry["style"] = "subtle"
            final_fillers.append(entry)
    
    df = pd.DataFrame(final_fillers)
    
    if not df.empty:
        df = df.sort_values("start").reset_index(drop=True)
    
    return df


def group_stutters(df_fillers: pd.DataFrame) -> pd.DataFrame:
    """
    Group consecutive stutter repetitions.
    
    Args:
        df_fillers: DataFrame with all filler/stutter events
        
    Returns:
        DataFrame with stutters grouped by repetition
    """
    df_stutters = df_fillers[df_fillers["type"] == "stutter"].copy()
    df_other = df_fillers[df_fillers["type"] != "stutter"].copy()
    
    if df_stutters.empty:
        return df_fillers
    
    grouped = []
    current = None
    
    for _, row in df_stutters.sort_values("start").iterrows():
        if current is None:
            current = row.to_dict()
            current["count"] = 1
            continue
        
        same_sound = row["raw_label"] == current["raw_label"]
        close_in_time = row["start"] - current["end"] <= GROUP_GAP_SEC
        
        if same_sound and close_in_time:
            current["end"] = row["end"]
            current["duration"] = current["end"] - current["start"]
            current["count"] += 1
        else:
            grouped.append(current)
            current = row.to_dict()
            current["count"] = 1
    
    if current:
        grouped.append(current)
    
    df_grouped_stutters = pd.DataFrame(grouped)
    
    # Combine with other events
    df_final = (
        pd.concat([df_other, df_grouped_stutters], ignore_index=True)
        .sort_values("start")
        .reset_index(drop=True)
    )
    
    # Filter out very short single stutters
    df_final = df_final[
        ~(
            (df_final["type"] == "stutter") &
            (df_final["count"].fillna(1) < 2) &
            (df_final["duration"] < 0.15)
        )
    ].reset_index(drop=True)
    
    return df_final
