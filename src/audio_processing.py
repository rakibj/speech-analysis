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
        segments.append({
            "text": seg["text"].strip(),
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "duration": float(seg["end"] - seg["start"]),
            "avg_word_confidence": sum(
                [float(w["probability"]) for w in seg["words"]]
            ) / (len(seg["words"]) if len(seg["words"]) > 0 else 0.0)
        })
    
    return pd.DataFrame(segments)


if __name__ == "__main__":
    # Quick test
    audio_path = "sample4.flac"
    result = transcribe_with_whisper(audio_path)
    df_words = extract_words_dataframe(result)
    print(f"Transcribed {len(df_words)} words")
    print(df_words.head())