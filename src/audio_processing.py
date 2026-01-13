# src/audio_processing.py
"""Audio loading and transcription utilities."""
import torch
import torchaudio
import soundfile as sf
import whisper
import whisperx
import pandas as pd
from typing import Tuple


def load_audio(path: str) -> Tuple[any, int]:
    """
    Load audio file and convert to mono 16kHz.
    
    Args:
        path: Path to audio file
        
    Returns:
        Tuple of (audio_array, sample_rate)
    """
    audio, sr = sf.read(path, dtype="float32")
    
    # Convert stereo to mono
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    
    # Resample to 16kHz if needed
    if sr != 16000:
        audio_tensor = torch.from_numpy(audio)
        audio = torchaudio.functional.resample(
            audio_tensor, sr, 16000
        ).numpy()
        sr = 16000
    
    return audio, sr


def transcribe_with_whisper(
    audio_path: str,
    model_name: str = "base",
    device: str = "cpu"
) -> dict:
    """
    Transcribe audio using Whisper with word timestamps.
    
    Args:
        audio_path: Path to audio file
        model_name: Whisper model size
        device: Device to run on ('cpu' or 'cuda')
        
    Returns:
        Dictionary with segments and word-level timestamps
    """
    model = whisper.load_model(model_name, device=device)
    
    result = model.transcribe(
        audio_path,
        task="transcribe",
        word_timestamps=True,
        fp16=False,
    )
    
    return result


def transcribe_verbatim_fillers(
    audio_path: str,
    model_name: str = "base",
    device: str = "cpu"
) -> dict:
    """
    Transcribe with explicit focus on capturing filler words.
    
    Args:
        audio_path: Path to audio file
        model_name: Whisper model size
        device: Device to run on
        
    Returns:
        Dictionary with verbatim transcription including fillers
    """
    model = whisper.load_model(model_name, device=device)
    
    result = model.transcribe(
        audio_path,
        task="transcribe",
        temperature=0,
        word_timestamps=True,
        condition_on_previous_text=False,
        initial_prompt=(
            "Transcribe verbatim. Include filler words like um, uh, er, "
            "false starts, repetitions, and hesitations."
        ),
        fp16=False,
    )
    
    return result


def align_words_whisperx(
    segments: list,
    audio: any,
    language_code: str = "en",
    device: str = None
) -> pd.DataFrame:
    """
    Align word timestamps using WhisperX for better accuracy.
    
    Args:
        segments: Whisper transcription segments
        audio: Audio array
        language_code: Language code for alignment model
        device: Device to run on (auto-detected if None)
        
    Returns:
        DataFrame with aligned word timestamps
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    align_model, metadata = whisperx.load_align_model(
        language_code=language_code,
        device=device
    )
    
    aligned = whisperx.align(
        segments,
        align_model,
        metadata,
        audio,
        device
    )
    
    aligned_words = []
    for seg in aligned["segments"]:
        for w in seg.get("words", []):
            if w["start"] is not None and w["end"] is not None:
                aligned_words.append({
                    "word": w["word"].strip().lower(),
                    "start": float(w["start"]),
                    "end": float(w["end"])
                })
    
    df = pd.DataFrame(aligned_words)
    return df.sort_values("start").reset_index(drop=True)


def extract_words_dataframe(result: dict) -> pd.DataFrame:
    """
    Extract word-level data from Whisper result.
    
    Args:
        result: Whisper transcription result
        
    Returns:
        DataFrame with word timestamps and confidence scores
    """
    words = []
    for seg in result["segments"]:
        for w in seg["words"]:
            words.append({
                "word": w["word"].strip(),
                "start": float(w["start"]),
                "end": float(w["end"]),
                "duration": float(w["end"] - w["start"]),
                "confidence": float(w["probability"])
            })
    
    return pd.DataFrame(words)



def extract_segments_dataframe(result: dict) -> pd.DataFrame:
    """
    Extract segment-level data from Whisper result.
    
    Args:
        result: Whisper transcription result
        
    Returns:
        DataFrame with segment timestamps and average confidence
    """
    segments = []
    for seg in result["segments"]:
        # Handle empty word list
        if len(seg["words"]) > 0:
            avg_confidence = sum(
                [float(w["probability"]) for w in seg["words"]]
            ) / len(seg["words"])
        else:
            avg_confidence = 0.0
        
        segments.append({
            "text": seg["text"].strip(),
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "duration": float(seg["end"] - seg["start"]),
            "avg_word_confidence": avg_confidence
        })
    
    return pd.DataFrame(segments)
# Add to audio_processing.py or create a new utility file

import re
import pandas as pd
from typing import Set

# Comprehensive filler patterns
FILLER_PATTERNS = {
    # Basic fillers
    'um', 'umm', 'ummm', 'uhm', 'uhhmm',
    'uh', 'uhh', 'uhhh', 'er', 'err', 'errr',
    'ah', 'ahh', 'ahhh', 'eh', 'ehh', 'ehhh',
    
    # British/formal variants
    'erm', 'errm', 'errmm',
    
    # Elongated versions
    'uuuh', 'uuum', 'aaah', 'mmm', 'hmm', 'hmmm',
    
    # False starts / discourse markers (optional - tune based on your needs)
    'like', 'you know', 'i mean', 'sort of', 'kind of',
    'basically', 'actually', 'literally', 'right', 'okay', 'ok',
    'so', 'well', 'yeah', 'yep', 'yup', 'nope',
}

# More conservative set (exclude discourse markers)
CORE_FILLERS = {
    'um', 'umm', 'ummm', 'uhm', 'uhhmm',
    'uh', 'uhh', 'uhhh', 'er', 'err', 'errr',
    'ah', 'ahh', 'ahhh', 'eh', 'ehh', 'ehhh',
    'erm', 'errm', 'errmm',
    'uuuh', 'uuum', 'aaah', 'mmm', 'hmm', 'hmmm',
}


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
    # Remove leading/trailing punctuation and whitespace
    word = re.sub(r'^[^\w]+|[^\w]+$', '', word.lower().strip())
    
    # Collapse multiple spaces
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
        if re.fullmatch(r'u+h*m+', normalized):  # um, umm, uhhm
            return True
        if re.fullmatch(r'u+h+', normalized):  # uh, uhh, uhhh
            return True
        if re.fullmatch(r'e+r+m*', normalized):  # er, err, erm
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


if __name__ == "__main__":
    # Quick test
    audio_path = "sample4.flac"
    result = transcribe_with_whisper(audio_path)
    df_words = extract_words_dataframe(result)
    print(f"Transcribed {len(df_words)} words")
    print(df_words.head())